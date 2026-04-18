"""
测试买卖点识别、趋势判断、背驰检测和级别递归验证功能
"""
import json
import time
from multi_agents.multi_level_chanlun_analyzer import MultiLevelChanLunAnalyzer


def test_enhanced_multi_level_analysis():
    """测试增强的多级别缠论分析"""
    print("=" * 80)
    print("测试增强的多级别缠论分析")
    print("=" * 80)

    start_time = time.time()

    # 创建分析器
    analyzer = MultiLevelChanLunAnalyzer(symbol="btcusdt")

    # 采集数据
    print("\n[1] 采集多级别K线数据...")
    analyzer.collect_all_levels_data()

    # 分析所有级别
    print("\n[2] 分析所有级别...")
    analyzer.analyze_all_levels()

    # 检查买卖点识别
    print("\n" + "=" * 80)
    print("买卖点识别结果")
    print("=" * 80)
    for level in analyzer.levels:
        if level in analyzer.all_analysis and analyzer.all_analysis[level]:
            buy_sell = analyzer.all_analysis[level]["buy_sell_points"]
            print(f"\n{level}级别:")
            print(f"  买入点: {buy_sell['total_buy_points']}个")
            print(f"  卖出点: {buy_sell['total_sell_points']}个")
            if buy_sell['latest_buy_point']:
                print(f"  最新买入点: {buy_sell['latest_buy_point']['type']} @ {buy_sell['latest_buy_point']['price']}")
            if buy_sell['latest_sell_point']:
                print(f"  最新卖出点: {buy_sell['latest_sell_point']['type']} @ {buy_sell['latest_sell_point']['price']}")
            print(f"  当前趋势: {buy_sell['trend']}")

    # 检查趋势判断
    print("\n" + "=" * 80)
    print("趋势判断结果")
    print("=" * 80)
    for level in analyzer.levels:
        if level in analyzer.all_analysis and analyzer.all_analysis[level]:
            trend = analyzer.all_analysis[level]["trend"]
            print(f"\n{level}级别:")
            print(f"  方向: {trend['direction']}")
            print(f"  强度: {trend['strength']:.1f}")
            print(f"  置信度: {trend['confidence']}")
            print(f"  描述: {trend['description']}")
            print(f"  预期方向: {trend['expected_direction']}")
            print(f"  风险水平: {trend['risk_level']}")

    # 检查背驰检测
    print("\n" + "=" * 80)
    print("背驰检测结果")
    print("=" * 80)
    for level in analyzer.levels:
        if level in analyzer.all_analysis and analyzer.all_analysis[level]:
            divergence = analyzer.all_analysis[level]["divergence"]
            print(f"\n{level}级别:")
            print(f"  是否背驰: {'有' if divergence['has_divergence'] else '无'}")
            if divergence['has_divergence']:
                print(f"  背驰类型: {divergence['divergence_type']}")
                print(f"  背驰级别: {divergence['divergence_level']}")
                print(f"  背驰强度: {divergence['divergence_strength']:.1f}")
                print(f"  MACD背驰: {'有' if divergence['macd_divergence'] else '无'}")
                print(f"  RSI背驰: {'有' if divergence['rsi_divergence'] else '无'}")
                print(f"  成交量背驰: {'有' if divergence['volume_divergence'] else '无'}")
                print(f"  描述: {divergence['description']}")
                if divergence['latest_divergence']:
                    print(f"  最新背驰点: {divergence['latest_divergence']['type']} @ {divergence['latest_divergence']['price']}")

    # 高阶理论分析
    print("\n[3] 高阶理论分析...")
    advanced_theory = analyzer.analyze_advanced_theory()

    # 生成综合报告
    print("\n[4] 生成综合报告...")
    report = analyzer.generate_comprehensive_report()

    # 检查级别递归验证
    print("\n" + "=" * 80)
    print("级别递归验证结果")
    print("=" * 80)
    recursion = report["level_recursion"]
    print(f"\n验证结果: {recursion['validation_result']}")
    print(f"整体一致性: {recursion['overall_consistency']:.1f}%")
    print(f"主导趋势: {recursion['dominant_trend']}")
    print(f"推荐操作级别: {recursion['recommended_level']}")
    print(f"风险评估: {recursion['risk_assessment']}")
    print(f"置信度: {recursion['confidence']}")
    print(f"\n级别对分析:")
    for pair in recursion['level_pairs']:
        print(f"  {pair['level1']} <-> {pair['level2']}:")
        print(f"    关系: {pair['relationship']}")
        print(f"    趋势一致性: {'是' if pair['trend_consistency'] else '否'}")
        print(f"    信号强度: {pair['signal_strength']:.1f}")
        print(f"    背驰数量: {pair['divergence_count']}")
        print(f"    买卖点匹配: {'是' if pair['buy_sell_match'] else '否'}")

    # 保存结果
    output_file = "/workspace/projects/data/enhanced_multi_level_analysis_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 80)
    print("综合决策")
    print("=" * 80)
    print(f"\n大趋势方向: {report['comprehensive_decision']['overall_trend']}")
    print(f"交易策略: {report['comprehensive_decision']['strategy']}")

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"\n分析结果已保存到: {output_file}")
    print(f"\n总执行时间: {execution_time:.2f}秒")

    print("\n" + "=" * 80)
    print("✅ 增强的多级别缠论分析测试成功！")
    print("=" * 80)


if __name__ == "__main__":
    test_enhanced_multi_level_analysis()
