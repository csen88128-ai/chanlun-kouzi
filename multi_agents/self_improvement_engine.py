#!/usr/bin/env python3
"""
自我改进引擎 - 生成改进建议和学习计划
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from multi_agents.knowledge_manager import KnowledgeManager
from multi_agents.skill_evaluator import SkillEvaluator
from multi_agents.execution_monitor import ExecutionMonitor


class Priority(Enum):
    """优先级"""
    CRITICAL = "紧急"
    HIGH = "高"
    MEDIUM = "中"
    LOW = "低"


@dataclass
class ImprovementAction:
    """改进行动"""
    id: str                       # 行动ID
    agent_type: str               # 智能体类型
    action_type: str              # 行动类型（学习/优化/修复）
    description: str              # 描述
    priority: Priority            # 优先级
    estimated_effort: str         # 预估工作量
    expected_impact: str          # 预期影响
    learning_resources: List[str] # 学习资源
    acceptance_criteria: str      # 验收标准
    status: str                   # 状态（待办/进行中/已完成）
    created_at: str              # 创建时间
    updated_at: str              # 更新时间


class SelfImprovementEngine:
    """自我改进引擎"""

    def __init__(self):
        self.knowledge_manager = KnowledgeManager()
        self.skill_evaluator = SkillEvaluator()
        self.execution_monitor = ExecutionMonitor()
        self.actions: List[ImprovementAction] = []
        self.actions_file = "/workspace/projects/data/improvement_actions.json"
        self._load_actions()

    def _load_actions(self):
        """加载改进行动"""
        try:
            with open(self.actions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.actions = [ImprovementAction(**item) for item in data]
        except FileNotFoundError:
            self.actions = []
        except Exception as e:
            print(f"加载改进行动失败: {e}")
            self.actions = []

    def _save_actions(self):
        """保存改进行动"""
        try:
            with open(self.actions_file, 'w', encoding='utf-8') as f:
                json.dump([asdict(action) for action in self.actions], f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存改进行动失败: {e}")

    def analyze_and_generate_actions(self) -> List[ImprovementAction]:
        """分析所有智能体并生成改进行动"""
        new_actions = []

        # 1. 分析知识缺口
        knowledge_gaps = self.knowledge_manager.identify_knowledge_gaps()
        for gap in knowledge_gaps:
            agent_type = gap["agent_type"]
            for item in gap["improvement_items"]:
                if item["confidence"] < 0.8:  # 只处理置信度低的
                    action = ImprovementAction(
                        id=f"{agent_type}_knowledge_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        agent_type=agent_type,
                        action_type="学习",
                        description=f"完善知识: {item['concept']} (当前掌握度{item['confidence']})",
                        priority=Priority.HIGH if item["confidence"] < 0.6 else Priority.MEDIUM,
                        estimated_effort="2-4小时",
                        expected_impact="提升准确性5-10%",
                        learning_resources=item.get("learning_resources", []),
                        acceptance_criteria=f"{item['concept']}知识完整度>90%",
                        status="待办",
                        created_at=datetime.now().isoformat(),
                        updated_at=datetime.now().isoformat()
                    )
                    new_actions.append(action)

        # 2. 分析技能差距
        skill_gaps = self.skill_evaluator.get_improvement_priority()
        for gap in skill_gaps[:5]:  # 只处理前5个
            agent_type = gap["agent_type"]
            action = ImprovementAction(
                id=f"{agent_type}_skill_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                agent_type=agent_type,
                action_type="优化",
                description=f"提升技能: {gap['metric_name']} (当前{gap['current_value']}, 目标{gap['target_value']})",
                priority=Priority.CRITICAL if gap["priority"] == "高" else Priority.HIGH,
                estimated_effort="4-8小时",
                expected_impact=f"提升{gap['gap']}分",
                learning_resources=[],
                acceptance_criteria=f"{gap['metric_name']}得分>{gap['target_value']}",
                status="待办",
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )
            new_actions.append(action)

        # 3. 分析执行问题
        improvement_candidates = self.execution_monitor.get_improvement_candidates()
        for candidate in improvement_candidates:
            agent_type = candidate["agent_type"]
            for reason in candidate["reasons"]:
                action = ImprovementAction(
                    id=f"{agent_type}_execution_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    agent_type=agent_type,
                    action_type="修复",
                    description=f"修复执行问题: {reason}",
                    priority=Priority.CRITICAL if candidate["priority"] == "高" else Priority.HIGH,
                    estimated_effort="1-3小时",
                    expected_impact="提升成功率10-20%",
                    learning_resources=[],
                    acceptance_criteria="成功率>95%",
                    status="待办",
                    created_at=datetime.now().isoformat(),
                    updated_at=datetime.now().isoformat()
                )
                new_actions.append(action)

        # 去重（基于描述）
        existing_descriptions = {a.description for a in self.actions}
        unique_new_actions = [a for a in new_actions if a.description not in existing_descriptions]

        # 添加到行动列表
        self.actions.extend(unique_new_actions)
        self._save_actions()

        return unique_new_actions

    def get_learning_plan(self, agent_type: str) -> Dict[str, Any]:
        """生成学习计划"""
        # 获取知识缺口
        knowledge_gaps = self.knowledge_manager.check_completeness(agent_type)
        # 获取技能差距
        skill_eval = self.skill_evaluator.evaluate_agent(agent_type)
        # 获取待办行动
        pending_actions = [a for a in self.actions if a.agent_type == agent_type and a.status == "待办"]

        # 按优先级排序
        pending_actions.sort(key=lambda x: {
            Priority.CRITICAL: 4,
            Priority.HIGH: 3,
            Priority.MEDIUM: 2,
            Priority.LOW: 1
        }.get(x.priority, 0), reverse=True)

        # 估算总工作量
        total_effort_hours = 0
        for action in pending_actions:
            if "2-4小时" in action.estimated_effort:
                total_effort_hours += 3
            elif "4-8小时" in action.estimated_effort:
                total_effort_hours += 6
            elif "1-3小时" in action.estimated_effort:
                total_effort_hours += 2

        # 估算完成时间（假设每天2小时）
        days_needed = (total_effort_hours / 2).__ceil__() if total_effort_hours > 0 else 0

        return {
            "agent_type": agent_type,
            "knowledge_completeness": knowledge_gaps["completeness_rate"],
            "skill_level": skill_eval["level"],
            "skill_score": skill_eval["average_score"],
            "pending_actions_count": len(pending_actions),
            "pending_actions": [
                {
                    "id": a.id,
                    "action_type": a.action_type,
                    "description": a.description,
                    "priority": a.priority.value,
                    "effort": a.estimated_effort,
                    "impact": a.expected_impact,
                    "resources": a.learning_resources
                }
                for a in pending_actions[:10]
            ],
            "total_effort_hours": total_effort_hours,
            "estimated_days": days_needed,
            "learning_resources": list(set(
                [r for a in pending_actions for r in a.learning_resources]
            ))
        }

    def update_action_status(self, action_id: str, status: str, notes: str = ""):
        """更新行动状态"""
        for action in self.actions:
            if action.id == action_id:
                action.status = status
                action.updated_at = datetime.now().isoformat()
                if notes:
                    action.description += f"\n更新: {notes}"
                break

        self._save_actions()

    def generate_system_report(self) -> Dict[str, Any]:
        """生成系统改进报告"""
        # 知识库摘要
        knowledge_summary = self.knowledge_manager.get_summary()

        # 技能评估摘要
        skill_summary = self.skill_evaluator.get_all_evaluations()

        # 执行统计摘要
        execution_summary = self.execution_monitor.get_all_stats()

        # 改进行动统计
        total_actions = len(self.actions)
        pending_actions = sum(1 for a in self.actions if a.status == "待办")
        in_progress_actions = sum(1 for a in self.actions if a.status == "进行中")
        completed_actions = sum(1 for a in self.actions if a.status == "已完成")

        # 按优先级统计
        priority_counts = {
            "紧急": sum(1 for a in self.actions if a.priority == Priority.CRITICAL and a.status != "已完成"),
            "高": sum(1 for a in self.actions if a.priority == Priority.HIGH and a.status != "已完成"),
            "中": sum(1 for a in self.actions if a.priority == Priority.MEDIUM and a.status != "已完成"),
            "低": sum(1 for a in self.actions if a.priority == Priority.LOW and a.status != "已完成")
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "knowledge": {
                "overall_completeness": knowledge_summary["overall_completeness"],
                "total_items": knowledge_summary["total_knowledge_items"],
                "complete": knowledge_summary["complete"],
                "needs_improvement": knowledge_summary["partial"] + knowledge_summary["missing"] + knowledge_summary["outdated"]
            },
            "skills": {
                "overall_average": skill_summary["overall_average"],
                "needs_improvement": skill_summary["needs_improvement"],
                "top_priorities": [
                    {
                        "agent_type": agent,
                        "score": evaluation["average_score"],
                        "needs_improvement": evaluation["needs_improvement"]
                    }
                    for agent, evaluation in skill_summary["agent_evaluations"].items()
                ]
            },
            "execution": {
                "total_executions": execution_summary["total_executions"],
                "overall_success_rate": execution_summary["overall_success_rate"],
                "needs_improvement": execution_summary["overall_success_rate"] < 95
            },
            "improvements": {
                "total_actions": total_actions,
                "pending": pending_actions,
                "in_progress": in_progress_actions,
                "completed": completed_actions,
                "by_priority": priority_counts
            },
            "overall_health": "健康" if (
                knowledge_summary["overall_completeness"] > 80 and
                skill_summary["overall_average"] > 80 and
                execution_summary["overall_success_rate"] > 90
            ) else "需要改进"
        }
