#!/usr/bin/env python3
"""
动力学分析智能体 - 动量、波动性、成交量分析
"""
import json
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool
from typing import Annotated
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
import os

from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.runtime_ctx.context import default_headers


@tool
def analyze_dynamics() -> str:
    """分析市场动力学指标

    Returns:
        动力学分析结果
    """
    try:
        # 读取数据
        data_dir = "/workspace/projects/data"
        df = pd.read_csv(f"{data_dir}/BTCUSDT_4h_latest.csv")

        # 计算涨跌幅
        df['change'] = df['close'].pct_change() * 100

        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # 计算MACD
        df['ema12'] = df['close'].ewm(span=12).mean()
        df['ema26'] = df['close'].ewm(span=26).mean()
        df['macd'] = df['ema12'] - df['ema26']
        df['signal'] = df['macd'].ewm(span=9).mean()
        df['histogram'] = df['macd'] - df['signal']

        # 计算波动率
        df['volatility'] = df['close'].rolling(window=20).std()

        # 成交量分析
        df['vol_ma'] = df['vol'].rolling(window=20).mean()
        df['vol_ratio'] = df['vol'] / df['vol_ma']

        latest = df.iloc[-1]

        # 判断RSI状态
        rsi_status = "超买" if latest['rsi'] > 70 else "超卖" if latest['rsi'] < 30 else "正常"

        # 判断MACD状态
        macd_signal = "金叉" if latest['macd'] > latest['signal'] else "死叉"
        macd_trend = "上升" if latest['histogram'] > 0 else "下降"

        # 波动性判断
        volatility_status = "高" if latest['volatility'] > df['volatility'].mean() else "低"

        result = {
            "status": "success",
            "rsi": float(latest['rsi']),
            "rsi_status": rsi_status,
            "macd": float(latest['macd']),
            "signal": float(latest['signal']),
            "macd_signal": macd_signal,
            "macd_trend": macd_trend,
            "histogram": float(latest['histogram']),
            "volatility": float(latest['volatility']),
            "volatility_status": volatility_status,
            "volume_ratio": float(latest['vol_ratio']),
            "volume_status": "放量" if latest['vol_ratio'] > 1.2 else "缩量",
            "momentum": float(df['change'].tail(5).mean())
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
    """构建动力学分析智能体"""
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

    system_prompt = """你是动力学分析智能体，负责分析市场动能和波动性。

# 核心职责
1. 使用 analyze_dynamics 工具分析动力学指标
2. 评估RSI、MACD、波动率等
3. 判断市场动量和成交量变化
4. 识别超买超卖状态

# 工作流程
1. 读取数据采集智能体的数据
2. 调用 analyze_dynamics 进行动力学分析
3. 评估市场动能
4. 判断入场时机

# 输出要求
必须包含：
- RSI状态（超买/超卖/正常）
- MACD信号（金叉/死叉）
- 波动性评估
- 成交量状态
- 动量方向
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[analyze_dynamics],
        state_schema=AgentState,
    )
