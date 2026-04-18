"""
动力学分析智能体
分析RSI、MACD、波动率、成交量等技术指标
计算动力学评分因子（25%权重）
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class SignalStrength(Enum):
    """信号强度"""
    STRONG = "强"
    MEDIUM = "中"
    WEAK = "弱"
    NONE = "无"


class TrendDirection(Enum):
    """趋势方向"""
    UP = "向上"
    DOWN = "向下"
    SIDEWAYS = "震荡"
    UNKNOWN = "未知"


@dataclass
class RSIAnalysis:
    """RSI分析结果"""
    current_rsi: float
    signal: str  # 超买、超卖、正常
    strength: SignalStrength
    direction: TrendDirection
    signal_score: float  # 0-100


@dataclass
class MACDAnalysis:
    """MACD分析结果"""
    macd: float
    signal: float
    histogram: float
    signal_type: str  # 金叉、死叉、正常
    strength: SignalStrength
    direction: TrendDirection
    signal_score: float  # 0-100


@dataclass
class VolatilityAnalysis:
    """波动率分析结果"""
    current_volatility: float
    volatility_trend: str  # 上升、下降、稳定
    volatility_level: str  # 高、中、低
    signal_score: float  # 0-100


@dataclass
class VolumeAnalysis:
    """成交量分析结果"""
    current_volume: float
    volume_ma: float
    volume_ratio: float  # 当前成交量/MA
    volume_trend: str  # 放量、缩量、正常
    volume_price_relationship: str  # 量价关系
    signal_score: float  # 0-100


@dataclass
class DynamicsAnalysisResult:
    """动力学分析综合结果"""
    rsi: RSIAnalysis
    macd: MACDAnalysis
    volatility: VolatilityAnalysis
    volume: VolumeAnalysis
    overall_score: float  # 综合评分 0-100
    overall_signal: str  # 综合信号
    overall_direction: str  # 综合方向
    dynamics_factor: float  # 动力学因子（0-1），用于决策制定（25%权重）
    description: str  # 综合描述


class DynamicsAnalyzer:
    """动力学分析器"""

    def __init__(self, df: pd.DataFrame):
        """
        初始化动力学分析器

        Args:
            df: K线数据
        """
        self.df = df.copy()
        self._calculate_indicators()

    def _calculate_indicators(self):
        """计算技术指标"""
        # 计算RSI
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        self.df['rsi'] = 100 - (100 / (1 + rs))

        # 计算MACD
        self.df['ema12'] = self.df['close'].ewm(span=12, adjust=False).mean()
        self.df['ema26'] = self.df['close'].ewm(span=26, adjust=False).mean()
        self.df['macd'] = self.df['ema12'] - self.df['ema26']
        self.df['signal'] = self.df['macd'].ewm(span=9, adjust=False).mean()
        self.df['histogram'] = self.df['macd'] - self.df['signal']

        # 计算波动率（标准差）
        self.df['returns'] = self.df['close'].pct_change()
        self.df['volatility'] = self.df['returns'].rolling(window=20).std() * 100

        # 计算成交量均线
        if 'volume' in self.df.columns:
            self.df['volume_ma20'] = self.df['volume'].rolling(window=20).mean()

    def analyze_rsi(self) -> RSIAnalysis:
        """
        分析RSI

        Returns:
            RSI分析结果
        """
        current_rsi = self.df['rsi'].iloc[-1]

        # 判断信号
        if current_rsi >= 70:
            signal = "超买"
            strength = SignalStrength.STRONG
            signal_score = max(0, 100 - current_rsi)  # 超买分数越低越好
        elif current_rsi <= 30:
            signal = "超卖"
            strength = SignalStrength.STRONG
            signal_score = current_rsi  # 超卖分数越高越好
        elif current_rsi >= 60:
            signal = "偏强"
            strength = SignalStrength.MEDIUM
            signal_score = 50 + (current_rsi - 60)
        elif current_rsi <= 40:
            signal = "偏弱"
            strength = SignalStrength.MEDIUM
            signal_score = 50 - (40 - current_rsi)
        else:
            signal = "正常"
            strength = SignalStrength.WEAK
            signal_score = 50

        # 判断方向
        rsi_prev = self.df['rsi'].iloc[-2]
        if current_rsi > rsi_prev:
            direction = TrendDirection.UP
        elif current_rsi < rsi_prev:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.SIDEWAYS

        return RSIAnalysis(
            current_rsi=current_rsi,
            signal=signal,
            strength=strength.value,
            direction=direction.value,
            signal_score=signal_score
        )

    def analyze_macd(self) -> MACDAnalysis:
        """
        分析MACD

        Returns:
            MACD分析结果
        """
        macd = self.df['macd'].iloc[-1]
        signal_line = self.df['signal'].iloc[-1]
        histogram = self.df['histogram'].iloc[-1]

        # 判断金叉死叉
        prev_macd = self.df['macd'].iloc[-2]
        prev_signal = self.df['signal'].iloc[-2]

        if macd > signal_line and prev_macd <= prev_signal:
            signal_type = "金叉"
            strength = SignalStrength.STRONG
            signal_score = 80
        elif macd < signal_line and prev_macd >= prev_signal:
            signal_type = "死叉"
            strength = SignalStrength.STRONG
            signal_score = 20
        elif macd > signal_line:
            signal_type = "多头排列"
            strength = SignalStrength.MEDIUM
            signal_score = 60
        elif macd < signal_line:
            signal_type = "空头排列"
            strength = SignalStrength.MEDIUM
            signal_score = 40
        else:
            signal_type = "正常"
            strength = SignalStrength.WEAK
            signal_score = 50

        # 判断方向
        if macd > 0:
            direction = TrendDirection.UP
        elif macd < 0:
            direction = TrendDirection.DOWN
        else:
            direction = TrendDirection.SIDEWAYS

        return MACDAnalysis(
            macd=macd,
            signal=signal_line,
            histogram=histogram,
            signal_type=signal_type,
            strength=strength.value,
            direction=direction.value,
            signal_score=signal_score
        )

    def analyze_volatility(self) -> VolatilityAnalysis:
        """
        分析波动率

        Returns:
            波动率分析结果
        """
        current_vol = self.df['volatility'].iloc[-1]
        prev_vol = self.df['volatility'].iloc[-2]

        # 判断波动率趋势
        if current_vol > prev_vol * 1.1:
            volatility_trend = "上升"
        elif current_vol < prev_vol * 0.9:
            volatility_trend = "下降"
        else:
            volatility_trend = "稳定"

        # 判断波动率水平
        vol_avg = self.df['volatility'].tail(20).mean()
        if current_vol > vol_avg * 1.5:
            volatility_level = "高"
            signal_score = 30  # 高波动率风险较大
        elif current_vol < vol_avg * 0.7:
            volatility_level = "低"
            signal_score = 70  # 低波动率适合布局
        else:
            volatility_level = "中"
            signal_score = 50

        return VolatilityAnalysis(
            current_volatility=current_vol,
            volatility_trend=volatility_trend,
            volatility_level=volatility_level,
            signal_score=signal_score
        )

    def analyze_volume(self) -> VolumeAnalysis:
        """
        分析成交量

        Returns:
            成交量分析结果
        """
        if 'volume' not in self.df.columns:
            return VolumeAnalysis(
                current_volume=0,
                volume_ma=0,
                volume_ratio=0,
                volume_trend="未知",
                volume_price_relationship="未知",
                signal_score=50
            )

        current_volume = self.df['volume'].iloc[-1]
        volume_ma = self.df['volume_ma20'].iloc[-1]

        # 计算成交量比率
        volume_ratio = current_volume / volume_ma if volume_ma != 0 else 1

        # 判断成交量趋势
        if volume_ratio > 1.5:
            volume_trend = "放量"
        elif volume_ratio < 0.7:
            volume_trend = "缩量"
        else:
            volume_trend = "正常"

        # 判断量价关系
        price_change = self.df['close'].iloc[-1] - self.df['close'].iloc[-2]
        prev_price_change = self.df['close'].iloc[-2] - self.df['close'].iloc[-3]

        if price_change > 0 and volume_ratio > 1.2:
            volume_price_relationship = "量价齐升"  # 做多信号
            signal_score = 80
        elif price_change < 0 and volume_ratio > 1.2:
            volume_price_relationship = "量价背离"  # 做空信号
            signal_score = 20
        elif price_change > 0 and volume_ratio < 0.8:
            volume_price_relationship = "价升量缩"  # 可能反转
            signal_score = 40
        elif price_change < 0 and volume_ratio < 0.8:
            volume_price_relationship = "价跌量缩"  # 可能企稳
            signal_score = 60
        else:
            volume_price_relationship = "正常"
            signal_score = 50

        return VolumeAnalysis(
            current_volume=current_volume,
            volume_ma=volume_ma,
            volume_ratio=volume_ratio,
            volume_trend=volume_trend,
            volume_price_relationship=volume_price_relationship,
            signal_score=signal_score
        )

    def analyze_dynamics(self) -> DynamicsAnalysisResult:
        """
        综合分析动力学指标

        Returns:
            动力学分析综合结果
        """
        # 分析各个指标
        rsi_result = self.analyze_rsi()
        macd_result = self.analyze_macd()
        volatility_result = self.analyze_volatility()
        volume_result = self.analyze_volume()

        # 计算综合评分（加权平均）
        # RSI: 25%, MACD: 30%, 波动率: 20%, 成交量: 25%
        overall_score = (
            rsi_result.signal_score * 0.25 +
            macd_result.signal_score * 0.30 +
            volatility_result.signal_score * 0.20 +
            volume_result.signal_score * 0.25
        )

        # 判断综合信号
        if overall_score >= 70:
            overall_signal = "强做多"
            overall_direction = "向上"
        elif overall_score >= 60:
            overall_signal = "偏多"
            overall_direction = "向上"
        elif overall_score <= 30:
            overall_signal = "强做空"
            overall_direction = "向下"
        elif overall_score <= 40:
            overall_signal = "偏空"
            overall_direction = "向下"
        else:
            overall_signal = "震荡"
            overall_direction = "震荡"

        # 计算动力学因子（0-1），用于决策制定（25%权重）
        dynamics_factor = overall_score / 100.0

        # 生成综合描述
        description = f"动力学分析：RSI={rsi_result.current_rsi:.1f}（{rsi_result.signal}），"
        description += f"MACD={macd_result.macd:.2f}（{macd_result.signal_type}），"
        description += f"波动率={volatility_result.current_volatility:.2f}%（{volatility_result.volatility_level}），"
        description += f"成交量={volume_result.volume_trend}（{volume_result.volume_price_relationship}），"
        description += f"综合评分={overall_score:.1f}（{overall_signal}）"

        return DynamicsAnalysisResult(
            rsi=rsi_result,
            macd=macd_result,
            volatility=volatility_result,
            volume=volume_result,
            overall_score=overall_score,
            overall_signal=overall_signal,
            overall_direction=overall_direction,
            dynamics_factor=dynamics_factor,
            description=description
        )


def analyze_dynamics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析动力学指标（便捷函数）

    Args:
        df: K线数据

    Returns:
        动力学分析结果（字典格式）
    """
    analyzer = DynamicsAnalyzer(df)
    result = analyzer.analyze_dynamics()

    return {
        'rsi': {
            'current_rsi': result.rsi.current_rsi,
            'signal': result.rsi.signal,
            'strength': result.rsi.strength,
            'direction': result.rsi.direction,
            'signal_score': result.rsi.signal_score
        },
        'macd': {
            'macd': result.macd.macd,
            'signal': result.macd.signal,
            'histogram': result.macd.histogram,
            'signal_type': result.macd.signal_type,
            'strength': result.macd.strength,
            'direction': result.macd.direction,
            'signal_score': result.macd.signal_score
        },
        'volatility': {
            'current_volatility': result.volatility.current_volatility,
            'volatility_trend': result.volatility.volatility_trend,
            'volatility_level': result.volatility.volatility_level,
            'signal_score': result.volatility.signal_score
        },
        'volume': {
            'current_volume': result.volume.current_volume,
            'volume_ma': result.volume.volume_ma,
            'volume_ratio': result.volume.volume_ratio,
            'volume_trend': result.volume.volume_trend,
            'volume_price_relationship': result.volume.volume_price_relationship,
            'signal_score': result.volume.signal_score
        },
        'overall_score': result.overall_score,
        'overall_signal': result.overall_signal,
        'overall_direction': result.overall_direction,
        'dynamics_factor': result.dynamics_factor,
        'description': result.description
    }
