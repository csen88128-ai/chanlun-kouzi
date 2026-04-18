#!/usr/bin/env python3
"""
测试缠论买卖点识别
"""
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

import pandas as pd
import json

# 导入缠论算法
from src.utils.chanlun_structure import ChanLunAnalyzer
from multi_agents.buy_sell_analyzer import BuySellAnalyzer

def test_chanlun_analysis():
    """测试缠论分析"""

    # 读取数据
    data_path = "/workspace/projects/data/BTCUSDT_4h_latest.csv"
    df = pd.read_csv(data_path)
    df = df.sort_values('timestamp').reset_index(drop=True)

    print(f"数据加载成功: {len(df)} 根K线")
    print(f"时间范围: {df.iloc[0]['timestamp']} ~ {df.iloc[-1]['timestamp']}")
    print(f"最新价格: {df.iloc[-1]['close']:.2f} USDT")
    print()

    # 1. 识别分型
    analyzer = ChanLunAnalyzer()
    fractals = analyzer.identify_fractals(df)

    print(f"【分型分析】")
    print(f"  总分型数量: {len(fractals)}")
    print(f"  顶分型: {sum(1 for f in fractals if f.type.value == 'top')}")
    print(f"  底分型: {sum(1 for f in fractals if f.type.value == 'bottom')}")
    if fractals:
        print(f"  最新顶分型: 价格 {fractals[-1].high:.2f} (索引 {fractals[-1].index})")
        bottoms = [f for f in fractals if f.type.value == 'bottom']
        if bottoms:
            print(f"  最新底分型: 价格 {bottoms[-1].low:.2f} (索引 {bottoms[-1].index})")
    print()

    # 2. 识别笔
    bis = analyzer.identify_bis(df, fractals)
    print(f"【笔分析】")
    print(f"  总笔数量: {len(bis)}")
    print(f"  向上笔: {sum(1 for b in bis if b.direction.value == 'up')}")
    print(f"  向下笔: {sum(1 for b in bis if b.direction.value == 'down')}")
    if bis:
        print(f"  最新笔: {bis[-1].direction.value} ({bis[-1].start_price:.2f} -> {bis[-1].end_price:.2f})")
    print()

    # 3. 识别线段
    print(f"【线段分析】")
    try:
        segments = analyzer.identify_segments(bis)
        print(f"  总线段数量: {len(segments)}")
        print(f"  向上线段: {sum(1 for s in segments if s.direction.value == 'up')}")
        print(f"  向下线段: {sum(1 for s in segments if s.direction.value == 'down')}")
        if segments:
            print(f"  最新线段: {segments[-1].direction.value} ({segments[-1].start_price:.2f} -> {segments[-1].end_price:.2f})")
    except Exception as e:
        print(f"  线段识别失败: {e}")
        import traceback
        traceback.print_exc()
        segments = []
    print()

    # 4. 识别中枢
    zhongshu_list = analyzer.identify_zhongshu(segments)
    print(f"【中枢分析】")
    print(f"  总中枢数量: {len(zhongshu_list)}")
    if zhongshu_list:
        latest = zhongshu_list[-1]
        print(f"  最新中枢:")
        print(f"    ZG (中枢上沿): {latest.high:.2f}")
        print(f"    ZD (中枢下沿): {latest.low:.2f}")
        print(f"    GG (中枢高点): {latest.high_point:.2f}")
        print(f"    DD (中枢低点): {latest.low_point:.2f}")
        print(f"    级别: {latest.level}")
        print(f"    线段数量: {len(latest.segment_list)}")
    print()

    # 5. 识别买卖点
    buy_sell_analyzer = BuySellAnalyzer()
    buy_sell_points = buy_sell_analyzer.identify_buy_sell_points(df, segments, zhongshu_list)

    print(f"【买卖点分析】")
    print(f"  总买卖点数量: {len(buy_sell_points)}")
    if buy_sell_points:
        print(f"  最近5个买卖点:")
        for point in buy_sell_points[-5:]:
            print(f"    {point.type.value}: 价格 {point.price:.2f} (索引 {point.index}, 强度 {point.strength:.2f})")

        latest_signal = buy_sell_analyzer.get_latest_signal()
        if latest_signal:
            print(f"\n  最新信号:")
            print(f"    类型: {latest_signal['type']}")
            print(f"    价格: {latest_signal['price']:.2f}")
            print(f"    级别: {latest_signal['level']}")
            print(f"    强度: {latest_signal['strength']:.2f}")
            print(f"    方向: {'买入' if latest_signal['is_buy'] else '卖出'}")
    else:
        print("  未检测到买卖点")
    print()

    # 6. 趋势判断
    if bis:
        print(f"【趋势判断】")
        if bis[-1].direction.value == 'up':
            print(f"  当前趋势: 上升")
        else:
            print(f"  当前趋势: 下降")

        if segments and len(segments) >= 3:
            recent = segments[-3:]
            up_count = sum(1 for s in recent if s.direction.value == 'up')
            if up_count >= 2:
                print(f"  短期趋势: 上升")
            else:
                print(f"  短期趋势: 下降")

        if zhongshu_list and df.iloc[-1]['close']:
            latest_zs = zhongshu_list[-1]
            current_price = df.iloc[-1]['close']
            if current_price > latest_zs.high_point:
                print(f"  当前阶段: 突破上涨")
            elif current_price < latest_zs.low_point:
                print(f"  当前阶段: 破位下跌")
            elif latest_zs.high >= current_price >= latest_zs.low:
                print(f"  当前阶段: 中枢震荡 (价格 {current_price:.2f} 在 [{latest_zs.low:.2f}, {latest_zs.high:.2f}])")
    print()

    print("="*80)
    print("✅ 缠论分析完成")
    print("="*80)


if __name__ == "__main__":
    test_chanlun_analysis()
