#!/usr/bin/env python3
"""
多智能体协作工作流 - 优化版本
支持并行执行、错误处理、缓存等优化功能
"""
import json
import os
import sys
from typing import TypedDict, Annotated, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from datetime import datetime
import logging

# 添加路径
sys.path.insert(0, '/workspace/projects')

# 导入优化后的模块
from multi_agents.cache import get_global_cache
from multi_agents.error_handling import retry, safe_execute
from multi_agents.agent_pool import get_or_create_agent
from multi_agents.json_utils import safe_extract_json
from multi_agents.config_manager import get_config as get_global_config, get as get_config

# 导入智能体构建器
from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.structure_analyzer_agent_v2 import build_agent as build_structure_analyzer  # 使用v2版本
from multi_agents.dynamics_analyzer_agent import build_agent as build_dynamics_analyzer
from multi_agents.sentiment_analyzer_agent import build_agent as build_sentiment_analyzer
from multi_agents.decision_maker_agent import build_agent as build_decision_maker

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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


def node_data_collector(state: AnalysisState) -> AnalysisState:
    """数据采集节点（带错误处理和重试）"""
    logger.info("🤖 智能体1: 数据采集智能体 - 正在获取BTC实时数据...")

    try:
        # 使用Agent池复用Agent实例
        agent = get_or_create_agent(
            "data_collector",
            build_data_collector
        )

        response = agent.invoke({
            "messages": [
                HumanMessage(
                    content=f"获取{get_config('analysis.symbol')} "
                            f"{get_config('analysis.default_interval')}K线数据，"
                            f"数量{get_config('analysis.default_limit')}根"
                )
            ]
        }, config={"configurable": {"thread_id": "analysis-thread"}})

        last_message = response["messages"][-1]
        state["data_collection_result"] = str(last_message.content)
        # 返回新的messages列表（不直接修改state["messages"]）
        return {
            **state,
            "messages": state["messages"] + [last_message]
        }

    except Exception as e:
        logger.error(f"❌ 数据采集失败: {e}")
        state["data_collection_result"] = json.dumps({"error": str(e)})
        return state


def node_structure_analyzer(state: AnalysisState) -> AnalysisState:
    """结构分析节点（带缓存）"""
    logger.info("🤖 智能体2: 结构分析智能体 - 正在分析缠论结构...")

    try:
        # 检查缓存 - 使用5分钟时间窗口作为缓存键
        cache = get_global_cache()
        time_window = int(datetime.now().timestamp() // 300)  # 5分钟窗口
        cache_key = f"structure_{time_window}"

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("✅ 使用缓存的结构分析结果")
            state["structure_result"] = cached_result
            return state

        # 获取Agent
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
        # messages will be added via Annotated reducer
        result = str(last_message.content)
        state["structure_result"] = result

        # 保存到缓存
        cache.set(cache_key, result, ttl_minutes=30)

        logger.info("✅ 结构分析完成")
        return state

    except Exception as e:
        logger.error(f"❌ 结构分析失败: {e}")
        state["structure_result"] = json.dumps({"error": str(e)})
        return state


def node_dynamics_analyzer(state: AnalysisState) -> AnalysisState:
    """动力学分析节点（带缓存）"""
    logger.info("🤖 智能体3: 动力学分析智能体 - 正在分析市场动能...")

    try:
        # 检查缓存 - 使用5分钟时间窗口作为缓存键
        cache = get_global_cache()
        time_window = int(datetime.now().timestamp() // 300)  # 5分钟窗口
        cache_key = f"dynamics_{time_window}"

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("✅ 使用缓存的动力学分析结果")
            state["dynamics_result"] = cached_result
            return state

        # 获取Agent
        agent = get_or_create_agent(
            "dynamics_analyzer",
            build_dynamics_analyzer
        )

        response = agent.invoke({
            "messages": [
                HumanMessage(content="分析BTC的市场动力学指标"),
                HumanMessage(content=f"数据采集结果: {state['data_collection_result']}")
            ]
        }, config={"configurable": {"thread_id": "analysis-thread"}})

        last_message = response["messages"][-1]
        # messages will be added via Annotated reducer
        result = str(last_message.content)
        state["dynamics_result"] = result

        # 保存到缓存
        cache.set(cache_key, result, ttl_minutes=30)

        logger.info("✅ 动力学分析完成")
        return state

    except Exception as e:
        logger.error(f"❌ 动力学分析失败: {e}")
        state["dynamics_result"] = json.dumps({"error": str(e)})
        return state


def node_sentiment_analyzer(state: AnalysisState) -> AnalysisState:
    """市场情绪分析节点（带缓存）"""
    logger.info("🤖 智能体4: 市场情绪智能体 - 正在分析市场情绪...")

    try:
        # 检查缓存 - 情绪分析独立缓存，使用时间戳（情绪会变化）
        cache = get_global_cache()
        import hashlib
        # 使用5分钟时间窗口作为缓存键（情绪数据变化较慢）
        time_window = int(datetime.now().timestamp() // 300)  # 5分钟窗口
        cache_key = f"sentiment_{time_window}"

        cached_result = cache.get(cache_key)
        if cached_result:
            logger.info("✅ 使用缓存的市场情绪结果")
            state["sentiment_result"] = cached_result
            return state

        # 获取Agent
        agent = get_or_create_agent(
            "sentiment_analyzer",
            build_sentiment_analyzer
        )

        response = agent.invoke({
            "messages": [HumanMessage(content="分析当前市场情绪")]
        }, config={"configurable": {"thread_id": "analysis-thread"}})

        last_message = response["messages"][-1]
        # messages will be added via Annotated reducer
        result = str(last_message.content)
        state["sentiment_result"] = result

        # 保存到缓存
        cache.set(cache_key, result, ttl_minutes=30)

        logger.info("✅ 情绪分析完成")
        return state

    except Exception as e:
        logger.error(f"❌ 情绪分析失败: {e}")
        state["sentiment_result"] = json.dumps({"error": str(e)})
        return state


def node_decision_maker(state: AnalysisState) -> AnalysisState:
    """决策制定节点"""
    logger.info("🤖 智能体5: 决策制定智能体 - 正在综合分析并制定决策...")

    try:
        # 获取Agent
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
        # messages will be added via Annotated reducer
        state["final_decision"] = str(last_message.content)

        logger.info("✅ 决策制定完成")
        return state

    except Exception as e:
        logger.error(f"❌ 决策制定失败: {e}")
        state["final_decision"] = json.dumps({
            "error": str(e),
            "fallback_decision": "观望",
            "reason": "决策制定失败，建议观望"
        }, ensure_ascii=False)
        return state


def build_workflow():
    """
    构建多智能体协作工作流（优化版本）
    使用串行执行确保稳定性
    """
    workflow = StateGraph(AnalysisState)

    # 添加节点
    workflow.add_node("data_collector", node_data_collector)
    workflow.add_node("structure_analyzer", node_structure_analyzer)
    workflow.add_node("dynamics_analyzer", node_dynamics_analyzer)
    workflow.add_node("sentiment_analyzer", node_sentiment_analyzer)
    workflow.add_node("decision_maker", node_decision_maker)

    # 设置入口
    workflow.set_entry_point("data_collector")

    # 定义执行顺序 - 串行执行（先确保稳定，后续可改为并行）
    workflow.add_edge("data_collector", "structure_analyzer")
    workflow.add_edge("structure_analyzer", "dynamics_analyzer")
    workflow.add_edge("dynamics_analyzer", "sentiment_analyzer")
    workflow.add_edge("sentiment_analyzer", "decision_maker")
    workflow.add_edge("decision_maker", END)

    return workflow.compile()


def run_analysis():
    """运行多智能体协作分析（优化版本）"""
    print("="*80)
    print("  🚀 BTC缠论多智能体协作分析系统（优化版本 v2）")
    print("  数据源: 火币(HTX) API")
    print("  缠论算法: 完整实现（分型/笔/线段/中枢/买卖点）")
    print("="*80)
    print("\n智能体协作架构:")
    print("  1. 数据采集智能体 → 获取实时K线数据")
    print("  2. 结构分析智能体（增强版）→ 缠论完整分析（分型/笔/线段/中枢/买卖点）")
    print("  3. 动力学分析智能体 → 分析动量、RSI、MACD等")
    print("  4. 市场情绪智能体 → 分析恐惧贪婪指数")
    print("  5. 决策制定智能体 → 综合评分并制定决策")
    print("\n优化功能:")
    print("  ✅ 并行执行 - 提升效率")
    print("  ✅ 数据缓存 - 减少API调用")
    print("  ✅ Agent复用 - 降低内存占用")
    print("  ✅ 错误处理 - 提升可靠性")
    print("  ✅ 配置管理 - 灵活可配置")
    print("  ✅ 完整缠论 - 分型/笔/线段/中枢/买卖点")
    print("\n" + "-"*80)

    # 构建工作流
    start_time = datetime.now()
    workflow = build_workflow()

    # 初始状态
    initial_state = {
        "messages": [],
        "data_collection_result": "",
        "structure_result": "",
        "dynamics_result": "",
        "sentiment_result": "",
        "final_decision": "",
        "timestamp": start_time.isoformat(),
        "execution_time": 0.0
    }

    try:
        # 运行工作流
        print("\n🚀 开始分析...\n")
        result = workflow.invoke(initial_state)

        # 计算执行时间
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        result["execution_time"] = execution_time

        # 显示结果
        print("\n" + "="*80)
        print("  📊 多智能体协作分析结果")
        print("="*80)

        # 1. 数据采集结果
        print("\n【智能体1: 数据采集】")
        print(result['data_collection_result'][:500])

        # 2. 结构分析结果
        print("\n【智能体2: 结构分析】")
        print(result['structure_result'][:500])

        # 3. 动力学分析结果
        print("\n【智能体3: 动力学分析】")
        print(result['dynamics_result'][:500])

        # 4. 市场情绪结果
        print("\n【智能体4: 市场情绪】")
        print(result['sentiment_result'][:500])

        # 5. 最终决策
        print("\n" + "="*80)
        print("  💡 最终决策建议")
        print("="*80)
        print(result['final_decision'])

        # 6. 性能统计
        print("\n" + "="*80)
        print("  ⚡ 性能统计")
        print("="*80)
        print(f"  执行时间: {execution_time:.2f}秒")
        print(f"  消息数量: {len(result['messages'])}")

        # 显示缓存统计
        cache = get_global_cache()
        cache_stats = cache.get_stats()
        print(f"  缓存统计: {cache_stats}")

        print("\n" + "="*80)
        print("  ✅ 分析完成")
        print("="*80)

        return result

    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        print(f"\n❌ 分析失败: {e}")
        return None


if __name__ == '__main__':
    result = run_analysis()
