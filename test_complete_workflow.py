#!/usr/bin/env python3
"""
测试完整工作流
"""
import sys
import time
import json
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.agent_pool import AgentPool
from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.structure_analyzer_agent_v2 import build_agent as build_structure_analyzer
from multi_agents.dynamics_analyzer_agent import build_agent as build_dynamics_analyzer
from multi_agents.sentiment_analyzer_agent import build_agent as build_sentiment_analyzer
from multi_agents.decision_maker_agent_v3 import build_agent as build_decision_maker
from multi_agents.data_validator import DataValidator
from multi_agents.logic_validator import LogicValidator
from langchain_core.messages import HumanMessage


def test_complete_workflow():
    """测试完整工作流"""
    print("=" * 60)
    print("测试完整工作流")
    print("=" * 60)

    execution_times = {}
    results = {}

    # 1. 数据采集
    print("\n[1] 数据采集智能体")
    start_time = time.time()
    try:
        AgentPool.register_agent("data_collector", build_data_collector)
        dc_agent = AgentPool.get_agent("data_collector")
        config = {"configurable": {"thread_id": "test_workflow"}}

        response = dc_agent.invoke(
            {"messages": [HumanMessage(content="获取BTCUSDT 4小时K线数据，200根。请返回JSON格式的数据摘要。")]},
            config
        )

        output = response["messages"][-1].content
        import re
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            results['data'] = json.loads(json_match.group(0))
            execution_times['data_collector'] = time.time() - start_time
            print(f"  ✓ 数据采集成功，耗时: {execution_times['data_collector']:.2f}秒")
            print(f"  ✓ 最新价格: {results['data'].get('latest_price')}")
        else:
            print(f"  ✗ 数据采集失败：未找到JSON")
            return False
    except Exception as e:
        print(f"  ✗ 数据采集失败: {e}")
        return False

    # 2. 结构分析
    print("\n[2] 结构分析智能体")
    start_time = time.time()
    try:
        AgentPool.register_agent("structure_analyzer", build_structure_analyzer)
        sa_agent = AgentPool.get_agent("structure_analyzer")

        response = sa_agent.invoke(
            {"messages": [HumanMessage(content=json.dumps(results['data']))]},
            config
        )

        output = response["messages"][-1].content
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            results['structure'] = json.loads(json_match.group(0))
            execution_times['structure_analyzer'] = time.time() - start_time
            print(f"  ✓ 结构分析成功，耗时: {execution_times['structure_analyzer']:.2f}秒")
        else:
            print(f"  ✗ 结构分析失败：未找到JSON")
            return False
    except Exception as e:
        print(f"  ✗ 结构分析失败: {e}")
        return False

    # 3. 动力学分析
    print("\n[3] 动力学分析智能体")
    start_time = time.time()
    try:
        AgentPool.register_agent("dynamics_analyzer", build_dynamics_analyzer)
        da_agent = AgentPool.get_agent("dynamics_analyzer")

        response = da_agent.invoke(
            {"messages": [HumanMessage(content=json.dumps(results['data']))]},
            config
        )

        output = response["messages"][-1].content
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            results['dynamics'] = json.loads(json_match.group(0))
            execution_times['dynamics_analyzer'] = time.time() - start_time
            print(f"  ✓ 动力学分析成功，耗时: {execution_times['dynamics_analyzer']:.2f}秒")
        else:
            print(f"  ✗ 动力学分析失败：未找到JSON")
            return False
    except Exception as e:
        print(f"  ✗ 动力学分析失败: {e}")
        return False

    # 4. 市场情绪分析
    print("\n[4] 市场情绪智能体")
    start_time = time.time()
    try:
        AgentPool.register_agent("sentiment_analyzer", build_sentiment_analyzer)
        sent_agent = AgentPool.get_agent("sentiment_analyzer")

        response = sent_agent.invoke(
            {"messages": [HumanMessage(content="获取当前BTC市场的恐惧贪婪指数")]},
            config
        )

        output = response["messages"][-1].content
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            results['sentiment'] = json.loads(json_match.group(0))
            execution_times['sentiment_analyzer'] = time.time() - start_time
            print(f"  ✓ 市场情绪分析成功，耗时: {execution_times['sentiment_analyzer']:.2f}秒")
        else:
            print(f"  ✗ 市场情绪分析失败：未找到JSON")
            return False
    except Exception as e:
        print(f"  ✗ 市场情绪分析失败: {e}")
        return False

    # 5. 决策制定
    print("\n[5] 决策制定智能体")
    start_time = time.time()
    try:
        AgentPool.register_agent("decision_maker", build_decision_maker)
        dm_agent = AgentPool.get_agent("decision_maker")

        input_msg = f"""基于以下分析结果制定交易决策:

数据采集:
{json.dumps(results['data'], ensure_ascii=False)[:500]}

结构分析:
{json.dumps(results['structure'], ensure_ascii=False)[:500]}

动力学分析:
{json.dumps(results['dynamics'], ensure_ascii=False)[:500]}

市场情绪:
{json.dumps(results['sentiment'], ensure_ascii=False)[:500]}
"""

        response = dm_agent.invoke(
            {"messages": [HumanMessage(content=input_msg)]},
            config
        )

        output = response["messages"][-1].content
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            results['decision'] = json.loads(json_match.group(0))
            execution_times['decision_maker'] = time.time() - start_time
            print(f"  ✓ 决策制定成功，耗时: {execution_times['decision_maker']:.2f}秒")
            print(f"  ✓ 决策: {results['decision'].get('decision')}")
            print(f"  ✓ 得分: {results['decision'].get('score')}")
        else:
            print(f"  ✗ 决策制定失败：未找到JSON")
            return False
    except Exception as e:
        print(f"  ✗ 决策制定失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 总结
    print("\n" + "=" * 60)
    print("工作流测试完成")
    print("=" * 60)

    total_time = sum(execution_times.values())
    print(f"\n执行时间统计:")
    for agent, exec_time in execution_times.items():
        print(f"  - {agent}: {exec_time:.2f}秒")
    print(f"  - 总计: {total_time:.2f}秒")

    print(f"\n决策结果:")
    print(f"  - 决策: {results['decision'].get('decision')}")
    print(f"  - 当前价格: {results['decision'].get('current_price')}")
    print(f"  - 得分: {results['decision'].get('score')}")

    trading_plan = results['decision'].get('trading_plan', {})
    if trading_plan:
        print(f"\n交易计划:")
        print(f"  - 入场价: {trading_plan.get('entry')}")
        print(f"  - 仓位: {trading_plan.get('position_size')}")
        print(f"  - 止盈: {trading_plan.get('take_profit')}")
        print(f"  - 止损: {trading_plan.get('stop_loss')}")

    # 保存结果
    report_file = "/workspace/projects/data/workflow_test_result.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "execution_times": execution_times,
            "total_time": total_time,
            "results": results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n结果已保存到: {report_file}")

    return True


if __name__ == "__main__":
    success = test_complete_workflow()

    if success:
        print("\n✓ 工作流测试成功！")
    else:
        print("\n✗ 工作流测试失败！")

    sys.exit(0 if success else 1)
