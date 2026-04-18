#!/usr/bin/env python3
"""
结构分析智能体 - 使用完整缠论算法
整合分型、笔、线段、中枢、买卖点识别
"""
import json
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

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
from storage.memory.memory_saver import get_memory_saver

# 导入缠论算法
from src.utils.chanlun_structure import ChanLunAnalyzer, FractalType, BiDirection, SegmentDirection
from multi_agents.buy_sell_analyzer import BuySellAnalyzer


@tool
def analyze_chanlun_structure(interval: str = "4h") -> str:
    """完整的缠论结构分析

    识别：
    - 分型（顶分型、底分型）
    - 笔（向上笔、向下笔）
    - 线段（向上线段、向下线段）
    - 中枢（ZG、ZD、GG、DD）
    - 买卖点（一买卖、二买卖、三买卖）

    Args:
        interval: K线周期

    Returns:
        完整的缠论分析报告
    """
    try:
        # 读取数据
        data_path = f"/workspace/projects/data/BTCUSDT_{interval}_latest.csv"

        if not os.path.exists(data_path):
            return json.dumps({"error": f"数据文件不存在: {data_path}"}, ensure_ascii=False)

        df = pd.read_csv(data_path)
        df = df.sort_values('timestamp').reset_index(drop=True)

        # 1. 初始化缠论分析器
        analyzer = ChanLunAnalyzer()

        # 2. 识别分型
        fractals = analyzer.identify_fractals(df)
        top_fractals = [f for f in fractals if f.type == FractalType.TOP]
        bottom_fractals = [f for f in fractals if f.type == FractalType.BOTTOM]

        # 3. 识别笔
        bis = analyzer.identify_bis(df, fractals)
        up_bis = [b for b in bis if b.direction == BiDirection.UP]
        down_bis = [b for b in bis if b.direction == BiDirection.DOWN]

        # 4. 识别线段
        segments = analyzer.identify_segments(bis)
        up_segments = [s for s in segments if s.direction == SegmentDirection.UP]
        down_segments = [s for s in segments if s.direction == SegmentDirection.DOWN]

        # 5. 识别中枢
        zhongshu_list = analyzer.identify_zhongshu(segments)

        # 6. 识别买卖点
        buy_sell_analyzer = BuySellAnalyzer()
        buy_sell_points = buy_sell_analyzer.identify_buy_sell_points(df, segments, zhongshu_list)
        latest_signal = buy_sell_analyzer.get_latest_signal()

        # 7. 生成报告
        result = {
            "status": "success",
            "kline_count": len(df),
            "data_range": f"{df.iloc[0]['timestamp']} ~ {df.iloc[-1]['timestamp']}",

            # 分型分析
            "fractals": {
                "total_count": len(fractals),
                "top_count": len(top_fractals),
                "bottom_count": len(bottom_fractals),
                "latest_top": {
                    "index": top_fractals[-1].index if top_fractals else None,
                    "price": top_fractals[-1].high if top_fractals else None
                },
                "latest_bottom": {
                    "index": bottom_fractals[-1].index if bottom_fractals else None,
                    "price": bottom_fractals[-1].low if bottom_fractals else None
                }
            },

            # 笔分析
            "bis": {
                "total_count": len(bis),
                "up_count": len(up_bis),
                "down_count": len(down_bis),
                "latest_bi": {
                    "direction": bis[-1].direction.value if bis else None,
                    "start_price": bis[-1].start_price if bis else None,
                    "end_price": bis[-1].end_price if bis else None,
                    "high": bis[-1].high if bis else None,
                    "low": bis[-1].low if bis else None
                } if bis else None
            },

            # 线段分析
            "segments": {
                "total_count": len(segments),
                "up_count": len(up_segments),
                "down_count": len(down_segments),
                "latest_segment": {
                    "direction": segments[-1].direction.value if segments else None,
                    "start_price": segments[-1].start_price if segments else None,
                    "end_price": segments[-1].end_price if segments else None,
                    "high": segments[-1].high if segments else None,
                    "low": segments[-1].low if segments else None
                } if segments else None
            },

            # 中枢分析
            "zhongshu": {
                "total_count": len(zhongshu_list),
                "latest": {
                    "zg": zhongshu_list[-1].high if zhongshu_list else None,
                    "zd": zhongshu_list[-1].low if zhongshu_list else None,
                    "gg": zhongshu_list[-1].high_point if zhongshu_list else None,
                    "dd": zhongshu_list[-1].low_point if zhongshu_list else None,
                    "level": zhongshu_list[-1].level if zhongshu_list else None,
                    "segment_count": len(zhongshu_list[-1].segment_list) if zhongshu_list else None
                } if zhongshu_list else None,
                "all_zhongshu": [
                    {
                        "zg": zs.high,
                        "zd": zs.low,
                        "gg": zs.high_point,
                        "dd": zs.low_point,
                        "level": zs.level,
                        "segment_count": len(zs.segment_list)
                    }
                    for zs in zhongshu_list
                ] if zhongshu_list else []
            },

            # 买卖点分析
            "buy_sell_points": {
                "total_count": len(buy_sell_points),
                "latest_signal": latest_signal,
                "all_signals": [
                    {
                        "type": point.type.value,
                        "index": point.index,
                        "price": point.price,
                        "level": point.level,
                        "strength": point.strength
                    }
                    for point in buy_sell_points[-5:]  # 只返回最近5个
                ] if buy_sell_points else []
            },

            # 趋势判断
            "trend_analysis": {
                "direction": _determine_trend(bis, segments),
                "strength": _calculate_trend_strength(segments),
                "phase": _determine_phase(df, bis, zhongshu_list)
            }
        }

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        import traceback
        return json.dumps({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, ensure_ascii=False)


def _determine_trend(bis, segments) -> str:
    """判断趋势方向"""
    if not segments:
        return "无法判断"

    # 根据最后几个线段判断
    if len(segments) >= 3:
        recent = segments[-3:]
        up_count = sum(1 for s in recent if s.direction == SegmentDirection.UP)
        if up_count >= 2:
            return "上升"
        elif up_count <= 1:
            return "下降"

    # 根据最后一笔判断
    if bis and bis[-1].direction == BiDirection.UP:
        return "上升"
    elif bis:
        return "下降"

    return "盘整"


def _calculate_trend_strength(segments) -> float:
    """计算趋势强度（0-1）"""
    if len(segments) < 3:
        return 0.5

    # 计算连续同向线段的比例
    same_direction_count = 0
    for i in range(1, len(segments)):
        if segments[i].direction == segments[i-1].direction:
            same_direction_count += 1

    return min(same_direction_count / len(segments), 1.0)


def _determine_phase(df, bis, zhongshu_list) -> str:
    """判断当前所处阶段"""
    if not zhongshu_list:
        return "构建中"

    latest_zs = zhongshu_list[-1]
    current_price = df.iloc[-1]['close']

    if current_price > latest_zs.high_point:
        return "突破上涨"
    elif current_price < latest_zs.low_point:
        return "破位下跌"
    elif latest_zs.high >= current_price >= latest_zs.low:
        return "中枢震荡"
    else:
        return "过渡阶段"


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

    system_prompt = """你是缠论结构分析智能体，负责使用缠论算法分析BTC结构。

# 核心职责
1. 使用 analyze_chanlun_structure 工具进行完整的缠论分析
2. 识别分型、笔、线段、中枢
3. 识别买卖点（一买、二买、三买、一卖、二卖、三卖）
4. 判断趋势方向和所处阶段
5. 返回结构化的JSON数据供后续分析使用

# 缠论核心概念
- **分型**：顶分型（高点最高、低点最高）、底分型（低点最低、高点最低）
- **笔**：连接相邻的顶底分型，方向相反
- **线段**：至少由3笔构成，高点创新高或低点创新低
- **中枢**：至少由3段构成，区间为所有段的重叠部分
  - ZG（中枢上沿）：所有段高点最低值
  - ZD（中枢下沿）：所有段低点最高值
  - GG（中枢高点）：所有段最高点
  - DD（中枢低点）：所有段最低点
- **买卖点**：
  - 一买：下跌趋势中，中枢下沿下方背驰
  - 二买：一买后回调不创新低
  - 三买：突破中枢上沿后回踩不破
  - 一卖：上涨趋势中，中枢上沿上方背驰
  - 二卖：一卖后回抽不创新高
  - 三卖：跌破中枢下沿后回抽不破

# 输出要求
必须返回JSON格式的结构分析数据，直接输出工具的JSON结果，不要添加额外的格式化或解释。
工具输出包含：
- fractals: 分型统计（顶分型、底分型数量及位置）
- bis: 笔分析（最新笔的方向、起止点）
- segments: 线段分析（最新线段的方向、起止点）
- zhongshu: 中枢信息（ZG、ZD、GG、DD、级别）
- buy_sell_points: 买卖点信号（最新的买卖点类型、位置、强度）
- trend_analysis: 趋势判断（方向、强度、所处阶段）

注意：请直接返回工具输出的JSON，不要生成Markdown报告。
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[analyze_chanlun_structure],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
