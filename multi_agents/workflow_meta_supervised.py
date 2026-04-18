#!/usr/bin/env python3
"""
带元智能体的监督工作流 - 完整的多智能体协作框架
"""
import os
import sys
import json
import time
from typing import TypedDict, Annotated
from datetime import datetime

sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from storage.memory.memory_saver import get_memory_saver

from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.structure_analyzer_agent_v2 import build_agent as build_structure_analyzer
from multi_agents.dynamics_analyzer_agent import build_agent as build_dynamics_analyzer
from multi_agents.sentiment_analyzer_agent import build_agent as build_sentiment_analyzer
from multi_agents.decision_maker_agent_v3 import build_agent as build_decision_maker
from multi_agents.supervisor import Supervisor
from multi_agents.data_validator import DataValidator
from multi_agents.logic_validator import LogicValidator
from multi_agents.execution_monitor import ExecutionMonitor, ExecutionStatus
from multi_agents.meta_agent import MetaAgent


class WorkflowState(TypedDict):
    """工作流状态"""
    messages: Annotated[list, add_messages]

    # 各阶段数据
    data_collector_output: str
    structure_analyzer_output: str
    dynamics_analyzer_output: str
    sentiment_analyzer_output: str
    decision_maker_output: str

    # 验证结果
    data_validation: dict
    structure_validation: dict
    dynamics_validation: dict
    sentiment_validation: dict
    decision_validation: dict

    # 元智能体报告
    meta_report: dict

    # 执行统计
    execution_times: dict
    validation_results: dict

    # 最终输出
    final_report: str

    # 错误信息
    errors: list


class MetaSupervisedWorkflow:
    """带元智能体的监督工作流"""

    def __init__(self):
        # 初始化智能体
        self.data_collector = build_data_collector()
        self.structure_analyzer = build_structure_analyzer()
        self.dynamics_analyzer = build_dynamics_analyzer()
        self.sentiment_analyzer = build_sentiment_analyzer()
        self.decision_maker = build_decision_maker()

        # 初始化验证器
        self.data_validator = DataValidator()
        self.logic_validator = LogicValidator()
        self.supervisor = Supervisor()

        # 初始化执行监控器
        self.execution_monitor = ExecutionMonitor()

        # 初始化元智能体
        self.meta_agent = MetaAgent()

        # 构建工作流图
        self.graph = self._build_graph()

    def _build_graph(self):
        """构建工作流图"""
        workflow = StateGraph(WorkflowState)

        # 添加节点
        workflow.add_node("data_collector", self._data_collector_node)
        workflow.add_node("validate_data", self._validate_data_node)
        workflow.add_node("structure_analyzer", self._structure_analyzer_node)
        workflow.add_node("validate_structure", self._validate_structure_node)
        workflow.add_node("dynamics_analyzer", self._dynamics_analyzer_node)
        workflow.add_node("validate_dynamics", self._validate_dynamics_node)
        workflow.add_node("sentiment_analyzer", self._sentiment_analyzer_node)
        workflow.add_node("validate_sentiment", self._validate_sentiment_node)
        workflow.add_node("decision_maker", self._decision_maker_node)
        workflow.add_node("validate_decision", self._validate_decision_node)
        workflow.add_node("meta_supervision", self._meta_supervision_node)
        workflow.add_node("generate_report", self._generate_report_node)

        # 定义边
        workflow.set_entry_point("data_collector")

        workflow.add_edge("data_collector", "validate_data")
        workflow.add_conditional_edges(
            "validate_data",
            self._should_continue_data,
            {
                "continue": "structure_analyzer",
                "reject": "generate_report"
            }
        )

        workflow.add_edge("structure_analyzer", "validate_structure")
        workflow.add_conditional_edges(
            "validate_structure",
            self._should_continue_structure,
            {
                "continue": "dynamics_analyzer",
                "reject": "generate_report"
            }
        )

        workflow.add_edge("dynamics_analyzer", "validate_dynamics")
        workflow.add_conditional_edges(
            "validate_dynamics",
            self._should_continue_dynamics,
            {
                "continue": "sentiment_analyzer",
                "reject": "generate_report"
            }
        )

        workflow.add_edge("sentiment_analyzer", "validate_sentiment")
        workflow.add_conditional_edges(
            "validate_sentiment",
            self._should_continue_sentiment,
            {
                "continue": "decision_maker",
                "reject": "generate_report"
            }
        )

        workflow.add_edge("decision_maker", "validate_decision")
        workflow.add_conditional_edges(
            "validate_decision",
            self._should_continue_decision,
            {
                "continue": "meta_supervision",
                "reject": "generate_report"
            }
        )

        workflow.add_edge("meta_supervision", "generate_report")
        workflow.add_edge("generate_report", END)

        return workflow.compile(checkpointer=get_memory_saver())

    def _data_collector_node(self, state: WorkflowState):
        """数据采集节点"""
        start_time = time.time()
        print("\n[数据采集智能体] 开始执行...")

        try:
            # 直接调用智能体获取数据
            config = {"configurable": {"thread_id": "btc_analysis"}}
            response = self.data_collector.invoke(
                {"messages": [HumanMessage(content="获取BTCUSDT 4小时K线数据，200根。请返回JSON格式的数据摘要。")]},
                config
            )

            output = response["messages"][-1].content if response["messages"] else ""
            execution_time = time.time() - start_time

            # 尝试从输出中提取JSON
            import re
            json_match = re.search(r'\{[\s\S]*\}', output)
            if json_match:
                output = json_match.group(0)
            else:
                # 如果找不到JSON，尝试解析整个输出
                try:
                    json.loads(output)
                except:
                    pass  # 保持原样

            print(f"[数据采集智能体] 执行完成，耗时: {execution_time:.2f}秒")

            # 记录执行
            try:
                self.execution_monitor.record_execution(
                    agent_type="data_collector",
                    status=ExecutionStatus.SUCCESS,
                    execution_time=execution_time,
                    input_data="获取BTCUSDT 4小时K线数据，200根",
                    output_data=output[:500],
                    errors=[],
                    warnings=[]
                )
            except:
                pass  # 忽略记录错误

            return {
                **state,
                "data_collector_output": output,
                "execution_times": {**state.get("execution_times", {}), "data_collector": execution_time}
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[数据采集智能体] 执行失败: {error_msg}")

            try:
                self.execution_monitor.record_execution(
                    agent_type="data_collector",
                    status=ExecutionStatus.FAILURE,
                    execution_time=time.time() - start_time,
                    input_data="获取BTCUSDT 4小时K线数据，200根",
                    output_data="",
                    errors=[error_msg],
                    warnings=[]
                )
            except:
                pass

            return {
                **state,
                "errors": state.get("errors", []) + [f"data_collector: {error_msg}"],
                "data_collector_output": ""
            }

    def _validate_data_node(self, state: WorkflowState):
        """验证数据采集结果"""
        print("\n[数据验证器] 验证数据采集结果...")

        validation = self.data_validator.validate_data(state["data_collector_output"], "data_collector")

        # 记录验证结果
        validation_results = state.get("validation_results", {})
        validation_results["data"] = validation

        return {
            **state,
            "data_validation": validation,
            "validation_results": validation_results
        }

    def _should_continue_data(self, state: WorkflowState):
        """决定是否继续"""
        validation = state["data_validation"]

        if validation["status"] == "CRITICAL" or validation["status"] == "ERROR":
            print(f"[数据验证器] 验证失败 ({validation['status']}): {validation['message']}")
            return "reject"

        print(f"[数据验证器] 验证通过 ({validation['status']})")
        return "continue"

    def _structure_analyzer_node(self, state: WorkflowState):
        """结构分析节点"""
        start_time = time.time()
        print("\n[结构分析智能体] 开始执行...")

        try:
            # 调用智能体
            config = {"configurable": {"thread_id": "btc_analysis"}}
            response = self.structure_analyzer.invoke(
                {"messages": [HumanMessage(content=state["data_collector_output"])]},
                config
            )

            output = response["messages"][-1].content if response["messages"] else ""
            execution_time = time.time() - start_time

            print(f"[结构分析智能体] 执行完成，耗时: {execution_time:.2f}秒")

            # 记录执行
            self.execution_monitor.record_execution(
                agent_type="structure_analyzer",
                status=ExecutionStatus.SUCCESS,
                execution_time=execution_time,
                input_data=state["data_collector_output"][:500],
                output_data=output[:500],
                errors=[],
                warnings=[]
            )

            return {
                **state,
                "structure_analyzer_output": output,
                "execution_times": {**state.get("execution_times", {}), "structure_analyzer": execution_time}
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[结构分析智能体] 执行失败: {error_msg}")

            self.execution_monitor.record_execution(
                agent_type="structure_analyzer",
                status=ExecutionStatus.FAILURE,
                execution_time=time.time() - start_time,
                input_data=state["data_collector_output"][:500],
                output_data="",
                errors=[error_msg],
                warnings=[]
            )

            return {
                **state,
                "errors": state.get("errors", []) + [f"structure_analyzer: {error_msg}"],
                "structure_analyzer_output": ""
            }

    def _validate_structure_node(self, state: WorkflowState):
        """验证结构分析结果"""
        print("\n[逻辑验证器] 验证结构分析结果...")

        # 验证缠论结构分析
        validation_result = self.logic_validator.validate_chanlun(state["structure_analyzer_output"], None)

        # 统计验证结果
        status_counts = {
            "通过": 0,
            "警告": 0,
            "错误": 0,
            "严重错误": 0
        }

        for v in validation_result:
            level_value = v.level.value
            if level_value in status_counts:
                status_counts[level_value] += 1

        # 确定整体状态
        if status_counts["严重错误"] > 0:
            overall_status = "CRITICAL"
        elif status_counts["错误"] > 0:
            overall_status = "ERROR"
        elif status_counts["警告"] > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

        validation = {
            "status": overall_status,
            "category": "structure",
            "message": f"验证完成: {status_counts['通过']}通过, {status_counts['警告']}警告, {status_counts['错误']}错误, {status_counts['严重错误']}严重",
            "validations": [
                {
                    "item": v.item,
                    "level": v.level.value,
                    "message": v.message,
                    "theory": v.theory,
                    "calculation": v.calculation,
                    "expected": str(v.expected),
                    "actual": str(v.actual),
                    "evidence": v.evidence
                }
                for v in validation_result
            ],
            "counts": status_counts,
            "pass": status_counts["通过"],
            "warning": status_counts["警告"],
            "error": status_counts["错误"],
            "critical": status_counts["严重错误"]
        }

        # 记录验证结果
        validation_results = state.get("validation_results", {})
        validation_results["structure"] = validation

        return {
            **state,
            "structure_validation": validation,
            "validation_results": validation_results
        }

    def _should_continue_structure(self, state: WorkflowState):
        """决定是否继续"""
        validation = state["structure_validation"]

        if validation["status"] == "CRITICAL" or validation["status"] == "ERROR":
            print(f"[逻辑验证器] 验证失败 ({validation['status']}): {validation['message']}")
            return "reject"

        print(f"[逻辑验证器] 验证通过 ({validation['status']})")
        return "continue"

    def _dynamics_analyzer_node(self, state: WorkflowState):
        """动力学分析节点"""
        start_time = time.time()
        print("\n[动力学分析智能体] 开始执行...")

        try:
            # 调用智能体
            config = {"configurable": {"thread_id": "btc_analysis"}}
            response = self.dynamics_analyzer.invoke(
                {"messages": [HumanMessage(content=state["data_collector_output"])]},
                config
            )

            output = response["messages"][-1].content if response["messages"] else ""
            execution_time = time.time() - start_time

            print(f"[动力学分析智能体] 执行完成，耗时: {execution_time:.2f}秒")

            # 记录执行
            self.execution_monitor.record_execution(
                agent_type="dynamics_analyzer",
                status=ExecutionStatus.SUCCESS,
                execution_time=execution_time,
                input_data=state["data_collector_output"][:500],
                output_data=output[:500],
                errors=[],
                warnings=[]
            )

            return {
                **state,
                "dynamics_analyzer_output": output,
                "execution_times": {**state.get("execution_times", {}), "dynamics_analyzer": execution_time}
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[动力学分析智能体] 执行失败: {error_msg}")

            self.execution_monitor.record_execution(
                agent_type="dynamics_analyzer",
                status=ExecutionStatus.FAILURE,
                execution_time=time.time() - start_time,
                input_data=state["data_collector_output"][:500],
                output_data="",
                errors=[error_msg],
                warnings=[]
            )

            return {
                **state,
                "errors": state.get("errors", []) + [f"dynamics_analyzer: {error_msg}"],
                "dynamics_analyzer_output": ""
            }

    def _validate_dynamics_node(self, state: WorkflowState):
        """验证动力学分析结果"""
        print("\n[逻辑验证器] 验证动力学分析结果...")

        # 验证动力学分析
        validation_result = self.logic_validator.validate_dynamics(state["dynamics_analyzer_output"], None)

        # 统计验证结果
        status_counts = {
            "通过": 0,
            "警告": 0,
            "错误": 0,
            "严重错误": 0
        }

        for v in validation_result:
            level_value = v.level.value
            if level_value in status_counts:
                status_counts[level_value] += 1

        # 确定整体状态
        if status_counts["严重错误"] > 0:
            overall_status = "CRITICAL"
        elif status_counts["错误"] > 0:
            overall_status = "ERROR"
        elif status_counts["警告"] > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

        validation = {
            "status": overall_status,
            "category": "dynamics",
            "message": f"验证完成: {status_counts['通过']}通过, {status_counts['警告']}警告, {status_counts['错误']}错误, {status_counts['严重错误']}严重",
            "validations": [
                {
                    "item": v.item,
                    "level": v.level.value,
                    "message": v.message,
                    "theory": v.theory,
                    "calculation": v.calculation,
                    "expected": str(v.expected),
                    "actual": str(v.actual),
                    "evidence": v.evidence
                }
                for v in validation_result
            ],
            "counts": status_counts,
            "pass": status_counts["通过"],
            "warning": status_counts["警告"],
            "error": status_counts["错误"],
            "critical": status_counts["严重错误"]
        }

        # 记录验证结果
        validation_results = state.get("validation_results", {})
        validation_results["dynamics"] = validation

        return {
            **state,
            "dynamics_validation": validation,
            "validation_results": validation_results
        }

    def _should_continue_dynamics(self, state: WorkflowState):
        """决定是否继续"""
        validation = state["dynamics_validation"]

        if validation["status"] == "CRITICAL" or validation["status"] == "ERROR":
            print(f"[逻辑验证器] 验证失败 ({validation['status']}): {validation['message']}")
            return "reject"

        print(f"[逻辑验证器] 验证通过 ({validation['status']})")
        return "continue"

    def _sentiment_analyzer_node(self, state: WorkflowState):
        """市场情绪分析节点"""
        start_time = time.time()
        print("\n[市场情绪智能体] 开始执行...")

        try:
            # 调用智能体
            config = {"configurable": {"thread_id": "btc_analysis"}}
            response = self.sentiment_analyzer.invoke(
                {"messages": [HumanMessage(content="获取当前BTC市场的恐惧贪婪指数")]},
                config
            )

            output = response["messages"][-1].content if response["messages"] else ""
            execution_time = time.time() - start_time

            print(f"[市场情绪智能体] 执行完成，耗时: {execution_time:.2f}秒")

            # 记录执行
            self.execution_monitor.record_execution(
                agent_type="sentiment_analyzer",
                status=ExecutionStatus.SUCCESS,
                execution_time=execution_time,
                input_data="获取当前BTC市场的恐惧贪婪指数",
                output_data=output[:500],
                errors=[],
                warnings=[]
            )

            return {
                **state,
                "sentiment_analyzer_output": output,
                "execution_times": {**state.get("execution_times", {}), "sentiment_analyzer": execution_time}
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[市场情绪智能体] 执行失败: {error_msg}")

            self.execution_monitor.record_execution(
                agent_type="sentiment_analyzer",
                status=ExecutionStatus.FAILURE,
                execution_time=time.time() - start_time,
                input_data="获取当前BTC市场的恐惧贪婪指数",
                output_data="",
                errors=[error_msg],
                warnings=[]
            )

            return {
                **state,
                "errors": state.get("errors", []) + [f"sentiment_analyzer: {error_msg}"],
                "sentiment_analyzer_output": ""
            }

    def _validate_sentiment_node(self, state: WorkflowState):
        """验证市场情绪分析结果"""
        print("\n[逻辑验证器] 验证市场情绪分析结果...")

        validation = self.data_validator.validate_data(state["sentiment_analyzer_output"], "sentiment_analyzer")

        # 记录验证结果
        validation_results = state.get("validation_results", {})
        validation_results["sentiment"] = validation

        return {
            **state,
            "sentiment_validation": validation,
            "validation_results": validation_results
        }

    def _should_continue_sentiment(self, state: WorkflowState):
        """决定是否继续"""
        validation = state["sentiment_validation"]

        if validation["status"] == "CRITICAL" or validation["status"] == "ERROR":
            print(f"[逻辑验证器] 验证失败 ({validation['status']}): {validation['message']}")
            return "reject"

        print(f"[逻辑验证器] 验证通过 ({validation['status']})")
        return "continue"

    def _decision_maker_node(self, state: WorkflowState):
        """决策制定节点"""
        start_time = time.time()
        print("\n[决策制定智能体] 开始执行...")

        # 合并所有分析结果
        input_msg = f"""基于以下分析结果制定交易决策:

数据采集结果:
{state['data_collector_output'][:1000]}

结构分析结果:
{state['structure_analyzer_output'][:1000]}

动力学分析结果:
{state['dynamics_analyzer_output'][:1000]}

市场情绪分析结果:
{state['sentiment_analyzer_output'][:1000]}
"""

        try:
            # 调用智能体
            config = {"configurable": {"thread_id": "btc_analysis"}}
            response = self.decision_maker.invoke(
                {"messages": [HumanMessage(content=input_msg)]},
                config
            )

            output = response["messages"][-1].content if response["messages"] else ""
            execution_time = time.time() - start_time

            print(f"[决策制定智能体] 执行完成，耗时: {execution_time:.2f}秒")

            # 记录执行
            self.execution_monitor.record_execution(
                agent_type="decision_maker",
                status=ExecutionStatus.SUCCESS,
                execution_time=execution_time,
                input_data=input_msg[:500],
                output_data=output[:500],
                errors=[],
                warnings=[]
            )

            return {
                **state,
                "decision_maker_output": output,
                "execution_times": {**state.get("execution_times", {}), "decision_maker": execution_time}
            }

        except Exception as e:
            error_msg = str(e)
            print(f"[决策制定智能体] 执行失败: {error_msg}")

            self.execution_monitor.record_execution(
                agent_type="decision_maker",
                status=ExecutionStatus.FAILURE,
                execution_time=time.time() - start_time,
                input_data=input_msg[:500],
                output_data="",
                errors=[error_msg],
                warnings=[]
            )

            return {
                **state,
                "errors": state.get("errors", []) + [f"decision_maker: {error_msg}"],
                "decision_maker_output": ""
            }

    def _validate_decision_node(self, state: WorkflowState):
        """验证决策制定结果"""
        print("\n[逻辑验证器] 验证决策制定结果...")

        # 从data_collector_output中提取当前价格
        import json
        current_price = None
        try:
            data = json.loads(state["data_collector_output"])
            current_price = data.get("latest_price")
            if current_price is None:
                # 尝试其他可能的字段名
                current_price = data.get("数据摘要", {}).get("最新价格")
        except:
            pass

        if current_price is None:
            print("[逻辑验证器] 无法获取当前价格，跳过决策验证")
            validation = {
                "status": "WARNING",
                "category": "decision",
                "message": "无法获取当前价格，跳过验证",
                "validations": [],
                "counts": {"通过": 0, "警告": 1, "错误": 0, "严重错误": 0},
                "pass": 0,
                "warning": 1,
                "error": 0,
                "critical": 0
            }
        else:
            # 验证决策
            validation_result = self.logic_validator.validate_decision(
                state["decision_maker_output"],
                current_price
            )

            # 统计验证结果
            status_counts = {
                "通过": 0,
                "警告": 0,
                "错误": 0,
                "严重错误": 0
            }

            for v in validation_result:
                level_value = v.level.value
                if level_value in status_counts:
                    status_counts[level_value] += 1

            # 确定整体状态
            if status_counts["严重错误"] > 0:
                overall_status = "CRITICAL"
            elif status_counts["错误"] > 0:
                overall_status = "ERROR"
            elif status_counts["警告"] > 0:
                overall_status = "WARNING"
            else:
                overall_status = "PASS"

            validation = {
                "status": overall_status,
                "category": "decision",
                "message": f"验证完成: {status_counts['通过']}通过, {status_counts['警告']}警告, {status_counts['错误']}错误, {status_counts['严重错误']}严重",
                "validations": [
                    {
                        "item": v.item,
                        "level": v.level.value,
                        "message": v.message,
                        "theory": v.theory,
                        "calculation": v.calculation,
                        "expected": str(v.expected),
                        "actual": str(v.actual),
                        "evidence": v.evidence
                    }
                    for v in validation_result
                ],
                "counts": status_counts,
                "pass": status_counts["通过"],
                "warning": status_counts["警告"],
                "error": status_counts["错误"],
                "critical": status_counts["严重错误"]
            }

        # 记录验证结果
        validation_results = state.get("validation_results", {})
        validation_results["decision"] = validation

        return {
            **state,
            "decision_validation": validation,
            "validation_results": validation_results
        }

    def _should_continue_decision(self, state: WorkflowState):
        """决定是否继续"""
        validation = state["decision_validation"]

        if validation["status"] == "CRITICAL" or validation["status"] == "ERROR":
            print(f"[逻辑验证器] 验证失败 ({validation['status']}): {validation['message']}")
            return "reject"

        print(f"[逻辑验证器] 验证通过 ({validation['status']})")
        return "continue"

    def _meta_supervision_node(self, state: WorkflowState):
        """元智能体监督节点"""
        print("\n[元智能体] 进行最终监督和改进建议...")

        # 获取系统状态
        system_status = self.meta_agent._check_system_status()

        # 获取改进建议
        improvement_recommendations = self.meta_agent._get_improvement_recommendations()

        # 生成学习计划
        learning_plans = self.meta_agent._generate_learning_plans()

        meta_report = {
            "system_status": json.loads(system_status),
            "improvement_recommendations": json.loads(improvement_recommendations),
            "learning_plans": json.loads(learning_plans),
            "timestamp": datetime.now().isoformat()
        }

        print(f"[元智能体] 监督完成")

        return {
            **state,
            "meta_report": meta_report
        }

    def _generate_report_node(self, state: WorkflowState):
        """生成最终报告节点"""
        print("\n[生成报告] 整合所有分析结果...")

        # 统计验证结果
        total_validations = len(state["validation_results"])
        passed_validations = sum(1 for v in state["validation_results"].values()
                                if v.get("status") in ["PASS", "WARNING"])
        failed_validations = total_validations - passed_validations

        # 统计执行时间
        total_time = sum(state["execution_times"].values()) if state["execution_times"] else 0

        # 生成报告
        report = f"""
===========================================
        BTC缠论分析报告
===========================================

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【执行概况】
- 总执行时间: {total_time:.2f}秒
- 验证通过: {passed_validations}/{total_validations}
- 验证失败: {failed_validations}
- 系统健康度: {state['meta_report'].get('system_status', {}).get('overall_health', '未知')}

【数据采集】
{state['data_collector_output'][:500]}

【结构分析（缠论）】
{state['structure_analyzer_output'][:500]}

【动力学分析】
{state['dynamics_analyzer_output'][:500]}

【市场情绪】
{state['sentiment_analyzer_output'][:500]}

【决策建议】
{state['decision_maker_output'][:800]}

【元智能体监督报告】
- 知识库完整度: {state['meta_report'].get('system_status', {}).get('knowledge_completeness', 0):.1f}%
- 技能平均分: {state['meta_report'].get('system_status', {}).get('skill_score', 0):.1f}
- 系统成功率: {state['meta_report'].get('system_status', {}).get('success_rate', 0):.1f}%
- 待改进项: {state['meta_report'].get('system_status', {}).get('pending_improvements', 0)}
- 紧急问题: {state['meta_report'].get('system_status', {}).get('critical_issues', 0)}

【改进建议】
{state['meta_report'].get('improvement_recommendations', {}).get('total_candidates', 0)}个改进候选

【执行统计】
"""
        for agent, exec_time in state["execution_times"].items():
            report += f"- {agent}: {exec_time:.2f}秒\n"

        report += """
===========================================
"""

        print(report)

        # 保存报告
        report_file = "/workspace/projects/data/btc_analysis_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n报告已保存到: {report_file}")

        return {
            **state,
            "final_report": report
        }

    def run(self, initial_message: str = ""):
        """运行工作流"""
        print("=" * 50)
        print("启动带元智能体的监督工作流")
        print("=" * 50)

        initial_state = {
            "messages": [HumanMessage(content=initial_message)] if initial_message else [],
            "data_collector_output": "",
            "structure_analyzer_output": "",
            "dynamics_analyzer_output": "",
            "sentiment_analyzer_output": "",
            "decision_maker_output": "",
            "data_validation": {},
            "structure_validation": {},
            "dynamics_validation": {},
            "sentiment_validation": {},
            "decision_validation": {},
            "meta_report": {},
            "execution_times": {},
            "validation_results": {},
            "final_report": "",
            "errors": []
        }

        config = {"configurable": {"thread_id": "btc_analysis"}}

        result = self.graph.invoke(initial_state, config)

        return result


if __name__ == "__main__":
    workflow = MetaSupervisedWorkflow()
    result = workflow.run("分析BTCUSDT 4小时K线，制定交易决策")
