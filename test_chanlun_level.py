#!/usr/bin/env python3
"""
测试缠论多级别分析
"""
import sys
import time
import json
import re
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.agent_pool import AgentPool
from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.structure_analyzer_agent_v2 import build_agent as build_structure_analyzer
from langchain_core.messages import HumanMessage


def test_chanlun_level_analysis():
    """测试缠论多级别分析"""
    print("=" * 80)
    print("测试缠论多级别分析")
    print("=" * 80)

    # 1. 数据采集
    print("\n[1] 数据采集智能体")
    start_time = time.time()
    try:
        AgentPool.register_agent("data_collector", build_data_collector)
        dc_agent = AgentPool.get_agent("data_collector")
        config = {"configurable": {"thread_id": "test_chanlun_level"}}

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
            print(f"  ✗ 数据采集失败")
            return False
    except Exception as e:
        print(f"  ✗ 数据采集失败: {e}")
        return False

    # 2. 结构分析（重点测试级别信息）
    print("\n[2] 结构分析智能体 - 缠论多级别分析")
    start_time = time.time()
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
            structure_result = json.loads(json_match.group(0))
            print(f"  ✓ 结构分析成功，耗时: {time.time() - start_time:.2f}秒")

            # 显示级别信息
            if 'level_info' in structure_result:
                level_info = structure_result['level_info']
                print(f"\n  📊 级别信息:")
                print(f"    时间级别: {level_info.get('time_level')}")
                print(f"    时间级别含义: {level_info.get('time_level_meaning')}")
                print(f"    中枢级别: {level_info.get('zhongshu_level')}级")
                print(f"    买卖点级别: {level_info.get('buy_sell_point_level')}级")
                print(f"    买卖点含义: {level_info.get('buy_sell_point_meaning')}")
                print(f"    交易意义: {level_info.get('trading_significance')}")
                print(f"    建议持仓周期: {level_info.get('holding_period')}")

            # 显示买卖点信息
            if 'buy_sell_points' in structure_result:
                buy_sell_points = structure_result['buy_sell_points']
                if buy_sell_points.get('latest_signal'):
                    latest_signal = buy_sell_points['latest_signal']
                    print(f"\n  🎯 最新买卖点信号:")
                    print(f"    类型: {latest_signal.get('type')}")
                    print(f"    价格: {latest_signal.get('price')}")
                    print(f"    级别: {latest_signal.get('level')}级")
                    print(f"    强度: {latest_signal.get('strength')}")
                    print(f"    是否买点: {latest_signal.get('is_buy', 'N/A')}")

                    # 级别解读
                    level = latest_signal.get('level')
                    point_type = latest_signal.get('type')

                    level_meaning = {
                        1: "短线信号",
                        2: "中线信号",
                        3: "长线信号"
                    }.get(level, "未知")

                    print(f"\n  📝 级别解读:")
                    print(f"    这是4h时间级别下的{level}级{point_type}")
                    print(f"    信号意义: {level_meaning}")
                    print(f"    适用场景: {level_info.get('holding_period')}")
            else:
                print(f"  ✗ 未找到买卖点信息")
        else:
            print(f"  ✗ 结构分析失败：未找到JSON")
            return False
    except Exception as e:
        print(f"  ✗ 结构分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)

    print(f"\n✅ 系统已支持缠论多级别分析")
    print(f"\n当前系统级别:")
    print(f"  - 时间级别: 4h（4小时K线）")
    print(f"  - 适用场景: 中线交易")
    print(f"  - 建议持仓: 2-7天")
    print(f"  - 信号类型: {level}级买卖点（{level_meaning}）")

    print(f"\n如果需要其他级别分析:")
    print(f"  - 1h级别: 短线交易，持仓1-3天")
    print(f"  - 日线级别: 长线交易，持仓1-4周")
    print(f"  - 15m级别: 超短线，持仓2-6小时")

    # 保存结果
    report_file = "/workspace/projects/data/chanlun_level_test_result.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "data_result": data_result,
            "structure_result": structure_result,
            "level_info": structure_result.get('level_info'),
            "latest_signal": structure_result.get('buy_sell_points', {}).get('latest_signal')
        }, f, ensure_ascii=False, indent=2)

    print(f"\n详细结果已保存到: {report_file}")

    return True


if __name__ == "__main__":
    success = test_chanlun_level_analysis()

    if success:
        print("\n✅ 缠论多级别分析测试成功！")
    else:
        print("\n❌ 缠论多级别分析测试失败！")

    sys.exit(0 if success else 1)
