#!/usr/bin/env python3
"""
BTC实时行情分析 - 使用火币API
"""
import sys
import os
import json
import pandas as pd

# 添加项目路径
os.chdir('/workspace/projects')
sys.path.insert(0, '/workspace/projects')

from src.tools.huobi_tools import HuobiDataCollector

def main():
    """主分析函数"""
    print("="*80)
    print("  🚀 BTC实时行情分析系统")
    print("  数据源: 火币(HTX) API")
    print("="*80)

    # 1. 获取K线数据
    print("\n📊 步骤1: 获取K线数据...")
    collector = HuobiDataCollector()

    try:
        # 获取4小时K线数据
        klines = collector.get_klines("btcusdt", "4hour", 200)
        df = collector.format_klines(klines)

        print(f"✅ 数据获取成功!")
        print(f"   K线数量: {len(df)}")
        print(f"   时间范围: {df['timestamp'].min()} ~ {df['timestamp'].max()}")
        print(f"   最新价格: ${df['close'].iloc[-1]:.2f}")
        print(f"   24h涨跌: {((df['close'].iloc[-1] - df['close'].iloc[-6]) / df['close'].iloc[-6] * 100):.2f}%")

        # 保存数据
        data_dir = "/workspace/projects/data"
        os.makedirs(data_dir, exist_ok=True)
        df.to_csv(f"{data_dir}/BTCUSDT_4h_latest.csv", index=False)
        print(f"   数据已保存: {data_dir}/BTCUSDT_4h_latest.csv")

    except Exception as e:
        print(f"❌ 数据获取失败: {e}")
        return

    # 2. 技术分析
    print("\n📈 步骤2: 技术分析...")
    try:
        # 计算技术指标
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()

        # 计算涨跌幅
        df['change'] = df['close'].pct_change() * 100

        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        print(f"✅ 技术指标计算完成")

    except Exception as e:
        print(f"❌ 技术分析失败: {e}")
        return

    # 3. 生成分析报告
    print("\n📋 步骤3: 生成分析报告...")
    print("="*80)
    print("  BTC实时行情分析报告")
    print("="*80)

    # 当前价格信息
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    print(f"\n【当前市场状态】")
    print(f"  最新价格: ${latest['close']:.2f}")
    print(f"  涨跌幅: {latest['change']:.2f}%")
    print(f"  最高价: ${latest['high']:.2f}")
    print(f"  最低价: ${latest['low']:.2f}")
    print(f"  成交量: {latest['volume']:.2f} BTC")
    print(f"  RSI指标: {latest['rsi']:.2f}")

    # 均线信息
    print(f"\n【均线分析】")
    print(f"  MA5: ${latest['ma5']:.2f}")
    print(f"  MA10: ${latest['ma10']:.2f}")
    print(f"  MA20: ${latest['ma20']:.2f}")
    print(f"  MA60: ${latest['ma60']:.2f}")

    # 趋势判断
    print(f"\n【趋势判断】")
    if latest['close'] > latest['ma5'] > latest['ma10'] > latest['ma20']:
        trend = "强势上升 📈🚀"
        advice = "多头排列，趋势强劲，可考虑逢低买入"
    elif latest['close'] < latest['ma5'] < latest['ma10'] < latest['ma20']:
        trend = "强势下降 📉📉"
        advice = "空头排列，趋势向下，建议观望或轻仓做空"
    elif latest['close'] > latest['ma20']:
        trend = "温和上升 📈"
        advice = "价格位于中期均线上方，趋势偏多"
    elif latest['close'] < latest['ma20']:
        trend = "温和下降 📉"
        advice = "价格位于中期均线下方，趋势偏空"
    else:
        trend = "震荡整理 ➡️"
        advice = "均线交织，方向不明，建议观望"

    print(f"  趋势方向: {trend}")
    print(f"  操作建议: {advice}")

    # RSI分析
    print(f"\n【RSI分析】")
    if latest['rsi'] > 70:
        rsi_status = "超买 ⚠️"
        rsi_advice = "RSI超买，注意回调风险，不宜追高"
    elif latest['rsi'] < 30:
        rsi_status = "超卖 💚"
        rsi_advice = "RSI超卖，可能存在反弹机会"
    else:
        rsi_status = "正常 ✅"
        rsi_advice = "RSI处于正常区间"

    print(f"  当前RSI: {latest['rsi']:.2f} - {rsi_status}")
    print(f"  分析: {rsi_advice}")

    # 价格区间分析
    print(f"\n【价格区间分析】")
    high_20 = df['high'].tail(20).max()
    low_20 = df['low'].tail(20).min()
    current_price = latest['close']

    price_position = ((current_price - low_20) / (high_20 - low_20)) * 100

    print(f"  20日最高: ${high_20:.2f}")
    print(f"  20日最低: ${low_20:.2f}")
    print(f"  当前价格位置: {price_position:.1f}% (0%为最低，100%为最高)")

    if price_position > 80:
        position_status = "高位 ⚠️"
        position_advice = "价格处于高位，注意风险控制"
    elif price_position < 20:
        position_status = "低位 💚"
        position_advice = "价格处于低位，可能存在机会"
    else:
        position_status = "中位 ✅"
        position_advice = "价格处于中间区间"

    print(f"  位置状态: {position_status}")
    print(f"  分析: {position_advice}")

    # 近期K线
    print(f"\n【最近5根4小时K线】")
    print(f"  {'时间':<20} {'开盘':<12} {'最高':<12} {'最低':<12} {'收盘':<12} {'涨跌幅':<10}")
    print(f"  {'-'*20} {'-'*12} {'-'*12} {'-'*12} {'-'*12} {'-'*10}")
    for i, row in df.tail(5).iterrows():
        time_str = str(row['timestamp']).replace(' ', 'T')[:16]
        change_str = f"{row['change']:.2f}%" if not pd.isna(row['change']) else "N/A"
        print(f"  {time_str:<20} ${row['open']:<11.2f} ${row['high']:<11.2f} ${row['low']:<11.2f} ${row['close']:<11.2f} {change_str:<10}")

    # 综合建议
    print(f"\n【综合操作建议】")
    if (latest['close'] > latest['ma20'] and
        latest['rsi'] < 70 and
        price_position < 80):
        print(f"  ✅ 建议方向: 买入")
        print(f"     依据: 均线多头排列，RSI未超买，价格未过高")
        print(f"     建议: 可考虑分批买入，设置5-8%止损")
    elif (latest['close'] < latest['ma20'] and
          latest['rsi'] > 30 and
          price_position > 20):
        print(f"  ❌ 建议方向: 卖出/观望")
        print(f"     依据: 均线空头排列，RSI未超卖")
        print(f"     建议: 建议观望或减仓，等待更好时机")
    else:
        print(f"  ⏸️  建议方向: 观望")
        print(f"     依据: 信号不明确，等待更多确认")
        print(f"     建议: 保持现有仓位，关注均线交叉和RSI变化")

    # 风险提示
    print(f"\n【重要风险提示】")
    print(f"  ⚠️  本分析仅供参考，不构成投资建议")
    print(f"  ⚠️  加密货币市场波动极大，请谨慎投资")
    print(f"  ⚠️  实际操作前请结合更多技术指标和基本面分析")
    print(f"  ⚠️  严格控制风险，合理管理仓位，不要使用杠杆")
    print(f"  ⚠️  只投资您能承受损失的资金")

    print("\n" + "="*80)
    print("  分析完成")
    print("="*80)

if __name__ == '__main__':
    main()
