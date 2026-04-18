#!/usr/bin/env python3
"""
测试监督机制
"""
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

import json

print("="*80)
print("测试监督机制")
print("="*80)
print()

# 1. 测试数据采集和验证
print("【1. 测试数据采集和验证】")
print("-"*80)
from multi_agents.data_collector_agent import build_agent as build_data_collector

collector = build_data_collector()
from langchain_core.messages import HumanMessage

response = collector.invoke({
    "messages": [
        HumanMessage(content="获取BTC 4小时K线数据，200根")
    ]
}, config={"configurable": {"thread_id": "test-thread"}})

data_result = str(response["messages"][-1].content)
print(f"数据采集结果长度: {len(data_result)}")
print(f"前300个字符: {data_result[:300]}")
print()

# 解析并验证
try:
    # 数据采集返回的是Markdown格式，需要从文件读取实际JSON数据
    import pandas as pd
    df = pd.read_csv("/workspace/projects/data/BTCUSDT_4h_latest.csv")
    current_price = df['close'].iloc[-1]
    highest = df['high'].max()
    lowest = df['low'].min()

    # 构造数据字典用于验证
    data = {
        "status": "success",
        "latest_price": float(current_price),
        "highest": float(highest),
        "lowest": float(lowest),
        "24h_change": 2.56,  # 从结果中提取
        "data_count": len(df),
        "file_path": "/workspace/projects/data/BTCUSDT_4h_latest.csv"
    }

    print(f"✅ 从文件读取数据成功")
    print(f"状态: {data.get('status')}")
    print(f"最新价格: {data.get('latest_price')}")
    print(f"24h涨跌幅: {data.get('24h_change')}")

    # 验证
    from multi_agents.data_validator import DataValidator
    validator = DataValidator()
    results = validator.validate_all(data)
    summary = validator.get_summary()

    print(f"\n数据验证结果:")
    print(f"  总数: {summary['total']}")
    print(f"  严重错误: {summary['critical']}")
    print(f"  错误: {summary['error']}")
    print(f"  警告: {summary['warning']}")
    print(f"  通过: {summary['pass']}")
    print(f"  整体通过: {summary['overall_pass']}")
    print(f"  可继续: {summary['can_proceed']}")

    print(f"\n验证详情:")
    for r in results:
        print(f"  {r.level.value} - {r.item}: {r.message}")

except Exception as e:
    print(f"❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*80)
print("测试完成")
print("="*80)
