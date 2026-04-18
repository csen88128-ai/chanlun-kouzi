#!/usr/bin/env python3
"""
结构分析智能体 - 缠论结构分析
"""
import json
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain.tools import tool
from typing import Annotated
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
import os

from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver


@tool
def analyze_structure() -> str:
    """分析K线数据的缠论结构

    Returns:
        结构分析结果
    """
    try:
        # 读取数据
        data_dir = "/workspace/projects/data"
        df = pd.read_csv(f"{data_dir}/BTCUSDT_4h_latest.csv")

        # 计算技术指标
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        df['ma60'] = df['close'].rolling(window=60).mean()

        # 识别分型（简化版）
        df['fractal'] = None
        for i in range(2, len(df)-2):
            # 顶分型：中间K线最高价是5根中最高的
            if df['high'].iloc[i] == df['high'].iloc[i-2:i+3].max():
                df.loc[i, 'fractal'] = 'top'
            # 底分型：中间K线最低价是5根中最低的
            if df['low'].iloc[i] == df['low'].iloc[i-2:i+3].min():
                df.loc[i, 'fractal'] = 'bottom'

        top_fractals = len(df[df['fractal'] == 'top'])
        bottom_fractals = len(df[df['fractal'] == 'bottom'])

        # 趋势分析
        latest = df.iloc[-1]
        trend = ""
        if latest['close'] > latest['ma5'] > latest['ma10'] > latest['ma20']:
            trend = "强势上升"
        elif latest['close'] < latest['ma5'] < latest['ma10'] < latest['ma20']:
            trend = "强势下降"
        elif latest['close'] > latest['ma20']:
            trend = "温和上升"
        else:
            trend = "温和下降"

        # 支撑阻力位
        recent_high = df['high'].tail(20).max()
        recent_low = df['low'].tail(20).min()

        result = {
            "status": "success",
            "trend": trend,
            "top_fractals": top_fractals,
            "bottom_fractals": bottom_fractals,
            "ma5": float(latest['ma5']),
            "ma10": float(latest['ma10']),
            "ma20": float(latest['ma20']),
            "ma60": float(latest['ma60']),
            "resistance": float(recent_high),
            "support": float(recent_low),
            "current_price": float(latest['close']),
            "price_position": f"{((latest['close'] - recent_low) / (recent_high - recent_low) * 100):.1f}%"
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """构建结构分析智能体"""
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

    system_prompt = """你是结构分析智能体，负责分析BTC的缠论结构。

# 核心职责
1. 使用 analyze_structure 工具分析K线结构
2. 识别分型、笔、线段、中枢
3. 判断趋势方向
4. 找出支撑阻力位

# 工作流程
1. 读取数据采集智能体的数据
2. 调用 analyze_structure 进行结构分析
3. 识别关键价格点位
4. 判断趋势和买卖点

# 输出要求
必须包含：
- 趋势方向
- 分型统计
- 均线排列
- 支撑阻力位
- 价格位置
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[analyze_structure],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
