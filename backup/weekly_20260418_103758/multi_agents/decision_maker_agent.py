#!/usr/bin/env python3
"""
决策制定智能体 - 综合所有分析并做出最终决策
"""
import json
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
def make_decision(
    structure_data: str,
    dynamics_data: str,
    sentiment_data: str
) -> str:
    """综合所有分析并做出最终交易决策

    Args:
        structure_data: 结构分析结果（JSON字符串）
        dynamics_data: 动力学分析结果（JSON字符串）
        sentiment_data: 情绪分析结果（JSON字符串）

    Returns:
        最终决策建议
    """
    try:
        structure = json.loads(structure_data)
        dynamics = json.loads(dynamics_data)
        sentiment = json.loads(sentiment_data)

        # 计算综合得分
        score = 0
        factors = []

        # 1. 趋势因子 (30%)
        if structure['trend'] == "强势上升":
            score += 30
            factors.append(f"趋势: +30 (强势上升)")
        elif structure['trend'] == "温和上升":
            score += 20
            factors.append(f"趋势: +20 (温和上升)")
        elif structure['trend'] == "温和下降":
            score -= 20
            factors.append(f"趋势: -20 (温和下降)")
        else:
            score -= 30
            factors.append(f"趋势: -30 (强势下降)")

        # 2. RSI因子 (20%)
        if dynamics['rsi'] < 30:
            score += 20
            factors.append(f"RSI: +20 (超卖)")
        elif dynamics['rsi'] < 45:
            score += 10
            factors.append(f"RSI: +10 (偏低)")
        elif dynamics['rsi'] > 70:
            score -= 20
            factors.append(f"RSI: -20 (超买)")
        elif dynamics['rsi'] > 55:
            score -= 10
            factors.append(f"RSI: -10 (偏高)")
        else:
            factors.append(f"RSI: +0 (正常)")

        # 3. MACD因子 (20%)
        if dynamics['macd_signal'] == "金叉" and dynamics['macd_trend'] == "上升":
            score += 20
            factors.append(f"MACD: +20 (金叉上升)")
        elif dynamics['macd_signal'] == "金叉":
            score += 10
            factors.append(f"MACD: +10 (金叉)")
        elif dynamics['macd_signal'] == "死叉" and dynamics['macd_trend'] == "下降":
            score -= 20
            factors.append(f"MACD: -20 (死叉下降)")
        else:
            score -= 10
            factors.append(f"MACD: -10 (死叉)")

        # 4. 价格位置因子 (15%)
        price_pos = float(structure['price_position'].rstrip('%'))
        if price_pos < 20:
            score += 15
            factors.append(f"价格位置: +15 (低位)")
        elif price_pos > 80:
            score -= 15
            factors.append(f"价格位置: -15 (高位)")
        else:
            factors.append(f"价格位置: +0 (中位)")

        # 5. 市场情绪因子 (15%)
        fgi = sentiment['fear_greed_index']
        if fgi < 25:
            score += 15
            factors.append(f"情绪: +15 (极度恐惧)")
        elif fgi < 45:
            score += 10
            factors.append(f"情绪: +10 (恐惧)")
        elif fgi > 75:
            score -= 15
            factors.append(f"情绪: -15 (极度贪婪)")
        elif fgi > 55:
            score -= 10
            factors.append(f"情绪: -10 (贪婪)")
        else:
            factors.append(f"情绪: +0 (中性)")

        # 归一化得分到 0-100
        normalized_score = max(0, min(100, (score + 100) / 2))

        # 决策
        if normalized_score >= 70:
            decision = "买入"
            emoji = "🟢"
            confidence = "高"
        elif normalized_score >= 55:
            decision = "偏多"
            emoji = "🟢"
            confidence = "中"
        elif normalized_score <= 30:
            decision = "卖出"
            emoji = "🔴"
            confidence = "高"
        elif normalized_score <= 45:
            decision = "偏空"
            emoji = "🔴"
            confidence = "中"
        else:
            decision = "观望"
            emoji = "🟡"
            confidence = "中"

        result = {
            "status": "success",
            "decision": decision,
            "emoji": emoji,
            "score": round(normalized_score, 2),
            "confidence": confidence,
            "factors": factors,
            "summary": f"综合得分: {normalized_score:.1f}/100"
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
    """构建决策制定智能体"""
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

    system_prompt = """你是决策制定智能体，负责综合所有分析结果并做出最终交易决策。

# 核心职责
1. 汇总结构、动力学、情绪分析结果
2. 使用 make_decision 工具进行综合评分
3. 基于综合得分做出交易决策
4. 给出具体的操作建议

# 工作流程
1. 收集各智能体的分析结果
2. 调用 make_decision 进行综合评分
3. 生成最终决策
4. 给出操作建议和风险提示

# 评分体系
- 趋势因子 (30%): 强势上升 +30, 温和上升 +20, 温和下降 -20, 强势下降 -30
- RSI因子 (20%): 超买 -20, 偏高 -10, 正常 0, 偏低 +10, 超卖 +20
- MACD因子 (20%): 金叉上升 +20, 金叉 +10, 死叉 -10, 死叉下降 -20
- 价格位置 (15%): 低位 +15, 中位 0, 高位 -15
- 市场情绪 (15%): 极度恐惧 +15, 恐惧 +10, 中性 0, 贪婪 -10, 极度贪婪 -15

# 决策标准
- 得分 >= 70: 买入
- 得分 55-69: 偏多
- 得分 46-54: 观望
- 得分 30-45: 偏空
- 得分 <= 29: 卖出

# 输出要求
必须包含：
- 最终决策（买入/偏多/观望/偏空/卖出）
- 综合得分
- 置信度
- 各因子得分
- 操作建议
- 风险提示
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[make_decision],
        state_schema=AgentState,
    )
