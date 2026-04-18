#!/usr/bin/env python3
"""
带监督机制的BTC缠论多智能体协作分析工作流
每个智能体执行后都会经过监督验证，确保有实锤依据和理论支撑
"""
import json
import sys
import os
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')
from typing import TypedDict, Annotated
from datetime import datetime
import logging

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage

# 导入智能体构建器
from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.structure_analyzer_agent_v2 import build_agent as build_structure_analyzer
from multi_agents.dynamics_analyzer_agent import build_agent as build_dynamics_analyzer
from multi_agents.sentiment_analyzer_agent import build_agent as build_sentiment_analyzer
from multi_agents.decision_maker_agent_v3 import build_agent as build_decision_maker

# 导入监督机制
from multi_agents.supervisor import Supervisor

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisState(TypedDict):
    """分析状态"""
    messages: Annotated[list, add_messages]
    data_collection_result: str
    structure_result: str
    dynamics_result: str
    sentiment_result: str
    final_decision: str
    timestamp: str
    execution_time: float
    validation_reports: list
    validation_passed: bool


# 导入缓存和配置
from multi_agents.cache import get_global_cache
from multi_agents.config_manager import get_config
from multi_agents.agent_pool import get_or_create_agent
from multi_agents.json_utils import safe_extract_json
from multi_agents.error_handling import retry, safe_execute


@retry(max_retries=3, backoff_factor=2)
def node_data_collector(state: AnalysisState) -> AnalysisState:
    """数据采集节点 + 监督验证"""
    logger.info("🤖 智能体1: 数据采集智能体")
    logger.info("🛡️ 监督验证: 数据来源和完整性")

    try:
        agent = get_or_create_agent(
            "data_collector",
            build_data_collector
        )

        response = agent.invoke({
            "messages": [
                HumanMessage(
                    content="获取BTC 4小时K线数据，200根"
                )
            ]
        }, config={"configurable": {"thread_id": "analysis-thread"}})

        last_message = response["messages"][-1]
        state["data_collection_result"] = str(last_message.content)

        # 监督验证
        supervisor = Supervisor()
        report = supervisor.supervise_data_collection(state["data_collection_result"])

        logger.info(f"🛡️ 监督结果: {report.overall_status.value}")
        if report.critical_issues:
            logger.error(f"🚨 严重错误: {report.critical_issues}")
        if report.error_issues:
            logger.warning(f"⚠️  错误: {report.error_issues}")
        if report.warning_issues:
            logger.info(f"ℹ️  警告: {report.warning_issues}")

        # 如果验证未通过，拒绝继续
        if not report.can_proceed:
            state["validation_passed"] = False
            state["validation_reports"] = [report.reasoning]
            logger.error("❌ 数据采集验证未通过，终止分析流程")
            return state

        state["validation_reports"] = [report.reasoning]
        logger.info("✅ 数据采集验证通过")
        return state

    except Exception as e:
        logger.error(f"❌ 数据采集失败: {e}")
        state["data_collection_result"] = json.dumps({"error": str(e)}, ensure_ascii=False)
        state["validation_passed"] = False
        return state


@retry(max_retries=3, backoff_factor=2)
def node_structure_analyzer(state: AnalysisState) -> AnalysisState:
    """结构分析节点 + 监督验证"""
    if not state.get("validation_passed", True):
        return state

    logger.info("🤖 智能体2: 结构分析智能体（缠论）")
    logger.info("🛡️ 监督验证: 缠论算法逻辑")

    try:
        # 检查缓存
        cache = get_global_cache()
        time_window = int(datetime.now().timestamp() // 300)
        cache_key = f"structure_{time_window}"

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("✅ 使用缓存的结构分析结果")
            state["structure_result"] = cached_result
            return state

        agent = get_or_create_agent(
            "structure_analyzer",
            build_structure_analyzer
        )

        response = agent.invoke({
            "messages": [
                HumanMessage(content="分析BTC的缠论结构"),
                HumanMessage(content=f"数据采集结果: {state['data_collection_result']}")
            ]
        }, config={"configurable": {"thread_id": "analysis-thread"}})

        last_message = response["messages"][-1]
        state["structure_result"] = str(last_message.content)

        # 监督验证
        supervisor = Supervisor()
        report = supervisor.supervise_structure_analysis(state["structure_result"])

        logger.info(f"🛡️ 监督结果: {report.overall_status.value}")
        if report.critical_issues:
            logger.error(f"🚨 严重错误: {report.critical_issues}")
        if report.error_issues:
            logger.warning(f"⚠️  错误: {report.error_issues}")
        if report.warning_issues:
            logger.info(f"ℹ️  警告: {report.warning_issues}")

        # 如果验证未通过，拒绝继续
        if not report.can_proceed:
            state["validation_passed"] = False
            state["validation_reports"].append(report.reasoning)
            logger.error("❌ 结构分析验证未通过，终止分析流程")
            return state

        state["validation_reports"].append(report.reasoning)

        # 缓存结果
        cache.set(cache_key, state["structure_result"], ttl=300)

        logger.info("✅ 结构分析验证通过")
        return state

    except Exception as e:
        logger.error(f"❌ 结构分析失败: {e}")
        state["structure_result"] = json.dumps({"error": str(e)}, ensure_ascii=False)
        state["validation_passed"] = False
        return state


@retry(max_retries=3, backoff_factor=2)
def node_dynamics_analyzer(state: AnalysisState) -> AnalysisState:
    """动力学分析节点 + 监督验证"""
    if not state.get("validation_passed", True):
        return state

    logger.info("🤖 智能体3: 动力学分析智能体")
    logger.info("🛡️ 监督验证: 计算逻辑验证")

    try:
        # 检查缓存
        cache = get_global_cache()
        time_window = int(datetime.now().timestamp() // 300)
        cache_key = f"dynamics_{time_window}"

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("✅ 使用缓存的动力学分析结果")
            state["dynamics_result"] = cached_result
            return state

        agent = get_or_create_agent(
            "dynamics_analyzer",
            build_dynamics_analyzer
        )

        response = agent.invoke({
            "messages": [
                HumanMessage(content="分析BTC的市场动力学指标")
            ]
        }, config={"configurable": {"thread_id": "analysis-thread"}})

        last_message = response["messages"][-1]
        state["dynamics_result"] = str(last_message.content)

        # 监督验证
        supervisor = Supervisor()
        report = supervisor.supervise_dynamics_analysis(state["dynamics_result"])

        logger.info(f"🛡️ 监督结果: {report.overall_status.value}")
        if report.critical_issues:
            logger.error(f"🚨 严重错误: {report.critical_issues}")
        if report.error_issues:
            logger.warning(f"⚠️  错误: {report.error_issues}")
        if report.warning_issues:
            logger.info(f"ℹ️  警告: {report.warning_issues}")

        # 如果验证未通过，拒绝继续
        if not report.can_proceed:
            state["validation_passed"] = False
            state["validation_reports"].append(report.reasoning)
            logger.error("❌ 动力学分析验证未通过，终止分析流程")
            return state

        state["validation_reports"].append(report.reasoning)

        # 缓存结果
        cache.set(cache_key, state["dynamics_result"], ttl=300)

        logger.info("✅ 动力学分析验证通过")
        return state

    except Exception as e:
        logger.error(f"❌ 动力学分析失败: {e}")
        state["dynamics_result"] = json.dumps({"error": str(e)}, ensure_ascii=False)
        state["validation_passed"] = False
        return state


@retry(max_retries=3, backoff_factor=2)
def node_sentiment_analyzer(state: AnalysisState) -> AnalysisState:
    """市场情绪分析节点 + 监督验证"""
    if not state.get("validation_passed", True):
        return state

    logger.info("🤖 智能体4: 市场情绪智能体")
    logger.info("🛡️ 监督验证: 情绪数据来源验证")

    try:
        # 检查缓存
        cache = get_global_cache()
        time_window = int(datetime.now().timestamp() // 300)
        cache_key = f"sentiment_{time_window}"

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("✅ 使用缓存的市场情绪结果")
            state["sentiment_result"] = cached_result
            return state

        agent = get_or_create_agent(
            "sentiment_analyzer",
            build_sentiment_analyzer
        )

        response = agent.invoke({
            "messages": [
                HumanMessage(content="获取市场情绪数据")
            ]
        }, config={"configurable": {"thread_id": "analysis-thread"}})

        last_message = response["messages"][-1]
        state["sentiment_result"] = str(last_message.content)

        # 监督验证
        supervisor = Supervisor()
        report = supervisor.supervise_sentiment_analysis(state["sentiment_result"])

        logger.info(f"🛡️ 监督结果: {report.overall_status.value}")
        if report.critical_issues:
            logger.error(f"🚨 严重错误: {report.critical_issues}")
        if report.error_issues:
            logger.warning(f"⚠️  错误: {report.error_issues}")
        if report.warning_issues:
            logger.info(f"ℹ️  警告: {report.warning_issues}")

        # 如果验证未通过，拒绝继续
        if not report.can_proceed:
            state["validation_passed"] = False
            state["validation_reports"].append(report.reasoning)
            logger.error("❌ 市场情绪验证未通过，终止分析流程")
            return state

        state["validation_reports"].append(report.reasoning)

        # 缓存结果
        cache.set(cache_key, state["sentiment_result"], ttl=300)

        logger.info("✅ 市场情绪验证通过")
        return state

    except Exception as e:
        logger.error(f"❌ 市场情绪分析失败: {e}")
        state["sentiment_result"] = json.dumps({"error": str(e)}, ensure_ascii=False)
        state["validation_passed"] = False
        return state


@retry(max_retries=3, backoff_factor=2)
def node_decision_maker(state: AnalysisState) -> AnalysisState:
    """决策制定节点 + 监督验证（关键！）"""
    if not state.get("validation_passed", True):
        return state

    logger.info("🤖 智能体5: 决策制定智能体")
    logger.info("🛡️ 监督验证: 止盈止损方向验证（关键！）")

    try:
        agent = get_or_create_agent(
            "decision_maker",
            build_decision_maker
        )

        response = agent.invoke({
            "messages": [
                HumanMessage(content="综合以下分析结果做出交易决策:"),
                HumanMessage(content=f"结构分析结果:\n{state['structure_result']}"),
                HumanMessage(content=f"动力学分析结果:\n{state['dynamics_result']}"),
                HumanMessage(content=f"市场情绪结果:\n{state['sentiment_result']}")
            ]
        }, config={"configurable": {"thread_id": "analysis-thread"}})

        last_message = response["messages"][-1]
        state["final_decision"] = str(last_message.content)

        # 获取当前价格用于验证
        import pandas as pd
        df = pd.read_csv("/workspace/projects/data/BTCUSDT_4h_latest.csv")
        current_price = df['close'].iloc[-1]

        # 监督验证（关键！）
        supervisor = Supervisor()
        report = supervisor.supervise_decision(state["final_decision"], current_price)

        logger.info(f"🛡️ 监督结果: {report.overall_status.value}")
        if report.critical_issues:
            logger.error(f"🚨 严重错误: {report.critical_issues}")
        if report.error_issues:
            logger.warning(f"⚠️  错误: {report.error_issues}")
        if report.warning_issues:
            logger.info(f"ℹ️  警告: {report.warning_issues}")

        # 如果验证未通过，拒绝输出
        if not report.can_proceed:
            state["validation_passed"] = False
            state["validation_reports"].append(report.reasoning)
            logger.error("❌ 决策制定验证未通过，拒绝输出最终研判")
            return state

        state["validation_reports"].append(report.reasoning)

        logger.info("✅ 决策制定验证通过")
        return state

    except Exception as e:
        logger.error(f"❌ 决策制定失败: {e}")
        state["final_decision"] = json.dumps({"error": str(e)}, ensure_ascii=False)
        state["validation_passed"] = False
        return state


def build_workflow():
    """构建带监督机制的多智能体协作工作流"""
    workflow = StateGraph(AnalysisState)

    # 添加节点
    workflow.add_node("data_collector", node_data_collector)
    workflow.add_node("structure_analyzer", node_structure_analyzer)
    workflow.add_node("dynamics_analyzer", node_dynamics_analyzer)
    workflow.add_node("sentiment_analyzer", node_sentiment_analyzer)
    workflow.add_node("decision_maker", node_decision_maker)

    # 设置入口
    workflow.set_entry_point("data_collector")

    # 定义执行顺序 - 串行执行（每个环节都有监督）
    workflow.add_edge("data_collector", "structure_analyzer")
    workflow.add_edge("structure_analyzer", "dynamics_analyzer")
    workflow.add_edge("dynamics_analyzer", "sentiment_analyzer")
    workflow.add_edge("sentiment_analyzer", "decision_maker")
    workflow.add_edge("decision_maker", END)

    return workflow.compile()


def run_analysis():
    """运行带监督机制的分析"""
    start_time = datetime.now()

    print("="*80)
    print("  🛡️ BTC缠论多智能体协作分析系统（监督版 v4）")
    print("  数据源: 火币(HTX) API")
    print("  缠论算法: 完整实现（分型/笔/线段/中枢/买卖点）")
    print("  决策逻辑: 已修复止盈止损方向错误")
    print("  监督机制: 每个环节验证，确保实锤依据和理论支撑")
    print("="*80)
    print("\n智能体协作架构:")
    print("  1. 数据采集智能体 → [数据验证] → 结构分析智能体")
    print("  2. 结构分析智能体 → [逻辑验证] → 动力学分析智能体")
    print("  3. 动力学分析智能体 → [逻辑验证] → 市场情绪智能体")
    print("  4. 市场情绪智能体 → [数据验证] → 决策制定智能体")
    print("  5. 决策制定智能体 → [综合验证] → 最终研判")
    print("\n监督机制:")
    print("  ✅ 数据验证 - 验证数据来源、完整性、时效性")
    print("  ✅ 逻辑验证 - 验证计算公式、算法逻辑、理论依据")
    print("  ✅ 方向验证 - 验证止盈止损方向（关键！）")
    print("  ✅ 综合审批 - 所有验证通过才输出最终研判")
    print("\n" + "-"*80)

    # 构建工作流
    workflow = build_workflow()

    # 初始化状态
    initial_state = {
        "messages": [],
        "data_collection_result": "",
        "structure_result": "",
        "dynamics_result": "",
        "sentiment_result": "",
        "final_decision": "",
        "timestamp": datetime.now().isoformat(),
        "execution_time": 0,
        "validation_reports": [],
        "validation_passed": True
    }

    # 运行工作流
    try:
        final_state = workflow.invoke(initial_state)
    except Exception as e:
        logger.error(f"工作流执行失败: {e}")
        final_state = initial_state
        final_state["validation_passed"] = False
        final_state["final_decision"] = json.dumps({"error": str(e)}, ensure_ascii=False)

    # 计算执行时间
    end_time = datetime.now()
    execution_time = (end_time - start_time).total_seconds()
    final_state["execution_time"] = execution_time

    print("\n" + "="*80)
    print("  📊 监督验证报告")
    print("="*80)

    # 输出验证报告
    print(f"\n验证链条:")
    for i, report in enumerate(final_state.get("validation_reports", []), 1):
        print(f"  {i}. {report}")

    # 检查最终验证结果
    if final_state.get("validation_passed", True):
        print("\n✅ 所有验证通过，可以输出最终研判")
        print("\n" + "="*80)
        print("  🎯 最终研判结果")
        print("="*80)
        print(final_state["final_decision"])
    else:
        print("\n❌ 验证未通过，拒绝输出最终研判")
        print("\n失败原因:")
        for report in final_state.get("validation_reports", []):
            print(f"  - {report}")

    print("\n" + "="*80)
    print(f"  ⏱️  总执行时间: {execution_time:.2f}秒")
    print("="*80)

    # 保存监督报告
    try:
        supervisor = Supervisor()
        # 重建报告对象（因为state中保存的是字符串）
        full_report = {
            "timestamp": datetime.now().isoformat(),
            "validation_reports": final_state.get("validation_reports", []),
            "validation_passed": final_state.get("validation_passed", False)
        }

        report_path = "/workspace/projects/data/supervision_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(full_report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 完整监督报告已保存: {report_path}")
    except Exception as e:
        print(f"\n⚠️  保存监督报告失败: {e}")

    return final_state


if __name__ == "__main__":
    run_analysis()
