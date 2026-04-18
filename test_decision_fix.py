#!/usr/bin/env python3
"""
快速测试决策制定智能体的止盈止损逻辑
"""
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

import json

print("="*80)
print("测试决策制定智能体的止盈止损逻辑")
print("="*80)
print()

# 构造测试数据
from multi_agents.decision_maker_agent_v3 import make_decision_v2

# 模拟结构分析数据（基于真实数据）
current_price = 76962.64

structure_test = json.dumps({
    "status": "success",
    "trend_analysis": {
        "direction": "上升",
        "strength": 0.7,
        "phase": "突破上涨"
    },
    "buy_sell_points": {
        "total_count": 6,
        "latest_signal": {
            "type": "三买",
            "index": 190,
            "price": 71235.0,
            "level": 1,
            "strength": 0.80,
            "is_buy": True
        }
    },
    "zhongshu": {
        "latest": {
            "zg": 71351.0,
            "zd": 68794.0,
            "gg": 76000.0,
            "dd": 67400.0,
            "level": 1
        }
    },
    "fractals": {
        "latest_top": {
            "index": 195,
            "price": 78316.0
        },
        "latest_bottom": {
            "index": 192,
            "price": 73811.0
        }
    }
})

# 模拟动力学数据
dynamics_test = json.dumps({
    "status": "success",
    "rsi": 68.29,
    "rsi_status": "正常",
    "macd": 1026.0,
    "signal": 843.0,
    "macd_signal": "金叉",
    "macd_trend": "上升",
    "histogram": 183.0
})

# 模拟情绪数据
sentiment_test = json.dumps({
    "status": "success",
    "fear_greed_index": 26,
    "sentiment": "恐惧"
})

print("【测试场景：做多（现价76962，中枢GG=76000）】")
print("-"*80)
result = make_decision_v2.func(
    structure_data=structure_test,
    dynamics_data=dynamics_test,
    sentiment_data=sentiment_test
)

result_json = json.loads(result)
print(f"决策: {result_json.get('decision')} {result_json.get('emoji')}")
print(f"综合得分: {result_json.get('score')}/100")
print(f"当前价格: {result_json.get('current_price')} USDT")
print()

trading_plan = result_json.get('trading_plan', {})
print("交易计划:")
print(f"  入场价格: {trading_plan.get('entry')} USDT")
print(f"  止盈目标:")
for tp in trading_plan.get('take_profit', []):
    level = tp.get('level')
    price = tp.get('price')
    target = tp.get('target')
    print(f"    TP{level}: {price} USDT ({target})")
print(f"  止损设置:")
for sl in trading_plan.get('stop_loss', []):
    level = sl.get('level')
    price = sl.get('price')
    target = sl.get('target')
    print(f"    SL{level}: {price} USDT ({target})")

print()
print("【止盈止损验证】")
print("-"*80)
entry = trading_plan.get('entry')
decision_type = result_json.get('decision')
all_valid = True

for tp in trading_plan.get('take_profit', []):
    if tp.get('price', 0) > entry:
        print(f"✅ 止盈TP{tp.get('level')}: {tp.get('price')} > 入场价{entry} (正确)")
    else:
        print(f"❌ 止盈TP{tp.get('level')}: {tp.get('price')} <= 入场价{entry} (错误!)")
        all_valid = False

for sl in trading_plan.get('stop_loss', []):
    if sl.get('price', 0) < entry:
        print(f"✅ 止损SL{sl.get('level')}: {sl.get('price')} < 入场价{entry} (正确)")
    else:
        print(f"❌ 止损SL{sl.get('level')}: {sl.get('price')} >= 入场价{entry} (错误!)")
        all_valid = False

print()
if all_valid:
    print("✅✅✅ 所有止盈止损价格方向正确！")
else:
    print("❌❌❌ 存在止盈止损价格方向错误！")

print()
print("【因子得分明细】")
print("-"*80)
for factor in result_json.get('factors', []):
    print(f"  {factor}")

print()
print("="*80)
