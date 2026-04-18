#!/usr/bin/env python3
"""
缠论买卖点识别模块
实现一买、二买、三买、一卖、二卖、三卖的识别
"""
import pandas as pd
from typing import List, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np


class BuySellType(Enum):
    """买卖点类型"""
    BUY_1 = "一买"      # 第一类买点：中枢下沿下方背驰
    BUY_2 = "二买"      # 第二类买点：中枢回踩不破下沿
    BUY_3 = "三买"      # 第三类买点：中枢上沿上方回踩不破上沿
    SELL_1 = "一卖"     # 第一类卖点：中枢上沿上方背驰
    SELL_2 = "二卖"     # 第二类卖点：中枢回抽不破上沿
    SELL_3 = "三卖"     # 第三类卖点：中枢下沿下方回抽不破下沿


@dataclass
class BuySellPoint:
    """买卖点"""
    type: BuySellType
    index: int                # K线索引
    price: float              # 价格
    level: int                # 级别（1级、2级）
    strength: float           # 强度（0-1）
    zhongshu_index: int       # 对应的中枢索引


class BuySellAnalyzer:
    """缠论买卖点分析器"""

    def __init__(self):
        self.buy_sell_points: List[BuySellPoint] = []

    def identify_buy_sell_points(
        self,
        df: pd.DataFrame,
        segments: List,
        zhongshu_list: List
    ) -> List[BuySellPoint]:
        """
        识别买卖点

        买卖点定义：
        - 一买：下跌趋势中，在最后一个中枢下沿下方出现背驰
        - 二买：一买后的回调不创新低，形成底分型
        - 三买：上升趋势中，突破中枢上沿后回踩不破上沿
        - 一卖：上涨趋势中，在最后一个中枢上沿上方出现背驰
        - 二卖：一卖后的回抽不创新高，形成顶分型
        - 三卖：下跌趋势中，跌破中枢下沿后回抽不破下沿

        Args:
            df: K线数据
            segments: 线段列表
            zhongshu_list: 中枢列表

        Returns:
            买卖点列表
        """
        if not zhongshu_list:
            return []

        buy_sell_points = []

        # 遍历所有中枢，查找买卖点
        for zs_idx, zs in enumerate(zhongshu_list):
            # 一买：中枢下沿下方的背驰
            buy1 = self._check_buy_1(df, zs, segments, zs_idx)
            if buy1:
                buy_sell_points.append(buy1)

            # 一卖：中枢上沿上方的背驰
            sell1 = self._check_sell_1(df, zs, segments, zs_idx)
            if sell1:
                buy_sell_points.append(sell1)

            # 二买：中枢回踩不破下沿
            buy2 = self._check_buy_2(df, zs, segments, zs_idx)
            if buy2:
                buy_sell_points.append(buy2)

            # 二卖：中枢回抽不破上沿
            sell2 = self._check_sell_2(df, zs, segments, zs_idx)
            if sell2:
                buy_sell_points.append(sell2)

            # 三买：突破中枢上沿后回踩不破上沿
            buy3 = self._check_buy_3(df, zs, segments, zs_idx)
            if buy3:
                buy_sell_points.append(buy3)

            # 三卖：跌破中枢下沿后回抽不破下沿
            sell3 = self._check_sell_3(df, zs, segments, zs_idx)
            if sell3:
                buy_sell_points.append(sell3)

        # 按索引排序
        buy_sell_points.sort(key=lambda x: x.index)
        self.buy_sell_points = buy_sell_points
        return buy_sell_points

    def _check_buy_1(self, df: pd.DataFrame, zs, segments: List, zs_idx: int) -> Optional[BuySellPoint]:
        """
        检查第一类买点
        条件：下跌趋势中，在中枢下沿下方出现背驰
        """
        # 找到中枢结束位置
        zs_end_idx = zs.end_index if hasattr(zs, 'end_index') else len(df) - 1

        # 查找中枢下沿下方的低点
        zs_low = zs.low if hasattr(zs, 'low') else zs['low']

        # 在中枢后的数据中寻找背驰
        for i in range(zs_end_idx + 1, len(df)):
            if df.iloc[i]['low'] < zs_low:
                # 检查是否背驰（简化版：检查RSI或MACD）
                if self._check_divergence(df, i, direction='buy'):
                    return BuySellPoint(
                        type=BuySellType.BUY_1,
                        index=i,
                        price=df.iloc[i]['low'],
                        level=1,
                        strength=0.9,
                        zhongshu_index=zs_idx
                    )

        return None

    def _check_sell_1(self, df: pd.DataFrame, zs, segments: List, zs_idx: int) -> Optional[BuySellPoint]:
        """
        检查第一类卖点
        条件：上涨趋势中，在中枢上沿上方出现背驰
        """
        zs_end_idx = zs.end_index if hasattr(zs, 'end_index') else len(df) - 1
        zs_high = zs.high if hasattr(zs, 'high') else zs['high']

        for i in range(zs_end_idx + 1, len(df)):
            if df.iloc[i]['high'] > zs_high:
                if self._check_divergence(df, i, direction='sell'):
                    return BuySellPoint(
                        type=BuySellType.SELL_1,
                        index=i,
                        price=df.iloc[i]['high'],
                        level=1,
                        strength=0.9,
                        zhongshu_index=zs_idx
                    )

        return None

    def _check_buy_2(self, df: pd.DataFrame, zs, segments: List, zs_idx: int) -> Optional[BuySellPoint]:
        """
        检查第二类买点
        条件：一买后的回调不创新低，形成底分型
        """
        # 简化实现：查找中枢上方的回调低点
        zs_high = zs.high if hasattr(zs, 'high') else zs['high']
        zs_low = zs.low if hasattr(zs, 'low') else zs['low']

        for i in range(zs.end_index + 1, len(df)):
            # 回调到中枢区间附近
            if df.iloc[i]['low'] > zs_low * 0.995:  # 允许0.5%误差
                if df.iloc[i]['low'] < zs_high:
                    return BuySellPoint(
                        type=BuySellType.BUY_2,
                        index=i,
                        price=df.iloc[i]['low'],
                        level=1,
                        strength=0.7,
                        zhongshu_index=zs_idx
                    )

        return None

    def _check_sell_2(self, df: pd.DataFrame, zs, segments: List, zs_idx: int) -> Optional[BuySellPoint]:
        """
        检查第二类卖点
        条件：一卖后的回抽不创新高，形成顶分型
        """
        zs_high = zs.high if hasattr(zs, 'high') else zs['high']
        zs_low = zs.low if hasattr(zs, 'low') else zs['low']

        for i in range(zs.end_index + 1, len(df)):
            # 回抽到中枢区间附近
            if df.iloc[i]['high'] < zs_high * 1.005:  # 允许0.5%误差
                if df.iloc[i]['high'] > zs_low:
                    return BuySellPoint(
                        type=BuySellType.SELL_2,
                        index=i,
                        price=df.iloc[i]['high'],
                        level=1,
                        strength=0.7,
                        zhongshu_index=zs_idx
                    )

        return None

    def _check_buy_3(self, df: pd.DataFrame, zs, segments: List, zs_idx: int) -> Optional[BuySellPoint]:
        """
        检查第三类买点
        条件：突破中枢上沿后回踩不破上沿
        """
        zs_high = zs.high if hasattr(zs, 'high') else zs['high']

        # 先找到突破中枢上沿的点
        for i in range(zs.end_index + 1, len(df)):
            if df.iloc[i]['close'] > zs_high:
                # 检查后续回踩是否破上沿
                for j in range(i + 1, len(df)):
                    if df.iloc[j]['low'] > zs_high * 0.998:  # 不破上沿
                        return BuySellPoint(
                            type=BuySellType.BUY_3,
                            index=j,
                            price=df.iloc[j]['low'],
                            level=1,
                            strength=0.8,
                            zhongshu_index=zs_idx
                        )
                    elif df.iloc[j]['close'] < zs_high:
                        # 跌破上沿，三买失败
                        break

        return None

    def _check_sell_3(self, df: pd.DataFrame, zs, segments: List, zs_idx: int) -> Optional[BuySellPoint]:
        """
        检查第三类卖点
        条件：跌破中枢下沿后回抽不破下沿
        """
        zs_low = zs.low if hasattr(zs, 'low') else zs['low']

        # 先找到跌破中枢下沿的点
        for i in range(zs.end_index + 1, len(df)):
            if df.iloc[i]['close'] < zs_low:
                # 检查后续回抽是否破下沿
                for j in range(i + 1, len(df)):
                    if df.iloc[j]['high'] < zs_low * 1.002:  # 不破下沿
                        return BuySellPoint(
                            type=BuySellType.SELL_3,
                            index=j,
                            price=df.iloc[j]['high'],
                            level=1,
                            strength=0.8,
                            zhongshu_index=zs_idx
                        )
                    elif df.iloc[j]['close'] > zs_low:
                        # 突破下沿，三卖失败
                        break

        return None

    def _check_divergence(self, df: pd.DataFrame, index: int, direction: str) -> bool:
        """
        检查背驰
        简化实现：使用价格和RSI的背离
        """
        if index < 10:
            return False

        # 计算简单的RSI
        if 'rsi' not in df.columns:
            df = self._calculate_rsi(df, period=14)

        current_rsi = df.iloc[index]['rsi']
        prev_rsi = df.iloc[index - 5]['rsi'] if index >= 5 else current_rsi

        if direction == 'buy':
            # 底背驰：价格创新低但RSI没有创新低
            if df.iloc[index]['low'] < df.iloc[index - 5]['low']:
                return current_rsi > prev_rsi
        else:  # sell
            # 顶背驰：价格创新高但RSI没有创新高
            if df.iloc[index]['high'] > df.iloc[index - 5]['high']:
                return current_rsi < prev_rsi

        return False

    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算RSI指标"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        df = df.copy()
        df['rsi'] = rsi
        return df

    def get_latest_signal(self) -> Optional[Dict]:
        """获取最新的买卖点信号"""
        if not self.buy_sell_points:
            return None

        latest = self.buy_sell_points[-1]
        return {
            "type": latest.type.value,
            "index": latest.index,
            "price": latest.price,
            "level": latest.level,
            "strength": latest.strength,
            "is_buy": "买" in latest.type.value
        }
