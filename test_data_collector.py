#!/usr/bin/env python3
"""
测试数据采集智能体
"""
import sys
import time
import json
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.agent_pool import AgentPool
from multi_agents.data_collector_agent import build_agent as build_data_collector
from multi_agents.data_validator import DataValidator


def test_data_collector():
    """测试数据采集智能体"""
    print("=" * 60)
    print("测试数据采集智能体")
    print("=" * 60)

    # 1. 注册并获取智能体
    print("\n[1] 初始化智能体...")
    AgentPool.register_agent("data_collector", build_data_collector)
    agent = AgentPool.get_agent("data_collector")
    print(f"  ✓ 智能体类型: {type(agent).__name__}")

    # 2. 调用智能体
    print("\n[2] 执行数据采集...")
    start_time = time.time()

    config = {"configurable": {"thread_id": "test_data_collector"}}

    try:
        from langchain_core.messages import HumanMessage

        response = agent.invoke(
            {"messages": [HumanMessage(content="获取BTCUSDT 4小时K线数据，200根。请返回JSON格式的数据摘要。")]},
            config
        )

        execution_time = time.time() - start_time

        # 提取输出
        output = response["messages"][-1].content if response["messages"] else ""
        print(f"  ✓ 执行完成，耗时: {execution_time:.2f}秒")
        print(f"  ✓ 输出长度: {len(output)} 字符")

        # 提取JSON
        import re
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            json_str = json_match.group(0)
            print(f"  ✓ 提取JSON成功，长度: {len(json_str)} 字符")

            # 解析JSON
            data = json.loads(json_str)
            print(f"  ✓ JSON解析成功")
            print(f"\n  数据内容:")
            print(f"    - 状态: {data.get('status')}")
            print(f"    - 最新价格: {data.get('latest_price')}")
            print(f"    - 最高价: {data.get('highest')}")
            print(f"    - 最低价: {data.get('lowest')}")
            print(f"    - 24h涨跌幅: {data.get('h24_change')}%")
            print(f"    - 时间范围: {data.get('time_range')}")

            # 3. 验证数据
            print("\n[3] 验证数据...")
            dv = DataValidator()
            validation = dv.validate_data(json_str, "data_collector")

            print(f"  ✓ 验证状态: {validation['status']}")
            print(f"  ✓ 通过: {validation['pass']}, 警告: {validation['warning']}, 错误: {validation['error']}")
            print(f"  ✓ 消息: {validation['message']}")

            # 4. 详细验证结果
            if validation['validations']:
                print(f"\n  验证详情:")
                for v in validation['validations'][:5]:  # 只显示前5个
                    symbol = "✓" if v['level'] == "通过" else "!" if v['level'] == "警告" else "✗"
                    print(f"    {symbol} {v['item']}: {v['level']} - {v['message']}")

            return True

        else:
            print(f"  ✗ 未找到JSON格式")
            print(f"  原始输出: {output[:500]}")
            return False

    except Exception as e:
        print(f"  ✗ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_data_collector()

    print("\n" + "=" * 60)
    if success:
        print("数据采集智能体测试成功！")
    else:
        print("数据采集智能体测试失败！")
    print("=" * 60)
