"""
市场情绪分析智能体
分析恐惧贪婪指数、资金流向等市场情绪指标
计算情绪评分因子（20%权重）
"""

import requests
import pandas as pd
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class SentimentLevel(Enum):
    """情绪级别"""
    EXTREME_FEAR = "极度恐惧"
    FEAR = "恐惧"
    NEUTRAL = "中性"
    GREED = "贪婪"
    EXTREME_GREED = "极度贪婪"


class FlowDirection(Enum):
    """流向方向"""
    INFLOW = "流入"
    OUTFLOW = "流出"
    NEUTRAL = "中性"


@dataclass
class FearGreedIndex:
    """恐惧贪婪指数"""
    value: int  # 0-100
    classification: str  # 分类
    timestamp: str
    trend: str  # 上升、下降、稳定
    sentiment_score: float  # 情绪评分 0-100


@dataclass
class MoneyFlowAnalysis:
    """资金流向分析"""
    net_flow: float  # 净流入
    flow_direction: FlowDirection
    flow_trend: str  # 上升、下降、稳定
    flow_strength: str  # 强、中、弱
    sentiment_score: float  # 情绪评分 0-100


@dataclass
class SentimentAnalysisResult:
    """市场情绪分析综合结果"""
    fear_greed: FearGreedIndex
    money_flow: MoneyFlowAnalysis
    overall_score: float  # 综合评分 0-100
    overall_sentiment: str  # 综合情绪
    sentiment_factor: float  # 情绪因子（0-1），用于决策制定（20%权重）
    description: str  # 综合描述


class SentimentAnalyzer:
    """市场情绪分析器"""

    def __init__(self):
        """初始化市场情绪分析器"""
        self.fg_api_url = "https://api.alternative.me/fng/"
        self.btc_api_url = "https://api.alternative.me/fng/?limit=30&coin=bitcoin"

    def get_fear_greed_index(self) -> Optional[FearGreedIndex]:
        """
        获取恐惧贪婪指数

        Returns:
            恐惧贪婪指数
        """
        try:
            response = requests.get(self.fg_api_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and len(data['data']) > 0:
                fg_data = data['data'][0]
                value = int(fg_data['value'])
                classification = fg_data['value_classification']
                timestamp = fg_data['timestamp']

                # 确定趋势（需要历史数据）
                trend = self._determine_fg_trend(value)

                # 计算情绪评分
                sentiment_score = value  # 0-100，越高越贪婪

                return FearGreedIndex(
                    value=value,
                    classification=classification,
                    timestamp=timestamp,
                    trend=trend,
                    sentiment_score=sentiment_score
                )

        except Exception as e:
            print(f"获取恐惧贪婪指数失败: {e}")

        # 如果API调用失败，返回中性值
        return FearGreedIndex(
            value=50,
            classification="中性",
            timestamp="",
            trend="稳定",
            sentiment_score=50.0
        )

    def _determine_fg_trend(self, current_value: int) -> str:
        """
        确定恐惧贪婪指数趋势

        Args:
            current_value: 当前值

        Returns:
            趋势（上升、下降、稳定）
        """
        try:
            # 获取历史数据判断趋势
            response = requests.get(f"{self.fg_api_url}?limit=7", timeout=10)
            response.raise_for_status()
            data = response.json()

            if 'data' in data and len(data['data']) >= 7:
                values = [int(item['value']) for item in data['data']]
                avg = sum(values) / len(values)

                if current_value > avg + 5:
                    return "上升"
                elif current_value < avg - 5:
                    return "下降"
                else:
                    return "稳定"

        except Exception as e:
            pass

        return "稳定"

    def analyze_money_flow(self, df: pd.DataFrame) -> MoneyFlowAnalysis:
        """
        分析资金流向

        Args:
            df: K线数据

        Returns:
            资金流向分析结果
        """
        if len(df) < 20:
            return MoneyFlowAnalysis(
                net_flow=0.0,
                flow_direction=FlowDirection.NEUTRAL,
                flow_trend="稳定",
                flow_strength="弱",
                sentiment_score=50.0
            )

        # 计算净流入（基于价格变化和成交量）
        if 'volume' in df.columns:
            # 使用最近20根K线
            recent_df = df.tail(20)

            # 计算价格变化
            price_change = recent_df['close'].iloc[-1] - recent_df['close'].iloc[0]
            volume_change = recent_df['volume'].iloc[-1] - recent_df['volume'].iloc[0]

            # 简化的资金流向计算
            net_flow = (price_change * volume_change) / 1e8  # 归一化

            # 判断流向
            if net_flow > 100:
                flow_direction = FlowDirection.INFLOW
                sentiment_score = min(100, 50 + net_flow / 10)
            elif net_flow < -100:
                flow_direction = FlowDirection.OUTFLOW
                sentiment_score = max(0, 50 + net_flow / 10)
            else:
                flow_direction = FlowDirection.NEUTRAL
                sentiment_score = 50.0

            # 判断趋势
            if abs(net_flow) > 500:
                flow_strength = "强"
            elif abs(net_flow) > 200:
                flow_strength = "中"
            else:
                flow_strength = "弱"

            flow_trend = "上升" if net_flow > 0 else "下降" if net_flow < 0 else "稳定"

        else:
            net_flow = 0.0
            flow_direction = FlowDirection.NEUTRAL
            flow_trend = "稳定"
            flow_strength = "弱"
            sentiment_score = 50.0

        return MoneyFlowAnalysis(
            net_flow=net_flow,
            flow_direction=flow_direction.value,
            flow_trend=flow_trend,
            flow_strength=flow_strength,
            sentiment_score=sentiment_score
        )

    def analyze_sentiment(self, df: pd.DataFrame) -> SentimentAnalysisResult:
        """
        综合分析市场情绪

        Args:
            df: K线数据

        Returns:
            市场情绪分析综合结果
        """
        # 获取恐惧贪婪指数
        fear_greed = self.get_fear_greed_index()

        # 分析资金流向
        money_flow = self.analyze_money_flow(df)

        # 计算综合评分（加权平均）
        # 恐惧贪婪指数: 60%, 资金流向: 40%
        overall_score = (
            fear_greed.sentiment_score * 0.60 +
            money_flow.sentiment_score * 0.40
        )

        # 判断综合情绪
        if overall_score >= 80:
            overall_sentiment = "极度贪婪"
        elif overall_score >= 60:
            overall_sentiment = "贪婪"
        elif overall_score >= 40:
            overall_sentiment = "中性"
        elif overall_score >= 20:
            overall_sentiment = "恐惧"
        else:
            overall_sentiment = "极度恐惧"

        # 计算情绪因子（0-1），用于决策制定（20%权重）
        sentiment_factor = overall_score / 100.0

        # 生成综合描述
        description = f"市场情绪：恐惧贪婪指数={fear_greed.value}（{fear_greed.classification}，{fear_greed.trend}），"
        description += f"资金流向={money_flow.flow_direction}（{money_flow.flow_strength}，{money_flow.flow_trend}），"
        description += f"综合情绪={overall_sentiment}（{overall_score:.1f}）"

        return SentimentAnalysisResult(
            fear_greed=fear_greed,
            money_flow=money_flow,
            overall_score=overall_score,
            overall_sentiment=overall_sentiment,
            sentiment_factor=sentiment_factor,
            description=description
        )


def analyze_sentiment(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析市场情绪（便捷函数）

    Args:
        df: K线数据

    Returns:
        市场情绪分析结果（字典格式）
    """
    analyzer = SentimentAnalyzer()
    result = analyzer.analyze_sentiment(df)

    return {
        'fear_greed': {
            'value': result.fear_greed.value,
            'classification': result.fear_greed.classification,
            'timestamp': result.fear_greed.timestamp,
            'trend': result.fear_greed.trend,
            'sentiment_score': result.fear_greed.sentiment_score
        },
        'money_flow': {
            'net_flow': result.money_flow.net_flow,
            'flow_direction': result.money_flow.flow_direction,
            'flow_trend': result.money_flow.flow_trend,
            'flow_strength': result.money_flow.flow_strength,
            'sentiment_score': result.money_flow.sentiment_score
        },
        'overall_score': result.overall_score,
        'overall_sentiment': result.overall_sentiment,
        'sentiment_factor': result.sentiment_factor,
        'description': result.description
    }
