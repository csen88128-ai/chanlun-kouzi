"""
跨市场联动相关工具
"""
import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


class CrossMarketCollector:
    """跨市场数据采集器"""

    def __init__(self):
        self.session = requests.Session()

    def get_stock_index(self, symbol: str = "SPX") -> Dict:
        """
        获取股票指数数据

        Args:
            symbol: 指数代码（SPX, NDX, DJI）

        Returns:
            指数数据
        """
        try:
            # 使用 Yahoo Finance API (简化版)
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            result = data.get("chart", {}).get("result", [])
            if not result:
                return {"error": "No data available"}

            meta = result[0].get("meta", {})
            regular_price = meta.get("regularMarketPrice", 0)
            previous_close = meta.get("previousClose", 0)

            change = regular_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close > 0 else 0

            return {
                "symbol": symbol,
                "price": regular_price,
                "previous_close": previous_close,
                "change": round(change, 2),
                "change_percent": round(change_percent, 2),
                "currency": meta.get("currency", "USD"),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    def get_gold_price(self) -> Dict:
        """
        获取黄金价格

        Returns:
            黄金价格数据
        """
        try:
            # 使用简化方式获取黄金价格
            url = "https://api.metals.live/v1/spot/gold"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            price = float(data.get("price", 0))
            currency = data.get("currency", "USD")

            return {
                "commodity": "Gold",
                "price": price,
                "currency": currency,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # 备用方案：使用固定值（模拟数据）
            return {
                "commodity": "Gold",
                "price": 2345.67,  # 模拟价格
                "currency": "USD",
                "note": "Using simulated data due to API limitation",
                "timestamp": datetime.now().isoformat()
            }

    def get_dollar_index(self) -> Dict:
        """
        获取美元指数（DXY）

        Returns:
            美元指数数据
        """
        try:
            # 使用Yahoo Finance获取美元指数
            url = "https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?interval=1d&range=5d"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            result = data.get("chart", {}).get("result", [])
            if not result:
                return {"error": "No data available"}

            meta = result[0].get("meta", {})
            price = meta.get("regularMarketPrice", 0)
            previous_close = meta.get("previousClose", 0)

            change = price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close > 0 else 0

            return {
                "index": "DXY",
                "price": price,
                "previous_close": previous_close,
                "change": round(change, 3),
                "change_percent": round(change_percent, 2),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            # 备用方案：使用固定值
            return {
                "index": "DXY",
                "price": 104.5,  # 模拟价格
                "change": 0.3,
                "change_percent": 0.29,
                "note": "Using simulated data due to API limitation",
                "timestamp": datetime.now().isoformat()
            }

    def analyze_correlation(self, btc_change: float, spx_change: float, gold_change: float, dxy_change: float) -> Dict:
        """
        分析比特币与各市场的相关性

        Args:
            btc_change: BTC涨跌幅
            spx_change: 标普500涨跌幅
            gold_change: 黄金涨跌幅
            dxy_change: 美元指数涨跌幅

        Returns:
            相关性分析结果
        """
        correlations = {}

        # BTC vs S&P 500
        if spx_change != 0:
            btc_spx_corr = "positive" if btc_change * spx_change > 0 else "negative"
            correlations["btc_spx"] = {
                "correlation": btc_spx_corr,
                "description": f"BTC与美股{'同向' if btc_spx_corr == 'positive' else '反向'}波动",
                "btc_change": round(btc_change, 2),
                "spx_change": round(spx_change, 2)
            }

        # BTC vs Gold
        if gold_change != 0:
            btc_gold_corr = "positive" if btc_change * gold_change > 0 else "negative"
            correlations["btc_gold"] = {
                "correlation": btc_gold_corr,
                "description": f"BTC与黄金{'同向' if btc_gold_corr == 'positive' else '反向'}波动",
                "btc_change": round(btc_change, 2),
                "gold_change": round(gold_change, 2)
            }

        # BTC vs DXY
        if dxy_change != 0:
            btc_dxy_corr = "positive" if btc_change * dxy_change > 0 else "negative"
            correlations["btc_dxy"] = {
                "correlation": btc_dxy_corr,
                "description": f"BTC与美元指数{'同向' if btc_dxy_corr == 'positive' else '反向'}波动",
                "note": "通常BTC与DXY呈负相关",
                "btc_change": round(btc_change, 2),
                "dxy_change": round(dxy_change, 2)
            }

        return correlations


# 全局实例
_cross_market_collector = CrossMarketCollector()


@tool
def get_cross_market_data(btc_change: float = 0.0) -> str:
    """
    获取跨市场数据

    Args:
        btc_change: BTC涨跌幅（百分比）

    Returns:
        跨市场数据报告 JSON
    """
    ctx = request_context.get() or new_context(method="get_cross_market_data")

    try:
        # 获取标普500
        spx_data = _cross_market_collector.get_stock_index("SPX")
        spx_change = spx_data.get("change_percent", 0) if "error" not in spx_data else 0

        # 获取黄金价格
        gold_data = _cross_market_collector.get_gold_price()
        gold_change = 0  # 黄金通常提供价格，需要历史数据计算涨跌幅

        # 获取美元指数
        dxy_data = _cross_market_collector.get_dollar_index()
        dxy_change = dxy_data.get("change_percent", 0) if "error" not in dxy_data else 0

        # 分析相关性
        correlations = _cross_market_collector.analyze_correlation(
            btc_change, spx_change, gold_change, dxy_change
        )

        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "us_stocks": {
                "spx": spx_data,
                "implication": "美股上涨通常提振风险偏好，利好BTC" if spx_change > 0 else "美股下跌通常抑制风险偏好，利空BTC"
            },
            "commodities": {
                "gold": gold_data,
                "implication": "黄金上涨通常表明避险需求，对BTC影响中性"
            },
            "currencies": {
                "dxy": dxy_data,
                "implication": "美元走强通常利空BTC" if dxy_change > 0 else "美元走弱通常利好BTC"
            },
            "correlations": correlations,
            "overall_sentiment": "neutral"
        }

        # 综合判断
        positive_signals = 0
        negative_signals = 0

        if spx_change > 0:
            positive_signals += 1
        else:
            negative_signals += 1

        if dxy_change < 0:
            positive_signals += 1
        else:
            negative_signals += 1

        if positive_signals > negative_signals:
            report["overall_sentiment"] = "bullish"
            report["overall_implication"] = "跨市场数据整体利好BTC"
        elif negative_signals > positive_signals:
            report["overall_sentiment"] = "bearish"
            report["overall_implication"] = "跨市场数据整体利空BTC"
        else:
            report["overall_sentiment"] = "neutral"
            report["overall_implication"] = "跨市场数据中性，影响有限"

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def get_crypto_market_dominance() -> str:
    """
    获取加密货币市场市值分布

    Returns:
        市值分布数据 JSON
    """
    ctx = request_context.get() or new_context(method="get_crypto_market_dominance")

    try:
        # 使用 CoinGecko API
        url = "https://api.coingecko.com/api/v3/global"
        response = _cross_market_collector.session.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        market_data = data.get("data", {})
        total_market_cap = market_data.get("total_market_cap", {}).get("usd", 0)
        btc_dominance = market_data.get("market_cap_percentage", {}).get("btc", 0)
        eth_dominance = market_data.get("market_cap_percentage", {}).get("eth", 0)

        # 解读
        if btc_dominance > 50:
            btc_status = "BTC主导地位稳固"
        elif btc_dominance > 40:
            btc_status = "BTC主导地位较强"
        else:
            btc_status = "BTC主导地位减弱，山寨币活跃"

        report = {
            "total_market_cap_usd": round(total_market_cap, 2),
            "btc_dominance": round(btc_dominance, 2),
            "eth_dominance": round(eth_dominance, 2),
            "btc_status": btc_status,
            "timestamp": datetime.now().isoformat()
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)
