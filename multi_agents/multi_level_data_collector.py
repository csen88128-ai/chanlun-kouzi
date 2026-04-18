"""
多级别K线数据采集器
支持5m、30m、4h、1d四个级别的数据采集
"""
import requests
import pandas as pd
import time
from typing import Dict, List
from datetime import datetime


class MultiLevelDataCollector:
    """多级别K线数据采集器"""

    def __init__(self, symbol="btcusdt"):
        """
        初始化数据采集器

        Args:
            symbol: 交易对，默认为BTCUSDT
        """
        self.symbol = symbol
        self.base_url = "https://api.huobi.pro/market/history/kline"

        # 级别配置
        self.level_config = {
            "5m": {
                "interval": "5min",
                "limit": 500,  # 足够的数据量
                "name": "5分钟级别"
            },
            "30m": {
                "interval": "30min",
                "limit": 400,
                "name": "30分钟级别"
            },
            "4h": {
                "interval": "4hour",
                "limit": 300,
                "name": "4小时级别"
            },
            "1d": {
                "interval": "1day",
                "limit": 200,
                "name": "日线级别"
            }
        }

    def _fetch_klines(self, interval: str, limit: int) -> List[Dict]:
        """
        从火币API获取K线数据

        Args:
            interval: K线间隔（如 "5min", "30min", "4hour", "1day"）
            limit: 获取的K线数量

        Returns:
            K线数据列表
        """
        try:
            params = {
                "symbol": self.symbol,
                "period": interval,
                "size": limit,
                "from": int(time.time()) - limit * 60 * 5  # 计算起始时间
            }

            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if "status" not in data or data["status"] != "ok":
                raise ValueError(f"API返回错误: {data}")

            return data["data"]

        except Exception as e:
            print(f"获取{interval}级别K线数据失败: {e}")
            return []

    def _process_klines(self, klines: List[Dict]) -> pd.DataFrame:
        """
        处理K线数据，转换为DataFrame

        Args:
            klines: 原始K线数据

        Returns:
            处理后的DataFrame
        """
        if not klines:
            return pd.DataFrame()

        # 火币返回的数据是倒序的，需要排序
        klines = sorted(klines, key=lambda x: x["id"])

        # 转换为DataFrame
        df = pd.DataFrame(klines)

        # 重命名列
        df = df.rename(columns={
            "id": "timestamp",
            "open": "open",
            "close": "close",
            "high": "high",
            "low": "low",
            "amount": "volume",
            "vol": "turnover"  # 成交额
        })

        # 转换时间戳
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")

        # 计算涨跌幅
        df["change"] = df["close"].diff()
        df["change_pct"] = df["close"].pct_change() * 100

        # 计算开盘价、收盘价、最高价、最低价的相对位置
        df["body"] = df["close"] - df["open"]  # 实体
        df["upper_shadow"] = df["high"] - df[["open", "close"]].max(axis=1)  # 上影线
        df["lower_shadow"] = df[["open", "close"]].min(axis=1) - df["low"]  # 下影线

        # K线类型
        df["is_red"] = df["close"] > df["open"]  # 阳线
        df["is_green"] = df["close"] < df["open"]  # 阴线
        df["is_doji"] = df["body"].abs() < df["close"] * 0.001  # 十字星

        return df

    def get_level_data(self, level: str) -> pd.DataFrame:
        """
        获取指定级别的K线数据

        Args:
            level: 级别（5m、30m、4h、1d）

        Returns:
            K线数据DataFrame
        """
        if level not in self.level_config:
            raise ValueError(f"不支持的级别: {level}，支持的级别: {list(self.level_config.keys())}")

        config = self.level_config[level]

        print(f"正在获取{config['name']}K线数据...")
        klines = self._fetch_klines(config["interval"], config["limit"])
        df = self._process_klines(klines)

        print(f"  ✓ 获取成功，K线数量: {len(df)}")
        if len(df) > 0:
            print(f"  ✓ 数据范围: {df.iloc[0]['timestamp']} ~ {df.iloc[-1]['timestamp']}")
            print(f"  ✓ 最新价格: {df.iloc[-1]['close']}")

        return df

    def get_all_levels(self) -> Dict[str, pd.DataFrame]:
        """
        获取所有级别的K线数据

        Returns:
            包含所有级别数据的字典
        """
        print("=" * 80)
        print("多级别K线数据采集")
        print("=" * 80)

        all_data = {}

        for level in ["5m", "30m", "4h", "1d"]:
            try:
                df = self.get_level_data(level)
                all_data[level] = df
                print()
            except Exception as e:
                print(f"  ✗ 获取{level}级别数据失败: {e}")
                print()
                all_data[level] = pd.DataFrame()

        return all_data

    def get_data_summary(self, all_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        获取数据摘要

        Args:
            all_data: 所有级别的数据

        Returns:
            数据摘要
        """
        summary = {
            "symbol": self.symbol,
            "levels": {},
            "collected_at": datetime.now().isoformat()
        }

        for level, df in all_data.items():
            if len(df) > 0:
                summary["levels"][level] = {
                    "name": self.level_config[level]["name"],
                    "kline_count": len(df),
                    "time_range": f"{df.iloc[0]['timestamp']} ~ {df.iloc[-1]['timestamp']}",
                    "latest_price": df.iloc[-1]["close"],
                    "h24_change": self._calculate_h24_change(df, level)
                }
            else:
                summary["levels"][level] = {
                    "name": self.level_config[level]["name"],
                    "status": "failed"
                }

        return summary

    def _calculate_h24_change(self, df: pd.DataFrame, level: str) -> float:
        """
        计算24小时涨跌幅

        Args:
            df: K线数据
            level: 级别

        Returns:
            24小时涨跌幅（百分比）
        """
        if len(df) < 2:
            return 0.0

        # 根据级别计算24小时前的K线索引
        if level == "5m":
            hours_24_index = len(df) - 24 * 12  # 24小时 = 288个5分钟K线
        elif level == "30m":
            hours_24_index = len(df) - 24 * 2  # 24小时 = 48个30分钟K线
        elif level == "4h":
            hours_24_index = len(df) - 6  # 24小时 = 6个4小时K线
        elif level == "1d":
            hours_24_index = len(df) - 1  # 24小时 = 1个日K线
        else:
            return 0.0

        if hours_24_index < 0:
            return 0.0

        price_24h_ago = df.iloc[hours_24_index]["close"]
        current_price = df.iloc[-1]["close"]

        return (current_price - price_24h_ago) / price_24h_ago * 100


if __name__ == "__main__":
    # 测试多级别数据采集
    print("=" * 80)
    print("测试多级别K线数据采集")
    print("=" * 80)

    collector = MultiLevelDataCollector(symbol="btcusdt")

    # 获取所有级别数据
    all_data = collector.get_all_levels()

    # 显示数据摘要
    print("\n" + "=" * 80)
    print("数据摘要")
    print("=" * 80)

    summary = collector.get_data_summary(all_data)

    print(f"\n交易对: {summary['symbol']}")
    print(f"采集时间: {summary['collected_at']}")

    for level, info in summary["levels"].items():
        print(f"\n{level} ({info['name']}):")
        if "status" in info:
            print(f"  状态: {info['status']}")
        else:
            print(f"  K线数量: {info['kline_count']}")
            print(f"  数据范围: {info['time_range']}")
            print(f"  最新价格: {info['latest_price']}")
            print(f"  24h涨跌: {info['h24_change']:.2f}%")
