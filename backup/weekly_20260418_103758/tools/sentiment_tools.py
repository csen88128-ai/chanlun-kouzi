"""
市场情绪相关工具
"""
import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


class MarketSentimentCollector:
    """市场情绪数据采集器"""

    def __init__(self):
        self.session = requests.Session()

    def get_fear_greed_index(self) -> Dict:
        """
        获取比特币恐惧与贪婪指数

        Returns:
            恐惧贪婪指数数据
        """
        try:
            # 使用 Alternative.me API
            url = "https://api.alternative.me/fng/"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get("data") and len(data["data"]) > 0:
                latest = data["data"][0]
                return {
                    "value": int(latest.get("value", 0)),
                    "classification": latest.get("value_classification", "Unknown"),
                    "timestamp": latest.get("timestamp", ""),
                    "time_until_update": data.get("time_until_update", "")
                }
            return {"error": "No data available"}
        except Exception as e:
            return {"error": str(e)}

    def interpret_fear_greed(self, value: int) -> Dict:
        """
        解释恐惧贪婪指数

        Args:
            value: 恐惧贪婪指数值（0-100）

        Returns:
            解释信息
        """
        if value >= 75:
            return {
                "sentiment": "extreme_greed",
                "description": "极度贪婪",
                "implication": "市场可能过热，建议谨慎，注意风险控制",
                "action": "考虑减仓或观望"
            }
        elif value >= 55:
            return {
                "sentiment": "greed",
                "description": "贪婪",
                "implication": "市场情绪乐观，但可能存在泡沫",
                "action": "保持谨慎，关注风险"
            }
        elif value >= 45:
            return {
                "sentiment": "neutral",
                "description": "中性",
                "implication": "市场情绪平稳",
                "action": "正常交易，关注技术面"
            }
        elif value >= 25:
            return {
                "sentiment": "fear",
                "description": "恐惧",
                "implication": "市场情绪悲观，可能存在机会",
                "action": "关注抄底机会，但需谨慎"
            }
        else:
            return {
                "sentiment": "extreme_fear",
                "description": "极度恐惧",
                "implication": "市场极度恐慌，可能接近底部",
                "action": "考虑逢低布局，但仍需控制风险"
            }

    def get_funding_rate(self, symbol: str = "BTCUSDT") -> Dict:
        """
        获取资金费率

        Args:
            symbol: 交易对

        Returns:
            资金费率数据
        """
        try:
            # 使用 Binance API
            url = f"https://fapi.binance.com/fapi/v1/premiumIndex?symbol={symbol}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            funding_rate = float(data.get("lastFundingRate", 0))
            mark_price = float(data.get("markPrice", 0))
            index_price = float(data.get("indexPrice", 0))

            # 资金费率解读
            funding_rate_percent = funding_rate * 100
            if funding_rate > 0.0001:
                interpretation = {
                    "sentiment": "bullish",
                    "description": "多头强",
                    "implication": "多头占优，费率为正，多头支付给空头"
                }
            elif funding_rate < -0.0001:
                interpretation = {
                    "sentiment": "bearish",
                    "description": "空头强",
                    "implication": "空头占优，费率为负，空头支付给多头"
                }
            else:
                interpretation = {
                    "sentiment": "balanced",
                    "description": "平衡",
                    "implication": "多空相对平衡"
                }

            return {
                "symbol": symbol,
                "funding_rate": funding_rate,
                "funding_rate_percent": round(funding_rate_percent, 4),
                "mark_price": mark_price,
                "index_price": index_price,
                "interpretation": interpretation,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}


# 全局实例
_sentiment_collector = MarketSentimentCollector()


@tool
def get_market_sentiment() -> str:
    """
    获取市场情绪数据

    Returns:
        市场情绪报告 JSON
    """
    ctx = request_context.get() or new_context(method="get_market_sentiment")

    try:
        # 获取恐惧贪婪指数
        fear_greed = _sentiment_collector.get_fear_greed_index()

        if "error" in fear_greed:
            return json.dumps({"error": fear_greed["error"]}, ensure_ascii=False, indent=2)

        # 解读恐惧贪婪指数
        interpretation = _sentiment_collector.interpret_fear_greed(fear_greed["value"])

        # 获取资金费率
        funding_rate = _sentiment_collector.get_funding_rate("BTCUSDT")

        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "fear_greed_index": {
                "value": fear_greed["value"],
                "classification": fear_greed["classification"],
                "sentiment": interpretation["sentiment"],
                "description": interpretation["description"],
                "implication": interpretation["implication"],
                "action": interpretation["action"],
                "time_until_update": fear_greed.get("time_until_update", "")
            },
            "funding_rate": funding_rate,
            "overall_sentiment": interpretation["sentiment"]
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def get_liquidation_data(symbol: str = "BTCUSDT", limit: int = 20) -> str:
    """
    获取爆仓数据

    Args:
        symbol: 交易对
        limit: 数量限制

    Returns:
        爆仓数据 JSON
    """
    ctx = request_context.get() or new_context(method="get_liquidation_data")

    try:
        # 使用 Binance API
        url = f"https://fapi.binance.com/fapi/v1/allForceOrders?symbol={symbol}&limit={limit}"
        response = _sentiment_collector.session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            return json.dumps({"error": "Invalid response format"}, ensure_ascii=False, indent=2)

        # 统计爆仓数据
        total_liquidations = len(data)
        long_liquidations = sum(1 for order in data if order.get("side") == "BUY")
        short_liquidations = sum(1 for order in data if order.get("side") == "SELL")

        total_value = sum(float(order.get("price", 0)) * float(order.get("executedQty", 0)) for order in data)

        # 解读
        if long_liquidations > short_liquidations * 1.5:
            market_implication = "多单爆仓较多，市场可能偏空"
        elif short_liquidations > long_liquidations * 1.5:
            market_implication = "空单爆仓较多，市场可能偏多"
        else:
            market_implication = "多空爆仓相对平衡"

        report = {
            "symbol": symbol,
            "total_liquidations": total_liquidations,
            "long_liquidations": long_liquidations,
            "short_liquidations": short_liquidations,
            "total_value": round(total_value, 2),
            "market_implication": market_implication,
            "recent_liquidations": data[:5],  # 只返回最近5条
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def get_open_interest(symbol: str = "BTCUSDT") -> str:
    """
    获取持仓量数据

    Args:
        symbol: 交易对

    Returns:
        持仓量数据 JSON
    """
    ctx = request_context.get() or new_context(method="get_open_interest")

    try:
        # 使用 Binance API
        url = f"https://fapi.binance.com/fapi/v1/openInterest?symbol={symbol}"
        response = _sentiment_collector.session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        open_interest = float(data.get("openInterest", 0))
        timestamp = data.get("time", 0)

        # 解读
        if open_interest > 0:
            implication = "持仓量增加，市场参与度提高"
        else:
            implication = "无持仓量数据"

        report = {
            "symbol": symbol,
            "open_interest": open_interest,
            "timestamp": timestamp,
            "implication": implication,
            "data_time": datetime.fromtimestamp(timestamp / 1000).isoformat() if timestamp > 0 else None
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)
