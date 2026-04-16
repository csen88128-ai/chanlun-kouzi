"""
测试算法优化效果
测试增强版中枢识别、线段延伸判断、背驰识别、趋势力度指标
"""
import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.chanlun_structure import ChanLunAnalyzer, Segment
from utils.chanlun_algorithms_v2 import (
    AdvancedChanLunAnalyzer,
    EnhancedDynamicsAnalyzer,
    TrendStrengthAnalyzer,
    ZhongShuV2,
    analyze_enhanced_structure,
    analyze_enhanced_divergence,
    analyze_trend_strength
)


def generate_test_data(n=200):
    """生成测试K线数据"""
    np.random.seed(42)

    data = []
    price = 50000

    for i in range(n):
        # 生成带趋势的价格
        trend = np.sin(i / 20) * 500  # 周期性趋势
        noise = np.random.normal(0, 100)  # 随机噪声
        price += trend * 0.05 + noise

        # 确保价格不为负
        price = max(price, 1000)

        high = price + abs(np.random.normal(0, 50))
        low = price - abs(np.random.normal(0, 50))
        close = price
        open_price = data[-1]['open'] if data else close

        volume = abs(np.random.normal(1000, 200))

        data.append({
            'timestamp': f"2026-04-16 {i:02d}:00:00",
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })

    return pd.DataFrame(data)


def test_enhanced_zhongshu_detection():
    """测试增强版中枢识别"""
    print("=" * 80)
    print("测试增强版中枢识别")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(200)

    # 使用原始分析器识别笔和线段
    original_analyzer = ChanLunAnalyzer()

    # 直接调用内部方法获取原始的bis和segments列表
    fractals = original_analyzer.identify_fractals(df)
    bis = original_analyzer.identify_bis(df, fractals)
    segments = original_analyzer.identify_segments(bis)

    print(f"✓ 生成测试数据: {len(df)} 根K线")
    print(f"✓ 识别笔数量: {len(bis)}")
    print(f"✓ 识别线段数量: {len(segments)}")
    print()

    # 使用增强版分析器识别中枢
    enhanced_analyzer = AdvancedChanLunAnalyzer()
    enhanced_zhongshus = enhanced_analyzer.enhanced_identify_zhongshu(df, segments)

    print(f"✓ 增强版中枢识别结果:")
    print(f"  - 识别中枢数量: {len(enhanced_zhongshus)}")
    print()

    if enhanced_zhongshus:
        for i, zs in enumerate(enhanced_zhongshus, 1):
            print(f"  中枢 {i}:")
            print(f"    - 上沿 (ZG): {zs.high:.2f}")
            print(f"    - 下沿 (ZD): {zs.low:.2f}")
            print(f"    - 高点 (GG): {zs.high_point:.2f}")
            print(f"    - 低点 (DD): {zs.low_point:.2f}")
            print(f"    - 级别: {zs.level}")
            print(f"    - 状态: {zs.status.value}")
            print(f"    - 线段数量: {zs.segment_count}")
            print(f"    - 强度: {zs.strength:.3f}")
            print(f"    - 重叠次数: {zs.overlap_count}")
            print()

    return True


def test_segment_extension():
    """测试线段延伸判断"""
    print("=" * 80)
    print("测试线段延伸判断")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(200)

    # 使用原始分析器识别线段
    original_analyzer = ChanLunAnalyzer()

    # 直接调用内部方法获取原始的segments列表
    fractals = original_analyzer.identify_fractals(df)
    bis = original_analyzer.identify_bis(df, fractals)
    segments = original_analyzer.identify_segments(bis)

    print(f"✓ 识别线段数量: {len(segments)}")
    print()

    if len(segments) >= 2:
        # 测试线段延伸判断
        enhanced_analyzer = AdvancedChanLunAnalyzer()

        # 检查最后两根线段的延伸情况
        if len(segments) >= 2:
            last_segment = segments[-1]
            prev_segments = segments[:-1]

            extension_info = enhanced_analyzer.check_segment_extension(
                prev_segments, last_segment, df
            )

            print(f"✓ 线段延伸判断结果:")
            print(f"  - 是否延伸: {extension_info['is_extending']}")
            print(f"  - 延伸类型: {extension_info['extension_type']}")
            print(f"  - 趋势强度: {extension_info['strength']:.3f}")

            if extension_info['break_point']:
                print(f"  - 突破点位: {extension_info['break_point']:.2f}")

            if extension_info['next_target']:
                print(f"  - 下一个目标: {extension_info['next_target']:.2f}")
            print()

    return True


def test_enhanced_divergence_detection():
    """测试增强版背驰检测"""
    print("=" * 80)
    print("测试增强版背驰检测")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(200)

    # 使用原始分析器识别笔
    original_analyzer = ChanLunAnalyzer()

    # 直接调用内部方法获取原始的bis列表
    fractals = original_analyzer.identify_fractals(df)
    bis = original_analyzer.identify_bis(df, fractals)

    print(f"✓ 识别笔数量: {len(bis)}")
    print()

    # 使用增强版分析器检测背驰
    enhanced_analyzer = EnhancedDynamicsAnalyzer()
    divergences = enhanced_analyzer.enhanced_divergence_detection(df, bis)

    print(f"✓ 增强版背驰检测结果:")
    print(f"  - 背驰数量: {len(divergences)}")
    print()

    if divergences:
        for i, div in enumerate(divergences, 1):
            print(f"  背驰 {i}:")
            print(f"    - 类型: {div['type']}")
            print(f"    - 背驰指标: {', '.join(div['divergence_types'])}")
            print(f"    - 价格: {div['price']:.2f}")
            print(f"    - 确认次数: {div['confirmation_count']}")
            print(f"    - 强度: {div['strength']:.3f}")
            print(f"    - 已确认: {div['confirmed']}")
            print()
    else:
        print("  - 未检测到背驰信号")
        print()

    return True


def test_trend_strength_analysis():
    """测试趋势力度分析"""
    print("=" * 80)
    print("测试趋势力度分析")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(200)

    # 使用趋势力度分析器
    trend_analyzer = TrendStrengthAnalyzer()
    trend_metrics = trend_analyzer.calculate_trend_strength(df, window=20)

    print(f"✓ 趋势力度分析结果:")
    print(f"  - ADX (平均趋向指数): {trend_metrics['adx']:.2f}")
    print(f"    * 0-25: 弱趋势或无趋势")
    print(f"    * 25-50: 中等趋势")
    print(f"    * 50-75: 强趋势")
    print(f"    * 75-100: 极强趋势")
    print()
    print(f"  - 价格趋势强度: {trend_metrics['price_trend']:.3f}")
    print(f"  - 动量强度: {trend_metrics['momentum']:.3f}")
    print(f"  - 波动率: {trend_metrics['volatility']:.3f}")
    print(f"  - 成交量强度: {trend_metrics['volume_strength']:.3f}")
    print()
    print(f"  - 综合趋势力度: {trend_metrics['trend_strength']:.3f}")
    print(f"  - 趋势方向: {trend_metrics['trend_direction']}")
    print()

    # 趋势解读
    adx = trend_metrics['adx']
    if adx < 25:
        trend_interpretation = "弱趋势或无趋势，建议观望"
    elif adx < 50:
        trend_interpretation = "中等趋势，可考虑交易"
    elif adx < 75:
        trend_interpretation = "强趋势，适合趋势跟踪"
    else:
        trend_interpretation = "极强趋势，注意风险控制"

    print(f"  - 趋势解读: {trend_interpretation}")
    print()

    return True


def test_algorithm_comparison():
    """测试算法对比"""
    print("=" * 80)
    print("算法对比测试")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data(200)

    # 原始算法
    original_analyzer = ChanLunAnalyzer()

    # 直接调用内部方法获取原始数据
    fractals = original_analyzer.identify_fractals(df)
    bis = original_analyzer.identify_bis(df, fractals)
    segments = original_analyzer.identify_segments(bis)
    zhongshu_list = original_analyzer.identify_zhongshu(segments)

    # 增强版算法
    enhanced_structure_analyzer = AdvancedChanLunAnalyzer()
    enhanced_divergence_analyzer = EnhancedDynamicsAnalyzer()
    trend_analyzer = TrendStrengthAnalyzer()

    enhanced_zhongshus = enhanced_structure_analyzer.enhanced_identify_zhongshu(df, segments)
    enhanced_divergences = enhanced_divergence_analyzer.enhanced_divergence_detection(df, bis)
    trend_metrics = trend_analyzer.calculate_trend_strength(df, window=20)

    print("算法对比结果:")
    print()
    print("1. 结构分析对比:")
    print(f"   - 原始算法:")
    print(f"     笔数量: {len(bis)}")
    print(f"     线段数量: {len(segments)}")
    print(f"     中枢数量: {len(zhongshu_list)}")
    print()
    print(f"   - 增强版算法:")
    print(f"     笔数量: {len(bis)}")
    print(f"     线段数量: {len(segments)}")
    print(f"     中枢数量: {len(enhanced_zhongshus)}")
    if enhanced_zhongshus:
        avg_strength = sum(zs.strength for zs in enhanced_zhongshus) / len(enhanced_zhongshus)
        print(f"     平均中枢强度: {avg_strength:.3f}")
    print()

    print("2. 背驰检测对比:")
    print(f"   - 原始算法: 0 个背驰 (原始版本未实现)")
    print(f"   - 增强版算法: {len(enhanced_divergences)} 个背驰")
    if enhanced_divergences:
        avg_strength = sum(d['strength'] for d in enhanced_divergences) / len(enhanced_divergences)
        print(f"     平均背驰强度: {avg_strength:.3f}")
    print()

    print("3. 新增功能:")
    print(f"   - 趋势力度分析: ADX={trend_metrics['adx']:.2f}, 综合强度={trend_metrics['trend_strength']:.3f}")
    print(f"   - 线段延伸判断: 已实现")
    print(f"   - 中枢强度计算: 已实现")
    print(f"   - 多重背驰确认: 已实现")
    print()

    return True


def main():
    """主测试函数"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 28 + "算法优化效果测试" + " " * 35 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # 测试增强版中枢识别
    try:
        success1 = test_enhanced_zhongshu_detection()
    except Exception as e:
        print(f"✗ 增强版中枢识别测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success1 = False

    print()

    # 测试线段延伸判断
    try:
        success2 = test_segment_extension()
    except Exception as e:
        print(f"✗ 线段延伸判断测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success2 = False

    print()

    # 测试增强版背驰检测
    try:
        success3 = test_enhanced_divergence_detection()
    except Exception as e:
        print(f"✗ 增强版背驰检测测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success3 = False

    print()

    # 测试趋势力度分析
    try:
        success4 = test_trend_strength_analysis()
    except Exception as e:
        print(f"✗ 趋势力度分析测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success4 = False

    print()

    # 测试算法对比
    try:
        success5 = test_algorithm_comparison()
    except Exception as e:
        print(f"✗ 算法对比测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success5 = False

    print()
    print("=" * 80)
    print("测试结果")
    print("=" * 80)
    print(f"增强版中枢识别: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"线段延伸判断: {'✓ 通过' if success2 else '✗ 失败'}")
    print(f"增强版背驰检测: {'✓ 通过' if success3 else '✗ 失败'}")
    print(f"趋势力度分析: {'✓ 通过' if success4 else '✗ 失败'}")
    print(f"算法对比: {'✓ 通过' if success5 else '✗ 失败'}")
    print()
    print("=" * 80)

    return success1 and success2 and success3 and success4 and success5


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
