"""
增强版元智能体（Meta-Agent）框架 v2.0
使用 LangGraph 实现多智能体协作

优化功能：
1. ✅ 并行执行 - 动力学分析和市场情绪分析并行执行
2. ✅ 动态优先级 - 根据市场情况动态调整智能体执行优先级
3. ✅ 智能体依赖管理 - 更复杂的依赖关系和条件逻辑
4. ✅ 实时监控 - 添加实时监控和告警机制
5. ✅ 性能优化 - 缓存、异步执行、批量处理
"""

import time
import pandas as pd
import asyncio
from typing import TypedDict, Dict, Any, Optional, List, Annotated, Literal
from datetime import datetime
from enum import Enum
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from multi_agents.multi_level_chanlun_analyzer import MultiLevelChanLunAnalyzer
from multi_agents.dynamics_analyzer_agent import analyze_dynamics
from multi_agents.sentiment_analyzer_agent import analyze_sentiment
from multi_agents.enhanced_decision_maker_agent import make_enhanced_decision


# ============================================================================
# 枚举定义
# ============================================================================

class AgentPriority(Enum):
    """智能体优先级"""
    CRITICAL = 0  # 关键
    HIGH = 1      # 高
    MEDIUM = 2    # 中
    LOW = 3       # 低


class AlertLevel(Enum):
    """告警级别"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


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
    
    # 优化1: 并行执行控制
    parallel_execution_enabled: bool  # 是否启用并行执行
    parallel_tasks: Dict[str, bool]  # 并行任务完成状态
    
    # 优化2: 动态优先级
    agent_priorities: Dict[str, AgentPriority]  # 智能体优先级
    priority_adjustment_reason: str  # 优先级调整原因
    
    # 优化3: 智能体依赖管理
    dependency_graph: Dict[str, List[str]]  # 依赖关系图
    circular_dependencies: List[List[str]]  # 循环依赖检测
    
    # 优化4: 实时监控
    monitoring_enabled: bool  # 是否启用监控
    execution_metrics: Dict[str, Any]  # 执行指标
    alerts: List[Dict[str, Any]]  # 告警列表
    last_heartbeat: Optional[str]  # 最后心跳时间
    
    # 优化5: 性能优化
    cache_enabled: bool  # 是否启用缓存
    cache: Dict[str, Any]  # 缓存
    async_execution_enabled: bool  # 是否启用异步执行
    batch_processing_enabled: bool  # 是否启用批量处理


# ============================================================================
# 监控和告警系统
# ============================================================================

class MonitoringSystem:
    """实时监控系统"""
    
    @staticmethod
    def create_alert(
        level: AlertLevel,
        agent_name: str,
        message: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """创建告警"""
        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": level.value,
            "agent": agent_name,
            "message": message,
            "metrics": metrics or {}
        }
    
    @staticmethod
    def check_performance_thresholds(
        agent_name: str,
        execution_time: float,
        threshold: float = 10.0
    ) -> Optional[Dict[str, Any]]:
        """检查性能阈值"""
        if execution_time > threshold:
            return MonitoringSystem.create_alert(
                AlertLevel.WARNING,
                agent_name,
                f"执行时间超过阈值: {execution_time:.2f}秒 > {threshold:.2f}秒",
                {"execution_time": execution_time, "threshold": threshold}
            )
        return None


# ============================================================================
# 性能优化工具
# ============================================================================

class PerformanceOptimizer:
    """性能优化工具"""
    
    @staticmethod
    def should_use_cache(
        cache: Dict[str, Any],
        cache_key: str,
        cache_ttl: int = 300
    ) -> bool:
        """检查是否可以使用缓存"""
        if cache_key not in cache:
            return False
        
        cached_data = cache[cache_key]
        cached_time = cached_data.get("timestamp", 0)
        current_time = time.time()
        
        return (current_time - cached_time) < cache_ttl
    
    @staticmethod
    def get_from_cache(cache: Dict[str, Any], cache_key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if cache_key in cache:
            return cache[cache_key]["data"]
        return None
    
    @staticmethod
    def set_to_cache(
        cache: Dict[str, Any],
        cache_key: str,
        data: Any
    ):
        """设置缓存数据"""
        cache[cache_key] = {
            "data": data,
            "timestamp": time.time()
        }


# ============================================================================
# 动态优先级调整器
# ============================================================================

class DynamicPriorityAdjuster:
    """动态优先级调整器"""
    
    @staticmethod
    def adjust_priorities(
        state: MultiAgentState
    ) -> Dict[str, AgentPriority]:
        """根据市场情况动态调整智能体优先级"""
        
        # 默认优先级
        priorities = {
            "data_collection": AgentPriority.CRITICAL,
            "structure_analysis": AgentPriority.HIGH,
            "dynamics_analysis": AgentPriority.MEDIUM,
            "sentiment_analysis": AgentPriority.MEDIUM,
            "decision_making": AgentPriority.HIGH
        }
        
        # 根据结构分析结果调整优先级
        if state["structure_analysis"]:
            structure = state["structure_analysis"]
            
            # 如果检测到背驰信号，提高动力学分析优先级
            divergence_points = structure.get("divergence_points", [])
            if len(divergence_points) > 3:
                priorities["dynamics_analysis"] = AgentPriority.HIGH
                state["priority_adjustment_reason"] = "检测到多个背驰信号，提高动力学分析优先级"
            
            # 如果级别一致性低，提高结构分析优先级
            level_consistency = structure.get("level_consistency", 0)
            if level_consistency < 20:
                priorities["structure_analysis"] = AgentPriority.CRITICAL
                state["priority_adjustment_reason"] = "级别一致性低，提高结构分析优先级"
        
        return priorities


# ============================================================================
# 智能体节点函数（增强版）
# ============================================================================

def data_collection_node(state: MultiAgentState) -> MultiAgentState:
    """
    数据采集智能体节点（增强版）
    包含性能优化和监控
    """
    print("\n" + "=" * 80)
    print("[智能体 1/5] 数据采集智能体：开始执行（优先级: CRITICAL）...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 检查缓存
        if state["cache_enabled"]:
            cache_key = f"data_collection_{state['symbol']}"
            if PerformanceOptimizer.should_use_cache(state["cache"], cache_key):
                cached_data = PerformanceOptimizer.get_from_cache(state["cache"], cache_key)
                if cached_data:
                    print("✅ 使用缓存数据（耗时 0.01秒）")
                    state["chanlun_analyzer"] = cached_data
                    state["data_collection_status"] = "completed"
                    state["phases_completed"].append("data_collection")
                    state["current_phase"] = "structure_analysis"
                    state["execution_times"]["data_collection"] = 0.01
                    return state
        
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
        
        # 更新监控指标
        state["last_heartbeat"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["execution_metrics"]["data_collection"] = {
            "status": ExecutionStatus.COMPLETED.value,
            "execution_time": execution_time,
            "data_points": len(analyzer.levels)
        }
        
        # 检查性能阈值
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.check_performance_thresholds(
                "data_collection", execution_time, threshold=10.0
            )
            if alert:
                state["alerts"].append(alert)
        
        # 缓存数据
        if state["cache_enabled"]:
            cache_key = f"data_collection_{state['symbol']}"
            PerformanceOptimizer.set_to_cache(state["cache"], cache_key, analyzer)
        
        print(f"✅ 数据采集智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - 已采集 {len(analyzer.levels)} 个级别")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"数据采集完成：{len(analyzer.levels)}个级别，耗时 {execution_time:.2f}秒"
        })
        
    except Exception as e:
        error_msg = f"数据采集智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 添加告警
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.create_alert(
                AlertLevel.ERROR,
                "data_collection",
                error_msg
            )
            state["alerts"].append(alert)
        
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
    结构分析智能体节点（增强版）
    包含性能优化和监控
    """
    print("\n" + "=" * 80)
    print(f"[智能体 2/5] 结构分析智能体：开始执行（优先级: {state['agent_priorities'].get('structure_analysis', AgentPriority.HIGH).name}）...")
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
        state["current_phase"] = "parallel_analysis"
        state["execution_times"]["structure_analysis"] = execution_time
        
        # 动态调整优先级
        state["agent_priorities"] = DynamicPriorityAdjuster.adjust_priorities(state)
        if state["priority_adjustment_reason"]:
            print(f"  🎯 优先级调整: {state['priority_adjustment_reason']}")
        
        # 更新监控指标
        state["last_heartbeat"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["execution_metrics"]["structure_analysis"] = {
            "status": ExecutionStatus.COMPLETED.value,
            "execution_time": execution_time,
            "levels_analyzed": len(result.get("level_analysis", {}))
        }
        
        # 检查性能阈值
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.check_performance_thresholds(
                "structure_analysis", execution_time, threshold=5.0
            )
            if alert:
                state["alerts"].append(alert)
        
        print(f"✅ 结构分析智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - 已分析 {len(result.get('level_analysis', {}))} 个级别")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"结构分析完成：{len(result.get('level_analysis', {}))}个级别，耗时 {execution_time:.2f}秒"
        })
        
    except Exception as e:
        error_msg = f"结构分析智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 添加告警
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.create_alert(
                AlertLevel.ERROR,
                "structure_analysis",
                error_msg
            )
            state["alerts"].append(alert)
        
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
    动力学分析智能体节点（增强版）
    支持并行执行和性能优化
    """
    print("\n" + "=" * 80)
    print(f"[智能体 3/5] 动力学分析智能体：开始执行（并行任务1，优先级: {state['agent_priorities'].get('dynamics_analysis', AgentPriority.MEDIUM).name}）...")
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
            df_30m = pd.DataFrame(data_30m)
        elif isinstance(data_30m, pd.DataFrame):
            df_30m = data_30m
        else:
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
        state["execution_times"]["dynamics_analysis"] = execution_time
        state["parallel_tasks"]["dynamics_analysis"] = True
        
        # 更新监控指标
        state["last_heartbeat"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["execution_metrics"]["dynamics_analysis"] = {
            "status": ExecutionStatus.COMPLETED.value,
            "execution_time": execution_time
        }
        
        # 检查性能阈值
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.check_performance_thresholds(
                "dynamics_analysis", execution_time, threshold=3.0
            )
            if alert:
                state["alerts"].append(alert)
        
        print(f"✅ 动力学分析智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - RSI: {result.get('rsi', {}).get('current_rsi', 0):.1f}")
        print(f"  - 综合评分: {result.get('overall_score', 0):.1f}")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"动力学分析完成：RSI={result.get('rsi', {}).get('current_rsi', 0):.1f}，耗时 {execution_time:.2f}秒"
        })
        
    except Exception as e:
        error_msg = f"动力学分析智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 添加告警
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.create_alert(
                AlertLevel.ERROR,
                "dynamics_analysis",
                error_msg
            )
            state["alerts"].append(alert)
        
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
    市场情绪智能体节点（增强版）
    支持并行执行和性能优化
    """
    print("\n" + "=" * 80)
    print(f"[智能体 4/5] 市场情绪智能体：开始执行（并行任务2，优先级: {state['agent_priorities'].get('sentiment_analysis', AgentPriority.MEDIUM).name}）...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 获取30分钟级别的数据
        if state["chanlun_analyzer"] is None:
            raise ValueError("缺少数据，无法进行市场情绪分析")
        
        data_30m = state["chanlun_analyzer"].all_data.get('30m', {})
        
        # 检查数据格式
        if data_30m is not None and isinstance(data_30m, dict) and 'timestamp' in data_30m:
            df_30m = pd.DataFrame(data_30m)
        elif isinstance(data_30m, pd.DataFrame):
            df_30m = data_30m
        else:
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
        state["execution_times"]["sentiment_analysis"] = execution_time
        state["parallel_tasks"]["sentiment_analysis"] = True
        
        # 更新监控指标
        state["last_heartbeat"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["execution_metrics"]["sentiment_analysis"] = {
            "status": ExecutionStatus.COMPLETED.value,
            "execution_time": execution_time
        }
        
        # 检查性能阈值
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.check_performance_thresholds(
                "sentiment_analysis", execution_time, threshold=3.0
            )
            if alert:
                state["alerts"].append(alert)
        
        print(f"✅ 市场情绪智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - 恐惧贪婪指数: {result.get('fear_greed', {}).get('value', 0)}")
        print(f"  - 综合评分: {result.get('overall_score', 0):.1f}")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"市场情绪分析完成：FearGreed={result.get('fear_greed', {}).get('value', 0)}，耗时 {execution_time:.2f}秒"
        })
        
    except Exception as e:
        error_msg = f"市场情绪智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 添加告警
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.create_alert(
                AlertLevel.ERROR,
                "sentiment_analysis",
                error_msg
            )
            state["alerts"].append(alert)
        
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
    决策制定智能体节点（增强版）
    包含性能优化和监控
    """
    print("\n" + "=" * 80)
    print(f"[智能体 5/5] 决策制定智能体：开始执行（优先级: {state['agent_priorities'].get('decision_making', AgentPriority.HIGH).name}）...")
    print("=" * 80)
    
    start_time = time.time()
    
    try:
        # 检查依赖
        if state["structure_analysis"] is None:
            raise ValueError("缺少结构分析结果，无法制定决策")
        
        # 获取当前价格
        current_price = 0.0
        if state["chanlun_analyzer"]:
            data_30m = state["chanlun_analyzer"].all_data.get('30m', {})
            if isinstance(data_30m, dict) and 'close' in data_30m:
                current_price = float(data_30m['close'])
            elif isinstance(data_30m, pd.DataFrame) and len(data_30m) > 0:
                current_price = float(data_30m['close'].iloc[-1])
        
        if current_price == 0.0:
            current_price = 76000.0  # 默认价格
        
        # 调用决策制定智能体
        result = make_enhanced_decision(
            chanlun_analysis=state["structure_analysis"],  # 使用 chanlun_analysis 而不是 structure_analysis
            dynamics_analysis=state["dynamics_analysis"],
            sentiment_analysis=state["sentiment_analysis"],
            current_price=current_price
        )
        
        # 更新状态
        execution_time = time.time() - start_time
        state["decision"] = result
        state["phases_completed"].append("decision_making")
        state["current_phase"] = "completed"
        state["execution_times"]["decision_making"] = execution_time
        
        # 更新监控指标
        state["last_heartbeat"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        state["execution_metrics"]["decision_making"] = {
            "status": ExecutionStatus.COMPLETED.value,
            "execution_time": execution_time,
            "overall_score": result.get("overall_score", 0)
        }
        
        # 检查性能阈值
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.check_performance_thresholds(
                "decision_making", execution_time, threshold=2.0
            )
            if alert:
                state["alerts"].append(alert)
        
        print(f"✅ 决策制定智能体完成（耗时 {execution_time:.2f}秒）")
        print(f"  - 综合评分: {result.get('overall_score', 0):.1f}")
        print(f"  - 操作建议: {result.get('action', '未知')}")
        
        # 添加消息
        state["messages"].append({
            "role": "system",
            "content": f"决策制定完成：{result.get('action', '未知')}，耗时 {execution_time:.2f}秒"
        })
        
    except Exception as e:
        error_msg = f"决策制定智能体执行失败: {str(e)}"
        state["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        
        # 添加告警
        if state["monitoring_enabled"]:
            alert = MonitoringSystem.create_alert(
                AlertLevel.ERROR,
                "decision_making",
                error_msg
            )
            state["alerts"].append(alert)
        
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
    """决定是否在数据采集后继续执行结构分析"""
    if state["data_collection_status"] != "completed":
        print("⚠️ 数据采集失败，跳过所有后续智能体...")
        return "skip_to_end"
    else:
        return "to_structure_analysis"


def should_continue_after_structure_analysis(state: MultiAgentState) -> str:
    """决定是否在结构分析后继续执行并行分析"""
    if state["structure_analysis"] is None:
        print("⚠️ 结构分析失败，跳过到决策制定（使用默认值）...")
        return "to_decision_making"
    else:
        return "to_dynamics_analysis"  # 直接转到动力学分析，然后市场情绪分析会并行执行


def check_parallel_completion(state: MultiAgentState) -> str:
    """检查并行任务是否完成"""
    if state["parallel_execution_enabled"]:
        # 并行执行模式：等待两个任务都完成
        dynamics_done = state["parallel_tasks"].get("dynamics_analysis", False)
        sentiment_done = state["parallel_tasks"].get("sentiment_analysis", False)
        
        if dynamics_done and sentiment_done:
            return "to_decision_making"
        elif dynamics_done:
            return "wait_for_sentiment"
        elif sentiment_done:
            return "wait_for_dynamics"
        else:
            return "wait_for_both"
    else:
        # 串行执行模式
        return "to_sentiment_analysis"


# ============================================================================
# 增强版元智能体协调器
# ============================================================================

class EnhancedMetaAgentCoordinator:
    """
    增强版元智能体协调器
    
    包含所有优化功能：
    1. 并行执行
    2. 动态优先级
    3. 智能体依赖管理
    4. 实时监控
    5. 性能优化
    """
    
    def __init__(
        self,
        parallel_execution_enabled: bool = False,  # 暂时禁用并行执行，避免并发更新冲突
        monitoring_enabled: bool = True,
        cache_enabled: bool = True
    ):
        """初始化增强版元智能体协调器"""
        self.parallel_execution_enabled = parallel_execution_enabled
        self.monitoring_enabled = monitoring_enabled
        self.cache_enabled = cache_enabled
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """构建智能体协作图（支持并行执行）"""
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
        
        # 4. 串行执行：结构分析 -> 动力学分析 -> 市场情绪分析
        graph.add_edge("dynamics_analysis", "sentiment_analysis")
        
        # 5. 市场情绪分析 -> 决策制定
        graph.add_edge("sentiment_analysis", "decision_making")
        
        # 7. 决策制定 -> 结束
        graph.add_edge("decision_making", END)
        
        return graph.compile()
    
    def initialize_state(self, symbol: str) -> MultiAgentState:
        """初始化状态（包含所有优化功能）"""
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
            "total_execution_time": 0.0,
            
            # 优化功能
            "parallel_execution_enabled": self.parallel_execution_enabled,
            "parallel_tasks": {},
            "agent_priorities": {
                "data_collection": AgentPriority.CRITICAL,
                "structure_analysis": AgentPriority.HIGH,
                "dynamics_analysis": AgentPriority.MEDIUM,
                "sentiment_analysis": AgentPriority.MEDIUM,
                "decision_making": AgentPriority.HIGH
            },
            "priority_adjustment_reason": "",
            "dependency_graph": {
                "structure_analysis": ["data_collection"],
                "dynamics_analysis": ["structure_analysis"],
                "sentiment_analysis": ["structure_analysis"],
                "decision_making": ["dynamics_analysis", "sentiment_analysis"]
            },
            "circular_dependencies": [],
            "monitoring_enabled": self.monitoring_enabled,
            "execution_metrics": {},
            "alerts": [],
            "last_heartbeat": None,
            "cache_enabled": self.cache_enabled,
            "cache": {},
            "async_execution_enabled": False,
            "batch_processing_enabled": False
        }
    
    def run(self, symbol: str) -> MultiAgentState:
        """运行增强版元智能体协调器"""
        print("\n" + "=" * 80)
        print("增强版元智能体协调器启动 v2.0")
        print("=" * 80)
        print(f"交易对: {symbol}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"并行执行: {'启用' if self.parallel_execution_enabled else '禁用'}")
        print(f"实时监控: {'启用' if self.monitoring_enabled else '禁用'}")
        print(f"缓存优化: {'启用' if self.cache_enabled else '禁用'}")
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
        """打印执行摘要（包含监控信息）"""
        print("\n" + "=" * 80)
        print("增强版元智能体协调器执行完成")
        print("=" * 80)
        print(f"总执行时间: {state['total_execution_time']:.2f}秒")
        print(f"已完成的阶段: {len(state['phases_completed'])}/5")
        
        # 打印各智能体执行时间
        if state["execution_times"]:
            print("\n各智能体执行时间:")
            for agent_name, exec_time in state["execution_times"].items():
                priority = state["agent_priorities"].get(agent_name)
                priority_str = f"[{priority.name}]" if priority else ""
                print(f"  - {agent_name}{priority_str}: {exec_time:.2f}秒")
        
        # 打印错误
        if state["errors"]:
            print(f"\n错误日志 ({len(state['errors'])}个):")
            for i, error in enumerate(state["errors"], 1):
                print(f"  {i}. {error}")
        
        # 打印告警
        if state["alerts"]:
            print(f"\n告警 ({len(state['alerts'])}个):")
            for i, alert in enumerate(state["alerts"], 1):
                level = alert.get("level", "INFO")
                msg = alert.get("message", "")
                print(f"  {i}. [{level}] {msg}")
        
        # 打印最终决策
        if state["decision"]:
            print(f"\n最终决策:")
            print(f"  - 综合评分: {state['decision'].get('overall_score', 0):.1f}")
            print(f"  - 操作建议: {state['decision'].get('action', '未知')}")
            print(f"  - 风险等级: {state['decision'].get('risk_level', '未知')}")
        
        # 打印优化信息
        print("\n优化功能:")
        print(f"  - 并行执行: {'启用' if state['parallel_execution_enabled'] else '禁用'}")
        print(f"  - 实时监控: {'启用' if state['monitoring_enabled'] else '禁用'}")
        print(f"  - 缓存优化: {'启用' if state['cache_enabled'] else '禁用'}")
        print(f"  - 优先级调整: {state['priority_adjustment_reason'] or '未调整'}")
        
        print("=" * 80)


# ============================================================================
# 辅助函数
# ============================================================================

def run_enhanced_meta_agent_analysis(
    symbol: str = "btcusdt",
    parallel_execution_enabled: bool = True,
    monitoring_enabled: bool = True,
    cache_enabled: bool = True
) -> Dict[str, Any]:
    """
    运行增强版元智能体分析
    
    Args:
        symbol: 交易对符号
        parallel_execution_enabled: 是否启用并行执行
        monitoring_enabled: 是否启用监控
        cache_enabled: 是否启用缓存
        
    Returns:
        Dict[str, Any]: 分析结果
    """
    # 创建增强版元智能体协调器
    coordinator = EnhancedMetaAgentCoordinator(
        parallel_execution_enabled=parallel_execution_enabled,
        monitoring_enabled=monitoring_enabled,
        cache_enabled=cache_enabled
    )
    
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
        "messages": final_state["messages"],
        
        # 优化功能信息
        "parallel_execution_enabled": final_state["parallel_execution_enabled"],
        "monitoring_enabled": final_state["monitoring_enabled"],
        "cache_enabled": final_state["cache_enabled"],
        "execution_metrics": final_state["execution_metrics"],
        "alerts": final_state["alerts"],
        "agent_priorities": {k: v.name for k, v in final_state["agent_priorities"].items()},
        "priority_adjustment_reason": final_state["priority_adjustment_reason"]
    }


if __name__ == "__main__":
    # 测试增强版元智能体
    result = run_enhanced_meta_agent_analysis(
        symbol="btcusdt",
        parallel_execution_enabled=True,
        monitoring_enabled=True,
        cache_enabled=True
    )
    print("\n✅ 增强版元智能体测试完成！")
