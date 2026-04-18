"""
增强版决策制定智能体
集成缠论结构因子、动力学因子、情绪因子、背驰信号因子、风险评估因子
重新计算综合评分

决策因子权重：
- 缠论结构因子：30%
- 动力学因子：25%
- 情绪因子：20%
- 背驰信号因子：15%
- 风险评估因子：10%
"""

import pandas as pd
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class Action(Enum):
    """操作类型"""
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    WEAK_BUY = "弱买入"
    HOLD = "持有"
    WEAK_SELL = "弱卖出"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"


class RiskLevel(Enum):
    """风险等级"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    VERY_HIGH = "极高"


@dataclass
class DecisionFactors:
    """决策因子"""
    chanlun_factor: float  # 缠论结构因子（0-1）30%权重
    dynamics_factor: float  # 动力学因子（0-1）25%权重
    sentiment_factor: float  # 情绪因子（0-1）20%权重
    divergence_factor: float  # 背驰信号因子（0-1）15%权重
    risk_factor: float  # 风险评估因子（0-1）10%权重


@dataclass
class DecisionResult:
    """决策结果"""
    overall_score: float  # 综合评分 0-100
    action: Action  # 操作类型
    confidence: str  # 置信度
    risk_level: RiskLevel  # 风险等级
    stop_loss: float  # 止损价格
    take_profit: float  # 止盈价格
    position_size: str  # 建议仓位
    holding_period: str  # 建议持仓周期
    factors: DecisionFactors  # 各因子详情
    reasoning: str  # 决策逻辑
    recommendation: str  # 建议


class EnhancedDecisionMaker:
    """增强版决策制定器"""

    def __init__(self):
        """初始化决策制定器"""

    def make_decision(self,
                      chanlun_analysis: Dict[str, Any],
                      dynamics_analysis: Dict[str, Any],
                      sentiment_analysis: Dict[str, Any],
                      current_price: float) -> DecisionResult:
        """
        综合制定决策

        Args:
            chanlun_analysis: 缠论分析结果
            dynamics_analysis: 动力学分析结果
            sentiment_analysis: 市场情绪分析结果
            current_price: 当前价格

        Returns:
            决策结果
        """
        # 提取各因子
        factors = self._extract_factors(
            chanlun_analysis,
            dynamics_analysis,
            sentiment_analysis
        )

        # 计算综合评分
        overall_score = self._calculate_overall_score(factors)

        # 确定操作类型
        action = self._determine_action(overall_score)

        # 确定置信度
        confidence = self._determine_confidence(factors, overall_score)

        # 评估风险等级
        risk_level = self._assess_risk_level(factors, overall_score)

        # 计算止盈止损
        stop_loss, take_profit = self._calculate_tp_sl(
            current_price,
            overall_score,
            action
        )

        # 建议仓位
        position_size = self._recommend_position_size(
            overall_score,
            risk_level,
            action
        )

        # 建议持仓周期
        holding_period = self._recommend_holding_period(
            chanlun_analysis,
            overall_score
        )

        # 生成决策逻辑
        reasoning = self._generate_reasoning(
            factors,
            overall_score,
            action
        )

        # 生成建议
        recommendation = self._generate_recommendation(
            action,
            confidence,
            risk_level,
            position_size
        )

        return DecisionResult(
            overall_score=overall_score,
            action=action.value,
            confidence=confidence,
            risk_level=risk_level.value,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            holding_period=holding_period,
            factors=factors,
            reasoning=reasoning,
            recommendation=recommendation
        )

    def _extract_factors(self,
                         chanlun_analysis: Dict[str, Any],
                         dynamics_analysis: Dict[str, Any],
                         sentiment_analysis: Dict[str, Any]) -> DecisionFactors:
        """
        提取决策因子

        Args:
            chanlun_analysis: 缠论分析结果
            dynamics_analysis: 动力学分析结果
            sentiment_analysis: 市场情绪分析结果

        Returns:
            决策因子
        """
        # 缠论结构因子（30%）
        chanlun_factor = self._calculate_chanlun_factor(chanlun_analysis)

        # 动力学因子（25%）
        dynamics_factor = dynamics_analysis.get('dynamics_factor', 0.5)

        # 情绪因子（20%）
        sentiment_factor = sentiment_analysis.get('sentiment_factor', 0.5)

        # 背驰信号因子（15%）
        divergence_factor = self._calculate_divergence_factor(chanlun_analysis)

        # 风险评估因子（10%）
        risk_factor = self._calculate_risk_factor(chanlun_analysis)

        return DecisionFactors(
            chanlun_factor=chanlun_factor,
            dynamics_factor=dynamics_factor,
            sentiment_factor=sentiment_factor,
            divergence_factor=divergence_factor,
            risk_factor=risk_factor
        )

    def _calculate_chanlun_factor(self, chanlun_analysis: Dict[str, Any]) -> float:
        """
        计算缠论结构因子

        Args:
            chanlun_analysis: 缠论分析结果

        Returns:
            缠论结构因子（0-1）
        """
        # 基于级别递归验证的一致性
        overall_consistency = chanlun_analysis.get('level_recursion', {}).get('overall_consistency', 0)

        # 基于买卖点
        buy_points = chanlun_analysis.get('buy_sell_points', {}).get('total_buy_points', 0)
        sell_points = chanlun_analysis.get('buy_sell_points', {}).get('total_sell_points', 0)

        # 基于趋势
        trend = chanlun_analysis.get('trend', {}).get('direction', '未知')

        # 计算因子
        factor = overall_consistency / 100.0

        # 如果有买入点，加分
        if buy_points > sell_points:
            factor += 0.1
        elif sell_points > buy_points:
            factor -= 0.1

        # 如果趋势明确，加分
        if trend == '向上':
            factor += 0.1
        elif trend == '向下':
            factor -= 0.1

        return max(0, min(1, factor))

    def _calculate_divergence_factor(self, chanlun_analysis: Dict[str, Any]) -> float:
        """
        计算背驰信号因子

        Args:
            chanlun_analysis: 缠论分析结果

        Returns:
            背驰信号因子（0-1）
        """
        # 检查背驰
        has_divergence = False
        divergence_type = 'unknown'

        for level in ['5m', '30m', '4h', '1d']:
            if level in chanlun_analysis.get('level_analysis', {}):
                divergence = chanlun_analysis['level_analysis'][level].get('divergence', {})
                if divergence.get('has_divergence'):
                    has_divergence = True
                    divergence_type = divergence.get('divergence_type', 'unknown')
                    break

        # 如果有顶背驰，降低因子（做空信号）
        if divergence_type == '顶背驰':
            return 0.2
        # 如果有底背驰，提高因子（做多信号）
        elif divergence_type == '底背驰':
            return 0.8
        else:
            return 0.5

    def _calculate_risk_factor(self, chanlun_analysis: Dict[str, Any]) -> float:
        """
        计算风险评估因子

        Args:
            chanlun_analysis: 缠论分析结果

        Returns:
            风险评估因子（0-1，值越大风险越大）
        """
        risk_assessment = chanlun_analysis.get('level_recursion', {}).get('risk_assessment', '中')

        if risk_assessment == '高':
            return 0.8
        elif risk_assessment == '中':
            return 0.5
        elif risk_assessment == '低':
            return 0.2
        else:
            return 0.5

    def _calculate_overall_score(self, factors: DecisionFactors) -> float:
        """
        计算综合评分

        Args:
            factors: 决策因子

        Returns:
            综合评分（0-100）
        """
        # 加权计算
        # 缠论结构因子：30%
        # 动力学因子：25%
        # 情绪因子：20%
        # 背驰信号因子：15%
        # 风险评估因子：10%（风险越高，分数越低）

        score = (
            factors.chanlun_factor * 30 +
            factors.dynamics_factor * 25 +
            factors.sentiment_factor * 20 +
            factors.divergence_factor * 15 +
            (1 - factors.risk_factor) * 10
        )

        return score

    def _determine_action(self, score: float) -> Action:
        """
        确定操作类型

        Args:
            score: 综合评分

        Returns:
            操作类型
        """
        if score >= 80:
            return Action.STRONG_BUY
        elif score >= 65:
            return Action.BUY
        elif score >= 55:
            return Action.WEAK_BUY
        elif score >= 45:
            return Action.HOLD
        elif score >= 35:
            return Action.WEAK_SELL
        elif score >= 20:
            return Action.SELL
        else:
            return Action.STRONG_SELL

    def _determine_confidence(self, factors: DecisionFactors, score: float) -> str:
        """
        确定置信度

        Args:
            factors: 决策因子
            score: 综合评分

        Returns:
            置信度
        """
        # 基于因子一致性
        factor_values = [
            factors.chanlun_factor,
            factors.dynamics_factor,
            factors.sentiment_factor,
            factors.divergence_factor
        ]

        mean_factor = sum(factor_values) / len(factor_values)
        std_factor = (sum((x - mean_factor) ** 2 for x in factor_values) / len(factor_values)) ** 0.5

        if std_factor < 0.2:
            return "高"
        elif std_factor < 0.4:
            return "中"
        else:
            return "低"

    def _assess_risk_level(self, factors: DecisionFactors, score: float) -> RiskLevel:
        """
        评估风险等级

        Args:
            factors: 决策因子
            score: 综合评分

        Returns:
            风险等级
        """
        # 基于风险因子和分数极端性
        if factors.risk_factor >= 0.8:
            return RiskLevel.VERY_HIGH
        elif factors.risk_factor >= 0.6:
            return RiskLevel.HIGH
        elif score >= 80 or score <= 20:
            return RiskLevel.HIGH
        else:
            return RiskLevel.MEDIUM

    def _calculate_tp_sl(self,
                         current_price: float,
                         score: float,
                         action: Action) -> tuple:
        """
        计算止盈止损

        Args:
            current_price: 当前价格
            score: 综合评分
            action: 操作类型

        Returns:
            (止损价格, 止盈价格)
        """
        # 默认止盈止损比例
        if action in [Action.STRONG_BUY, Action.BUY]:
            # 做多
            sl_percent = 0.02  # 2%止损
            tp_percent = 0.05  # 5%止盈
            stop_loss = current_price * (1 - sl_percent)
            take_profit = current_price * (1 + tp_percent)
        elif action in [Action.STRONG_SELL, Action.SELL]:
            # 做空
            sl_percent = 0.02
            tp_percent = 0.05
            stop_loss = current_price * (1 + sl_percent)
            take_profit = current_price * (1 - tp_percent)
        else:
            # 观望
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.05

        # 根据评分调整
        score_factor = score / 100.0
        if score_factor > 0.7:
            # 高分，放宽止盈止损
            take_profit = current_price * (1 + tp_percent * 1.5) if action in [Action.STRONG_BUY, Action.BUY] else current_price * (1 - tp_percent * 1.5)
        elif score_factor < 0.3:
            # 低分，收紧止盈止损
            take_profit = current_price * (1 + tp_percent * 0.5) if action in [Action.STRONG_BUY, Action.BUY] else current_price * (1 - tp_percent * 0.5)

        return stop_loss, take_profit

    def _recommend_position_size(self,
                                  score: float,
                                  risk_level: RiskLevel,
                                  action: Action) -> str:
        """
        建议仓位

        Args:
            score: 综合评分
            risk_level: 风险等级
            action: 操作类型

        Returns:
            建议仓位
        """
        if risk_level == RiskLevel.VERY_HIGH:
            return "0% (观望)"
        elif risk_level == RiskLevel.HIGH:
            if action in [Action.STRONG_BUY, Action.STRONG_SELL]:
                return "10% (轻仓)"
            else:
                return "0% (观望)"
        else:
            if action in [Action.STRONG_BUY, Action.STRONG_SELL]:
                return "30% (中仓)"
            elif action in [Action.BUY, Action.SELL]:
                return "20% (轻中仓)"
            elif action in [Action.WEAK_BUY, Action.WEAK_SELL]:
                return "10% (轻仓)"
            else:
                return "0% (观望)"

    def _recommend_holding_period(self,
                                   chanlun_analysis: Dict[str, Any],
                                   score: float) -> str:
        """
        建议持仓周期

        Args:
            chanlun_analysis: 缠论分析结果
            score: 综合评分

        Returns:
            建议持仓周期
        """
        # 基于级别
        dominant_trend = chanlun_analysis.get('level_recursion', {}).get('dominant_trend', '未知')
        recommended_level = chanlun_analysis.get('level_recursion', {}).get('recommended_level', '30m')

        if recommended_level == '5m':
            return "1-3天"
        elif recommended_level == '30m':
            return "3-7天"
        elif recommended_level == '4h':
            return "1-4周"
        elif recommended_level == '1d':
            return "1-3个月"
        else:
            return "1-2周"

    def _generate_reasoning(self,
                             factors: DecisionFactors,
                             overall_score: float,
                             action: Action) -> str:
        """
        生成决策逻辑

        Args:
            factors: 决策因子
            overall_score: 综合评分
            action: 操作类型

        Returns:
            决策逻辑
        """
        reasoning = f"综合评分{overall_score:.1f}，操作类型：{action.value}。\n"
        reasoning += f"决策因子：缠论结构({factors.chanlun_factor:.2f}) + 动力学({factors.dynamics_factor:.2f}) + "
        reasoning += f"情绪({factors.sentiment_factor:.2f}) + 背驰({factors.divergence_factor:.2f}) + "
        reasoning += f"风险({factors.risk_factor:.2f})。\n"

        if factors.chanlun_factor > 0.7:
            reasoning += "缠论结构显示强烈信号。"
        elif factors.chanlun_factor < 0.3:
            reasoning += "缠论结构信号较弱。"
        else:
            reasoning += "缠论结构信号中性。"

        reasoning += " "

        if factors.dynamics_factor > 0.7:
            reasoning += "动力学指标显示强趋势。"
        elif factors.dynamics_factor < 0.3:
            reasoning += "动力学指标显示弱趋势。"
        else:
            reasoning += "动力学指标中性。"

        reasoning += " "

        if factors.sentiment_factor > 0.7:
            reasoning += "市场情绪偏向贪婪。"
        elif factors.sentiment_factor < 0.3:
            reasoning += "市场情绪偏向恐惧。"
        else:
            reasoning += "市场情绪中性。"

        return reasoning

    def _generate_recommendation(self,
                                  action: Action,
                                  confidence: str,
                                  risk_level: RiskLevel,
                                  position_size: str) -> str:
        """
        生成建议

        Args:
            action: 操作类型
            confidence: 置信度
            risk_level: 风险等级
            position_size: 建议仓位

        Returns:
            建议
        """
        recommendation = f"建议操作：{action.value}。\n"
        recommendation += f"置信度：{confidence}，风险等级：{risk_level.value}。\n"
        recommendation += f"建议仓位：{position_size}。\n"

        if risk_level == RiskLevel.VERY_HIGH:
            recommendation += "风险极高，建议谨慎操作或观望。"
        elif risk_level == RiskLevel.HIGH:
            recommendation += "风险较高，建议轻仓操作。"
        else:
            recommendation += "风险适中，按计划操作。"

        return recommendation


def make_enhanced_decision(chanlun_analysis: Dict[str, Any],
                            dynamics_analysis: Dict[str, Any],
                            sentiment_analysis: Dict[str, Any],
                            current_price: float) -> Dict[str, Any]:
    """
    制定增强版决策（便捷函数）

    Args:
        chanlun_analysis: 缠论分析结果
        dynamics_analysis: 动力学分析结果
        sentiment_analysis: 市场情绪分析结果
        current_price: 当前价格

    Returns:
        决策结果（字典格式）
    """
    maker = EnhancedDecisionMaker()
    result = maker.make_decision(chanlun_analysis, dynamics_analysis, sentiment_analysis, current_price)

    return {
        'overall_score': result.overall_score,
        'action': result.action,
        'confidence': result.confidence,
        'risk_level': result.risk_level,
        'stop_loss': result.stop_loss,
        'take_profit': result.take_profit,
        'position_size': result.position_size,
        'holding_period': result.holding_period,
        'factors': {
            'chanlun_factor': result.factors.chanlun_factor,
            'dynamics_factor': result.factors.dynamics_factor,
            'sentiment_factor': result.factors.sentiment_factor,
            'divergence_factor': result.factors.divergence_factor,
            'risk_factor': result.factors.risk_factor
        },
        'reasoning': result.reasoning,
        'recommendation': result.recommendation
    }
