"""
历史决策回溯模块
记录和分析历史交易决策
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class DecisionRecord:
    """决策记录"""
    decision_id: str
    timestamp: str
    symbol: str
    interval: str

    # 决策内容
    direction: str  # long, short, neutral
    confidence: float  # 0-100
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[List[float]]
    position_size: Optional[float]
    risk_level: str  # low, medium, high

    # 分析结果
    structure_analysis: str
    dynamics_analysis: str
    sentiment_analysis: str
    cross_market_analysis: str
    onchain_analysis: str

    # 决策依据
    decision_reason: str
    key_factors: List[str]

    # 执行结果（后填充）
    executed: bool = False
    execution_time: Optional[str] = None
    actual_entry_price: Optional[float] = None

    # 交易结果（后填充）
    closed: bool = False
    close_time: Optional[str] = None
    close_price: Optional[float] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None

    # 评估
    correct: Optional[bool] = None  # 决策是否正确
    score: Optional[float] = None  # 决策评分 0-100


class DecisionHistory:
    """决策历史管理器"""

    def __init__(self):
        self.decisions: List[DecisionRecord] = []
        self.history_file: Optional[str] = None

    def load_history(self, history_file: Optional[str] = None) -> bool:
        """
        加载历史决策

        Args:
            history_file: 历史文件路径

        Returns:
            是否成功加载
        """
        if history_file is None:
            workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
            simulation_dir = os.path.join(workspace_path, "simulation")
            history_file = os.path.join(simulation_dir, "decision_history.json")

        self.history_file = history_file

        if not os.path.exists(history_file):
            # 创建空文件
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False, indent=2)
            return True

        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.decisions = [DecisionRecord(**item) for item in data]
            return True
        except Exception as e:
            print(f"加载历史失败: {str(e)}")
            return False

    def save_history(self) -> bool:
        """
        保存历史决策

        Returns:
            是否成功保存
        """
        if self.history_file is None:
            return False

        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                data = [asdict(dec) for dec in self.decisions]
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存历史失败: {str(e)}")
            return False

    def record_decision(
        self,
        symbol: str,
        interval: str,
        decision_data: Dict[str, Any],
        analysis_results: Dict[str, Any]
    ) -> DecisionRecord:
        """
        记录决策

        Args:
            symbol: 交易对
            interval: K线周期
            decision_data: 决策数据
            analysis_results: 各维度分析结果

        Returns:
            决策记录
        """
        decision_id = f"{symbol}_{interval}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # 解析决策数据（从文本中提取）
        direction = self._extract_direction(decision_data.get('agent_response', ''))
        confidence = self._extract_confidence(decision_data.get('agent_response', ''))
        entry_price = self._extract_price(decision_data.get('agent_response', ''), 'entry')
        stop_loss = self._extract_price(decision_data.get('agent_response', ''), 'stop_loss')
        take_profit = self._extract_take_profit(decision_data.get('agent_response', ''))
        position_size = self._extract_position_size(decision_data.get('agent_response', ''))
        risk_level = self._extract_risk_level(decision_data.get('agent_response', ''))

        # 提取关键因素
        key_factors = self._extract_key_factors(decision_data.get('agent_response', ''))

        # 创建决策记录
        record = DecisionRecord(
            decision_id=decision_id,
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            interval=interval,
            direction=direction,
            confidence=confidence,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            risk_level=risk_level,
            structure_analysis=analysis_results.get('structure_analysis', {}).get('agent_response', '')[:500],
            dynamics_analysis=analysis_results.get('dynamics_analysis', {}).get('agent_response', '')[:500],
            sentiment_analysis=analysis_results.get('sentiment_analysis', {}).get('agent_response', '')[:500],
            cross_market_analysis=analysis_results.get('cross_market_analysis', {}).get('agent_response', '')[:500],
            onchain_analysis=analysis_results.get('onchain_analysis', {}).get('agent_response', '')[:500],
            decision_reason=decision_data.get('agent_response', '')[:200],
            key_factors=key_factors
        )

        self.decisions.append(record)
        self.save_history()

        return record

    def update_decision_result(
        self,
        decision_id: str,
        executed: bool = False,
        actual_entry_price: Optional[float] = None,
        closed: bool = False,
        close_price: Optional[float] = None,
        pnl: Optional[float] = None,
        pnl_percent: Optional[float] = None
    ) -> bool:
        """
        更新决策结果

        Args:
            decision_id: 决策ID
            executed: 是否执行
            actual_entry_price: 实际入场价格
            closed: 是否平仓
            close_price: 平仓价格
            pnl: 盈亏金额
            pnl_percent: 盈亏百分比

        Returns:
            是否成功更新
        """
        for dec in self.decisions:
            if dec.decision_id == decision_id:
                if executed:
                    dec.executed = executed
                    dec.execution_time = datetime.now().isoformat()
                    dec.actual_entry_price = actual_entry_price

                if closed:
                    dec.closed = closed
                    dec.close_time = datetime.now().isoformat()
                    dec.close_price = close_price
                    dec.pnl = pnl
                    dec.pnl_percent = pnl_percent

                    # 评估决策
                    if pnl_percent is not None:
                        dec.correct = pnl_percent > 0
                        # 简单评分：盈利100分，亏损0分，中间按比例
                        if pnl_percent > 0:
                            dec.score = min(100, 50 + pnl_percent * 2)
                        else:
                            dec.score = max(0, 50 + pnl_percent * 2)

                self.save_history()
                return True

        return False

    def get_decision_statistics(self, last_n: int = 50) -> Dict[str, Any]:
        """
        获取决策统计

        Args:
            last_n: 统计最近N条决策

        Returns:
            统计数据
        """
        recent_decisions = self.decisions[-last_n:] if len(self.decisions) > last_n else self.decisions

        if not recent_decisions:
            return {"total": 0}

        total = len(recent_decisions)
        executed = sum(1 for d in recent_decisions if d.executed)
        closed = sum(1 for d in recent_decisions if d.closed)

        # 方向统计
        long_count = sum(1 for d in recent_decisions if d.direction == 'long')
        short_count = sum(1 for d in recent_decisions if d.direction == 'short')
        neutral_count = sum(1 for d in recent_decisions if d.direction == 'neutral')

        # 盈亏统计
        profit_count = sum(1 for d in recent_decisions if d.pnl and d.pnl > 0)
        loss_count = sum(1 for d in recent_decisions if d.pnl and d.pnl < 0)

        total_pnl = sum(d.pnl for d in recent_decisions if d.pnl is not None)
        avg_pnl = total_pnl / closed if closed > 0 else 0

        # 胜率
        win_rate = (profit_count / closed * 100) if closed > 0 else 0

        # 平均置信度
        avg_confidence = sum(d.confidence for d in recent_decisions) / total if total > 0 else 0

        return {
            "total": total,
            "executed": executed,
            "closed": closed,
            "direction": {
                "long": long_count,
                "short": short_count,
                "neutral": neutral_count
            },
            "pnl": {
                "profit_count": profit_count,
                "loss_count": loss_count,
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(avg_pnl, 2),
                "win_rate": round(win_rate, 2)
            },
            "avg_confidence": round(avg_confidence, 2)
        }

    def get_decision_by_id(self, decision_id: str) -> Optional[DecisionRecord]:
        """
        根据ID获取决策

        Args:
            decision_id: 决策ID

        Returns:
            决策记录
        """
        for dec in self.decisions:
            if dec.decision_id == decision_id:
                return dec
        return None

    def get_recent_decisions(self, n: int = 10) -> List[DecisionRecord]:
        """
        获取最近的决策

        Args:
            n: 数量

        Returns:
            决策列表
        """
        return self.decisions[-n:] if len(self.decisions) > n else self.decisions

    def generate_decision_report(self, last_n: int = 20) -> str:
        """
        生成决策报告

        Args:
            last_n: 报告包含最近N条决策

        Returns:
            Markdown格式的报告
        """
        stats = self.get_decision_statistics(last_n)
        recent_decisions = self.get_recent_decisions(last_n)

        lines = []
        lines.append("# 历史决策回溯报告")
        lines.append("")
        lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**统计范围**: 最近{last_n}条决策")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 统计摘要
        lines.append("## 决策统计")
        lines.append("")
        lines.append(f"- **总决策数**: {stats['total']}")
        lines.append(f"- **已执行**: {stats['executed']}")
        lines.append(f"- **已平仓**: {stats['closed']}")
        lines.append("")
        lines.append("### 方向分布")
        lines.append(f"- **做多**: {stats['direction']['long']}")
        lines.append(f"- **做空**: {stats['direction']['short']}")
        lines.append(f"- **观望**: {stats['direction']['neutral']}")
        lines.append("")
        lines.append("### 盈亏统计")
        lines.append(f"- **盈利次数**: {stats['pnl']['profit_count']}")
        lines.append(f"- **亏损次数**: {stats['pnl']['loss_count']}")
        lines.append(f"- **总盈亏**: {stats['pnl']['total_pnl']}")
        lines.append(f"- **平均盈亏**: {stats['pnl']['avg_pnl']}")
        lines.append(f"- **胜率**: {stats['pnl']['win_rate']}%")
        lines.append("")
        lines.append(f"### 平均置信度")
        lines.append(f"- **置信度**: {stats['avg_confidence']}%")
        lines.append("")
        lines.append("---")
        lines.append("")

        # 最近决策
        lines.append("## 最近决策")
        lines.append("")

        for i, dec in enumerate(reversed(recent_decisions), 1):
            lines.append(f"### 决策 {i}")
            lines.append(f"- **时间**: {dec.timestamp}")
            lines.append(f"- **方向**: {dec.direction}")
            lines.append(f"- **置信度**: {dec.confidence}%")
            lines.append(f"- **入场价格**: {dec.entry_price}")
            lines.append(f"- **止损**: {dec.stop_loss}")
            lines.append(f"- **止盈**: {dec.take_profit}")
            lines.append(f"- **仓位**: {dec.position_size}")
            lines.append(f"- **风险等级**: {dec.risk_level}")
            lines.append(f"- **执行**: {'是' if dec.executed else '否'}")
            lines.append(f"- **平仓**: {'是' if dec.closed else '否'}")

            if dec.closed:
                lines.append(f"- **平仓价格**: {dec.close_price}")
                lines.append(f"- **盈亏**: {dec.pnl}")
                lines.append(f"- **盈亏%**: {dec.pnl_percent}%")
                lines.append(f"- **正确**: {'是' if dec.correct else '否'}")
                lines.append(f"- **评分**: {dec.score}")

            lines.append("")

        return "\n".join(lines)

    def _extract_direction(self, text: str) -> str:
        """从文本中提取方向"""
        text_lower = text.lower()
        if '做多' in text_lower or 'long' in text_lower or '买入' in text_lower:
            return 'long'
        elif '做空' in text_lower or 'short' in text_lower or '卖出' in text_lower:
            return 'short'
        else:
            return 'neutral'

    def _extract_confidence(self, text: str) -> float:
        """从文本中提取置信度"""
        import re
        match = re.search(r'置信度[：:]\s*(\d+)%', text)
        if match:
            return float(match.group(1))
        return 50.0  # 默认值

    def _extract_price(self, text: str, price_type: str) -> Optional[float]:
        """从文本中提取价格"""
        import re
        if price_type == 'entry':
            pattern = r'入场[价格]?[：:]\s*(\d+\.?\d*)'
        elif price_type == 'stop_loss':
            pattern = r'止损[价格]?[：:]\s*(\d+\.?\d*)'
        else:
            return None

        match = re.search(pattern, text)
        if match:
            return float(match.group(1))
        return None

    def _extract_take_profit(self, text: str) -> Optional[List[float]]:
        """从文本中提取止盈价格"""
        import re
        matches = re.findall(r'止盈[价格]?[：:]\s*(\d+\.?\d*)', text)
        if matches:
            return [float(m) for m in matches]
        return None

    def _extract_position_size(self, text: str) -> Optional[float]:
        """从文本中提取仓位"""
        import re
        match = re.search(r'仓位[：:]\s*(\d+\.?\d*)%', text)
        if match:
            return float(match.group(1))
        return None

    def _extract_risk_level(self, text: str) -> str:
        """从文本中提取风险等级"""
        text_lower = text.lower()
        if '高' in text_lower or 'high' in text_lower:
            return 'high'
        elif '低' in text_lower or 'low' in text_lower:
            return 'low'
        else:
            return 'medium'

    def _extract_key_factors(self, text: str) -> List[str]:
        """从文本中提取关键因素"""
        import re
        factors = []

        # 简单提取关键因素
        patterns = [
            r'结构.*?(?=，|。|$)',
            r'背驰.*?(?=，|。|$)',
            r'共振.*?(?=，|。|$)',
            r'突破.*?(?=，|。|$)',
            r'支撑.*?(?=，|。|$)',
            r'阻力.*?(?=，|。|$)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            factors.extend(matches)

        return list(set(factors[:5]))  # 最多返回5个关键因素


# 全局实例
_decision_history = DecisionHistory()
_decision_history.load_history()


def record_decision(
    symbol: str,
    interval: str,
    decision_data: Dict[str, Any],
    analysis_results: Dict[str, Any]
) -> DecisionRecord:
    """
    记录决策的快捷函数

    Args:
        symbol: 交易对
        interval: K线周期
        decision_data: 决策数据
        analysis_results: 各维度分析结果

    Returns:
        决策记录
    """
    return _decision_history.record_decision(symbol, interval, decision_data, analysis_results)


def get_decision_statistics(last_n: int = 50) -> Dict[str, Any]:
    """
    获取决策统计的快捷函数

    Args:
        last_n: 统计最近N条决策

    Returns:
        统计数据
    """
    return _decision_history.get_decision_statistics(last_n)


def generate_decision_report(last_n: int = 20) -> str:
    """
    生成决策报告的快捷函数

    Args:
        last_n: 报告包含最近N条决策

    Returns:
        Markdown格式的报告
    """
    return _decision_history.generate_decision_report(last_n)
