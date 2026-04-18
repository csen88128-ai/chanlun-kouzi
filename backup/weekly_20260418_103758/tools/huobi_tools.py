"""
火币(HTX) 数据采集工具
"""
import os
import json
import requests
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional


class HuobiDataCollector:
    """火币(HTX) 数据采集器"""

    BASE_URL = "https://api.huobi.pro"
    # 备用域名
    BACKUP_URLS = [
        "https://api.huobi.de.com",
        "https://api.huobi.vn.com",
        "https://api.hbdm.vn"
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _make_request(self, endpoint: str, params: dict, timeout: int = 10) -> dict:
        """
        发送请求，自动尝试备用域名

        Args:
            endpoint: API端点
            params: 请求参数
            timeout: 超时时间

        Returns:
            响应数据
        """
        urls_to_try = [self.BASE_URL] + self.BACKUP_URLS

        for base_url in urls_to_try:
            try:
                response = self.session.get(
                    f"{base_url}{endpoint}",
                    params=params,
                    timeout=timeout
                )
                response.raise_for_status()
                data = response.json()

                # 火币API返回格式：{"status": "ok", "data": [...]}
                if data.get('status') == 'ok':
                    return data.get('data', [])
                elif 'err-msg' in data:
                    raise Exception(f"API错误: {data.get('err-msg')}")
                else:
                    return data

            except Exception as e:
                if base_url == urls_to_try[-1]:
                    raise
                continue

        raise Exception("所有API端点均连接失败")

    def get_klines(
        self,
        symbol: str = "btcusdt",
        interval: str = "1h",
        limit: int = 500,
        from_ts: Optional[int] = None
    ) -> List[dict]:
        """
        获取K线数据

        Args:
            symbol: 交易对，如 btcusdt (小写)
            interval: K线间隔，如 1min, 5min, 15min, 60min(1h), 4hour, 1day
            limit: 数量限制，最大 2000
            from_ts: 开始时间戳（秒）

        Returns:
            K线数据列表
        """
        params = {
            "symbol": symbol.lower(),
            "period": interval,
            "size": min(limit, 2000)
        }

        if from_ts:
            params["from"] = from_ts

        try:
            # 使用火币的历史K线接口（注意：不需要 /v1 前缀）
            data = self._make_request("/market/history/kline", params)
            return data
        except Exception as e:
            raise Exception(f"获取K线数据失败: {str(e)}")

    def format_klines(self, klines: List[dict]) -> pd.DataFrame:
        """
        格式化K线数据为DataFrame

        Args:
            klines: 原始K线数据

        Returns:
            格式化后的DataFrame
        """
        if not klines:
            raise Exception("K线数据为空")

        # 火币返回的数据格式
        df = pd.DataFrame(klines)

        # 重命名列以匹配币安格式
        column_mapping = {
            'id': 'timestamp',
            'open': 'open',
            'close': 'close',
            'high': 'high',
            'low': 'low',
            'vol': 'volume',
            'count': 'trades',
            'bid_vol': 'bid_volume',
            'ask_vol': 'ask_volume'
        }

        df.rename(columns=column_mapping, inplace=True)

        # 按时间排序（火币返回的是倒序）
        df = df.sort_values('timestamp').reset_index(drop=True)

        # 转换时间戳（火币是秒，需要转换为毫秒）
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df['close_time'] = df['timestamp'] + pd.Timedelta(hours=4)  # 4小时

        # 转换数据类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col])

        return df

    def get_latest_price(self, symbol: str = "btcusdt") -> dict:
        """
        获取最新价格

        Args:
            symbol: 交易对

        Returns:
            最新价格数据
        """
        try:
            # 直接使用 requests 而不是 _make_request，因为这个接口返回的是 dict 而不是 list
            for base_url in [self.BASE_URL] + self.BACKUP_URLS:
                try:
                    response = self.session.get(
                        f"{base_url}/market/detail/merged",
                        params={"symbol": symbol.lower()},
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()
                    if data.get('status') == 'ok':
                        return data.get('tick', {})
                except Exception as e:
                    if base_url == (self.BACKUP_URLS[-1] if self.BACKUP_URLS else self.BASE_URL):
                        raise
                    continue

            raise Exception("所有API端点均连接失败")
        except Exception as e:
            raise Exception(f"获取最新价格失败: {str(e)}")


# 全局实例
_collector = HuobiDataCollector()


def get_kline_data_huobi(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    limit: int = 500
) -> str:
    """
    获取火币(HTX) K线数据

    Args:
        symbol: 交易对，如 BTCUSDT
        interval: K线间隔，如 1m, 5m, 15m, 1h, 4h, 1d
        limit: 数量限制，默认500

    Returns:
        JSON格式的K线数据摘要
    """
    try:
        # 转换为火币格式
        interval_mapping = {
            '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
            '1h': '60min', '2h': '120min', '4h': '4hour', '6h': '6hour',
            '12h': '12hour', '1d': '1day', '1w': '1week', '1M': '1mon'
        }
        huobi_interval = interval_mapping.get(interval, interval)
        huobi_symbol = symbol.replace('/', '').lower()

        # 获取原始数据
        klines = _collector.get_klines(
            symbol=huobi_symbol,
            interval=huobi_interval,
            limit=limit
        )

        # 格式化为DataFrame
        df = _collector.format_klines(klines)

        # 保存到本地
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        data_dir = os.path.join(workspace_path, "data")
        os.makedirs(data_dir, exist_ok=True)

        filename = f"{symbol}_{interval}_huobi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = os.path.join(data_dir, filename)
        df.to_csv(filepath, index=False)

        # 生成数据摘要
        summary = {
            "source": "Huobi (HTX)",
            "symbol": symbol,
            "interval": interval,
            "data_count": len(df),
            "time_range": {
                "start": str(df['timestamp'].min()),
                "end": str(df['timestamp'].max())
            },
            "price_stats": {
                "latest_close": float(df['close'].iloc[-1]),
                "highest": float(df['high'].max()),
                "lowest": float(df['low'].min()),
                "average_volume": float(df['volume'].mean()),
                "price_change": float((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100)
            },
            "file_path": filepath,
            "recent_candles": [
                {
                    "timestamp": str(row['timestamp']),
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row['volume'])
                }
                for _, row in df.tail(5).iterrows()
            ]
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False, indent=2)
