#!/usr/bin/env python3
"""
BTC缠论实时分析（简化版）- 使用火币API
"""
import sys
import os
import json
import pandas as pd

# 添加项目路径
os.chdir('/workspace/projects')
sys.path.insert(0, '/workspace/projects')

from src.tools.huobi_tools import HuobiDataCollector
from src.utils.chanlun_structure import ChanLunAnalyzer

def main():
    """主分析函数"""
    print("="*80)
    print("  🚀 BTC缠论实时分析系统")
    print("  数据源: 火币(HTX) API")
    print("="*80)

    # 1. 获取K线数据
    print("\n📊 步骤1: 获取K线数据...")
    collector = HuobiDataCollector()

    try:
        # 获取4小时K线数据（更适合缠论分析）
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

    # 2. 缠论结构分析
    print("\n📐 步骤2: 缠论结构分析...")
    try:
        analyzer = ChanLunAnalyzer()

        # 识别分型
        df = analyzer.identify_fractals(df)
        print(f"✅ 分型识别完成")
        print(f"   顶分型数量: {len(df[df['fractal_type'] == 'top'])}")
        print(f"   底分型数量: {len(df[df['fractal_type'] == 'bottom'])}")

        # 构建笔
        df = analyzer.build_bi(df)
        print(f"✅ 笔构建完成")
        print(f"   笔的数量: {len(df[df['bi_id'].notna()])}")

        # 构建线段
        df = analyzer.build_segment(df)
        print(f"✅ 线段构建完成")
        segments = df[df['segment_id'].notna()]
        print(f"   线段数量: {len(segments) // 2}")  # 每条线段有起点和终点

        # 识别中枢
        centers = analyzer.identify_zhongshu(df)
        print(f"✅ 中枢识别完成")
        print(f"   中枢数量: {len(centers)}")

        # 识别买卖点
        buy_points, sell_points = analyzer.identify_trading_points(df)
        print(f"✅ 买卖点识别完成")
        print(f"   买点数量: {len(buy_points)}")
        print(f"   卖点数量: {len(sell_points)}")

    except Exception as e:
        print(f"❌ 缠论分析失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. 生成分析报告
    print("\n📋 步骤3: 生成分析报告...")
    print("="*80)
    print("  缠论分析结果")
    print("="*80)

    # 当前价格信息
    latest = df.iloc[-1]
    print(f"\n【当前市场状态】")
    print(f"  最新价格: ${latest['close']:.2f}")
    print(f"  最高价: ${latest['high']:.2f}")
    print(f"  最低价: ${latest['low']:.2f}")
    print(f"  成交量: {latest['volume']:.2f} BTC")

    # 中枢信息
    if centers:
        print(f"\n【中枢信息】")
        for i, center in enumerate(centers[-3:], 1):  # 显示最近3个中枢
            print(f"  中枢{i}:")
            print(f"    区间: ${center['high']:.2f} - ${center['low']:.2f}")
            print(f"    位置: {center['start_time']} ~ {center['end_time']}")

    # 买卖点信息
    if buy_points or sell_points:
        print(f"\n【交易信号】")
        if buy_points:
            print(f"  最近买点:")
            for bp in buy_points[-2:]:  # 显示最近2个买点
                print(f"    时间: {bp['time']}")
                print(f"    价格: ${bp['price']:.2f}")
                print(f"    类型: {bp['type']}")

        if sell_points:
            print(f"  最近卖点:")
            for sp in sell_points[-2:]:  # 显示最近2个卖点
                print(f"    时间: {sp['time']}")
                print(f"    价格: ${sp['price']:.2f}")
                print(f"    类型: {sp['type']}")

    # 趋势判断
    print(f"\n【趋势判断】")
    if len(df) >= 10:
        ma_short = df['close'].tail(5).mean()
        ma_long = df['close'].tail(20).mean()

        if ma_short > ma_long:
            trend = "上升 📈"
            advice = "建议逢低买入，注意止损"
        elif ma_short < ma_long:
            trend = "下降 📉"
            advice = "建议观望或轻仓做空"
        else:
            trend = "横盘 ➡️"
            advice = "建议观望，等待方向突破"

        print(f"  短期均线(5): ${ma_short:.2f}")
        print(f"  长期均线(20): ${ma_long:.2f}")
        print(f"  趋势方向: {trend}")
        print(f"  操作建议: {advice}")

    # 风险提示
    print(f"\n【风险提示】")
    print(f"  ⚠️  本分析仅供参考，不构成投资建议")
    print(f"  ⚠️  实际操作前请结合更多技术指标")
    print(f"  ⚠️  严格控制风险，合理管理仓位")

    print("\n" + "="*80)
    print("  分析完成")
    print("="*80)

if __name__ == '__main__':
    main()
