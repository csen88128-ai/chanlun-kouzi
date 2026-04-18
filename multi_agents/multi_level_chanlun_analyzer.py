"""
多级别缠论分析器
整合多级别数据采集、结构分析、级别递归验证、高阶理论分析
"""
import pandas as pd
from typing import Dict, List, Optional
import sys
import os

# 添加路径
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.multi_level_data_collector import MultiLevelDataCollector
from multi_agents.advanced_chanlun_theory import AdvancedChanLunTheory
from src.utils.chanlun_structure import ChanLunAnalyzer


class MultiLevelChanLunAnalyzer:
    """多级别缠论分析器"""

    def __init__(self, symbol="btcusdt"):
        """
        初始化多级别缠论分析器

        Args:
            symbol: 交易对
        """
        self.symbol = symbol
        self.data_collector = MultiLevelDataCollector(symbol)
        self.advanced_theory = AdvancedChanLunTheory()

        # 级别配置
        self.levels = ["5m", "30m", "4h", "1d"]

        # 存储分析结果
        self.all_data = {}
        self.all_analysis = {}

    def collect_all_levels_data(self) -> Dict[str, pd.DataFrame]:
        """
        采集所有级别的K线数据

        Returns:
            所有级别的K线数据
        """
        print("=" * 80)
        print("采集多级别K线数据")
        print("=" * 80)

        self.all_data = self.data_collector.get_all_levels()

        # 显示数据摘要
        summary = self.data_collector.get_data_summary(self.all_data)
        print("\n" + "=" * 80)
        print("数据摘要")
        print("=" * 80)

        for level, info in summary["levels"].items():
            if "status" not in info:
                print(f"\n{level} ({info['name']}):")
                print(f"  K线数量: {info['kline_count']}")
                print(f"  最新价格: {info['latest_price']}")
                print(f"  24h涨跌: {info['h24_change']:.2f}%")

        return self.all_data

    def analyze_single_level(self, level: str, df: pd.DataFrame) -> Dict:
        """
        分析单个级别的缠论结构

        Args:
            level: 级别名称
            df: K线数据

        Returns:
            该级别的缠论分析结果
        """
        print(f"\n分析{level}级别...")

        result = {
            "level": level,
            "level_name": self.data_collector.level_config[level]["name"],
            "kline_count": len(df),
            "fractals": None,
            "bi": None,
            "segment": None,
            "zhongshu": None,
            "buy_sell_points": None,
            "trend": None,
            "divergence": None
        }

        try:
            # 使用 ChanLunAnalyzer 进行分析
            analyzer = ChanLunAnalyzer()

            # 1. 识别分型
            fractals = analyzer.identify_fractals(df)
            analyzer.fractals = fractals
            result["fractals"] = {
                "total": len(fractals),
                "top_count": sum(1 for f in fractals if f.type.value == "top"),
                "bottom_count": sum(1 for f in fractals if f.type.value == "bottom"),
                "latest": fractals[-1].__dict__ if fractals else None
            }

            # 2. 识别笔（需要传递fractals）
            bi = analyzer.identify_bis(df, fractals)
            analyzer.bis = bi
            result["bi"] = {
                "total": len(bi),
                "up_count": sum(1 for b in bi if b.direction.value == "up"),
                "down_count": sum(1 for b in bi if b.direction.value == "down"),
                "latest": bi[-1].__dict__ if bi else None
            }

            # 3. 识别线段（不传递参数，使用self.bis）
            segment = analyzer.identify_segments(df)
            analyzer.segments = segment
            result["segment"] = {
                "total": len(segment),
                "up_count": sum(1 for s in segment if s.direction.value == "up"),
                "down_count": sum(1 for s in segment if s.direction.value == "down"),
                "latest": segment[-1].__dict__ if segment else None
            }

            # 4. 识别中枢（不传递参数，使用self.segments）
            zhongshu = analyzer.identify_zhongshu(df)
            analyzer.zhongshu_list = zhongshu
            result["zhongshu"] = {
                "total": len(zhongshu),
                "latest": zhongshu[-1].__dict__ if zhongshu else None
            }

            # 5. 识别买卖点
            buy_sell_points = analyzer.identify_buy_sell_points(df)
            result["buy_sell_points"] = {
                "total": len(buy_sell_points),
                "latest": buy_sell_points[-1].__dict__ if buy_sell_points else None
            }

            # 6. 判断趋势
            trend = analyzer.determine_trend(df)
            result["trend"] = trend

            # 7. 检测背驰
            divergence = analyzer.check_divergence(df)
            result["divergence"] = divergence

            print(f"  ✓ 分析完成")
            print(f"    - 分型: {result['fractals']['total']}个")
            print(f"    - 笔: {result['bi']['total']}根")
            print(f"    - 线段: {result['segment']['total']}段")
            print(f"    - 中枢: {result['zhongshu']['total']}个")
            print(f"    - 买卖点: {result['buy_sell_points']['total']}个")
            print(f"    - 趋势: {result['trend'].get('direction', '未知')}")

        except Exception as e:
            print(f"  ✗ 分析失败: {e}")
            import traceback
            traceback.print_exc()

        return result

    def analyze_all_levels(self) -> Dict:
        """
        分析所有级别的缠论结构

        Returns:
            所有级别的缠论分析结果
        """
        print("\n" + "=" * 80)
        print("多级别缠论结构分析")
        print("=" * 80)

        self.all_analysis = {}

        for level in self.levels:
            if level in self.all_data and len(self.all_data[level]) > 0:
                self.all_analysis[level] = self.analyze_single_level(level, self.all_data[level])
            else:
                print(f"\n{level}级别无数据，跳过分析")
                self.all_analysis[level] = None

        return self.all_analysis

    def analyze_advanced_theory(self) -> Dict:
        """
        分析高阶缠论理论（小转大、九段升级、区间套）

        Returns:
            高阶理论分析结果
        """
        print("\n" + "=" * 80)
        print("高阶缠论理论分析")
        print("=" * 80)

        result = {
            "small_to_big": {},
            "nine_segment_upgrade": {},
            "interval_nested": {}
        }

        # 1. 检测小转大（5m -> 30m, 30m -> 4h）
        print("\n[1] 检测小转大:")
        for big_level, small_level in [("30m", "5m"), ("4h", "30m"), ("1d", "4h")]:
            if big_level in self.all_data and small_level in self.all_data:
                small_to_big = self.advanced_theory.detect_small_to_big(
                    self.all_data[small_level],
                    self.all_data[big_level]
                )
                result["small_to_big"][f"{small_level}_to_{big_level}"] = small_to_big

                if small_to_big["has_small_to_big"]:
                    print(f"  ⚠️ {small_level}→{big_level}: 小转大！")
                    print(f"    {small_to_big['description']}")
                else:
                    print(f"  ✓ {small_level}→{big_level}: 未检测到小转大")

        # 2. 检测九段升级
        print("\n[2] 检测九段升级:")
        for level in self.levels:
            if level in self.all_analysis and self.all_analysis[level]:
                segment_data = self.all_analysis[level]["segment"]
                if segment_data and "segment_count" in segment_data:
                    # 这里需要从segment数据中提取实际的线段列表
                    # 暂时用线段数量代替
                    nine_segment = self.advanced_theory.detect_nine_segment_upgrade(
                        [{"price": i} for i in range(segment_data["total"])]
                    )
                    result["nine_segment_upgrade"][level] = nine_segment

                    print(f"  {level}: {segment_data['total']}段线段")
                    print(f"    {nine_segment['description']}")

        # 3. 检测区间套
        print("\n[3] 检测区间套:")
        interval_nested = self.advanced_theory.detect_interval_nested(self.all_data)
        result["interval_nested"] = interval_nested

        if interval_nested["has_interval_nested"]:
            print(f"  🎯 区间套！")
            print(f"    {interval_nested['description']}")
            print(f"    可靠性: {interval_nested['reliability']}")
            print(f"    操作建议: {interval_nested['action']}")
        else:
            print(f"  ✓ 未检测到区间套")

        return result

    def generate_comprehensive_report(self) -> Dict:
        """
        生成综合报告

        Returns:
            综合分析报告
        """
        report = {
            "symbol": self.symbol,
            "levels": self.levels,
            "level_analysis": {},
            "advanced_theory": {},
            "comprehensive_decision": {}
        }

        # 1. 各级别分析
        for level in self.levels:
            if level in self.all_analysis and self.all_analysis[level]:
                report["level_analysis"][level] = self.all_analysis[level]

        # 2. 高阶理论分析
        report["advanced_theory"] = self.analyze_advanced_theory()

        # 3. 综合决策（基于日线级别的大趋势）
        if "1d" in self.all_analysis and self.all_analysis["1d"]:
            daily_trend = self.all_analysis["1d"]["trend"]
            if daily_trend and "direction" in daily_trend:
                report["comprehensive_decision"]["overall_trend"] = daily_trend["direction"]

                # 根据大趋势给出建议
                if daily_trend["direction"] == "上涨":
                    report["comprehensive_decision"]["strategy"] = "在大趋势上涨中寻找小级别的买点"
                elif daily_trend["direction"] == "下跌":
                    report["comprehensive_decision"]["strategy"] = "在大趋势下跌中寻找小级别的卖点"
                else:
                    report["comprehensive_decision"]["strategy"] = "大趋势不明，观望为主"
            else:
                report["comprehensive_decision"]["overall_trend"] = "未知"
                report["comprehensive_decision"]["strategy"] = "日线级别分析失败，无法判断大趋势"
        else:
            report["comprehensive_decision"]["overall_trend"] = "未知"
            report["comprehensive_decision"]["strategy"] = "日线级别无数据，无法判断大趋势"

        return report


if __name__ == "__main__":
    print("=" * 80)
    print("测试多级别缠论分析器")
    print("=" * 80)

    # 创建分析器
    analyzer = MultiLevelChanLunAnalyzer(symbol="btcusdt")

    # 采集数据
    analyzer.collect_all_levels_data()

    # 分析所有级别
    analyzer.analyze_all_levels()

    # 高阶理论分析
    advanced_theory = analyzer.analyze_advanced_theory()

    # 生成综合报告
    report = analyzer.generate_comprehensive_report()

    print("\n" + "=" * 80)
    print("综合报告")
    print("=" * 80)

    print(f"\n大趋势方向: {report['comprehensive_decision'].get('overall_trend', '未知')}")
    print(f"交易策略: {report['comprehensive_decision'].get('strategy', '未知')}")
