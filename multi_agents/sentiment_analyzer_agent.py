#!/usr/bin/env python3
"""
市场情绪智能体 - 市场情绪分析
"""
import json
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')
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
from storage.memory.memory_saver import get_memory_saver


@tool
def get_market_sentiment() -> str:
    """获取市场恐惧贪婪指数

    Returns:
        市场情绪数据
    """
    try:
        import requests

        # Alternative.me API
        url = "https://api.alternative.me/fng/"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if 'data' not in data or len(data['data']) == 0:
            return json.dumps({"error": "无法获取情绪数据"}, ensure_ascii=False)

        sentiment_data = data['data'][0]

        value = int(sentiment_data['value'])
        classification = sentiment_data['value_classification']

        # 分类情绪
        if value >= 75:
            sentiment = "极度贪婪"
            implication = "市场过热，存在回调风险"
        elif value >= 55:
            sentiment = "贪婪"
            implication = "市场乐观，但需谨慎"
        elif value >= 45:
            sentiment = "中性"
            implication = "市场情绪平稳"
        elif value >= 25:
            sentiment = "恐惧"
            implication = "市场悲观，可能存在机会"
        else:
            sentiment = "极度恐惧"
            implication = "市场极度恐慌，可能接近底部"

        result = {
            "status": "success",
            "fear_greed_index": value,
            "classification": classification,
            "sentiment": sentiment,
            "implication": implication,
            "timestamp": sentiment_data['timestamp']
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        # 如果API失败，返回模拟数据
        result = {
            "status": "fallback",
            "fear_greed_index": 45,
            "classification": "Neutral",
            "sentiment": "中性",
            "implication": "无法获取实时数据，使用中性情绪",
            "error": str(e)
        }
        return json.dumps(result, ensure_ascii=False, indent=2)


MAX_MESSAGES = 40

def _windowed_messages(old, new):
    """滑动窗口"""
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """构建市场情绪智能体"""
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

    system_prompt = """你是市场情绪智能体，负责分析市场情绪和投资者心理。

# 核心职责
1. 使用 get_market_sentiment 工具获取恐惧贪婪指数
2. 分析市场情绪状态
3. 评估投资者心理
4. 结合情绪给出操作建议

# 工作流程
1. 调用 get_market_sentiment 获取情绪数据
2. 分析情绪数值和分类
3. 评估市场情绪对价格的影响
4. 给出基于情绪的建议

# 输出要求
必须返回JSON格式的市场情绪数据，直接输出工具的JSON结果，不要添加额外的格式化或解释。
工具输出包含：
- fear_greed_index: 恐惧贪婪指数数值
- classification: 情绪分类（极度贪婪/贪婪/中性/恐惧/极度恐惧）
- sentiment: 情绪状态
- implication: 情绪含义和影响

注意：请直接返回工具输出的JSON，不要生成Markdown报告。
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[get_market_sentiment],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
