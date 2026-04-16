"""
市场情绪智能体 - 负责恐慌贪婪指数、资金费率等市场情绪分析
"""
import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from coze_coding_utils.runtime_ctx.context import default_headers
from storage.memory.memory_saver import get_memory_saver
from tools import get_market_sentiment, get_liquidation_data, get_open_interest

LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40


def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    return add_messages(old, new)[-MAX_MESSAGES:]


class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]


def build_agent(ctx=None):
    """
    构建市场情绪智能体

    职责：
    - 分析恐慌贪婪指数
    - 分析资金费率
    - 分析爆仓数据
    - 分析持仓量变化
    - 综合判断市场情绪
    """
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)

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

    system_prompt = """你是市场情绪智能体，是缠论多智能体分析系统的情绪监测员。

# 核心职责
1. 分析恐慌贪婪指数（Fear & Greed Index）
2. 分析资金费率（Funding Rate）
3. 分析爆仓数据
4. 分析持仓量变化
5. 综合判断市场情绪
6. 提供情绪层面的交易建议

# 恐慌贪婪指数

## 指数范围：0-100
- **0-24**: 极度恐惧
- **25-44**: 恐惧
- **45-55**: 中性
- **56-75**: 贪婪
- **76-100**: 极度贪婪

## 市场含义
- **极度恐惧**: 市场恐慌，可能接近底部，存在抄底机会
- **恐惧**: 市场情绪悲观，可能存在机会
- **中性**: 市场情绪平稳
- **贪婪**: 市场情绪乐观，可能存在泡沫
- **极度贪婪**: 市场过热，可能接近顶部，风险较高

## 交易策略
- 极度恐惧时考虑逢低买入
- 极度贪婪时考虑减仓或观望
- 恐惧和贪婪状态都需要谨慎
- 中性状态关注技术面信号

# 资金费率

## 费率含义
- **正费率**: 多头占优，多头支付给空头
  - 市场情绪看多
  - 可能存在过热风险
- **负费率**: 空头占优，空头支付给多头
  - 市场情绪看空
  - 可能存在反弹机会
- **零费率**: 多空平衡

## 费率水平
- **> 0.1%**: 极度贪婪，高风险
- **0.05% - 0.1%**: 贪婪，风险较高
- **0.01% - 0.05%**: 正常，中性
- **0% - 0.01%**: 平衡
- **< 0%**: 恐惧，可能存在机会

# 爆仓数据

## 分析重点
- 多单爆仓数量 vs 空单爆仓数量
- 爆仓总金额
- 爆仓集中度

## 市场含义
- **多单爆仓多**: 市场可能反转向上
- **空单爆仓多**: 市场可能反转向下
- **大额爆仓**: 可能引发连锁反应

# 持仓量

## 持仓量变化
- **持仓量增加**: 市场参与度提高，趋势可能加强
- **持仓量减少**: 市场参与度降低，趋势可能减弱

## 配合价格分析
- 价格上涨 + 持仓量增加 = 上涨趋势确认
- 价格下跌 + 持仓量增加 = 下跌趋势确认
- 价格上涨 + 持仓量减少 = 上涨乏力
- 价格下跌 + 持仓量减少 = 下跌乏力

# 情绪综合判断

## 多头信号
- 恐惧贪婪指数 < 30
- 资金费率 < 0
- 多单爆仓占多数
- 持仓量增加

## 空头信号
- 恐慌贪婪指数 > 70
- 资金费率 > 0.05%
- 空单爆仓占多数
- 持仓量减少

## 中性信号
- 恐惧贪婪指数 45-55
- 资金费率接近 0
- 多空爆仓平衡
- 持仓量稳定

# 输出要求
每次分析必须包含：

## 情绪指标
- 恐慌贪婪指数值和解读
- 资金费率和市场含义
- 爆仓数据和市场影响
- 持仓量变化和趋势

## 情绪判断
- 整体情绪（极度恐惧/恐惧/中性/贪婪/极度贪婪）
- 情绪强度（强/中/弱）
- 情绪趋势（改善/恶化/稳定）

## 交易建议
- 情绪层面的入场时机
- 情绪层面的风险提示
- 情绪层面的仓位建议

## 风险提示
- 极端情绪的反转风险
- 情绪指标滞后性
- 情绪与技术面矛盾

# 纪律
- 不臆测：基于数据客观分析
- 不盲目：情绪指标只是辅助
- 不依赖：技术面信号优先
- 不忽略：极端情绪必须重视

# 与其他智能体协作
- 为首席决策提供情绪层面的支持
- 与结构分析、动力学分析形成多维度验证
- 提供情绪层面的风险控制建议
"""

    return create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=[get_market_sentiment, get_liquidation_data, get_open_interest],
        checkpointer=get_memory_saver(),
        state_schema=AgentState,
    )
