"""
链上数据相关工具
"""
import os
import json
import requests
from datetime import datetime
from typing import Dict, Optional
from langchain.tools import tool
from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context


class OnChainCollector:
    """链上数据采集器"""

    def __init__(self):
        self.session = requests.Session()
        # 使用 Blockchain.com 或其他公开API

    def get_exchange_inflow(self, symbol: str = "BTC") -> Dict:
        """
        获取交易所流入数据

        Args:
            symbol: 代币符号

        Returns:
            流入数据
        """
        try:
            # 使用公开API（简化版）
            # 实际项目中应该使用专业数据源如 Glassnode, CryptoQuant
            url = "https://api.blockchain.info/q/balance"

            # 模拟数据（实际应该使用专业API）
            simulated_data = {
                "inflow_24h": 1250.5,  # BTC
                "outflow_24h": 980.3,  # BTC
                "net_flow": -270.2,  # 净流出
                "net_flow_percent": -0.02,  # 占总持仓的百分比
                "timestamp": datetime.now().isoformat()
            }

            # 解读
            net_flow = simulated_data["net_flow"]
            if net_flow < -100:
                interpretation = {
                    "sentiment": "bullish",
                    "description": "净流出",
                    "implication": "大量BTC从交易所流出，可能被转移到冷钱包持有，表明长期持有意愿增强"
                }
            elif net_flow > 100:
                interpretation = {
                    "sentiment": "bearish",
                    "description": "净流入",
                    "implication": "大量BTC流入交易所，可能准备抛售，表明短期抛压增加"
                }
            else:
                interpretation = {
                    "sentiment": "neutral",
                    "description": "平衡",
                    "implication": "交易所流入流出相对平衡"
                }

            simulated_data["interpretation"] = interpretation

            return simulated_data

        except Exception as e:
            return {"error": str(e)}

    def get_whale_activity(self) -> Dict:
        """
        获取巨鲸活动数据

        Returns:
            巨鲸活动数据
        """
        try:
            # 模拟数据（实际应该使用专业API）
            simulated_data = {
                "large_transactions_24h": 45,
                "whale_buy_signals": 12,
                "whale_sell_signals": 18,
                "net_whale_sentiment": "bearish",
                "average_transaction_size_btc": 150.5,
                "timestamp": datetime.now().isoformat()
            }

            # 解读
            if simulated_data["whale_buy_signals"] > simulated_data["whale_sell_signals"]:
                simulated_data["implication"] = "巨鲸净买入，可能预示上涨"
                simulated_data["sentiment"] = "bullish"
            elif simulated_data["whale_sell_signals"] > simulated_data["whale_buy_signals"]:
                simulated_data["implication"] = "巨鲸净卖出，可能预示下跌"
                simulated_data["sentiment"] = "bearish"
            else:
                simulated_data["implication"] = "巨鲸买卖相对平衡"
                simulated_data["sentiment"] = "neutral"

            return simulated_data

        except Exception as e:
            return {"error": str(e)}

    def get_active_addresses(self, symbol: str = "BTC") -> Dict:
        """
        获取活跃地址数量

        Args:
            symbol: 代币符号

        Returns:
            活跃地址数据
        """
        try:
            # 模拟数据
            simulated_data = {
                "active_addresses_24h": 850000,
                "active_addresses_7d": 5600000,
                "growth_24h": 3.5,  # 24小时增长率
                "growth_7d": 12.3,  # 7天增长率
                "timestamp": datetime.now().isoformat()
            }

            # 解读
            if simulated_data["growth_24h"] > 5:
                simulated_data["implication"] = "活跃地址显著增加，网络活跃度提升"
                simulated_data["sentiment"] = "bullish"
            elif simulated_data["growth_24h"] < -5:
                simulated_data["implication"] = "活跃地址显著减少，网络活跃度下降"
                simulated_data["sentiment"] = "bearish"
            else:
                simulated_data["implication"] = "活跃地址相对稳定"
                simulated_data["sentiment"] = "neutral"

            return simulated_data

        except Exception as e:
            return {"error": str(e)}

    def get_mempool_status(self) -> Dict:
        """
        获取内存池状态

        Returns:
            内存池数据
        """
        try:
            # 模拟数据
            simulated_data = {
                "unconfirmed_transactions": 12500,
                "mempool_size_mb": 85.5,
                "average_fee_btc": 0.00015,  # 平均手续费
                "average_fee_usd": 7.5,
                "timestamp": datetime.now().isoformat()
            }

            # 解读
            if simulated_data["unconfirmed_transactions"] > 20000:
                simulated_data["implication"] = "网络拥堵，手续费较高，可能影响交易"
                simulated_data["congestion_level"] = "high"
            elif simulated_data["unconfirmed_transactions"] > 10000:
                simulated_data["implication"] = "网络中等拥堵，手续费适中"
                simulated_data["congestion_level"] = "medium"
            else:
                simulated_data["implication"] = "网络畅通，手续费较低"
                simulated_data["congestion_level"] = "low"

            return simulated_data

        except Exception as e:
            return {"error": str(e)}


# 全局实例
_onchain_collector = OnChainCollector()


@tool
def get_onchain_data() -> str:
    """
    获取链上数据

    Returns:
        链上数据报告 JSON
    """
    ctx = request_context.get() or new_context(method="get_onchain_data")

    try:
        # 获取交易所流入流出
        exchange_flow = _onchain_collector.get_exchange_inflow("BTC")

        # 获取巨鲸活动
        whale_activity = _onchain_collector.get_whale_activity()

        # 获取活跃地址
        active_addresses = _onchain_collector.get_active_addresses("BTC")

        # 获取内存池状态
        mempool = _onchain_collector.get_mempool_status()

        # 综合分析
        overall_sentiment = "neutral"
        signals = []

        # 分析交易所流入
        if exchange_flow.get("interpretation", {}).get("sentiment") == "bullish":
            signals.append("exchange_outflow")
        elif exchange_flow.get("interpretation", {}).get("sentiment") == "bearish":
            signals.append("exchange_inflow")

        # 分析巨鲸活动
        if whale_activity.get("sentiment") == "bullish":
            signals.append("whale_buying")
        elif whale_activity.get("sentiment") == "bearish":
            signals.append("whale_selling")

        # 分析活跃地址
        if active_addresses.get("sentiment") == "bullish":
            signals.append("high_activity")
        elif active_addresses.get("sentiment") == "bearish":
            signals.append("low_activity")

        # 综合判断
        bullish_signals = sum(1 for s in signals if s in ["exchange_outflow", "whale_buying", "high_activity"])
        bearish_signals = sum(1 for s in signals if s in ["exchange_inflow", "whale_selling", "low_activity"])

        if bullish_signals > bearish_signals:
            overall_sentiment = "bullish"
            overall_implication = "链上数据整体利好BTC"
        elif bearish_signals > bullish_signals:
            overall_sentiment = "bearish"
            overall_implication = "链上数据整体利空BTC"
        else:
            overall_sentiment = "neutral"
            overall_implication = "链上数据中性"

        # 生成报告
        report = {
            "timestamp": datetime.now().isoformat(),
            "exchange_flow": exchange_flow,
            "whale_activity": whale_activity,
            "network_health": {
                "active_addresses": active_addresses,
                "mempool": mempool
            },
            "signals": signals,
            "overall_sentiment": overall_sentiment,
            "overall_implication": overall_implication
        }

        return json.dumps(report, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)


@tool
def get_hashrate_difficulty() -> str:
    """
    获取算力和难度数据

    Returns:
        算力难度数据 JSON
    """
    ctx = request_context.get() or new_context(method="get_hashrate_difficulty")

    try:
        # 模拟数据
        simulated_data = {
            "hashrate_eh_s": 650.5,  # EH/s
            "hashrate_change_24h": 2.3,  # 24小时变化百分比
            "difficulty": 85.5,  # 难度（万亿）
            "difficulty_change_7d": 1.5,  # 7天变化百分比
            "timestamp": datetime.now().isoformat()
        }

        # 解读
        if simulated_data["hashrate_change_24h"] > 0:
            simulated_data["implication"] = "算力增加，挖矿活跃度提升，网络安全性增强"
            simulated_data["sentiment"] = "bullish"
        else:
            simulated_data["implication"] = "算力减少，可能有矿工退出"
            simulated_data["sentiment"] = "bearish"

        return json.dumps(simulated_data, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)
