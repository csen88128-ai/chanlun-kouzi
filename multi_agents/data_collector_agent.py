#!/usr/bin/env python3
"""
数据采集智能体 - 使用火币API获取BTC数据
"""
import json
import sys
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain.tools import tool
from typing import Annotated
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
import os

# 添加路径
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver


# 火币API工具
@tool
def get_btc_klines(interval: str = "4h", limit: int = 200) -> str:
    """获取火币BTC K线数据

    Args:
        interval: K线周期 (1m, 5m, 15m, 1h, 4h, 1d)
        limit: K线数量

    Returns:
        K线数据摘要
    """
    ctx = request_context.get() or new_context(method="get_btc_klines")

    try:
        import requests
        import pandas as pd

        # 火币API
        url = "https://api.huobi.pro/market/history/kline"

        # 周期映射
        period_mapping = {
            '1m': '1min', '5m': '5min', '15m': '15min', '30m': '30min',
            '1h': '60min', '2h': '120min', '4h': '4hour', '6h': '6hour',
            '12h': '12hour', '1d': '1day', '1w': '1week', '1M': '1mon'
        }

        period = period_mapping.get(interval, '4hour')

        params = {
            "symbol": "btcusdt",
            "period": period,
            "size": min(limit, 2000)
        }

        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get('status') != 'ok':
            return json.dumps({
                "error": f"API返回错误: {data.get('err-msg', '未知错误')}"
            }, ensure_ascii=False)

        klines = data.get('data', [])

        if not klines or len(klines) == 0:
            return json.dumps({
                "error": "未获取到K线数据"
            }, ensure_ascii=False)

        # 转换为DataFrame
        df = pd.DataFrame(klines)
        df = df.sort_values('id').reset_index(drop=True)

        # 计算涨跌幅
        df['timestamp'] = pd.to_datetime(df['id'], unit='s')
        df['change'] = df['close'].pct_change() * 100

        # 保存数据
        data_dir = "/workspace/projects/data"
        os.makedirs(data_dir, exist_ok=True)
        df.to_csv(f"{data_dir}/BTCUSDT_{interval}_latest.csv", index=False)

        # 返回摘要
        summary = {
            "status": "success",
            "symbol": "BTCUSDT",
            "interval": interval,
            "data_count": len(df),
            "latest_price": float(df['close'].iloc[-1]),
            "highest": float(df['high'].max()),
            "lowest": float(df['low'].min()),
            "24h_change": float(df['change'].iloc[-1]) if len(df) > 0 else 0,
            "time_range": f"{df['timestamp'].min()} ~ {df['timestamp'].max()}",
            "file_path": f"{data_dir}/BTCUSDT_{interval}_latest.csv"
        }

        return json.dumps(summary, ensure_ascii=False, indent=2)

    except requests.exceptions.RequestException as e:
        return json.dumps({
            "error": f"网络请求失败: {str(e)}"
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({
            "error": f"数据获取失败: {str(e)}"
        }, ensure_ascii=False)


MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """构建数据采集智能体"""
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, "config/agent_llm_config.json")

    with open(config_path, 'r', encoding='utf-8') as f:
        cfg = json.load(f)

    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")

    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        },
        default_headers=default_headers(ctx) if ctx else {}
    )

    system_prompt = """你是数据采集智能体，负责从火币交易所获取BTC实时数据。

# 核心职责
1. 使用 get_btc_klines 工具获取K线数据
2. 确保数据完整性和质量
3. 返回数据摘要供后续分析使用

# 工作流程
1. 接收数据请求（周期、数量）
2. 调用 get_btc_klines 获取数据
3. 检查数据质量
4. 返回详细的数据摘要

# 输出要求
必须包含：
- 最新价格
- 最高/最低价
- 涨跌幅
- 数据时间范围
- 数据质量评估
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[get_btc_klines],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
