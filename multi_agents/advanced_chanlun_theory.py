"""
高阶缠论理论实现
包括：小转大、九段升级、区间套、级别递归验证
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple
import numpy as np


class AdvancedChanLunTheory:
    """高阶缠论理论分析"""

    def __init__(self):
        """初始化高阶缠论理论分析器"""
        pass

    def detect_small_to_big(self, small_level_data: pd.DataFrame, big_level_data: pd.DataFrame) -> Dict:
        """
        检测小转大（小级别转折引发大级别转折）

        Args:
            small_level_data: 小级别K线数据（如5m）
            big_level_data: 大级别K线数据（如30m）

        Returns:
            小转大分析结果
        """
        result = {
            "has_small_to_big": False,
            "small_level_signal": None,
            "big_level_status": None,
            "risk_level": "低",
            "description": "",
            "action": ""
        }

        # 1. 检测小级别的背驰信号
        small_divergence = self._detect_divergence(small_level_data)

        # 2. 检测大级别的背驰状态
        big_divergence = self._detect_divergence(big_level_data)

        # 3. 判断是否为小转大
        if small_divergence["has_divergence"] and not big_divergence["has_divergence"]:
            # 小级别有背驰，大级别无背驰 = 小转大
            result["has_small_to_big"] = True
            result["small_level_signal"] = small_divergence
            result["big_level_status"] = "无背驰"
            result["risk_level"] = "高"
            result["description"] = f"小级别出现{small_divergence['type']}，大级别无背驰，可能引发大级别转折"
            result["action"] = "警惕小转大，及时平仓或反手"
        else:
            result["description"] = "未检测到小转大信号"

        return result

    def detect_nine_segment_upgrade(self, segments: List[Dict]) -> Dict:
        """
        检测九段升级（中枢线段数量达到9段，升级）

        Args:
            segments: 线段列表

        Returns:
            九段升级分析结果
        """
        result = {
            "has_upgrade": False,
            "segment_count": len(segments),
            "current_level": 1,
            "upgrade_level": None,
            "description": "",
            "action": ""
        }

        segment_count = len(segments)

        # 检查线段数量
        if segment_count >= 27:
            result["has_upgrade"] = True
            result["current_level"] = 1
            result["upgrade_level"] = 3
            result["description"] = f"线段数量达到{segment_count}段，中枢级别从1级升级到3级"
            result["action"] = "买卖点级别提升，增加持仓时间和空间"
        elif segment_count >= 9:
            result["has_upgrade"] = True
            result["current_level"] = 1
            result["upgrade_level"] = 2
            result["description"] = f"线段数量达到{segment_count}段，中枢级别从1级升级到2级"
            result["action"] = "买卖点级别提升，增加持仓时间和空间"
        else:
            result["description"] = f"线段数量为{segment_count}段，未达到升级标准（需要9段）"

        return result

    def detect_interval_nested(self, level_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        检测区间套（多个级别同时出现背驰）

        Args:
            level_data: 多级别数据，key为级别名（5m、30m、4h、1d），value为DataFrame

        Returns:
            区间套分析结果
        """
        result = {
            "has_interval_nested": False,
            "divergence_levels": [],
            "divergence_count": 0,
            "divergence_type": None,
            "reliability": "低",
            "description": "",
            "action": ""
        }

        # 检测每个级别的背驰
        divergence_signals = {}
        for level, df in level_data.items():
            divergence = self._detect_divergence(df)
            if divergence["has_divergence"]:
                divergence_signals[level] = divergence

        # 统计背驰级别数量
        divergence_count = len(divergence_signals)
        result["divergence_count"] = divergence_count

        if divergence_count >= 2:
            # 至少2个级别同时背驰 = 区间套
            result["has_interval_nested"] = True
            result["divergence_levels"] = list(divergence_signals.keys())
            result["reliability"] = "高" if divergence_count >= 3 else "中"

            # 检查背驰类型是否一致
            divergence_types = [d["type"] for d in divergence_signals.values()]
            if len(set(divergence_types)) == 1:
                result["divergence_type"] = divergence_types[0]
                result["description"] = f"{'、'.join(result['divergence_levels'])}级别同时出现{result['divergence_type']}，区间套信号"
                result["action"] = "区间套是最可靠的买卖点，可以加大仓位，止损可以设置得更宽"
            else:
                result["description"] = f"多个级别出现背驰，但类型不一致"
                result["action"] = "关注后续走势，等待信号确认"
        else:
            result["description"] = f"仅{divergence_count}个级别出现背驰，未形成区间套"

        return result

    def validate_level_recursion(self, level_data: Dict[str, pd.DataFrame], bi_data: Dict[str, List]) -> Dict:
        """
        验证级别递归关系（大级别一笔 = 小级别一段）

        Args:
            level_data: 多级别K线数据
            bi_data: 多级别笔数据

        Returns:
            级别递归验证结果
        """
        result = {
            "is_valid": True,
            "validations": [],
            "consistency_score": 0.0,
            "description": ""
        }

        # 验证：大级别一笔 = 小级别一段
        validation_pairs = [
            ("1d", "4h"),
            ("4h", "30m"),
            ("30m", "5m")
        ]

        validations = []
        for big_level, small_level in validation_pairs:
            if big_level not in bi_data or small_level not in bi_data:
                continue

            big_bi_count = len(bi_data[big_level])
            small_segment_count = len(bi_data[small_level]) // 3  # 粗略估计：一段约等于3笔

            # 验证一致性（允许一定误差）
            ratio = small_segment_count / big_bi_count if big_bi_count > 0 else 0
            is_valid = 0.8 <= ratio <= 1.2  # 允许20%误差

            validation = {
                "big_level": big_level,
                "small_level": small_level,
                "rule": f"{big_level}级别的一笔 = {small_level}级别的一段",
                "big_bi_count": big_bi_count,
                "small_segment_count": small_segment_count,
                "ratio": ratio,
                "is_valid": is_valid
            }

            validations.append(validation)

            if not is_valid:
                result["is_valid"] = False

        result["validations"] = validations

        # 计算一致性得分
        if validations:
            valid_count = sum(1 for v in validations if v["is_valid"])
            result["consistency_score"] = valid_count / len(validations) * 100

        result["description"] = f"级别递归验证完成，一致性得分: {result['consistency_score']:.1f}%"

        return result

    def _detect_divergence(self, df: pd.DataFrame) -> Dict:
        """
        检测背驰（简化版）

        Args:
            df: K线数据

        Returns:
            背驰检测结果
        """
        result = {
            "has_divergence": False,
            "type": None,
            "strength": 0.0,
            "price": None
        }

        if len(df) < 10:
            return result

        # 计算MACD
        df["ema12"] = df["close"].ewm(span=12, adjust=False).mean()
        df["ema26"] = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = df["ema12"] - df["ema26"]
        df["signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["histogram"] = df["macd"] - df["signal"]

        # 检测顶背驰（价格上涨，MACD柱减弱）
        if df.iloc[-1]["close"] > df.iloc[-5]["close"]:  # 价格上涨
            if df.iloc[-1]["histogram"] < df.iloc[-5]["histogram"]:  # MACD柱减弱
                result["has_divergence"] = True
                result["type"] = "顶背驰"
                result["strength"] = abs(df.iloc[-5]["histogram"] - df.iloc[-1]["histogram"])
                result["price"] = df.iloc[-1]["close"]

        # 检测底背驰（价格下跌，MACD柱增强）
        elif df.iloc[-1]["close"] < df.iloc[-5]["close"]:  # 价格下跌
            if df.iloc[-1]["histogram"] > df.iloc[-5]["histogram"]:  # MACD柱增强
                result["has_divergence"] = True
                result["type"] = "底背驰"
                result["strength"] = abs(df.iloc[-5]["histogram"] - df.iloc[-1]["histogram"])
                result["price"] = df.iloc[-1]["close"]

        return result

    def analyze_zhongshu_extension(self, segments: List[Dict], zhongshu: Dict) -> Dict:
        """
        分析中枢延伸（判断是否形成九段升级）

        Args:
            segments: 线段列表
            zhongshu: 中枢信息

        Returns:
            中枢延伸分析结果
        """
        result = {
            "segment_count": len(segments),
            "is_nine_segment": False,
            "upgrade_level": None,
            "extension_type": "正常",
            "description": ""
        }

        segment_count = len(segments)

        # 判断中枢延伸类型
        if segment_count < 5:
            result["extension_type"] = "正常（3-4段）"
            result["description"] = f"中枢线段数量为{segment_count}段，处于正常范围"
        elif segment_count < 9:
            result["extension_type"] = "延伸（5-8段）"
            result["description"] = f"中枢线段数量为{segment_count}段，处于延伸状态"
        elif segment_count < 27:
            result["extension_type"] = "九段升级（9-26段）"
            result["is_nine_segment"] = True
            result["upgrade_level"] = 2
            result["description"] = f"中枢线段数量达到{segment_count}段，从1级升级到2级"
        else:
            result["extension_type"] = "多次升级（27段以上）"
            result["is_nine_segment"] = True
            result["upgrade_level"] = 3
            result["description"] = f"中枢线段数量达到{segment_count}段，从1级升级到3级"

        return result


if __name__ == "__main__":
    print("=" * 80)
    print("高阶缠论理论测试")
    print("=" * 80)

    # 创建高阶缠论理论分析器
    analyzer = AdvancedChanLunTheory()

    # 测试九段升级
    print("\n[1] 测试九段升级:")
    test_segments_5 = [{"price": i} for i in range(5)]
    result_5 = analyzer.detect_nine_segment_upgrade(test_segments_5)
    print(f"  5段线段: {result_5['description']}")

    test_segments_9 = [{"price": i} for i in range(9)]
    result_9 = analyzer.detect_nine_segment_upgrade(test_segments_9)
    print(f"  9段线段: {result_9['description']}")

    test_segments_27 = [{"price": i} for i in range(27)]
    result_27 = analyzer.detect_nine_segment_upgrade(test_segments_27)
    print(f"  27段线段: {result_27['description']}")

    print("\n[2] 测试完成")
