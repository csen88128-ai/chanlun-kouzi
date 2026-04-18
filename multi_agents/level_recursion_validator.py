"""
缠论级别递归验证模块
深度验证不同级别之间的递归关系

缠论级别递归理论：
1. 级别递归：小级别的结构嵌套在大级别中
2. 区间套：不同级别同时出现背驰，形成共振
3. 级别配合：小级别信号需要大级别确认
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum


class RecursionValidationResult(Enum):
    """递归验证结果"""
    VALID = "通过"  # 通过
    INVALID = "不通过"  # 不通过
    PARTIAL = "部分通过"  # 部分通过
    UNKNOWN = "未知"  # 未知


class LevelRelationship(Enum):
    """级别关系"""
    PARENT_CHILD = "父子关系"  # 父子关系（大级别包含小级别）
    CONSISTENT = "一致"  # 趋势一致
    CONFLICT = "冲突"  # 趋势冲突
    REINFORCE = "强化"  # 强化信号
    CANCEL = "抵消"  # 抵消信号


@dataclass
class LevelPairAnalysis:
    """级别对分析"""
    level1: str  # 级别1
    level2: str  # 级别2
    relationship: LevelRelationship  # 级别关系
    trend_consistency: bool  # 趋势是否一致
    signal_strength: float  # 信号强度（0-100）
    divergence_count: int  # 背驰数量
    buy_sell_match: bool  # 买卖点是否匹配
    description: str  # 描述


@dataclass
class RecursionAnalysisResult:
    """递归分析结果"""
    is_valid: bool  # 是否有效
    validation_result: RecursionValidationResult  # 验证结果
    level_pairs: List[LevelPairAnalysis]  # 级别对分析
    overall_consistency: float  # 整体一致性（0-100）
    dominant_trend: str  # 主导趋势
    recommended_level: str  # 推荐操作级别
    risk_assessment: str  # 风险评估
    confidence: str  # 置信度
    description: str  # 描述


class LevelRecursionValidator:
    """级别递归验证器"""

    def __init__(self, level_results: Dict[str, Any]):
        """
        初始化级别递归验证器

        Args:
            level_results: 各级别分析结果字典
        """
        self.level_results = level_results

    def validate_recursion(self) -> RecursionAnalysisResult:
        """
        验证级别递归关系

        Returns:
            递归分析结果
        """
        # 分析所有级别对
        level_pairs = self._analyze_level_pairs()

        # 计算整体一致性
        overall_consistency = self._calculate_overall_consistency(level_pairs)

        # 确定主导趋势
        dominant_trend = self._determine_dominant_trend()

        # 推荐操作级别
        recommended_level = self._recommend_level(level_pairs)

        # 风险评估
        risk_assessment = self._assess_risk(level_pairs, overall_consistency)

        # 确定置信度
        confidence = self._determine_confidence(overall_consistency)

        # 确定验证结果
        if overall_consistency >= 80:
            validation_result = RecursionValidationResult.VALID
            is_valid = True
        elif overall_consistency >= 50:
            validation_result = RecursionValidationResult.PARTIAL
            is_valid = True
        else:
            validation_result = RecursionValidationResult.INVALID
            is_valid = False

        # 生成描述
        description = self._generate_description(validation_result, overall_consistency, dominant_trend)

        return RecursionAnalysisResult(
            is_valid=is_valid,
            validation_result=validation_result,
            level_pairs=level_pairs,
            overall_consistency=overall_consistency,
            dominant_trend=dominant_trend,
            recommended_level=recommended_level,
            risk_assessment=risk_assessment,
            confidence=confidence,
            description=description
        )

    def _analyze_level_pairs(self) -> List[LevelPairAnalysis]:
        """
        分析所有级别对

        Returns:
            级别对分析列表
        """
        level_pairs = []
        levels = list(self.level_results.keys())

        # 分析相邻级别对
        for i in range(len(levels) - 1):
            level1 = levels[i]
            level2 = levels[i + 1]
            pair_analysis = self._analyze_single_pair(level1, level2)
            level_pairs.append(pair_analysis)

        # 分析跨级别对（可选）
        if len(levels) >= 3:
            level1 = levels[0]
            level3 = levels[2]
            pair_analysis = self._analyze_single_pair(level1, level3)
            level_pairs.append(pair_analysis)

        return level_pairs

    def _analyze_single_pair(self, level1: str, level2: str) -> LevelPairAnalysis:
        """
        分析单个级别对

        Args:
            level1: 级别1
            level2: 级别2

        Returns:
            级别对分析
        """
        result1 = self.level_results.get(level1, {})
        result2 = self.level_results.get(level2, {})

        # 确定级别关系
        relationship = self._determine_level_relationship(level1, level2)

        # 检查趋势一致性
        trend1 = result1.get('trend', {}).get('direction', '未知')
        trend2 = result2.get('trend', {}).get('direction', '未知')
        trend_consistency = self._check_trend_consistency(trend1, trend2)

        # 计算信号强度
        signal_strength = self._calculate_signal_strength(result1, result2)

        # 统计背驰数量
        divergence_count = self._count_divergences(result1, result2)

        # 检查买卖点匹配
        buy_sell_match = self._check_buy_sell_match(result1, result2)

        # 生成描述
        description = self._generate_pair_description(level1, level2, relationship, trend_consistency)

        return LevelPairAnalysis(
            level1=level1,
            level2=level2,
            relationship=relationship,
            trend_consistency=trend_consistency,
            signal_strength=signal_strength,
            divergence_count=divergence_count,
            buy_sell_match=buy_sell_match,
            description=description
        )

    def _determine_level_relationship(self, level1: str, level2: str) -> LevelRelationship:
        """
        确定级别关系

        Args:
            level1: 级别1
            level2: 级别2

        Returns:
            级别关系
        """
        result1 = self.level_results.get(level1, {})
        result2 = self.level_results.get(level2, {})

        trend1 = result1.get('trend', {}).get('direction', '未知')
        trend2 = result2.get('trend', {}).get('direction', '未知')

        # 两个级别都是上涨
        if trend1 == '向上' and trend2 == '向上':
            return LevelRelationship.REINFORCE
        # 两个级别都是下跌
        elif trend1 == '向下' and trend2 == '向下':
            return LevelRelationship.REINFORCE
        # 两个级别趋势一致但不是同向
        elif trend1 == trend2:
            return LevelRelationship.CONSISTENT
        # 趋势冲突
        else:
            return LevelRelationship.CONFLICT

    def _check_trend_consistency(self, trend1: str, trend2: str) -> bool:
        """
        检查趋势一致性

        Args:
            trend1: 趋势1
            trend2: 趋势2

        Returns:
            是否一致
        """
        # 如果趋势相同，认为一致
        if trend1 == trend2 and trend1 in ['向上', '向下']:
            return True
        # 如果都是盘整，也认为一致
        if trend1 == '盘整' and trend2 == '盘整':
            return True
        # 否则认为不一致
        return False

    def _calculate_signal_strength(self, result1: Dict, result2: Dict) -> float:
        """
        计算信号强度

        Args:
            result1: 结果1
            result2: 结果2

        Returns:
            信号强度（0-100）
        """
        strength = 0.0

        # 基于趋势强度
        trend_strength1 = result1.get('trend', {}).get('strength', 0)
        trend_strength2 = result2.get('trend', {}).get('strength', 0)
        strength += (trend_strength1 + trend_strength2) / 2 * 0.4

        # 基于买卖点数量
        buy_points1 = result1.get('buy_sell_points', {}).get('total_buy_points', 0)
        sell_points1 = result1.get('buy_sell_points', {}).get('total_sell_points', 0)
        buy_points2 = result2.get('buy_sell_points', {}).get('total_buy_points', 0)
        sell_points2 = result2.get('buy_sell_points', {}).get('total_sell_points', 0)
        total_points = buy_points1 + sell_points1 + buy_points2 + sell_points2
        strength += min(40, total_points * 5)

        # 基于背驰强度
        divergence_strength1 = result1.get('divergence', {}).get('divergence_strength', 0)
        divergence_strength2 = result2.get('divergence', {}).get('divergence_strength', 0)
        strength += (divergence_strength1 + divergence_strength2) / 2 * 0.2

        return min(100, strength)

    def _count_divergences(self, result1: Dict, result2: Dict) -> int:
        """
        统计背驰数量

        Args:
            result1: 结果1
            result2: 结果2

        Returns:
            背驰数量
        """
        count = 0

        if result1.get('divergence', {}).get('has_divergence'):
            count += 1

        if result2.get('divergence', {}).get('has_divergence'):
            count += 1

        return count

    def _check_buy_sell_match(self, result1: Dict, result2: Dict) -> bool:
        """
        检查买卖点是否匹配

        Args:
            result1: 结果1
            result2: 结果2

        Returns:
            是否匹配
        """
        latest_buy1 = result1.get('buy_sell_points', {}).get('latest_buy_point')
        latest_sell1 = result1.get('buy_sell_points', {}).get('latest_sell_point')
        latest_buy2 = result2.get('buy_sell_points', {}).get('latest_buy_point')
        latest_sell2 = result2.get('buy_sell_points', {}).get('latest_sell_point')

        # 如果两个级别都有买入点，认为匹配
        if latest_buy1 and latest_buy2:
            return True

        # 如果两个级别都有卖出点，认为匹配
        if latest_sell1 and latest_sell2:
            return True

        return False

    def _generate_pair_description(self, level1: str, level2: str,
                                    relationship: LevelRelationship, trend_consistency: bool) -> str:
        """
        生成级别对描述

        Args:
            level1: 级别1
            level2: 级别2
            relationship: 级别关系
            trend_consistency: 趋势一致性

        Returns:
            描述
        """
        relationship_str = relationship.value
        consistency_str = "一致" if trend_consistency else "不一致"

        return f"{level1}与{level2}：级别关系为{relationship_str}，趋势{consistency_str}"

    def _calculate_overall_consistency(self, level_pairs: List[LevelPairAnalysis]) -> float:
        """
        计算整体一致性

        Args:
            level_pairs: 级别对分析列表

        Returns:
            整体一致性（0-100）
        """
        if not level_pairs:
            return 0.0

        # 基于趋势一致性
        trend_consistency_count = sum(1 for pair in level_pairs if pair.trend_consistency)
        trend_consistency_score = trend_consistency_count / len(level_pairs) * 50

        # 基于信号强度
        avg_signal_strength = sum(pair.signal_strength for pair in level_pairs) / len(level_pairs)
        signal_score = avg_signal_strength * 0.5

        return min(100, trend_consistency_score + signal_score)

    def _determine_dominant_trend(self) -> str:
        """
        确定主导趋势

        Returns:
            主导趋势
        """
        trends = []
        for level_name, result in self.level_results.items():
            trend = result.get('trend', {}).get('direction', '未知')
            trends.append(trend)

        # 统计趋势
        trend_counts = {}
        for trend in trends:
            trend_counts[trend] = trend_counts.get(trend, 0) + 1

        # 找出最多的趋势
        dominant_trend = max(trend_counts.items(), key=lambda x: x[1])[0]

        return dominant_trend

    def _recommend_level(self, level_pairs: List[LevelPairAnalysis]) -> str:
        """
        推荐操作级别

        Args:
            level_pairs: 级别对分析列表

        Returns:
            推荐级别
        """
        # 简化策略：推荐信号强度最高的级别
        best_pair = max(level_pairs, key=lambda x: x.signal_strength)
        return best_pair.level2

    def _assess_risk(self, level_pairs: List[LevelPairAnalysis], overall_consistency: float) -> str:
        """
        评估风险

        Args:
            level_pairs: 级别对分析列表
            overall_consistency: 整体一致性

        Returns:
            风险评估
        """
        # 检查是否有冲突
        has_conflict = any(pair.relationship == LevelRelationship.CONFLICT for pair in level_pairs)

        if has_conflict:
            return "高"
        elif overall_consistency >= 80:
            return "低"
        elif overall_consistency >= 50:
            return "中"
        else:
            return "高"

    def _determine_confidence(self, overall_consistency: float) -> str:
        """
        确定置信度

        Args:
            overall_consistency: 整体一致性

        Returns:
            置信度
        """
        if overall_consistency >= 80:
            return "高"
        elif overall_consistency >= 50:
            return "中"
        else:
            return "低"

    def _generate_description(self, validation_result: RecursionValidationResult,
                              overall_consistency: float, dominant_trend: str) -> str:
        """
        生成描述

        Args:
            validation_result: 验证结果
            overall_consistency: 整体一致性
            dominant_trend: 主导趋势

        Returns:
            描述
        """
        result_str = validation_result.value

        description = f"级别递归验证{result_str}"

        if validation_result == RecursionValidationResult.VALID:
            description += f"，整体一致性{overall_consistency:.1f}%，主导趋势为{dominant_trend}"
        elif validation_result == RecursionValidationResult.PARTIAL:
            description += f"，整体一致性{overall_consistency:.1f}%，部分级别信号冲突，建议谨慎操作"
        else:
            description += f"，整体一致性{overall_consistency:.1f}%，级别信号严重冲突，建议观望"

        return description


def validate_level_recursion(level_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证级别递归（便捷函数）

    Args:
        level_results: 各级别分析结果字典

    Returns:
        递归分析结果（字典格式）
    """
    validator = LevelRecursionValidator(level_results)
    result = validator.validate_recursion()

    return {
        'is_valid': result.is_valid,
        'validation_result': result.validation_result.value,
        'level_pairs': [
            {
                'level1': pair.level1,
                'level2': pair.level2,
                'relationship': pair.relationship.value,
                'trend_consistency': pair.trend_consistency,
                'signal_strength': pair.signal_strength,
                'divergence_count': pair.divergence_count,
                'buy_sell_match': pair.buy_sell_match,
                'description': pair.description
            }
            for pair in result.level_pairs
        ],
        'overall_consistency': result.overall_consistency,
        'dominant_trend': result.dominant_trend,
        'recommended_level': result.recommended_level,
        'risk_assessment': result.risk_assessment,
        'confidence': result.confidence,
        'description': result.description
    }
