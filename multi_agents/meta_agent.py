"""
元智能体（Meta-Agent）框架
使用 LangGraph 实现多智能体协作（串行执行版本）

功能：
1. 智能体调度与管理
2. 串行执行有依赖的智能体
3. 条件分支和动态路由
4. 异常处理和自动重试
5. 智能体间通信
"""

import time
import pandas as pd
from typing import TypedDict, Dict, Any, Optional, List, Annotated
from datetime import datetime
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from multi_agents.multi_level_chanlun_analyzer import MultiLevelChanLunAnalyzer
from multi_agents.dynamics_analyzer_agent import analyze_dynamics
from multi_agents.sentiment_analyzer_agent import analyze_sentiment
from multi_agents.enhanced_decision_maker_agent import make_enhanced_decision


# ============================================================================
# 元智能体状态定义
# ============================================================================

class MultiAgentState(TypedDict):
    """多智能体协作的共享状态"""
    
    # 输入
    symbol: str
    start_time: Optional[str]
    chanlun_analyzer: Optional[MultiLevelChanLunAnalyzer]
    
    # 数据采集智能体输出
    data_collection_status: Optional[str]
    
    # 结构分析智能体输出
    structure_analysis: Optional[Dict[str, Any]]
    
    # 动力学分析智能体输出
    dynamics_analysis: Optional[Dict[str, Any]]
    
    # 市场情绪智能体输出
    sentiment_analysis: Optional[Dict[str, Any]]
    
    # 决策制定智能体输出
    decision: Optional[Dict[str, Any]]
    
    # 元智能体控制
    current_phase: str  # 当前阶段
    phases_completed: List[str]  # 已完成的阶段
    errors: List[str]  # 错误日志
    retry_count: Dict[str, int]  # 各智能体的重试次数
    messages: Annotated[List, add_messages]  # 智能体间消息
    
    # 执行统计
    execution_times: Dict[str, float]  # 各智能体执行时间
    total_execution_time: float  # 总执行时间


# ============================================================================
# 智能体节点函数
# ============================================================================

def data_collection_node(state: MultiAgentState) -> MultiAgentState:
    """
    数据采集智能体节点
    负责采集多级别K线数据
    """
    print("\n" + "=" * 80)
    print("[智能体 1/5] 数据采集智能体：开始执行...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 创建多级别缠论分析器
        analyzer = MultiLevelChanLunAnalyzer(state["symbol"])
        
        # 采集所有级别的数据
        analyzer.collect_all_levels_data()
        
        # 更新状态
        execution_time = time.time() - start_time
        state["chanlun_analyzer"] = analyzer
        state["data_collection_status"] = "completed"
        state["phases_completed"].append("data_collection")
        state["current_phase"] = "structure_analysis"
        state["execution_times"]["data_collection"] = execution_time
        
        print(f"✅ 数据采集智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - 已采集 {len(analyzer.levels)} 个级别")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"数据采集完成：{len(analyzer.levels)}个级别"
        })
        
    except Exception as e:
        error_msg = f"数据采集智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 重试逻辑
        retry_key = "data_collection"
        state["retry_count"][retry_key] = state["retry_count"].get(retry_key, 0) + 1
        if state["retry_count"][retry_key] < 3:
            print(f"  🔁 第 {state['retry_count'][retry_key]} 次重试...")
            return data_collection_node(state)
        else:
            print(f"  ⚠️ 重试次数已达上限，继续执行后续智能体...")
    
    return state


def structure_analysis_node(state: MultiAgentState) -> MultiAgentState:
    """
    结构分析智能体节点
    负责多级别缠论结构分析
    """
    print("\n" + "=" * 80)
    print("[智能体 2/5] 结构分析智能体：开始执行...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 检查依赖
        if state["chanlun_analyzer"] is None:
            raise ValueError("缺少数据采集结果，无法进行结构分析")
        
        # 执行结构分析
        state["chanlun_analyzer"].analyze_all_levels()
        
        # 生成综合报告
        result = state["chanlun_analyzer"].generate_comprehensive_report()
        
        # 更新状态
        execution_time = time.time() - start_time
        state["structure_analysis"] = result
        state["phases_completed"].append("structure_analysis")
        state["current_phase"] = "dynamics_analysis"
        state["execution_times"]["structure_analysis"] = execution_time
        
        print(f"✅ 结构分析智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - 已分析 {len(result.get('level_analysis', {}))} 个级别")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"结构分析完成：{len(result.get('level_analysis', {}))}个级别"
        })
        
    except Exception as e:
        error_msg = f"结构分析智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 重试逻辑
        retry_key = "structure_analysis"
        state["retry_count"][retry_key] = state["retry_count"].get(retry_key, 0) + 1
        if state["retry_count"][retry_key] < 3:
            print(f"  🔁 第 {state['retry_count'][retry_key]} 次重试...")
            return structure_analysis_node(state)
        else:
            print(f"  ⚠️ 重试次数已达上限，继续执行后续智能体...")
    
    return state


def dynamics_analysis_node(state: MultiAgentState) -> MultiAgentState:
    """
    动力学分析智能体节点
    负责RSI、MACD、波动率、成交量分析
    """
    print("\n" + "=" * 80)
    print("[智能体 3/5] 动力学分析智能体：开始执行...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 检查依赖
        if state["chanlun_analyzer"] is None:
            raise ValueError("缺少数据，无法进行动力学分析")
        
        # 获取30分钟级别的数据
        data_30m = state["chanlun_analyzer"].all_data.get('30m', {})
        
        # 检查数据格式
        if data_30m is not None and isinstance(data_30m, dict) and 'timestamp' in data_30m:
            # 数据格式是字典，需要转换为DataFrame
            df_30m = pd.DataFrame(data_30m)
        elif isinstance(data_30m, pd.DataFrame):
            # 已经是DataFrame
            df_30m = data_30m
        else:
            # 尝试获取df键
            df_30m = data_30m.get('df') if isinstance(data_30m, dict) else None

        if df_30m is None or len(df_30m) == 0:
            print("  ⚠️ 30分钟级别数据不足，返回默认值")
            result = {
                'rsi': {'current_rsi': 50, 'signal': '正常', 'signal_score': 50},
                'macd': {'signal_type': '正常', 'signal_score': 50},
                'overall_score': 50.0,
                'overall_signal': '震荡',
                'dynamics_factor': 0.5,
                'description': '数据不足，无法分析'
            }
        else:
            # 调用动力学分析智能体
            result = analyze_dynamics(df_30m)
        
        # 更新状态
        execution_time = time.time() - start_time
        state["dynamics_analysis"] = result
        state["phases_completed"].append("dynamics_analysis")
        state["current_phase"] = "sentiment_analysis"
        state["execution_times"]["dynamics_analysis"] = execution_time
        
        print(f"✅ 动力学分析智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - RSI: {result.get('rsi', {}).get('current_rsi', 0):.1f}")
        print(f"  - 综合评分: {result.get('overall_score', 0):.1f}")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"动力学分析完成：RSI={result.get('rsi', {}).get('current_rsi', 0):.1f}"
        })
        
    except Exception as e:
        error_msg = f"动力学分析智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 重试逻辑
        retry_key = "dynamics_analysis"
        state["retry_count"][retry_key] = state["retry_count"].get(retry_key, 0) + 1
        if state["retry_count"][retry_key] < 3:
            print(f"  🔁 第 {state['retry_count'][retry_key]} 次重试...")
            return dynamics_analysis_node(state)
        else:
            print(f"  ⚠️ 重试次数已达上限，继续执行后续智能体...")
    
    return state


def sentiment_analysis_node(state: MultiAgentState) -> MultiAgentState:
    """
    市场情绪智能体节点
    负责恐惧贪婪指数和资金流向分析
    """
    print("\n" + "=" * 80)
    print("[智能体 4/5] 市场情绪智能体：开始执行...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 获取30分钟级别的数据
        if state["chanlun_analyzer"] is None:
            raise ValueError("缺少数据，无法进行市场情绪分析")
        
        data_30m = state["chanlun_analyzer"].all_data.get('30m', {})
        
        # 检查数据格式
        if data_30m is not None and isinstance(data_30m, dict) and 'timestamp' in data_30m:
            # 数据格式是字典，需要转换为DataFrame
            df_30m = pd.DataFrame(data_30m)
        elif isinstance(data_30m, pd.DataFrame):
            # 已经是DataFrame
            df_30m = data_30m
        else:
            # 尝试获取df键
            df_30m = data_30m.get('df') if isinstance(data_30m, dict) else None

        if df_30m is None or len(df_30m) == 0:
            print("  ⚠️ 30分钟级别数据不足，返回默认值")
            result = {
                'fear_greed': {'value': 50, 'classification': 'Neutral'},
                'money_flow': {'flow_direction': '中性'},
                'overall_sentiment': '中性',
                'overall_score': 50.0,
                'sentiment_factor': 0.5,
                'description': '数据不足，无法分析'
            }
        else:
            # 调用市场情绪智能体
            result = analyze_sentiment(df_30m)
        
        # 更新状态
        execution_time = time.time() - start_time
        state["sentiment_analysis"] = result
        state["phases_completed"].append("sentiment_analysis")
        state["current_phase"] = "decision_making"
        state["execution_times"]["sentiment_analysis"] = execution_time
        
        print(f"✅ 市场情绪智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - 恐惧贪婪指数: {result.get('fear_greed', {}).get('value', 0)}")
        print(f"  - 综合评分: {result.get('overall_score', 0):.1f}")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"市场情绪分析完成：FearGreed={result.get('fear_greed', {}).get('value', 0)}"
        })
        
    except Exception as e:
        error_msg = f"市场情绪智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 重试逻辑
        retry_key = "sentiment_analysis"
        state["retry_count"][retry_key] = state["retry_count"].get(retry_key, 0) + 1
        if state["retry_count"][retry_key] < 3:
            print(f"  🔁 第 {state['retry_count'][retry_key]} 次重试...")
            return sentiment_analysis_node(state)
        else:
            print(f"  ⚠️ 重试次数已达上限，继续执行后续智能体...")
    
    return state


def decision_making_node(state: MultiAgentState) -> MultiAgentState:
    """
    决策制定智能体节点
    负责综合决策制定
    """
    print("\n" + "=" * 80)
    print("[智能体 5/5] 决策制定智能体：开始执行...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 检查依赖
        if state["structure_analysis"] is None:
            raise ValueError("缺少结构分析结果，无法制定决策")
        
        # 调用决策制定智能体
        result = make_enhanced_decision(
            structure_analysis=state["structure_analysis"],
            dynamics_analysis=state["dynamics_analysis"],
            sentiment_analysis=state["sentiment_analysis"]
        )
        
        # 更新状态
        execution_time = time.time() - start_time
        state["decision"] = result
        state["phases_completed"].append("decision_making")
        state["current_phase"] = "completed"
        state["execution_times"]["decision_making"] = execution_time
        
        print(f"✅ 决策制定智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - 综合评分: {result.get('overall_score', 0):.1f}")
        print(f"  - 操作建议: {result.get('action', '未知')}")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"决策制定完成：{result.get('action', '未知')}"
        })
        
    except Exception as e:
        error_msg = f"决策制定智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 重试逻辑
        retry_key = "decision_making"
        state["retry_count"][retry_key] = state["retry_count"].get(retry_key, 0) + 1
        if state["retry_count"][retry_key] < 3:
            print(f"  🔁 第 {state['retry_count'][retry_key]} 次重试...")
            return decision_making_node(state)
        else:
            print(f"  ⚠️ 重试次数已达上限，继续执行后续智能体...")
    
    return state


# ============================================================================
# 条件分支函数
# ============================================================================

def should_continue_after_data_collection(state: MultiAgentState) -> str:
    """
    决定是否在数据采集后继续执行结构分析
    """
    if state["data_collection_status"] != "completed":
        # 数据采集失败，跳过所有后续智能体
        print("⚠️ 数据采集失败，跳过所有后续智能体...")
        return "skip_to_end"
    else:
        return "to_structure_analysis"


def should_continue_after_structure_analysis(state: MultiAgentState) -> str:
    """
    决定是否在结构分析后继续执行动力学分析
    """
    if state["structure_analysis"] is None:
        # 结构分析失败，跳过到决策制定（使用默认值）
        print("⚠️ 结构分析失败，跳过到决策制定（使用默认值）...")
        return "to_decision_making"
    else:
        return "to_dynamics_analysis"


def should_continue_after_dynamics_analysis(state: MultiAgentState) -> str:
    """
    决定是否在动力学分析后继续执行市场情绪分析
    """
    if state["dynamics_analysis"] is None:
        # 动力学分析失败，继续执行市场情绪分析
        print("⚠️ 动力学分析失败，继续执行市场情绪分析...")
        return "to_sentiment_analysis"
    else:
        return "to_sentiment_analysis"


# ============================================================================
# 元智能体协调器
# ============================================================================

class MetaAgentCoordinator:
    """
    元智能体协调器
    
    负责协调和管理多个智能体的执行
    """
    
    def __init__(self):
        """初始化元智能体协调器"""
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """
        构建智能体协作图
        
        Returns:
            StateGraph: 智能体协作图
        """
        # 创建状态图
        graph = StateGraph(MultiAgentState)
        
        # 添加节点
        graph.add_node("data_collection", data_collection_node)
        graph.add_node("structure_analysis", structure_analysis_node)
        graph.add_node("dynamics_analysis", dynamics_analysis_node)
        graph.add_node("sentiment_analysis", sentiment_analysis_node)
        graph.add_node("decision_making", decision_making_node)
        
        # 添加边和条件分支
        
        # 1. 开始 -> 数据采集
        graph.set_entry_point("data_collection")
        
        # 2. 数据采集 -> 条件分支
        graph.add_conditional_edges(
            "data_collection",
            should_continue_after_data_collection,
            {
                "to_structure_analysis": "structure_analysis",
                "skip_to_end": END
            }
        )
        
        # 3. 结构分析 -> 条件分支
        graph.add_conditional_edges(
            "structure_analysis",
            should_continue_after_structure_analysis,
            {
                "to_dynamics_analysis": "dynamics_analysis",
                "to_decision_making": "decision_making"
            }
        )
        
        # 4. 动力学分析 -> 市场情绪分析
        graph.add_edge("dynamics_analysis", "sentiment_analysis")
        
        # 5. 市场情绪分析 -> 决策制定
        graph.add_edge("sentiment_analysis", "decision_making")
        
        # 6. 决策制定 -> 结束
        graph.add_edge("decision_making", END)
        
        return graph.compile()
    
    def initialize_state(self, symbol: str) -> MultiAgentState:
        """
        初始化状态
        
        Args:
            symbol: 交易对符号
            
        Returns:
            MultiAgentState: 初始状态
        """
        return {
            "symbol": symbol,
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "chanlun_analyzer": None,
            "data_collection_status": None,
            "structure_analysis": None,
            "dynamics_analysis": None,
            "sentiment_analysis": None,
            "decision": None,
            "current_phase": "data_collection",
            "phases_completed": [],
            "errors": [],
            "retry_count": {},
            "messages": [],
            "execution_times": {},
            "total_execution_time": 0.0
        }
    
    def run(self, symbol: str) -> MultiAgentState:
        """
        运行元智能体协调器
        
        Args:
            symbol: 交易对符号
            
        Returns:
            MultiAgentState: 最终状态
        """
        print("\n" + "=" * 80)
        print("元智能体协调器启动")
        print("=" * 80)
        print(f"交易对: {symbol}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        start_time = time.time()
        
        # 初始化状态
        initial_state = self.initialize_state(symbol)
        
        try:
            # 运行图
            final_state = self.graph.invoke(initial_state)
            
            # 计算总执行时间
            final_state["total_execution_time"] = time.time() - start_time
            
            # 打印摘要
            self._print_summary(final_state)
            
            return final_state
            
        except Exception as e:
            print(f"\n❌ 元智能体协调器执行失败: {str(e)}")
            raise
    
    def _print_summary(self, state: MultiAgentState):
        """
        打印执行摘要
        
        Args:
            state: 最终状态
        """
        print("\n" + "=" * 80)
        print("元智能体协调器执行完成")
        print("=" * 80)
        print(f"总执行时间: {state['total_execution_time']:.2f}秒")
        print(f"已完成的阶段: {len(state['phases_completed'])}/5")
        
        # 打印各智能体执行时间
        if state["execution_times"]:
            print("\n各智能体执行时间:")
            for agent_name, exec_time in state["execution_times"].items():
                print(f"  - {agent_name}: {exec_time:.2f}秒")
        
        # 打印错误
        if state["errors"]:
            print(f"\n错误日志 ({len(state['errors'])}个):")
            for i, error in enumerate(state["errors"], 1):
                print(f"  {i}. {error}")
        
        # 打印最终决策
        if state["decision"]:
            print(f"\n最终决策:")
            print(f"  - 综合评分: {state['decision'].get('overall_score', 0):.1f}")
            print(f"  - 操作建议: {state['decision'].get('action', '未知')}")
            print(f"  - 风险等级: {state['decision'].get('risk_level', '未知')}")
        
        print("=" * 80)


# ============================================================================
# 辅助函数
# ============================================================================

def run_meta_agent_analysis(symbol: str = "btcusdt") -> Dict[str, Any]:
    """
    运行元智能体分析
    
    Args:
        symbol: 交易对符号
        
    Returns:
        Dict[str, Any]: 分析结果
    """
    # 创建元智能体协调器
    coordinator = MetaAgentCoordinator()
    
    # 运行元智能体
    final_state = coordinator.run(symbol)
    
    # 返回结果
    return {
        "symbol": symbol,
        "start_time": final_state["start_time"],
        "total_execution_time": final_state["total_execution_time"],
        "phases_completed": final_state["phases_completed"],
        "execution_times": final_state["execution_times"],
        "errors": final_state["errors"],
        "data_collection_status": final_state["data_collection_status"],
        "structure_analysis": final_state["structure_analysis"],
        "dynamics_analysis": final_state["dynamics_analysis"],
        "sentiment_analysis": final_state["sentiment_analysis"],
        "decision": final_state["decision"],
        "messages": final_state["messages"]
    }


if __name__ == "__main__":
    # 测试元智能体
    result = run_meta_agent_analysis("btcusdt")
    print("\n✅ 元智能体测试完成！")
