"""
缠论背驰检测模块
基于MACD、RSI等技术指标检测背驰

缠论背驰定义：
1. 顶背驰：价格创出新高，但技术指标（如MACD）没有创出新高，预示上涨动力衰竭
2. 底背驰：价格创出新低，但技术指标（如MACD）没有创出新低，预示下跌动力衰竭
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import pandas as pd
import numpy as np


class DivergenceType(Enum):
    """背驰类型"""
    TOP = "顶背驰"  # 顶背驰
    BOTTOM = "底背驰"  # 底背驰
    NONE = "无背驰"  # 无背驰


class DivergenceLevel(Enum):
    """背驰级别"""
    STRONG = "强背驰"  # 强背驰
    MEDIUM = "中等背驰"  # 中等背驰
    WEAK = "弱背驰"  # 弱背驰


@dataclass
class DivergencePoint:
    """背驰点"""
    type: DivergenceType  # 背驰类型
    level: DivergenceLevel  # 背驰级别
    index: int  # K线索引
    price: float  # 价格
    macd_value: float  # MACD值
    rsi_value: Optional[float] = None  # RSI值
    volume: Optional[float] = None  # 成交量
    strength: float = 0.0  # 背驰强度（0-100）
    description: str = ""  # 描述


@dataclass
class DivergenceAnalysisResult:
    """背驰分析结果"""
    has_divergence: bool  # 是否有背驰
    divergence_type: DivergenceType  # 背驰类型
    divergence_level: DivergenceLevel  # 背驰级别
    divergence_points: List[DivergencePoint]  # 背驰点列表
    latest_divergence: Optional[DivergencePoint] = None  # 最新背驰点
    macd_divergence: bool = False  # MACD背驰
    rsi_divergence: bool = False  # RSI背驰
    volume_divergence: bool = False  # 成交量背驰
    divergence_strength: float = 0.0  # 综合背驰强度
    description: str = ""  # 描述


class DivergenceDetector:
    """背驰检测器"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化背驰检测器

        Args:
            df: K线数据
        """
        self.df = df.copy()
        self._calculate_indicators()

    def _calculate_indicators(self):
        """计算技术指标"""
        # 计算MACD
        self.df['ema12'] = self.df['close'].ewm(span=12, adjust=False).mean()
        self.df['ema26'] = self.df['close'].ewm(span=26, adjust=False).mean()
        self.df['macd'] = self.df['ema12'] - self.df['ema26']
        self.df['signal'] = self.df['macd'].ewm(span=9, adjust=False).mean()
        self.df['histogram'] = self.df['macd'] - self.df['signal']

        # 计算RSI
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))

    def detect_divergence(self, lookback: int = 20) -> DivergenceAnalysisResult:
        """
        检测背驰

        Args:
            lookback: 回看K线数量

        Returns:
            背驰分析结果
        """
        # 检测顶背驰
        top_divergence = self._detect_top_divergence(lookback)

        # 检测底背驰
        bottom_divergence = self._detect_bottom_divergence(lookback)

        # 综合判断
        if top_divergence:
            divergence_type = DivergenceType.TOP
            divergence_points = top_divergence
        elif bottom_divergence:
            divergence_type = DivergenceType.BOTTOM
            divergence_points = bottom_divergence
        else:
            divergence_type = DivergenceType.NONE
            divergence_points = []

        # 确定背驰级别
        divergence_level = self._determine_divergence_level(divergence_points)

        # 检测各种指标的背驰
        macd_divergence = self._check_macd_divergence(lookback)
        rsi_divergence = self._check_rsi_divergence(lookback)
        volume_divergence = self._check_volume_divergence(lookback)

        # 计算综合背驰强度
        divergence_strength = self._calculate_divergence_strength(
            macd_divergence, rsi_divergence, volume_divergence
        )

        # 生成描述
        description = self._generate_description(divergence_type, divergence_level, divergence_strength)

        # 获取最新背驰点
        latest_divergence = divergence_points[-1] if divergence_points else None

        return DivergenceAnalysisResult(
            has_divergence=len(divergence_points) > 0,
            divergence_type=divergence_type,
            divergence_level=divergence_level,
            divergence_points=divergence_points,
            latest_divergence=latest_divergence,
            macd_divergence=macd_divergence,
            rsi_divergence=rsi_divergence,
            volume_divergence=volume_divergence,
            divergence_strength=divergence_strength,
            description=description
        )

    def _detect_top_divergence(self, lookback: int) -> List[DivergencePoint]:
        """
        检测顶背驰

        Args:
            lookback: 回看K线数量

        Returns:
            顶背驰点列表
        """
        divergence_points = []

        if len(self.df) < lookback + 5:
            return divergence_points

        # 获取最近lookback根K线
        recent_df = self.df.tail(lookback)

        # 寻找价格高点
        for i in range(1, len(recent_df) - 1):
            prev_price = recent_df['close'].iloc[i - 1]
            current_price = recent_df['close'].iloc[i]
            next_price = recent_df['close'].iloc[i + 1]

            # 当前价格是局部高点
            if current_price > prev_price and current_price > next_price:
                # 检查是否有MACD背驰
                prev_macd = recent_df['macd'].iloc[i - 1]
                current_macd = recent_df['macd'].iloc[i]
                next_macd = recent_df['macd'].iloc[i + 1]

                # MACD没有创新高
                if current_macd < prev_macd or current_macd < next_macd:
                    # 检查是否是最近的高点
                    is_latest_high = current_price == recent_df['close'].max()

                    # 计算背驰强度
                    strength = self._calculate_top_divergence_strength(recent_df, i)

                    point = DivergencePoint(
                        type=DivergenceType.TOP,
                        level=DivergenceLevel.MEDIUM if strength >= 50 else DivergenceLevel.WEAK,
                        index=len(self.df) - lookback + i,
                        price=current_price,
                        macd_value=current_macd,
                        rsi_value=recent_df['rsi'].iloc[i] if 'rsi' in recent_df.columns else None,
                        volume=recent_df['volume'].iloc[i] if 'volume' in recent_df.columns else None,
                        strength=strength,
                        description=f"价格创出新高，但MACD没有创新高，顶背驰信号（强度: {strength:.1f}）"
                    )
                    divergence_points.append(point)

        return divergence_points

    def _detect_bottom_divergence(self, lookback: int) -> List[DivergencePoint]:
        """
        检测底背驰

        Args:
            lookback: 回看K线数量

        Returns:
            底背驰点列表
        """
        divergence_points = []

        if len(self.df) < lookback + 5:
            return divergence_points

        # 获取最近lookback根K线
        recent_df = self.df.tail(lookback)

        # 寻找价格低点
        for i in range(1, len(recent_df) - 1):
            prev_price = recent_df['close'].iloc[i - 1]
            current_price = recent_df['close'].iloc[i]
            next_price = recent_df['close'].iloc[i + 1]

            # 当前价格是局部低点
            if current_price < prev_price and current_price < next_price:
                # 检查是否有MACD背驰
                prev_macd = recent_df['macd'].iloc[i - 1]
                current_macd = recent_df['macd'].iloc[i]
                next_macd = recent_df['macd'].iloc[i + 1]

                # MACD没有创新低
                if current_macd > prev_macd or current_macd > next_macd:
                    # 检查是否是最近的低点
                    is_latest_low = current_price == recent_df['close'].min()

                    # 计算背驰强度
                    strength = self._calculate_bottom_divergence_strength(recent_df, i)

                    point = DivergencePoint(
                        type=DivergenceType.BOTTOM,
                        level=DivergenceLevel.MEDIUM if strength >= 50 else DivergenceLevel.WEAK,
                        index=len(self.df) - lookback + i,
                        price=current_price,
                        macd_value=current_macd,
                        rsi_value=recent_df['rsi'].iloc[i] if 'rsi' in recent_df.columns else None,
                        volume=recent_df['volume'].iloc[i] if 'volume' in recent_df.columns else None,
                        strength=strength,
                        description=f"价格创出新低，但MACD没有创新低，底背驰信号（强度: {strength:.1f}）"
                    )
                    divergence_points.append(point)

        return divergence_points

    def _calculate_top_divergence_strength(self, recent_df: pd.DataFrame, index: int) -> float:
        """
        计算顶背驰强度

        Args:
            recent_df: 最近K线数据
            index: 背驰点索引

        Returns:
            背驰强度（0-100）
        """
        try:
            # 价格创新高的幅度
            current_price = recent_df['close'].iloc[index]
            prev_high = recent_df['close'].iloc[:index].max()
            price_increase = (current_price - prev_high) / prev_high * 100

            # MACD没有创新高的幅度
            current_macd = recent_df['macd'].iloc[index]
            prev_high_macd = recent_df['macd'].iloc[:index].max()
            macd_decrease = (prev_high_macd - current_macd) / abs(prev_high_macd) * 100 if prev_high_macd != 0 else 0

            # RSI是否超买
            rsi_value = recent_df['rsi'].iloc[index] if 'rsi' in recent_df.columns else 50
            rsi_overbought = max(0, rsi_value - 70)

            # 综合强度
            strength = min(100, price_increase * 2 + macd_decrease * 3 + rsi_overbought)

            return strength
        except Exception as e:
            return 0.0

    def _calculate_bottom_divergence_strength(self, recent_df: pd.DataFrame, index: int) -> float:
        """
        计算底背驰强度

        Args:
            recent_df: 最近K线数据
            index: 背驰点索引

        Returns:
            背驰强度（0-100）
        """
        try:
            # 价格创新低的幅度
            current_price = recent_df['close'].iloc[index]
            prev_low = recent_df['close'].iloc[:index].min()
            price_decrease = (prev_low - current_price) / prev_low * 100

            # MACD没有创新低的幅度
            current_macd = recent_df['macd'].iloc[index]
            prev_low_macd = recent_df['macd'].iloc[:index].min()
            macd_increase = (current_macd - prev_low_macd) / abs(prev_low_macd) * 100 if prev_low_macd != 0 else 0

            # RSI是否超卖
            rsi_value = recent_df['rsi'].iloc[index] if 'rsi' in recent_df.columns else 50
            rsi_oversold = max(0, 30 - rsi_value)

            # 综合强度
            strength = min(100, price_decrease * 2 + macd_increase * 3 + rsi_oversold)

            return strength
        except Exception as e:
            return 0.0

    def _determine_divergence_level(self, divergence_points: List[DivergencePoint]) -> DivergenceLevel:
        """
        确定背驰级别

        Args:
            divergence_points: 背驰点列表

        Returns:
            背驰级别
        """
        if not divergence_points:
            return DivergenceLevel.WEAK

        # 基于最新背驰点的强度
        latest_strength = divergence_points[-1].strength

        if latest_strength >= 70:
            return DivergenceLevel.STRONG
        elif latest_strength >= 40:
            return DivergenceLevel.MEDIUM
        else:
            return DivergenceLevel.WEAK

    def _check_macd_divergence(self, lookback: int) -> bool:
        """
        检查MACD背驰

        Args:
            lookback: 回看K线数量

        Returns:
            是否有MACD背驰
        """
        if len(self.df) < lookback:
            return False

        recent_df = self.df.tail(lookback)

        # 检查顶背驰
        price_high_index = recent_df['close'].idxmax()
        macd_high_index = recent_df['macd'].idxmax()

        if price_high_index != macd_high_index:
            return True

        # 检查底背驰
        price_low_index = recent_df['close'].idxmin()
        macd_low_index = recent_df['macd'].idxmin()

        if price_low_index != macd_low_index:
            return True

        return False

    def _check_rsi_divergence(self, lookback: int) -> bool:
        """
        检查RSI背驰

        Args:
            lookback: 回看K线数量

        Returns:
            是否有RSI背驰
        """
        if len(self.df) < lookback or 'rsi' not in self.df.columns:
            return False

        recent_df = self.df.tail(lookback)

        # 检查顶背驰：价格创新高，RSI没有创新高
        price_high_index = recent_df['close'].idxmax()
        rsi_high_index = recent_df['rsi'].idxmax()

        if price_high_index != rsi_high_index:
            return True

        # 检查底背驰：价格创新低，RSI没有创新低
        price_low_index = recent_df['close'].idxmin()
        rsi_low_index = recent_df['rsi'].idxmin()

        if price_low_index != rsi_low_index:
            return True

        return False

    def _check_volume_divergence(self, lookback: int) -> bool:
        """
        检查成交量背驰

        Args:
            lookback: 回看K线数量

        Returns:
            是否有成交量背驰
        """
        if len(self.df) < lookback or 'volume' not in self.df.columns:
            return False

        recent_df = self.df.tail(lookback)

        # 检查上涨时的成交量
        price_increasing = recent_df['close'].diff() > 0
        volume_decreasing = recent_df['volume'].diff() < 0

        # 价格上涨但成交量减少，可能是顶背驰
        if (price_increasing & volume_decreasing).sum() > lookback * 0.3:
            return True

        return False

    def _calculate_divergence_strength(self, macd_divergence: bool, rsi_divergence: bool, volume_divergence: bool) -> float:
        """
        计算综合背驰强度

        Args:
            macd_divergence: MACD背驰
            rsi_divergence: RSI背驰
            volume_divergence: 成交量背驰

        Returns:
            综合背驰强度（0-100）
        """
        strength = 0.0

        if macd_divergence:
            strength += 50
        if rsi_divergence:
            strength += 30
        if volume_divergence:
            strength += 20

        return min(100, strength)

    def _generate_description(self, divergence_type: DivergenceType, divergence_level: DivergenceLevel, strength: float) -> str:
        """
        生成背驰描述

        Args:
            divergence_type: 背驰类型
            divergence_level: 背驰级别
            strength: 背驰强度

        Returns:
            背驰描述
        """
        if divergence_type == DivergenceType.NONE:
            return "未检测到背驰信号"

        type_str = "顶背驰" if divergence_type == DivergenceType.TOP else "底背驰"
        level_str = divergence_level.value

        description = f"{level_str}{type_str}信号（强度: {strength:.1f}）"

        if divergence_type == DivergenceType.TOP:
            description += "，预示上涨动力衰竭，可能形成顶部"
        else:
            description += "，预示下跌动力衰竭，可能形成底部"

        return description


def detect_divergence(df: pd.DataFrame, lookback: int = 20) -> Dict[str, Any]:
    """
    检测背驰（便捷函数）

    Args:
        df: K线数据
        lookback: 回看K线数量

    Returns:
        背驰分析结果（字典格式）
    """
    detector = DivergenceDetector(df)
    result = detector.detect_divergence(lookback)

    return {
        'has_divergence': result.has_divergence,
        'divergence_type': result.divergence_type.value,
        'divergence_level': result.divergence_level.value,
        'divergence_points': [
            {
                'type': point.type.value,
                'level': point.level.value,
                'index': point.index,
                'price': point.price,
                'macd_value': point.macd_value,
                'rsi_value': point.rsi_value,
                'volume': point.volume,
                'strength': point.strength,
                'description': point.description
            }
            for point in result.divergence_points
        ],
        'latest_divergence': {
            'type': result.latest_divergence.type.value,
            'level': result.latest_divergence.level.value,
            'index': result.latest_divergence.index,
            'price': result.latest_divergence.price,
            'macd_value': result.latest_divergence.macd_value,
            'strength': result.latest_divergence.strength,
            'description': result.latest_divergence.description
        } if result.latest_divergence else None,
        'macd_divergence': result.macd_divergence,
        'rsi_divergence': result.rsi_divergence,
        'volume_divergence': result.volume_divergence,
        'divergence_strength': result.divergence_strength,
        'description': result.description
    }
