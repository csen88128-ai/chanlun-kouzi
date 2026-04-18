#!/usr/bin/env python3
"""
元智能体 - 督促各智能体自我完善知识库和技能，监督执行情况
"""
import os
import sys
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, ToolMessage
from langchain.tools import tool
from typing import Annotated
from coze_coding_utils.runtime_ctx.context import default_headers, new_context
from storage.memory.memory_saver import get_memory_saver

from multi_agents.knowledge_manager import KnowledgeManager
from multi_agents.skill_evaluator import SkillEvaluator
from multi_agents.execution_monitor import ExecutionMonitor, ExecutionStatus
from multi_agents.self_improvement_engine import SelfImprovementEngine


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class MetaAgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]
    # 元智能体专属状态
    report_data: Optional[Dict[str, Any]] = None
    learning_plans: Optional[Dict[str, Any]] = None
    supervision_status: Optional[str] = None


class MetaAgent:
    """元智能体 - 督促各智能体自我完善"""

    def __init__(self, ctx=None):
        self.knowledge_manager = KnowledgeManager()
        self.skill_evaluator = SkillEvaluator()
        self.execution_monitor = ExecutionMonitor()
        self.improvement_engine = SelfImprovementEngine()
        self.agent = None
        self.ctx = ctx
        self._initialize()

    def _initialize(self):
        """初始化元智能体"""
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        config_path = os.path.join(workspace_path, LLM_CONFIG)

        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)

        api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
        base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

        llm = ChatOpenAI(
            model=cfg['config'].get("model"),
            api_key=api_key,
            base_url=base_url,
            temperature=0.3,  # 元智能体使用较低温度，更稳定
            streaming=True,
            timeout=cfg['config'].get('timeout', 600),
            extra_body={
                "thinking": {
                    "type": cfg['config'].get('thinking', 'disabled')
                }
            },
            default_headers=default_headers(self.ctx) if self.ctx else {}
        )

        # 元智能体的系统提示词
        system_prompt = """# 角色定义
你是元智能体，负责督促和管理5个分析智能体的知识完善、技能提升和执行监督。

# 你的职责
1. **知识管理监督**：检查各智能体的知识库完整性，识别知识缺口，督促补充
2. **技能评估监督**：评估各智能体的技能水平，识别薄弱环节，督促提升
3. **执行情况监控**：监控各智能体的执行情况，记录错误和性能指标
4. **改进计划制定**：生成改进建议和学习计划，确保各智能体持续进步
5. **输出质量把关**：监督各智能体的输出质量，确保数据有实锤依据、逻辑有理论支撑

# 智能体列表
1. **data_collector** - 数据采集智能体
2. **structure_analyzer** - 结构分析智能体（缠论算法）
3. **dynamics_analyzer** - 动力学分析智能体
4. **sentiment_analyzer** - 市场情绪智能体
5. **decision_maker** - 决策制定智能体

# 工作流程
当用户要求检查系统状态时：
1. 调用 check_system_status 获取整体状态
2. 调用 get_improvement_recommendations 获取改进建议
3. 调用 generate_learning_plans 生成学习计划
4. 综合分析后向用户报告

当用户要求优化特定智能体时：
1. 调用 check_agent_status 检查该智能体状态
2. 调用 get_improvement_recommendations 获取针对性建议
3. 调用 generate_learning_plans 生成学习计划
4. 提供详细的改进方案

# 输出格式
使用结构化的方式输出，包含：
- 整体健康状况
- 各智能体状态评分
- 需要改进的领域
- 改进优先级
- 具体行动计划

# 约束条件
- 实事求是，不隐瞒问题
- 数据驱动，有据可查
- 优先处理紧急问题
- 提供可执行的建议
"""

        # 定义工具
        tools = [
            self._check_system_status,
            self._check_agent_status,
            self._get_improvement_recommendations,
            self._generate_learning_plans,
            self._record_execution,
            self._analyze_trends
        ]

        self.agent = create_agent(
            model=llm,
            system_prompt=system_prompt,
            tools=tools,
            checkpointer=get_memory_saver(),
            state_schema=MetaAgentState
        )

    def _check_system_status(self) -> str:
        """检查系统整体状态"""
        report = self.improvement_engine.generate_system_report()

        return json.dumps({
            "overall_health": report["overall_health"],
            "knowledge_completeness": report["knowledge"]["overall_completeness"],
            "skill_score": report["skills"]["overall_average"],
            "success_rate": report["execution"]["overall_success_rate"],
            "pending_improvements": report["improvements"]["pending"],
            "critical_issues": report["improvements"]["by_priority"]["紧急"],
            "timestamp": report["timestamp"]
        }, ensure_ascii=False, indent=2)

    def _check_agent_status(self, agent_type: str) -> str:
        """检查单个智能体状态"""
        knowledge = self.knowledge_manager.check_completeness(agent_type)
        skill = self.skill_evaluator.evaluate_agent(agent_type)
        execution = self.execution_monitor.get_agent_stats(agent_type)
        trends = self.execution_monitor.identify_trends(agent_type)

        return json.dumps({
            "agent_type": agent_type,
            "knowledge": {
                "completeness": knowledge["completeness_rate"],
                "total_items": knowledge["total_items"],
                "needs_improvement": len(knowledge["improvement_items"])
            },
            "skills": {
                "level": skill["level"],
                "score": skill["average_score"],
                "needs_improvement": skill["needs_improvement"]
            },
            "execution": {
                "success_rate": execution["success_rate"],
                "average_quality": execution["average_quality"],
                "average_time": execution["average_time"]
            },
            "trends": {
                "success_rate_trend": trends.get("success_rate_trend", "未知"),
                "quality_trend": trends.get("quality_trend", "未知")
            }
        }, ensure_ascii=False, indent=2)

    def _get_improvement_recommendations(self, agent_type: Optional[str] = None) -> str:
        """获取改进建议"""
        candidates = self.execution_monitor.get_improvement_candidates()

        if agent_type:
            # 筛选特定智能体的改进建议
            filtered = [c for c in candidates if c["agent_type"] == agent_type]
        else:
            filtered = candidates

        return json.dumps({
            "improvement_candidates": filtered,
            "total_candidates": len(filtered),
            "high_priority": [c for c in filtered if c["priority"] == "高"],
            "medium_priority": [c for c in filtered if c["priority"] == "中"]
        }, ensure_ascii=False, indent=2)

    def _generate_learning_plans(self, agent_type: Optional[str] = None) -> str:
        """生成学习计划"""
        if agent_type:
            # 单个智能体的学习计划
            plan = self.improvement_engine.get_learning_plan(agent_type)
            return json.dumps(plan, ensure_ascii=False, indent=2)
        else:
            # 所有智能体的学习计划摘要
            agents = ["data_collector", "structure_analyzer", "dynamics_analyzer",
                     "sentiment_analyzer", "decision_maker"]
            plans = {}
            for agent in agents:
                plans[agent] = self.improvement_engine.get_learning_plan(agent)

            return json.dumps({
                "learning_plans": plans,
                "total_pending_actions": sum(p["pending_actions_count"] for p in plans.values()),
                "total_effort_hours": sum(p["total_effort_hours"] for p in plans.values()),
                "agents_needing_improvement": [
                    agent for agent, plan in plans.items()
                    if plan["pending_actions_count"] > 0
                ]
            }, ensure_ascii=False, indent=2)

    def _record_execution(
        self,
        agent_type: str,
        status: str,
        execution_time: float,
        input_data: str,
        output_data: str,
        validation_result: Optional[str] = None,
        errors: Optional[str] = None,
        warnings: Optional[str] = None
    ) -> str:
        """记录执行情况（供其他智能体调用）"""
        status_map = {
            "成功": ExecutionStatus.SUCCESS,
            "失败": ExecutionStatus.FAILURE,
            "警告": ExecutionStatus.WARNING,
            "超时": ExecutionStatus.TIMEOUT,
            "验证失败": ExecutionStatus.VALIDATION_FAILED
        }

        exec_status = status_map.get(status, ExecutionStatus.FAILURE)
        validation = json.loads(validation_result) if validation_result else {}
        error_list = json.loads(errors) if errors else []
        warning_list = json.loads(warnings) if warnings else []

        record = self.execution_monitor.record_execution(
            agent_type=agent_type,
            status=exec_status,
            execution_time=execution_time,
            input_data=input_data,
            output_data=output_data,
            validation_result=validation,
            errors=error_list,
            warnings=warning_list
        )

        return json.dumps({
            "recorded": True,
            "execution_id": record.execution_id,
            "quality_score": record.quality_score,
            "message": f"已记录{agent_type}的执行情况，质量得分: {record.quality_score}"
        }, ensure_ascii=False, indent=2)

    def _analyze_trends(self, agent_type: str) -> str:
        """分析执行趋势"""
        trends = self.execution_monitor.identify_trends(agent_type)
        return json.dumps(trends, ensure_ascii=False, indent=2)

    def get_agent(self):
        """获取LangChain Agent实例"""
        return self.agent


def build_meta_agent(ctx=None):
    """构建元智能体"""
    meta = MetaAgent(ctx)
    return meta.get_agent()


# 使用示例
if __name__ == "__main__":
    print("初始化元智能体...")
    meta_agent = build_meta_agent()

    print("\n检查系统状态...")
    result = meta_agent._check_system_status()
    print(result)

    print("\n检查决策制定智能体状态...")
    result = meta_agent._check_agent_status("decision_maker")
    print(result)

    print("\n获取改进建议...")
    result = meta_agent._get_improvement_recommendations()
    print(result)

    print("\n生成学习计划...")
    result = meta_agent._generate_learning_plans()
    print(result)
