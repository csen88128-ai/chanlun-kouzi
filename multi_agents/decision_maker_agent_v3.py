#!/usr/bin/env python3
"""
决策制定智能体 - 综合所有分析并做出最终决策（修复版 v3）
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
import pandas as pd

from coze_coding_utils.log.write_log import request_context
from coze_coding_utils.runtime_ctx.context import new_context
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver


@tool
def make_decision_v2(
    structure_data: str,
    dynamics_data: str,
    sentiment_data: str
) -> str:
    """综合所有分析并做出最终交易决策（修复版）

    Args:
        structure_data: 结构分析结果（JSON字符串）
        dynamics_data: 动力学分析结果（JSON字符串）
        sentiment_data: 情绪分析结果（JSON字符串）

    Returns:
        最终决策建议，包含止盈止损
    """
    try:
        structure = json.loads(structure_data)
        dynamics = json.loads(dynamics_data)
        sentiment = json.loads(sentiment_data)

        # 获取当前价格
        data_dir = "/workspace/projects/data"
        df = pd.read_csv(f"{data_dir}/BTCUSDT_4h_latest.csv")
        current_price = df['close'].iloc[-1]

        # 计算综合得分
        score = 0
        factors = []

        # 1. 趋势因子 (25%)
        trend_direction = structure.get('trend_analysis', {}).get('direction', '无法判断')
        if trend_direction == "上升":
            score += 25
            factors.append(f"趋势: +25 (上升)")
        elif trend_direction == "下降":
            score -= 25
            factors.append(f"趋势: -25 (下降)")
        else:
            factors.append(f"趋势: +0 (盘整)")

        # 2. 缠论买卖点因子 (20%)
        buy_sell_points = structure.get('buy_sell_points', {})
        latest_signal = buy_sell_points.get('latest_signal')
        if latest_signal and latest_signal.get('is_buy'):
            signal_type = latest_signal.get('type')
            if signal_type == "一买":
                score += 20
                factors.append(f"缠论: +20 (一买, 强度{latest_signal.get('strength', 0):.2f})")
            elif signal_type == "二买":
                score += 15
                factors.append(f"缠论: +15 (二买, 强度{latest_signal.get('strength', 0):.2f})")
            elif signal_type == "三买":
                score += 10
                factors.append(f"缠论: +10 (三买, 强度{latest_signal.get('strength', 0):.2f})")
        elif latest_signal and not latest_signal.get('is_buy'):
            signal_type = latest_signal.get('type')
            if signal_type == "一卖":
                score -= 20
                factors.append(f"缠论: -20 (一卖, 强度{latest_signal.get('strength', 0):.2f})")
            elif signal_type == "二卖":
                score -= 15
                factors.append(f"缠论: -15 (二卖, 强度{latest_signal.get('strength', 0):.2f})")
            elif signal_type == "三卖":
                score -= 10
                factors.append(f"缠论: -10 (三卖, 强度{latest_signal.get('strength', 0):.2f})")
        else:
            factors.append(f"缠论: +0 (无买卖点信号)")

        # 3. RSI因子 (15%)
        rsi = dynamics.get('rsi', 50)
        if rsi < 30:
            score += 15
            factors.append(f"RSI: +15 (超卖 {rsi:.1f})")
        elif rsi < 45:
            score += 8
            factors.append(f"RSI: +8 (偏低 {rsi:.1f})")
        elif rsi > 70:
            score -= 15
            factors.append(f"RSI: -15 (超买 {rsi:.1f})")
        elif rsi > 55:
            score -= 8
            factors.append(f"RSI: -8 (偏高 {rsi:.1f})")
        else:
            factors.append(f"RSI: +0 (正常 {rsi:.1f})")

        # 4. MACD因子 (15%)
        macd_signal = dynamics.get('macd_signal', '中性')
        macd_trend = dynamics.get('macd_trend', '中性')
        if macd_signal == "金叉" and macd_trend == "上升":
            score += 15
            factors.append(f"MACD: +15 (金叉上升)")
        elif macd_signal == "金叉":
            score += 8
            factors.append(f"MACD: +8 (金叉)")
        elif macd_signal == "死叉" and macd_trend == "下降":
            score -= 15
            factors.append(f"MACD: -15 (死叉下降)")
        else:
            score -= 8
            factors.append(f"MACD: -8 (死叉)")

        # 5. 价格位置因子 (10%)
        zhongshu = structure.get('zhongshu', {}).get('latest')
        if zhongshu:
            zg = zhongshu.get('zg', 0)
            zd = zhongshu.get('zd', 0)
            gg = zhongshu.get('gg', 0)
            dd = zhongshu.get('dd', 0)

            if current_price < dd:
                score += 10
                factors.append(f"位置: +10 (低于中枢低点)")
            elif current_price < zd:
                score += 5
                factors.append(f"位置: +5 (低于中枢下沿)")
            elif current_price > gg:
                score -= 10
                factors.append(f"位置: -10 (高于中枢高点)")
            elif current_price > zg:
                score -= 5
                factors.append(f"位置: -5 (高于中枢上沿)")
            else:
                factors.append(f"位置: +0 (中枢区间内)")
        else:
            factors.append(f"位置: +0 (无中枢)")

        # 6. 市场情绪因子 (15%)
        fgi = sentiment.get('fear_greed_index', 50)
        if fgi < 25:
            score += 15
            factors.append(f"情绪: +15 (极度恐惧 {fgi})")
        elif fgi < 45:
            score += 8
            factors.append(f"情绪: +8 (恐惧 {fgi})")
        elif fgi > 75:
            score -= 15
            factors.append(f"情绪: -15 (极度贪婪 {fgi})")
        elif fgi > 55:
            score -= 8
            factors.append(f"情绪: -8 (贪婪 {fgi})")
        else:
            factors.append(f"情绪: +0 (中性 {fgi})")

        # 归一化得分到 0-100
        normalized_score = max(0, min(100, (score + 50)))

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

        # 生成止盈止损
        tp_sl = _calculate_tp_sl(
            decision=decision,
            current_price=current_price,
            structure=structure,
            dynamics=dynamics
        )

        result = {
            "status": "success",
            "decision": decision,
            "emoji": emoji,
            "score": round(normalized_score, 2),
            "confidence": confidence,
            "current_price": round(current_price, 2),
            "factors": factors,
            "summary": f"综合得分: {normalized_score:.1f}/100",
            "trading_plan": tp_sl
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        import traceback
        return json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, ensure_ascii=False)


def _calculate_tp_sl(decision: str, current_price: float, structure: dict, dynamics: dict) -> dict:
    """计算止盈止损（修复版）"""
    plan = {
        "entry": round(current_price, 2),
        "position_size": "20%",
        "take_profit": [],
        "stop_loss": [],
        "risk_reward_ratio": []
    }

    zhongshu = structure.get('zhongshu', {}).get('latest')
    fractals = structure.get('fractals', {})

    if decision in ["买入", "偏多"]:
        # 做多 - 止盈必须高于现价
        if zhongshu:
            gg = zhongshu.get('gg', 0)
            zg = zhongshu.get('zg', 0)
            if gg > current_price:
                tp1 = round(gg, 2)
                plan["take_profit"].append({"level": 1, "price": tp1, "target": "中枢高点"})
            elif zg > current_price:
                tp1 = round(zg, 2)
                plan["take_profit"].append({"level": 1, "price": tp1, "target": "中枢上沿"})
            else:
                tp1 = round(current_price * 1.02, 2)
                plan["take_profit"].append({"level": 1, "price": tp1, "target": "上涨2%"})

            # TP2: 前期高点
            latest_top = fractals.get('latest_top', {}).get('price')
            if latest_top and latest_top > current_price:
                tp2 = round(latest_top, 2)
                plan["take_profit"].append({"level": 2, "price": tp2, "target": "前期高点"})
            else:
                tp2 = round(current_price * 1.04, 2)
                plan["take_profit"].append({"level": 2, "price": tp2, "target": "上涨4%"})

            # TP3: 整数关口
            tp3 = round((int(current_price / 1000) + 3) * 1000, 2)
            plan["take_profit"].append({"level": 3, "price": tp3, "target": "整数关口"})

            # 止损：必须低于现价
            dd = zhongshu.get('dd', 0)
            zd = zhongshu.get('zd', 0)
            if dd < current_price:
                sl1 = round(dd, 2)
                plan["stop_loss"].append({"level": 1, "price": sl1, "target": "中枢低点"})
            elif zd < current_price:
                sl1 = round(zd, 2)
                plan["stop_loss"].append({"level": 1, "price": sl1, "target": "中枢下沿"})
            else:
                sl1 = round(current_price * 0.97, 2)
                plan["stop_loss"].append({"level": 1, "price": sl1, "target": "回调3%"})

            sl2 = round(current_price * 0.95, 2)
            plan["stop_loss"].append({"level": 2, "price": sl2, "target": "回调5%"})

    elif decision in ["卖出", "偏空"]:
        # 做空 - 止盈必须低于现价
        if zhongshu:
            dd = zhongshu.get('dd', 0)
            zd = zhongshu.get('zd', 0)
            if dd < current_price:
                tp1 = round(dd, 2)
                plan["take_profit"].append({"level": 1, "price": tp1, "target": "中枢低点"})
            elif zd < current_price:
                tp1 = round(zd, 2)
                plan["take_profit"].append({"level": 1, "price": tp1, "target": "中枢下沿"})
            else:
                tp1 = round(current_price * 0.98, 2)
                plan["take_profit"].append({"level": 1, "price": tp1, "target": "下跌2%"})

            latest_bottom = fractals.get('latest_bottom', {}).get('price')
            if latest_bottom and latest_bottom < current_price:
                tp2 = round(latest_bottom, 2)
                plan["take_profit"].append({"level": 2, "price": tp2, "target": "前期低点"})
            else:
                tp2 = round(current_price * 0.96, 2)
                plan["take_profit"].append({"level": 2, "price": tp2, "target": "下跌4%"})

            # 止损：必须高于现价
            gg = zhongshu.get('gg', 0)
            zg = zhongshu.get('zg', 0)
            if gg > current_price:
                sl1 = round(gg, 2)
                plan["stop_loss"].append({"level": 1, "price": sl1, "target": "中枢高点"})
            elif zg > current_price:
                sl1 = round(zg, 2)
                plan["stop_loss"].append({"level": 1, "price": sl1, "target": "中枢上沿"})
            else:
                sl1 = round(current_price * 1.03, 2)
                plan["stop_loss"].append({"level": 1, "price": sl1, "target": "反弹3%"})

    else:
        plan["take_profit"].append({"note": "观望，无止盈目标"})
        plan["stop_loss"].append({"note": "观望，无止损设置"})

    # 计算盈亏比
    if plan["take_profit"] and plan["stop_loss"]:
        tp1_price = plan["take_profit"][0].get("price", current_price)
        sl1_price = plan["stop_loss"][0].get("price", current_price)
        if decision in ["买入", "偏多"]:
            risk = current_price - sl1_price
            reward = tp1_price - current_price
        else:
            risk = sl1_price - current_price
            reward = current_price - tp1_price

        if risk > 0:
            rr_ratio = round(reward / risk, 2)
            plan["risk_reward_ratio"].append(rr_ratio)

    return plan


MAX_MESSAGES = 40

def _windowed_messages(old, new):
    return add_messages(old, new)[-MAX_MESSAGES:]

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
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
2. 使用 make_decision_v2 工具进行综合评分
3. 基于综合得分做出交易决策
4. 给出具体的操作建议（入场、止盈、止损）

# 评分体系（修复版）
- 趋势因子 (25%): 上升 +25, 下降 -25, 盘整 0
- 缠论买卖点 (20%): 一买 +20, 二买 +15, 三买 +10, 一卖 -20, 二卖 -15, 三卖 -10
- RSI因子 (15%): 超买 -15, 偏高 -8, 正常 0, 偏低 +8, 超卖 +15
- MACD因子 (15%): 金叉上升 +15, 金叉 +8, 死叉 -8, 死叉下降 -15
- 价格位置 (10%): 基于中枢计算，低于中枢低点 +10, 高于中枢高点 -10
- 市场情绪 (15%): 极度恐惧 +15, 恐惧 +8, 中性 0, 贪婪 -8, 极度贪婪 -15

# 决策标准
- 得分 >= 70: 买入
- 得分 55-69: 偏多
- 得分 46-54: 观望
- 得分 30-45: 偏空
- 得分 <= 29: 卖出

# 止盈止损规则（重要！）
- 做多：止盈必须高于现价，止损必须低于现价
- 做空：止盈必须低于现价，止损必须高于现价
- 基于中枢、分型、技术指标计算
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[make_decision_v2],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
