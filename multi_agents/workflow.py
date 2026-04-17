#!/usr/bin/env python3
"""
多智能体协作工作流 - BTC缠论分析
"""
import json
import os
import sys
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph.message import add_messages
from datetime import datetime

# 添加路径
sys.path.insert(0, '/workspace/projects')

# 导入智能体
from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.structure_analyzer_agent import build_agent as build_structure_analyzer
from multi_agents.dynamics_analyzer_agent import build_agent as build_dynamics_analyzer
from multi_agents.sentiment_analyzer_agent import build_agent as build_sentiment_analyzer
from multi_agents.decision_maker_agent import build_agent as build_decision_maker


class AnalysisState(TypedDict):
    """分析状态"""
    messages: list
    data_collection_result: str
    structure_result: str
    dynamics_result: str
    sentiment_result: str
    final_decision: str
    timestamp: str


def node_data_collector(state: AnalysisState) -> AnalysisState:
    """数据采集节点"""
    print("\n🤖 智能体1: 数据采集智能体 - 正在获取BTC实时数据...")

    agent = build_data_collector()

    response = agent.invoke({
        "messages": [HumanMessage(content="获取BTCUSDT 4小时K线数据，数量200根")]
    }, config={"configurable": {"thread_id": "analysis-thread"}})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["data_collection_result"] = str(last_message.content)

    print("✅ 数据采集完成")
    return state


def node_structure_analyzer(state: AnalysisState) -> AnalysisState:
    """结构分析节点"""
    print("\n🤖 智能体2: 结构分析智能体 - 正在分析缠论结构...")

    agent = build_structure_analyzer()

    response = agent.invoke({
        "messages": [
            HumanMessage(content="分析BTC的缠论结构"),
            HumanMessage(content=f"数据采集结果: {state['data_collection_result']}")
        ]
    }, config={"configurable": {"thread_id": "analysis-thread"}})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["structure_result"] = str(last_message.content)

    print("✅ 结构分析完成")
    return state


def node_dynamics_analyzer(state: AnalysisState) -> AnalysisState:
    """动力学分析节点"""
    print("\n🤖 智能体3: 动力学分析智能体 - 正在分析市场动能...")

    agent = build_dynamics_analyzer()

    response = agent.invoke({
        "messages": [
            HumanMessage(content="分析BTC的市场动力学指标"),
            HumanMessage(content=f"数据采集结果: {state['data_collection_result']}")
        ]
    }, config={"configurable": {"thread_id": "analysis-thread"}})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["dynamics_result"] = str(last_message.content)

    print("✅ 动力学分析完成")
    return state


def node_sentiment_analyzer(state: AnalysisState) -> AnalysisState:
    """市场情绪分析节点"""
    print("\n🤖 智能体4: 市场情绪智能体 - 正在分析市场情绪...")

    agent = build_sentiment_analyzer()

    response = agent.invoke({
        "messages": [HumanMessage(content="分析当前市场情绪")]
    }, config={"configurable": {"thread_id": "analysis-thread"}})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["sentiment_result"] = str(last_message.content)

    print("✅ 情绪分析完成")
    return state


def node_decision_maker(state: AnalysisState) -> AnalysisState:
    """决策制定节点"""
    print("\n🤖 智能体5: 决策制定智能体 - 正在综合分析并制定决策...")

    agent = build_decision_maker()

    # 提取JSON数据
    import re

    def extract_json(text):
        """从文本中提取JSON"""
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return match.group()
        return text

    structure_json = extract_json(state['structure_result'])
    dynamics_json = extract_json(state['dynamics_result'])
    sentiment_json = extract_json(state['sentiment_result'])

    response = agent.invoke({
        "messages": [
            HumanMessage(content=f"综合以下分析结果做出交易决策:"),
            HumanMessage(content=f"结构分析结果: {structure_json}"),
            HumanMessage(content=f"动力学分析结果: {dynamics_json}"),
            HumanMessage(content=f"市场情绪结果: {sentiment_json}")
        ]
    }, config={"configurable": {"thread_id": "analysis-thread"}})

    last_message = response["messages"][-1]
    state["messages"].append(last_message)
    state["final_decision"] = str(last_message.content)

    print("✅ 决策制定完成")
    return state


def build_workflow():
    """构建多智能体协作工作流"""
    workflow = StateGraph(AnalysisState)

    # 添加节点
    workflow.add_node("data_collector", node_data_collector)
    workflow.add_node("structure_analyzer", node_structure_analyzer)
    workflow.add_node("dynamics_analyzer", node_dynamics_analyzer)
    workflow.add_node("sentiment_analyzer", node_sentiment_analyzer)
    workflow.add_node("decision_maker", node_decision_maker)

    # 设置入口
    workflow.set_entry_point("data_collector")

    # 定义执行顺序
    workflow.add_edge("data_collector", "structure_analyzer")
    workflow.add_edge("structure_analyzer", "dynamics_analyzer")
    workflow.add_edge("dynamics_analyzer", "sentiment_analyzer")
    workflow.add_edge("sentiment_analyzer", "decision_maker")
    workflow.add_edge("decision_maker", END)

    return workflow.compile()


def run_analysis():
    """运行多智能体协作分析"""
    print("="*80)
    print("  🚀 BTC缠论多智能体协作分析系统")
    print("  数据源: 火币(HTX) API")
    print("="*80)
    print("\n智能体协作架构:")
    print("  1. 数据采集智能体 → 获取实时K线数据")
    print("  2. 结构分析智能体 → 分析缠论结构和趋势")
    print("  3. 动力学分析智能体 → 分析动量、RSI、MACD等")
    print("  4. 市场情绪智能体 → 分析恐惧贪婪指数")
    print("  5. 决策制定智能体 → 综合评分并制定决策")
    print("\n" + "-"*80)

    # 构建工作流
    workflow = build_workflow()

    # 初始状态
    initial_state = {
        "messages": [],
        "data_collection_result": "",
        "structure_result": "",
        "dynamics_result": "",
        "sentiment_result": "",
        "final_decision": "",
        "timestamp": datetime.now().isoformat()
    }

    try:
        # 运行工作流
        print("\n🚀 开始分析...\n")
        result = workflow.invoke(initial_state)

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

        print("\n" + "="*80)
        print("  ✅ 分析完成")
        print("="*80)

        return result

    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    result = run_analysis()
