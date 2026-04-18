"""
缠论趋势判断模块
基于中枢和线段的方向判断趋势

缠论趋势定义：
1. 向上趋势：价格不断创出新高，低点不断抬高
2. 向下趋势：价格不断创出新低，高点不断降低
3. 盘整：价格在中枢区间内震荡
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
import pandas as pd


class TrendDirection(Enum):
    """趋势方向"""
    UP = "向上"  # 向上趋势
    DOWN = "向下"  # 向下趋势
    CONSOLIDATION = "盘整"  # 盘整
    UNKNOWN = "未知"  # 未知


@dataclass
class TrendInfo:
    """趋势信息"""
    direction: TrendDirection  # 趋势方向
    strength: float  # 趋势强度（0-100）
    confidence: str  # 置信度（高、中、低）
    description: str  # 描述
    start_price: float  # 起始价格
    end_price: float  # 结束价格
    start_index: int  # 起始索引
    end_index: int  # 结束索引
    duration: int  # 持续时间（K线数量）
    zhongshu_level: int  # 关联的中枢级别
    support_level: Optional[float] = None  # 支撑位
    resistance_level: Optional[float] = None  # 阻力位


@dataclass
class TrendAnalysisResult:
    """趋势分析结果"""
    current_trend: TrendInfo  # 当前趋势
    trend_changes: List[TrendInfo]  # 趋势变化历史
    trend_strength: float  # 趋势强度
    trend_duration: int  # 趋势持续时间
    expected_direction: str  # 预期方向
    risk_level: str  # 风险水平


class TrendAnalyzer:
    """趋势分析器"""

    def __init__(self, df: pd.DataFrame, bi: List[Any], segment: List[Any], zhongshu: Any):
        """
        初始化趋势分析器

        Args:
            df: K线数据
            bi: 笔列表
            segment: 线段列表
            zhongshu: 中枢对象
        """
        self.df = df
        self.bi = bi
        self.segment = segment
        self.zhongshu = zhongshu

    def analyze_trend(self) -> TrendAnalysisResult:
        """
        分析趋势

        Returns:
            趋势分析结果
        """
        # 判断当前趋势
        current_trend = self._determine_current_trend()

        # 获取趋势变化历史
        trend_changes = self._get_trend_changes()

        # 计算趋势强度
        trend_strength = self._calculate_trend_strength()

        # 计算趋势持续时间
        trend_duration = current_trend.duration

        # 预期方向
        expected_direction = self._predict_next_direction(current_trend)

        # 风险水平
        risk_level = self._assess_risk_level(current_trend, trend_strength)

        return TrendAnalysisResult(
            current_trend=current_trend,
            trend_changes=trend_changes,
            trend_strength=trend_strength,
            trend_duration=trend_duration,
            expected_direction=expected_direction,
            risk_level=risk_level
        )

    def _determine_current_trend(self) -> TrendInfo:
        """
        判断当前趋势

        Returns:
            当前趋势信息
        """
        # 获取中枢信息
        zhongshu_info = self._get_zhongshu_info()

        # 判断趋势方向
        direction = self._judge_trend_direction(zhongshu_info)

        # 计算趋势强度
        strength = self._calculate_current_trend_strength(direction)

        # 确定置信度
        confidence = self._determine_confidence(strength)

        # 生成描述
        description = self._generate_description(direction, strength)

        # 起始和结束信息
        start_index, end_index = self._get_trend_range(direction)
        start_price = self.df['close'].iloc[start_index]
        end_price = self.df['close'].iloc[end_index]

        # 支撑位和阻力位
        support_level = zhongshu_info.get('low') if zhongshu_info else None
        resistance_level = zhongshu_info.get('high') if zhongshu_info else None

        return TrendInfo(
            direction=direction,
            strength=strength,
            confidence=confidence,
            description=description,
            start_price=start_price,
            end_price=end_price,
            start_index=start_index,
            end_index=end_index,
            duration=end_index - start_index,
            zhongshu_level=zhongshu_info.get('level', 1) if zhongshu_info else 1,
            support_level=support_level,
            resistance_level=resistance_level
        )

    def _get_zhongshu_info(self) -> Dict[str, Any]:
        """
        获取中枢信息

        Returns:
            中枢信息字典
        """
        if self.zhongshu is None or not hasattr(self.zhongshu, '__dict__'):
            return {}

        try:
            if hasattr(self.zhongshu, 'high') and hasattr(self.zhongshu, 'low'):
                return {
                    'high': self.zhongshu.high,
                    'low': self.zhongshu.low,
                    'high_point': self.zhongshu.high_point if hasattr(self.zhongshu, 'high_point') else self.zhongshu.high,
                    'low_point': self.zhongshu.low_point if hasattr(self.zhongshu, 'low_point') else self.zhongshu.low,
                    'level': self.zhongshu.level if hasattr(self.zhongshu, 'level') else 1,
                    'start_index': self.zhongshu.start_index if hasattr(self.zhongshu, 'start_index') else 0,
                    'end_index': self.zhongshu.end_index if hasattr(self.zhongshu, 'end_index') else len(self.df) - 1,
                }
        except Exception as e:
            pass

        return {}

    def _judge_trend_direction(self, zhongshu_info: Dict[str, Any]) -> TrendDirection:
        """
        判断趋势方向

        Args:
            zhongshu_info: 中枢信息

        Returns:
            趋势方向
        """
        if not self.segment or len(self.segment) < 2:
            return TrendDirection.UNKNOWN

        # 方法1：基于线段方向
        recent_segments = self.segment[-5:] if len(self.segment) >= 5 else self.segment
        up_count = sum(1 for seg in recent_segments if hasattr(seg, 'direction') and seg.direction == 'up')
        down_count = sum(1 for seg in recent_segments if hasattr(seg, 'direction') and seg.direction == 'down')

        # 方法2：基于价格位置
        latest_price = self.df['close'].iloc[-1]
        ma20 = self.df['close'].rolling(window=20).mean().iloc[-1]
        ma60 = self.df['close'].rolling(window=60).mean().iloc[-1]

        # 综合判断
        if up_count > down_count and latest_price > ma20 > ma60:
            return TrendDirection.UP
        elif down_count > up_count and latest_price < ma20 < ma60:
            return TrendDirection.DOWN
        else:
            # 检查是否在中枢区间内
            if zhongshu_info and zhongshu_info['low'] <= latest_price <= zhongshu_info['high']:
                return TrendDirection.CONSOLIDATION
            else:
                return TrendDirection.UNKNOWN

    def _calculate_current_trend_strength(self, direction: TrendDirection) -> float:
        """
        计算当前趋势强度

        Args:
            direction: 趋势方向

        Returns:
            趋势强度（0-100）
        """
        if direction == TrendDirection.UNKNOWN:
            return 0.0

        # 基于最近20根K线的价格变化
        recent_prices = self.df['close'].tail(20)
        price_change = (recent_prices.iloc[-1] - recent_prices.iloc[0]) / recent_prices.iloc[0] * 100

        # 基于线段一致性
        if self.segment:
            recent_segments = self.segment[-5:] if len(self.segment) >= 5 else self.segment
            consistent_count = sum(1 for seg in recent_segments
                                  if hasattr(seg, 'direction') and
                                  ((direction == TrendDirection.UP and seg.direction == 'up') or
                                   (direction == TrendDirection.DOWN and seg.direction == 'down')))
            consistency = consistent_count / len(recent_segments) if recent_segments else 0
        else:
            consistency = 0

        # 综合强度
        strength = min(100, (abs(price_change) * 10 + consistency * 50))

        return strength

    def _determine_confidence(self, strength: float) -> str:
        """
        确定置信度

        Args:
            strength: 趋势强度

        Returns:
            置信度（高、中、低）
        """
        if strength >= 70:
            return "高"
        elif strength >= 40:
            return "中"
        else:
            return "低"

    def _generate_description(self, direction: TrendDirection, strength: float) -> str:
        """
        生成趋势描述

        Args:
            direction: 趋势方向
            strength: 趋势强度

        Returns:
            趋势描述
        """
        if direction == TrendDirection.UP:
            if strength >= 70:
                return "强势上涨趋势，价格持续创出新高，多头力量强劲"
            elif strength >= 40:
                return "温和上涨趋势，价格稳步上涨，多头占优"
            else:
                return "弱势上涨趋势，上涨动力不足，可能转为盘整"
        elif direction == TrendDirection.DOWN:
            if strength >= 70:
                return "强势下跌趋势，价格持续创出新低，空头力量强劲"
            elif strength >= 40:
                return "温和下跌趋势，价格稳步下跌，空头占优"
            else:
                return "弱势下跌趋势，下跌动力不足，可能转为盘整"
        elif direction == TrendDirection.CONSOLIDATION:
            return "盘整震荡，价格在中枢区间内波动，方向不明"
        else:
            return "趋势不明，等待方向确认"

    def _get_trend_range(self, direction: TrendDirection) -> tuple:
        """
        获取趋势范围

        Args:
            direction: 趋势方向

        Returns:
            (起始索引, 结束索引)
        """
        # 简化处理：返回最近60根K线的范围
        start_index = max(0, len(self.df) - 60)
        end_index = len(self.df) - 1
        return start_index, end_index

    def _get_trend_changes(self) -> List[TrendInfo]:
        """
        获取趋势变化历史

        Returns:
            趋势变化列表
        """
        # 简化处理：基于线段方向变化
        changes = []

        if not self.segment or len(self.segment) < 2:
            return changes

        # 识别线段方向变化点
        for i in range(1, len(self.segment)):
            prev_seg = self.segment[i - 1]
            curr_seg = self.segment[i]

            if hasattr(prev_seg, 'direction') and hasattr(curr_seg, 'direction'):
                if prev_seg.direction != curr_seg.direction:
                    # 检测到趋势变化
                    direction = TrendDirection.UP if curr_seg.direction == 'up' else TrendDirection.DOWN
                    start_index = curr_seg.start_index if hasattr(curr_seg, 'start_index') else 0
                    end_index = curr_seg.end_index if hasattr(curr_seg, 'end_index') else len(self.df) - 1

                    change = TrendInfo(
                        direction=direction,
                        strength=50.0,  # 默认强度
                        confidence="中",
                        description=f"趋势从{'上涨' if prev_seg.direction == 'up' else '下跌'}转为{'上涨' if curr_seg.direction == 'up' else '下跌'}",
                        start_price=self.df['close'].iloc[start_index],
                        end_price=self.df['close'].iloc[end_index],
                        start_index=start_index,
                        end_index=end_index,
                        duration=end_index - start_index,
                        zhongshu_level=1
                    )
                    changes.append(change)

        return changes

    def _calculate_trend_strength(self) -> float:
        """
        计算趋势强度

        Returns:
            趋势强度（0-100）
        """
        # 基于最近30根K线的波动率
        recent_prices = self.df['close'].tail(30)
        returns = recent_prices.pct_change().dropna()
        volatility = returns.std() * 100

        # 基于趋势一致性
        if self.segment and len(self.segment) >= 5:
            recent_segments = self.segment[-5:]
            consistent_count = sum(1 for seg in recent_segments if hasattr(seg, 'direction') and seg.direction == recent_segments[-1].direction)
            consistency = consistent_count / len(recent_segments)
        else:
            consistency = 0

        # 综合强度
        strength = min(100, (volatility * 5 + consistency * 50))

        return strength

    def _predict_next_direction(self, current_trend: TrendInfo) -> str:
        """
        预测下一阶段方向

        Args:
            current_trend: 当前趋势

        Returns:
            预期方向
        """
        if current_trend.direction == TrendDirection.UP:
            if current_trend.strength >= 70:
                return "继续向上"
            elif current_trend.strength >= 40:
                return "可能回调后继续向上"
            else:
                return "可能转为盘整或回调"
        elif current_trend.direction == TrendDirection.DOWN:
            if current_trend.strength >= 70:
                return "继续向下"
            elif current_trend.strength >= 40:
                return "可能反弹后继续向下"
            else:
                return "可能转为盘整或反弹"
        else:
            return "方向不明，等待突破"

    def _assess_risk_level(self, current_trend: TrendInfo, trend_strength: float) -> str:
        """
        评估风险水平

        Args:
            current_trend: 当前趋势
            trend_strength: 趋势强度

        Returns:
            风险水平（高、中、低）
        """
        if current_trend.direction == TrendDirection.CONSOLIDATION or current_trend.direction == TrendDirection.UNKNOWN:
            return "中"

        if trend_strength >= 70:
            return "高"  # 强势趋势，反转风险增加
        elif trend_strength >= 40:
            return "中"
        else:
            return "低"


def analyze_trend(df: pd.DataFrame, bi: List[Any], segment: List[Any], zhongshu: Any) -> Dict[str, Any]:
    """
    分析趋势（便捷函数）

    Args:
        df: K线数据
        bi: 笔列表
        segment: 线段列表
        zhongshu: 中枢对象

    Returns:
        趋势分析结果（字典格式）
    """
    analyzer = TrendAnalyzer(df, bi, segment, zhongshu)
    result = analyzer.analyze_trend()

    return {
        'direction': result.current_trend.direction.value,
        'strength': result.current_trend.strength,
        'confidence': result.current_trend.confidence,
        'description': result.current_trend.description,
        'start_price': result.current_trend.start_price,
        'end_price': result.current_trend.end_price,
        'start_index': result.current_trend.start_index,
        'end_index': result.current_trend.end_index,
        'duration': result.current_trend.duration,
        'zhongshu_level': result.current_trend.zhongshu_level,
        'support_level': result.current_trend.support_level,
        'resistance_level': result.current_trend.resistance_level,
        'trend_strength': result.trend_strength,
        'expected_direction': result.expected_direction,
        'risk_level': result.risk_level,
        'trend_changes_count': len(result.trend_changes)
    }
