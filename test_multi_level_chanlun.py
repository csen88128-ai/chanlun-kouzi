#!/usr/bin/env python3
"""
测试多级别缠论分析
验证多级别数据采集、结构分析、高阶理论分析功能
"""
import sys
import json
import time
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.multi_level_chanlun_analyzer import MultiLevelChanLunAnalyzer


def test_multi_level_chanlun_analysis():
    """测试多级别缠论分析"""
    print("=" * 80)
    print("测试多级别缠论分析")
    print("=" * 80)

    start_time = time.time()

    # 创建分析器
    analyzer = MultiLevelChanLunAnalyzer(symbol="btcusdt")

    # 1. 采集数据
    print("\n[1] 采集多级别K线数据...")
    all_data = analyzer.collect_all_levels_data()

    data_valid = True
    for level, df in all_data.items():
        if len(df) == 0:
            print(f"  ✗ {level}级别数据为空")
            data_valid = False
        else:
            print(f"  ✓ {level}级别: {len(df)}根K线")

    if not data_valid:
        print("\n数据采集失败，终止测试")
        return False

    # 2. 分析所有级别
    print("\n[2] 分析所有级别...")
    all_analysis = analyzer.analyze_all_levels()

    for level in analyzer.levels:
        if level in all_analysis and all_analysis[level]:
            analysis = all_analysis[level]
            print(f"\n  {level}级别分析结果:")
            if analysis['fractals']:
                print(f"    - 分型: {analysis['fractals']['total']}个")
            if analysis['bi']:
                print(f"    - 笔: {analysis['bi']['total']}根")
            if analysis['segment']:
                print(f"    - 线段: {analysis['segment']['total']}段")
            if analysis['zhongshu']:
                print(f"    - 中枢: {analysis['zhongshu']['total']}个")
            if analysis['buy_sell_points']:
                print(f"    - 买卖点: {analysis['buy_sell_points']['total']}个")
            if analysis['trend']:
                print(f"    - 趋势: {analysis['trend'].get('direction', '未知')}")

    # 3. 高阶理论分析
    print("\n[3] 高阶缠论理论分析...")
    advanced_theory = analyzer.analyze_advanced_theory()

    # 4. 生成综合报告
    print("\n[4] 生成综合报告...")
    report = analyzer.generate_comprehensive_report()

    # 5. 显示综合决策
    print("\n" + "=" * 80)
    print("综合决策")
    print("=" * 80)

    if "comprehensive_decision" in report:
        decision = report["comprehensive_decision"]
        print(f"\n大趋势方向: {decision.get('overall_trend', '未知')}")
        print(f"交易策略: {decision.get('strategy', '未知')}")

    # 6. 保存结果
    output_file = "/workspace/projects/data/multi_level_analysis_result.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n分析结果已保存到: {output_file}")

    # 7. 执行时间
    execution_time = time.time() - start_time
    print(f"\n总执行时间: {execution_time:.2f}秒")

    return True


if __name__ == "__main__":
    success = test_multi_level_chanlun_analysis()

    if success:
        print("\n✅ 多级别缠论分析测试成功！")
    else:
        print("\n❌ 多级别缠论分析测试失败！")

    sys.exit(0 if success else 1)
