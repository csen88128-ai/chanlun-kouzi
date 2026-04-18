#!/usr/bin/env python3
"""
测试并行执行效果
比较串行执行和并行执行的时间差异
"""
import sys
import time
import asyncio
import json
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.agent_pool import AgentPool
from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.structure_analyzer_agent_v2 import build_agent as build_structure_analyzer
from multi_agents.dynamics_analyzer_agent import build_agent as build_dynamics_analyzer
from multi_agents.sentiment_analyzer_agent import build_agent as build_sentiment_analyzer
from multi_agents.decision_maker_agent_v3 import build_agent as build_decision_maker
from langchain_core.messages import HumanMessage
import re


async def run_agent_async(agent, message, config, agent_name):
    """异步运行单个智能体"""
    try:
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=message)]},
            config
        )
        output = response["messages"][-1].content
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            return {
                "agent_name": agent_name,
                "success": True,
                "data": json.loads(json_match.group(0))
            }
        else:
            return {
                "agent_name": agent_name,
                "success": False,
                "error": "未找到JSON"
            }
    except Exception as e:
        return {
            "agent_name": agent_name,
            "success": False,
            "error": str(e)
        }


async def parallel_execution_workflow(data_result, config):
    """并行执行工作流（结构、动力学、情绪分析）"""
    print("=" * 60)
    print("并行执行工作流")
    print("=" * 60)

    start_time = time.time()

    # 并行执行三个分析智能体
    tasks = []
    results = {}

    # 结构分析
    AgentPool.register_agent("structure_analyzer", build_structure_analyzer)
    sa_agent = AgentPool.get_agent("structure_analyzer")
    tasks.append(run_agent_async(
        sa_agent,
        json.dumps(data_result),
        config,
        "structure_analyzer"
    ))

    # 动力学分析
    AgentPool.register_agent("dynamics_analyzer", build_dynamics_analyzer)
    da_agent = AgentPool.get_agent("dynamics_analyzer")
    tasks.append(run_agent_async(
        da_agent,
        json.dumps(data_result),
        config,
        "dynamics_analyzer"
    ))

    # 市场情绪分析
    AgentPool.register_agent("sentiment_analyzer", build_sentiment_analyzer)
    sent_agent = AgentPool.get_agent("sentiment_analyzer")
    tasks.append(run_agent_async(
        sent_agent,
        "获取当前BTC市场的恐惧贪婪指数",
        config,
        "sentiment_analyzer"
    ))

    # 等待所有任务完成
    parallel_results = await asyncio.gather(*tasks)

    execution_time = time.time() - start_time

    print(f"\n并行执行结果:")
    for result in parallel_results:
        if result["success"]:
            print(f"  ✓ {result['agent_name']}: 成功")
            results[result["agent_name"]] = result["data"]
        else:
            print(f"  ✗ {result['agent_name']}: {result['error']}")

    print(f"\n并行执行总耗时: {execution_time:.2f}秒")

    return results, execution_time


def serial_execution_workflow(data_result, config):
    """串行执行工作流"""
    print("=" * 60)
    print("串行执行工作流")
    print("=" * 60)

    start_time = time.time()
    execution_times = {}
    results = {}

    # 结构分析
    print("\n[1] 结构分析智能体")
    task_start = time.time()
    try:
        AgentPool.register_agent("structure_analyzer", build_structure_analyzer)
        sa_agent = AgentPool.get_agent("structure_analyzer")

        response = sa_agent.invoke(
            {"messages": [HumanMessage(content=json.dumps(data_result))]},
            config
        )

        output = response["messages"][-1].content
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            results['structure_analyzer'] = json.loads(json_match.group(0))
            execution_times['structure_analyzer'] = time.time() - task_start
            print(f"  ✓ 结构分析成功，耗时: {execution_times['structure_analyzer']:.2f}秒")
        else:
            print(f"  ✗ 结构分析失败：未找到JSON")
    except Exception as e:
        print(f"  ✗ 结构分析失败: {e}")

    # 动力学分析
    print("\n[2] 动力学分析智能体")
    task_start = time.time()
    try:
        AgentPool.register_agent("dynamics_analyzer", build_dynamics_analyzer)
        da_agent = AgentPool.get_agent("dynamics_analyzer")

        response = da_agent.invoke(
            {"messages": [HumanMessage(content=json.dumps(data_result))]},
            config
        )

        output = response["messages"][-1].content
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            results['dynamics_analyzer'] = json.loads(json_match.group(0))
            execution_times['dynamics_analyzer'] = time.time() - task_start
            print(f"  ✓ 动力学分析成功，耗时: {execution_times['dynamics_analyzer']:.2f}秒")
        else:
            print(f"  ✗ 动力学分析失败：未找到JSON")
    except Exception as e:
        print(f"  ✗ 动力学分析失败: {e}")

    # 市场情绪分析
    print("\n[3] 市场情绪智能体")
    task_start = time.time()
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
            results['sentiment_analyzer'] = json.loads(json_match.group(0))
            execution_times['sentiment_analyzer'] = time.time() - task_start
            print(f"  ✓ 市场情绪分析成功，耗时: {execution_times['sentiment_analyzer']:.2f}秒")
        else:
            print(f"  ✗ 市场情绪分析失败：未找到JSON")
    except Exception as e:
        print(f"  ✗ 市场情绪分析失败: {e}")

    total_time = time.time() - start_time

    print(f"\n串行执行总耗时: {total_time:.2f}秒")

    return results, total_time


def test_parallel_vs_serial():
    """测试并行与串行执行的对比"""
    print("=" * 60)
    print("测试并行执行 vs 串行执行")
    print("=" * 60)

    config = {"configurable": {"thread_id": "test_parallel"}}

    # 1. 数据采集（两种模式都需要）
    print("\n[0] 数据采集智能体（准备测试数据）")
    start_time = time.time()
    try:
        AgentPool.register_agent("data_collector", build_data_collector)
        dc_agent = AgentPool.get_agent("data_collector")

        response = dc_agent.invoke(
            {"messages": [HumanMessage(content="获取BTCUSDT 4小时K线数据，200根。请返回JSON格式的数据摘要。")]},
            config
        )

        output = response["messages"][-1].content
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            data_result = json.loads(json_match.group(0))
            print(f"  ✓ 数据采集成功，耗时: {time.time() - start_time:.2f}秒")
            print(f"  ✓ 最新价格: {data_result.get('latest_price')}")
        else:
            print(f"  ✗ 数据采集失败：未找到JSON")
            return False
    except Exception as e:
        print(f"  ✗ 数据采集失败: {e}")
        return False

    # 2. 串行执行
    print("\n\n")
    serial_results, serial_time = serial_execution_workflow(data_result, config)

    # 3. 并行执行
    print("\n\n")
    parallel_results, parallel_time = asyncio.run(parallel_execution_workflow(data_result, config))

    # 4. 性能对比
    print("\n\n")
    print("=" * 60)
    print("性能对比报告")
    print("=" * 60)

    print(f"\n执行时间对比:")
    print(f"  - 串行执行: {serial_time:.2f}秒")
    print(f"  - 并行执行: {parallel_time:.2f}秒")
    print(f"  - 节省时间: {serial_time - parallel_time:.2f}秒")
    print(f"  - 性能提升: {((serial_time - parallel_time) / serial_time * 100):.1f}%")

    print(f"\n结果对比:")
    agents = ['structure_analyzer', 'dynamics_analyzer', 'sentiment_analyzer']
    for agent in agents:
        if agent in serial_results and agent in parallel_results:
            print(f"  ✓ {agent}: 两种模式都成功")
        elif agent in serial_results:
            print(f"  ! {agent}: 仅串行成功")
        elif agent in parallel_results:
            print(f"  ! {agent}: 仅并行成功")
        else:
            print(f"  ✗ {agent}: 两种模式都失败")

    # 保存报告
    report_file = "/workspace/projects/data/parallel_vs_serial_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "serial_time": serial_time,
            "parallel_time": parallel_time,
            "time_saved": serial_time - parallel_time,
            "performance_improvement": (serial_time - parallel_time) / serial_time * 100,
            "serial_results": serial_results,
            "parallel_results": parallel_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存到: {report_file}")

    return True


if __name__ == "__main__":
    success = test_parallel_vs_serial()

    if success:
        print("\n✓ 并行执行测试完成！")
    else:
        print("\n✗ 并行执行测试失败！")

    sys.exit(0 if success else 1)
