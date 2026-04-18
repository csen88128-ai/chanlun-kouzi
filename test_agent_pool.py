#!/usr/bin/env python3
"""
测试AgentPool修复
"""
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.agent_pool import AgentPool
from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.structure_analyzer_agent_v2 import build_agent as build_structure_analyzer
from multi_agents.dynamics_analyzer_agent import build_agent as build_dynamics_analyzer
from multi_agents.sentiment_analyzer_agent import build_agent as build_sentiment_analyzer
from multi_agents.decision_maker_agent_v3 import build_agent as build_decision_maker


def test_agent_pool():
    """测试AgentPool"""
    print("=" * 60)
    print("测试AgentPool修复")
    print("=" * 60)

    # 1. 测试注册
    print("\n[1] 注册智能体...")
    AgentPool.register_agent("data_collector", build_data_collector)
    AgentPool.register_agent("structure_analyzer", build_structure_analyzer)
    AgentPool.register_agent("dynamics_analyzer", build_dynamics_analyzer)
    AgentPool.register_agent("sentiment_analyzer", build_sentiment_analyzer)
    AgentPool.register_agent("decision_maker", build_decision_maker)

    stats = AgentPool.get_stats()
    print(f"  ✓ 已注册构建器: {stats['registered_builders']}")
    print(f"  ✓ 已加载实例: {stats['total_agents']}")
    print(f"  ✓ 智能体类型: {stats['agent_types']}")

    # 2. 测试获取智能体
    print("\n[2] 获取智能体...")
    try:
        dc_agent = AgentPool.get_agent("data_collector")
        print(f"  ✓ data_collector: {type(dc_agent).__name__}")
    except Exception as e:
        print(f"  ✗ data_collector: {e}")

    try:
        sa_agent = AgentPool.get_agent("structure_analyzer")
        print(f"  ✓ structure_analyzer: {type(sa_agent).__name__}")
    except Exception as e:
        print(f"  ✗ structure_analyzer: {e}")

    try:
        da_agent = AgentPool.get_agent("dynamics_analyzer")
        print(f"  ✓ dynamics_analyzer: {type(da_agent).__name__}")
    except Exception as e:
        print(f"  ✗ dynamics_analyzer: {e}")

    try:
        sent_agent = AgentPool.get_agent("sentiment_analyzer")
        print(f"  ✓ sentiment_analyzer: {type(sent_agent).__name__}")
    except Exception as e:
        print(f"  ✗ sentiment_analyzer: {e}")

    try:
        dm_agent = AgentPool.get_agent("decision_maker")
        print(f"  ✓ decision_maker: {type(dm_agent).__name__}")
    except Exception as e:
        print(f"  ✗ decision_maker: {e}")

    # 3. 再次检查统计
    print("\n[3] 检查统计...")
    stats = AgentPool.get_stats()
    print(f"  ✓ 已加载实例: {stats['total_agents']}")
    print(f"  ✓ 智能体类型: {stats['agent_types']}")

    # 4. 测试复用
    print("\n[4] 测试复用...")
    dc_agent2 = AgentPool.get_agent("data_collector")
    print(f"  ✓ 复用data_collector: {dc_agent is dc_agent2}")

    # 5. 测试便捷函数
    print("\n[5] 测试便捷函数...")
    from multi_agents.agent_pool import get_or_create_agent

    dc_agent3 = get_or_create_agent("data_collector")
    print(f"  ✓ get_or_create_agent: {type(dc_agent3).__name__}")
    print(f"  ✓ 复用成功: {dc_agent3 is dc_agent}")

    print("\n" + "=" * 60)
    print("AgentPool测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_agent_pool()
