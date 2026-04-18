"""
研报生成模块
生成Markdown格式的缠论分析研报
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ReportSection:
    """研报章节"""
    title: str
    content: str
    importance: str = "normal"  # high, normal, low


class ReportGenerator:
    """研报生成器"""

    def __init__(self):
        self.sections: list[ReportSection] = []

    def add_section(self, title: str, content: str, importance: str = "normal"):
        """添加章节"""
        self.sections.append(ReportSection(title, content, importance))

    def generate_markdown(self, save_path: Optional[str] = None) -> str:
        """
        生成Markdown格式的研报

        Args:
            save_path: 保存路径（可选）

        Returns:
            Markdown格式的研报
        """
        lines = []

        # 标题
        lines.append("# 缠论技术分析研报")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**分析师**: 缠论多智能体分析系统")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 目录
        lines.append("## 目录")
        lines.append("")
        for i, section in enumerate(self.sections, 1):
            marker = "⭐" if section.importance == "high" else ""
            lines.append(f"{i}. [{section.title}](#{section.title.replace(' ', '-')}) {marker}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 各章节内容
        for section in self.sections:
            lines.append(f"## {section.title}")
            if section.importance == "high":
                lines.append("⭐ **重点关注**")
            lines.append("")
            lines.append(section.content)
            lines.append("")
            lines.append("---")
            lines.append("")

        # 免责声明
        lines.append("## 免责声明")
        lines.append("")
        lines.append("""
本报告基于缠论理论体系和多智能体分析系统生成，仅供参考，不构成投资建议。

**风险提示**：
- 数字货币交易风险极高，价格波动剧烈
- 技术分析仅供参考，不保证准确性
- 请根据自身风险承受能力谨慎决策
- 建议在模拟盘充分验证后再考虑实盘
- 严格控制风险，合理分配仓位
""")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**报告结束**")

        markdown_content = "\n".join(lines)

        # 保存到文件
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

        return markdown_content

    def generate_summary_report(
        self,
        symbol: str,
        interval: str,
        structure_data: Dict[str, Any],
        dynamics_data: Dict[str, Any],
        sentiment_data: Dict[str, Any],
        cross_market_data: Dict[str, Any],
        onchain_data: Dict[str, Any],
        decision_data: Dict[str, Any],
        save_path: Optional[str] = None
    ) -> str:
        """
        生成综合研报

        Args:
            symbol: 交易对
            interval: K线周期
            structure_data: 结构分析数据
            dynamics_data: 动力学分析数据
            sentiment_data: 市场情绪数据
            cross_market_data: 跨市场数据
            onchain_data: 链上数据
            decision_data: 决策数据
            save_path: 保存路径

        Returns:
            Markdown格式的研报
        """
        self.sections = []

        # 1. 核心摘要
        self._add_summary_section(symbol, interval, decision_data)

        # 2. 结构分析
        self._add_structure_section(structure_data)

        # 3. 动力学分析
        self._add_dynamics_section(dynamics_data)

        # 4. 市场情绪
        self._add_sentiment_section(sentiment_data)

        # 5. 跨市场分析
        self._add_cross_market_section(cross_market_data)

        # 6. 链上数据
        self._add_onchain_section(onchain_data)

        # 7. 交易决策
        self._add_decision_section(decision_data)

        # 8. 风险提示
        self._add_risk_section()

        # 生成Markdown
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        reports_dir = os.path.join(workspace_path, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        if save_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_path = os.path.join(reports_dir, f"{symbol}_{interval}_{timestamp}.md")

        return self.generate_markdown(save_path)

    def _add_summary_section(self, symbol: str, interval: str, decision_data: Dict[str, Any]):
        """添加核心摘要章节"""
        content = f"""
### 基本信息
- **交易对**: {symbol}
- **分析周期**: {interval}
- **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### 核心观点
{decision_data.get('agent_response', '无决策数据')[:500]}...

### 关键指标
请参考以下各章节的详细分析。
"""
        self.add_section("核心摘要", content, "high")

    def _add_structure_section(self, structure_data: Dict[str, Any]):
        """添加结构分析章节"""
        content = f"""
### 结构统计
{structure_data.get('agent_response', '无结构分析数据')[:800]}

### 结构判断
- **走势类型**: 根据笔线段中枢判断
- **完成度**: 分析走势完成程度
- **关键点位**: 支撑位和阻力位
"""
        self.add_section("结构分析", content, "high")

    def _add_dynamics_section(self, dynamics_data: Dict[str, Any]):
        """添加动力学分析章节"""
        content = f"""
### MACD指标
{dynamics_data.get('agent_response', '无动力学分析数据')[:800]}

### 背驰信号
- **顶背驰**: 是否存在顶背驰
- **底背驰**: 是否存在底背驰
- **背驰强度**: 强背驰/弱背驰

### 动量分析
- **市场动量**: 动量强弱判断
- **趋势方向**: 上涨/下跌/盘整
"""
        self.add_section("动力学分析", content, "high")

    def _add_sentiment_section(self, sentiment_data: Dict[str, Any]):
        """添加市场情绪章节"""
        content = f"""
### 恐慌贪婪指数
{sentiment_data.get('agent_response', '无情绪分析数据')[:600]}

### 资金费率
- **费率水平**: 正费率/负费率/零费率
- **市场含义**: 多头强/空头强/平衡

### 爆仓数据
- **爆仓情况**: 多单vs空单爆仓
- **市场影响**: 对价格的影响
"""
        self.add_section("市场情绪", content, "normal")

    def _add_cross_market_section(self, cross_market_data: Dict[str, Any]):
        """添加跨市场分析章节"""
        content = f"""
### 美股市场
{cross_market_data.get('agent_response', '无跨市场分析数据')[:600]}

### 黄金市场
- **黄金价格**: 当前价格和走势
- **与BTC关系**: 避险属性

### 美元指数
- **DXY走势**: 美元指数变化
- **与BTC关系**: 负相关性

### 综合判断
跨市场整体影响：利好/利空/中性
"""
        self.add_section("跨市场联动", content, "normal")

    def _add_onchain_section(self, onchain_data: Dict[str, Any]):
        """添加链上数据章节"""
        content = f"""
### 交易所流入流出
{onchain_data.get('agent_response', '无链上数据')[:600]}

### 巨鲸活动
- **巨鲸动向**: 买入/卖出信号
- **影响程度**: 对市场的影响

### 网络健康
- **活跃地址**: 地址数量和变化
- **网络状态**: 拥堵/畅通

### 算力难度
- **算力变化**: 增加或减少
- **挖矿活跃度**: 挖矿状况
"""
        self.add_section("链上数据", content, "normal")

    def _add_decision_section(self, decision_data: Dict[str, Any]):
        """添加交易决策章节"""
        content = f"""
### 交易决策
{decision_data.get('agent_response', '无决策数据')}

### 操作建议
- **交易方向**: 做多/做空/观望
- **入场价格**: 建议入场价位
- **止损价格**: 止损价位
- **止盈目标**: 目标价位
- **建议仓位**: 建议仓位大小
- **风险等级**: 高/中/低
- **置信度**: 决策置信度

### 注意事项
- 严格执行止损
- 控制仓位大小
- 多维度信号确认
- 模拟盘验证后再实盘
"""
        self.add_section("交易决策", content, "high")

    def _add_risk_section(self):
        """添加风险提示章节"""
        content = """
### 技术风险
- 技术分析仅供参考
- 市场可能出现突发变化
- 信号可能失效

### 市场风险
- 价格波动剧烈
- 流动性风险
- 监管政策风险

### 操作风险
- 止损执行不及时
- 仓位控制不当
- 情绪化交易

### 风控建议
1. 单笔交易不超过总资金的20%
2. 严格设置止损，及时止损
3. 避免追涨杀跌
4. 保持理性，不受情绪影响
5. 模拟盘验证后再实盘
6. 持续学习和优化策略
"""
        self.add_section("风险提示", content, "high")


# 全局实例
_report_generator = ReportGenerator()


def generate_report(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    structure_data: Optional[Dict[str, Any]] = None,
    dynamics_data: Optional[Dict[str, Any]] = None,
    sentiment_data: Optional[Dict[str, Any]] = None,
    cross_market_data: Optional[Dict[str, Any]] = None,
    onchain_data: Optional[Dict[str, Any]] = None,
    decision_data: Optional[Dict[str, Any]] = None,
    save_path: Optional[str] = None
) -> str:
    """
    生成研报告捷函数

    Args:
        symbol: 交易对
        interval: K线周期
        structure_data: 结构分析数据
        dynamics_data: 动力学分析数据
        sentiment_data: 市场情绪数据
        cross_market_data: 跨市场数据
        onchain_data: 链上数据
        decision_data: 决策数据
        save_path: 保存路径

    Returns:
        研报内容和保存路径
    """
    # 使用默认值
    if structure_data is None:
        structure_data = {"agent_response": "暂无数据"}
    if dynamics_data is None:
        dynamics_data = {"agent_response": "暂无数据"}
    if sentiment_data is None:
        sentiment_data = {"agent_response": "暂无数据"}
    if cross_market_data is None:
        cross_market_data = {"agent_response": "暂无数据"}
    if onchain_data is None:
        onchain_data = {"agent_response": "暂无数据"}
    if decision_data is None:
        decision_data = {"agent_response": "暂无数据"}

    # 生成研报
    markdown_content = _report_generator.generate_summary_report(
        symbol=symbol,
        interval=interval,
        structure_data=structure_data,
        dynamics_data=dynamics_data,
        sentiment_data=sentiment_data,
        cross_market_data=cross_market_data,
        onchain_data=onchain_data,
        decision_data=decision_data,
        save_path=save_path
    )

    # 获取保存路径
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    reports_dir = os.path.join(workspace_path, "reports")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    default_save_path = os.path.join(reports_dir, f"{symbol}_{interval}_{timestamp}.md")

    return {
        "content": markdown_content,
        "save_path": save_path or default_save_path,
        "timestamp": datetime.now().isoformat()
    }
