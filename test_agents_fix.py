#!/usr/bin/env python3
"""
测试修复后的多智能体系统
"""
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

import json
from langchain_core.messages import HumanMessage

print("="*80)
print("测试修复后的BTC缠论多智能体协作分析系统")
print("="*80)
print()

# 测试数据采集
print("【1. 测试数据采集智能体】")
print("-"*80)
from multi_agents.data_collector_agent import build_agent as build_data_collector
collector = build_data_collector()
response = collector.invoke({
    "messages": [
        HumanMessage(content="获取BTC 4小时K线数据，200根")
    ]
}, config={"configurable": {"thread_id": "test-thread"}})
collector_result = str(response["messages"][-1].content)
print(collector_result[:500])
print()

# 解析数据采集结果
try:
    import re
    price_match = re.search(r'"latest_price":\s*([\d.]+)', collector_result)
    if price_match:
        current_price = float(price_match.group(1))
        print(f"✅ 当前价格: {current_price} USDT")
except:
    print("⚠️  无法解析价格")
    current_price = None

print()
print("【2. 测试结构分析智能体（缠论v2）】")
print("-"*80)
from multi_agents.structure_analyzer_agent_v2 import build_agent as build_structure_analyzer
structure = build_structure_analyzer()
response = structure.invoke({
    "messages": [
        HumanMessage(content="分析BTC的缠论结构")
    ]
}, config={"configurable": {"thread_id": "test-thread"}})
structure_result = str(response["messages"][-1].content)
print(structure_result[:800])
print()

# 解析结构分析结果
try:
    structure_json = json.loads(structure_result)
    if structure_json.get('status') == 'success':
        trend = structure_json.get('trend_analysis', {}).get('direction')
        buy_sell = structure_json.get('buy_sell_points', {}).get('latest_signal')
        zhongshu = structure_json.get('zhongshu', {}).get('latest')
        print(f"✅ 趋势: {trend}")
        print(f"✅ 买卖点: {buy_sell.get('type') if buy_sell else '无'}")
        if zhongshu:
            print(f"✅ 中枢: ZG={zhongshu.get('zg')}, ZD={zhongshu.get('zd')}, GG={zhongshu.get('gg')}, DD={zhongshu.get('dd')}")
except Exception as e:
    print(f"⚠️  解析结构分析失败: {e}")

print()
print("【3. 测试动力学分析智能体】")
print("-"*80)
from multi_agents.dynamics_analyzer_agent import build_agent as build_dynamics_analyzer
dynamics = build_dynamics_analyzer()
response = dynamics.invoke({
    "messages": [
        HumanMessage(content="分析BTC的市场动力学指标")
    ]
}, config={"configurable": {"thread_id": "test-thread"}})
dynamics_result = str(response["messages"][-1].content)
print(dynamics_result[:600])
print()

# 解析动力学分析结果
try:
    import re
    rsi_match = re.search(r'"rsi":\s*([\d.]+)', dynamics_result)
    macd_match = re.search(r'"macd_signal":\s*"([^"]+)"', dynamics_result)
    if rsi_match and macd_match:
        rsi = float(rsi_match.group(1))
        macd_signal = macd_match.group(1)
        print(f"✅ RSI: {rsi}")
        print(f"✅ MACD: {macd_signal}")
except Exception as e:
    print(f"⚠️  解析动力学分析失败: {e}")

print()
print("【4. 测试市场情绪智能体】")
print("-"*80)
from multi_agents.sentiment_analyzer_agent import build_agent as build_sentiment_analyzer
sentiment = build_sentiment_analyzer()
response = sentiment.invoke({
    "messages": [
        HumanMessage(content="获取市场情绪数据")
    ]
}, config={"configurable": {"thread_id": "test-thread"}})
sentiment_result = str(response["messages"][-1].content)
print(sentiment_result[:500])
print()

# 解析情绪分析结果
try:
    import re
    fgi_match = re.search(r'"fear_greed_index":\s*(\d+)', sentiment_result)
    if fgi_match:
        fgi = int(fgi_match.group(1))
        print(f"✅ 恐惧贪婪指数: {fgi}")
except Exception as e:
    print(f"⚠️  解析情绪分析失败: {e}")

print()
print("【5. 测试决策制定智能体（v2修复版）】")
print("-"*80)
from multi_agents.decision_maker_agent_v2 import build_agent as build_decision_maker
decision = build_decision_maker()

# 调用make_decision_v2工具
from multi_agents.decision_maker_agent_v2 import make_decision_v2

# 准备输入数据
structure_input = structure_result if 'structure_result' in locals() else '{}'
dynamics_input = dynamics_result if 'dynamics_result' in locals() else '{}'
sentiment_input = sentiment_result if 'sentiment_result' in locals() else '{}'

# 调用工具
decision_result = make_decision_v2.func(
    structure_data=structure_input,
    dynamics_data=dynamics_input,
    sentiment_data=sentiment_input
)

print(decision_result)
print()

# 解析决策结果
try:
    decision_json = json.loads(decision_result)
    if decision_json.get('status') == 'success':
        print()
        print("="*80)
        print("✅ 决策分析结果")
        print("="*80)
        print(f"决策: {decision_json.get('decision')} {decision_json.get('emoji')}")
        print(f"综合得分: {decision_json.get('score')}/100")
        print(f"置信度: {decision_json.get('confidence')}")
        print(f"当前价格: {decision_json.get('current_price')} USDT")
        print()
        print("因子得分:")
        for factor in decision_json.get('factors', []):
            print(f"  {factor}")
        print()
        trading_plan = decision_json.get('trading_plan', {})
        print("交易计划:")
        print(f"  入场价格: {trading_plan.get('entry')} USDT")
        print(f"  仓位建议: {trading_plan.get('position_size')}")
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
        if trading_plan.get('risk_reward_ratio'):
            print(f"  盈亏比: {trading_plan['risk_reward_ratio'][0]}")
        print()
        print("="*80)
        print("✅ 止盈止损验证")
        print("="*80)
        entry = trading_plan.get('entry')
        decision_type = decision_json.get('decision')
        tp_valid = True
        sl_valid = True
        for tp in trading_plan.get('take_profit', []):
            if decision_type in ['买入', '偏多']:
                if tp.get('price', 0) <= entry:
                    print(f"❌ 止盈TP{tp.get('level')}价格{tp.get('price')} <= 入场价{entry} (错误!)")
                    tp_valid = False
                else:
                    print(f"✅ 止盈TP{tp.get('level')}: {tp.get('price')} > 入场价{entry} (正确)")
            elif decision_type in ['卖出', '偏空']:
                if tp.get('price', 0) >= entry:
                    print(f"❌ 止盈TP{tp.get('level')}价格{tp.get('price')} >= 入场价{entry} (错误!)")
                    tp_valid = False
                else:
                    print(f"✅ 止盈TP{tp.get('level')}: {tp.get('price')} < 入场价{entry} (正确)")
        for sl in trading_plan.get('stop_loss', []):
            if decision_type in ['买入', '偏多']:
                if sl.get('price', 0) >= entry:
                    print(f"❌ 止损SL{sl.get('level')}价格{sl.get('price')} >= 入场价{entry} (错误!)")
                    sl_valid = False
                else:
                    print(f"✅ 止损SL{sl.get('level')}: {sl.get('price')} < 入场价{entry} (正确)")
            elif decision_type in ['卖出', '偏空']:
                if sl.get('price', 0) <= entry:
                    print(f"❌ 止损SL{sl.get('level')}价格{sl.get('price')} <= 入场价{entry} (错误!)")
                    sl_valid = False
                else:
                    print(f"✅ 止损SL{sl.get('level')}: {sl.get('price')} > 入场价{entry} (正确)")
        print()
        if tp_valid and sl_valid:
            print("✅ 所有止盈止损价格方向正确！")
        else:
            print("❌ 存在止盈止损价格方向错误！")
except Exception as e:
    import traceback
    print(f"⚠️  解析决策失败: {e}")
    traceback.print_exc()

print()
print("="*80)
print("测试完成")
print("="*80)
