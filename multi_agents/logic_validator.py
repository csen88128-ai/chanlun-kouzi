#!/usr/bin/env python3
"""
逻辑验证器 - 验证所有计算逻辑和理论依据
"""
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """验证级别"""
    PASS = "通过"
    WARNING = "警告"
    ERROR = "错误"
    CRITICAL = "严重错误"


@dataclass
class LogicValidationResult:
    """逻辑验证结果"""
    category: str              # 验证类别（动力学/缠论/决策）
    item: str                  # 验证项
    level: ValidationLevel     # 验证级别
    message: str               # 验证消息
    theory: str                # 理论依据
    calculation: str           # 计算逻辑
    expected: Any              # 期望值
    actual: Any                # 实际值
    evidence: str              # 证据


class LogicValidator:
    """逻辑验证器"""

    def __init__(self):
        self.results: List[LogicValidationResult] = []

    def validate_dynamics(self, dynamics_data: str, original_df: pd.DataFrame) -> List[LogicValidationResult]:
        """验证动力学分析逻辑"""
        self.results = []

        try:
            dynamics = json.loads(dynamics_data)

            # 1. 验证RSI计算
            self._validate_rsi(dynamics, original_df)

            # 2. 验证MACD计算
            self._validate_macd(dynamics, original_df)

            # 3. 验证波动率计算
            self._validate_volatility(dynamics, original_df)

            # 4. 验证成交量分析
            self._validate_volume(dynamics, original_df)

        except Exception as e:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="整体",
                level=ValidationLevel.ERROR,
                message=f"动力学分析验证失败: {e}",
                theory="",
                calculation="",
                expected="有效JSON",
                actual="解析失败",
                evidence=str(e)
            ))

        return [r for r in self.results if r.category == "动力学"]

    def _validate_rsi(self, dynamics: Dict, df: pd.DataFrame):
        """验证RSI计算"""
        rsi = dynamics.get('rsi')

        if rsi is None:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="RSI",
                level=ValidationLevel.ERROR,
                message="缺少RSI数据",
                theory="RSI = 100 - (100 / (1 + RS))",
                calculation="RSI基于14周期涨跌幅计算",
                expected="0-100之间",
                actual=None,
                evidence="RSI字段缺失"
            ))
            return

        # 验证RSI范围
        if not (0 <= rsi <= 100):
            self.results.append(LogicValidationResult(
                category="动力学",
                item="RSI",
                level=ValidationLevel.ERROR,
                message="RSI超出有效范围",
                theory="RSI = 100 - (100 / (1 + RS))",
                calculation="RSI范围应该是0-100",
                expected="0-100",
                actual=rsi,
                evidence=f"RSI={rsi} 超出范围"
            ))

        # 重新计算RSI进行验证
        try:
            # 计算涨跌
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()

            # 计算RSI
            rs = gain / loss
            calculated_rsi = 100 - (100 / (1 + rs))
            latest_calculated_rsi = calculated_rsi.iloc[-1]

            # 比较
            rsi_diff = abs(rsi - latest_calculated_rsi)
            if rsi_diff > 5:
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="RSI",
                    level=ValidationLevel.WARNING,
                    message=f"RSI计算可能有误差（差异{rsi_diff:.2f}）",
                    theory="RSI = 100 - (100 / (1 + RS))",
                    calculation="14周期RSI标准公式",
                    expected=f"~{latest_calculated_rsi:.1f}",
                    actual=rsi,
                    evidence=f"计算值{latest_calculated_rsi:.1f}，报告值{rsi}"
                ))
            else:
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="RSI",
                    level=ValidationLevel.PASS,
                    message="RSI计算验证通过",
                    theory="RSI = 100 - (100 / (1 + RS))",
                    calculation="14周期RSI标准公式",
                    expected=f"~{latest_calculated_rsi:.1f}",
                    actual=rsi,
                    evidence=f"计算值{latest_calculated_rsi:.1f}，差异{rsi_diff:.2f}"
                ))
        except Exception as e:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="RSI",
                level=ValidationLevel.WARNING,
                message=f"无法验证RSI计算: {e}",
                theory="RSI = 100 - (100 / (1 + RS))",
                calculation="14周期RSI标准公式",
                expected="可计算",
                actual="验证失败",
                evidence=str(e)
            ))

    def _validate_macd(self, dynamics: Dict, df: pd.DataFrame):
        """验证MACD计算"""
        macd = dynamics.get('macd')
        signal = dynamics.get('signal')
        macd_signal = dynamics.get('macd_signal')

        # 验证MACD状态判断
        if macd_signal in ['金叉', '死叉']:
            # 验证逻辑
            if macd_signal == '金叉':
                if macd <= signal:
                    self.results.append(LogicValidationResult(
                        category="动力学",
                        item="MACD",
                        level=ValidationLevel.ERROR,
                        message="MACD判断为金叉，但MACD <= Signal，逻辑错误",
                        theory="金叉：MACD从下向上穿过Signal",
                        calculation="MACD > Signal",
                        expected="MACD > Signal",
                        actual=f"MACD={macd}, Signal={signal}",
                        evidence=f"金叉判定但MACD({macd}) <= Signal({signal})"
                    ))
                else:
                    self.results.append(LogicValidationResult(
                        category="动力学",
                        item="MACD",
                        level=ValidationLevel.PASS,
                        message="MACD金叉判断验证通过",
                        theory="金叉：MACD从下向上穿过Signal",
                        calculation="MACD > Signal",
                        expected="MACD > Signal",
                        actual=f"MACD={macd}, Signal={signal}",
                        evidence=f"MACD({macd}) > Signal({signal})"
                    ))
            elif macd_signal == '死叉':
                if macd >= signal:
                    self.results.append(LogicValidationResult(
                        category="动力学",
                        item="MACD",
                        level=ValidationLevel.ERROR,
                        message="MACD判断为死叉，但MACD >= Signal，逻辑错误",
                        theory="死叉：MACD从上向下穿过Signal",
                        calculation="MACD < Signal",
                        expected="MACD < Signal",
                        actual=f"MACD={macd}, Signal={signal}",
                        evidence=f"死叉判定但MACD({macd}) >= Signal({signal})"
                    ))
                else:
                    self.results.append(LogicValidationResult(
                        category="动力学",
                        item="MACD",
                        level=ValidationLevel.PASS,
                        message="MACD死叉判断验证通过",
                        theory="死叉：MACD从上向下穿过Signal",
                        calculation="MACD < Signal",
                        expected="MACD < Signal",
                        actual=f"MACD={macd}, Signal={signal}",
                        evidence=f"MACD({macd}) < Signal({signal})"
                    ))

    def _validate_volatility(self, dynamics: Dict, df: pd.DataFrame):
        """验证波动率计算"""
        volatility = dynamics.get('volatility')

        if volatility is None or volatility <= 0:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="波动率",
                level=ValidationLevel.ERROR,
                message="波动率数据无效",
                theory="波动率 = 20周期价格标准差",
                calculation="std(df['close'], 20)",
                expected="> 0",
                actual=volatility,
                evidence="波动率字段缺失或为0"
            ))
        else:
            # 验证波动率合理性
            avg_price = df['close'].mean()
            volatility_ratio = volatility / avg_price

            if volatility_ratio > 0.2:  # 超过20%波动率可能异常
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="波动率",
                    level=ValidationLevel.WARNING,
                    message=f"波动率过高（{volatility_ratio:.1%}），需确认",
                    theory="波动率 = 20周期价格标准差",
                    calculation="std(df['close'], 20)",
                    expected="< 20%",
                    actual=f"{volatility_ratio:.1%}",
                    evidence=f"波动率{volatility} / 平均价格{avg_price} = {volatility_ratio:.1%}"
                ))

    def _validate_volume(self, dynamics: Dict, df: pd.DataFrame):
        """验证成交量分析"""
        volume_status = dynamics.get('volume_status')

        if not volume_status:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="成交量",
                level=ValidationLevel.WARNING,
                message="缺少成交量分析",
                theory="成交量分析：当前成交量 vs 20周期均量",
                calculation="比较当前成交量与均量",
                expected="存在",
                actual=None,
                evidence="volume_status字段缺失"
            ))

    def validate_chanlun(self, structure_data: str, original_df: pd.DataFrame) -> List[LogicValidationResult]:
        """验证缠论分析逻辑"""
        self.results = []

        try:
            structure = json.loads(structure_data)

            # 1. 验证分型识别
            self._validate_fractals(structure, original_df)

            # 2. 验证笔识别
            self._validate_bis(structure, original_df)

            # 3. 验证线段识别
            self._validate_segments(structure, original_df)

            # 4. 验证中枢识别
            self._validate_zhongshu(structure, original_df)

        except Exception as e:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="整体",
                level=ValidationLevel.ERROR,
                message=f"缠论分析验证失败: {e}",
                theory="",
                calculation="",
                expected="有效JSON",
                actual="解析失败",
                evidence=str(e)
            ))

        return [r for r in self.results if r.category == "缠论"]

    def _validate_fractals(self, structure: Dict, df: pd.DataFrame):
        """验证分型识别"""
        fractals = structure.get('fractals', {})
        total_count = fractals.get('total_count', 0)
        top_count = fractals.get('top_count', 0)
        bottom_count = fractals.get('bottom_count', 0)

        # 验证数量关系
        if total_count != top_count + bottom_count:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="分型数量",
                level=ValidationLevel.ERROR,
                message="分型总数不等于顶分型+底分型",
                theory="分型总数 = 顶分型 + 底分型",
                calculation=f"{top_count} + {bottom_count}",
                expected=f"{top_count + bottom_count}",
                actual=total_count,
                evidence=f"总数{total_count} != 顶{top_count} + 底{bottom_count}"
            ))

        # 验证分型定义
        latest_top = fractals.get('latest_top', {})
        latest_bottom = fractals.get('latest_bottom', {})

        if latest_top and 'index' in latest_top:
            idx = latest_top['index']
            if idx < len(df):
                # 验证顶分型定义：高点最高，低点最高
                row = df.iloc[idx]
                if idx > 0 and idx < len(df) - 1:
                    prev_row = df.iloc[idx - 1]
                    next_row = df.iloc[idx + 1]

                    if not (row['high'] >= prev_row['high'] and row['high'] >= next_row['high']):
                        self.results.append(LogicValidationResult(
                            category="缠论",
                            item="顶分型定义",
                            level=ValidationLevel.ERROR,
                            message="顶分型的高点不是最高的",
                            theory="顶分型：高点最高，低点最高",
                            calculation="high >= prev_high and high >= next_high",
                            expected="高点最高",
                            actual=f"high={row['high']}, prev={prev_row['high']}, next={next_row['high']}",
                            evidence=f"索引{idx}的高点{row['high']}不是最高的"
                        ))

    def _validate_bis(self, structure: Dict, df: pd.DataFrame):
        """验证笔识别"""
        bis_info = structure.get('bis', {})
        total_count = bis_info.get('total_count', 0)
        up_count = bis_info.get('up_count', 0)
        down_count = bis_info.get('down_count', 0)

        # 验证数量关系
        if total_count != up_count + down_count:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="笔数量",
                level=ValidationLevel.ERROR,
                message="笔总数不等于向上笔+向下笔",
                theory="笔总数 = 向上笔 + 向下笔",
                calculation=f"{up_count} + {down_count}",
                expected=f"{up_count + down_count}",
                actual=total_count,
                evidence=f"总数{total_count} != 上{up_count} + 下{down_count}"
            ))

    def _validate_segments(self, structure: Dict, df: pd.DataFrame):
        """验证线段识别"""
        segments_info = structure.get('segments', {})
        total_count = segments_info.get('total_count', 0)

        # 验证线段定义：至少3笔
        if total_count > 0:
            bis_count = structure.get('bis', {}).get('total_count', 0)
            if bis_count > 0 and total_count > bis_count / 3:
                self.results.append(LogicValidationResult(
                    category="缠论",
                    item="线段数量",
                    level=ValidationLevel.WARNING,
                    message="线段数量可能过多，每段笔数可能不足3笔",
                    theory="线段至少由3笔构成",
                    calculation="每段 >= 3笔",
                    expected=f"<= {bis_count // 3}",
                    actual=total_count,
                    evidence=f"{total_count}段 / {bis_count}笔 = {bis_count/total_count:.1f}笔/段"
                ))

    def _validate_zhongshu(self, structure: Dict, df: pd.DataFrame):
        """验证中枢识别"""
        zhongshu_info = structure.get('zhongshu', {})
        latest = zhongshu_info.get('latest')

        if latest:
            zg = latest.get('zg')
            zd = latest.get('zd')
            gg = latest.get('gg')
            dd = latest.get('dd')

            # 验证中枢定义
            if zg is not None and zd is not None:
                if zg <= zd:
                    self.results.append(LogicValidationResult(
                        category="缠论",
                        item="中枢定义",
                        level=ValidationLevel.ERROR,
                        message="中枢上沿(ZG)不大于中枢下沿(ZD)",
                        theory="中枢上沿 > 中枢下沿",
                        calculation="ZG = min(各段高点), ZD = max(各段低点)",
                        expected="ZG > ZD",
                        actual=f"ZG={zg}, ZD={zd}",
                        evidence="中枢上沿必须大于中枢下沿"
                    ))

            # 验证区间关系
            if gg and dd and zg and zd:
                if not (gg >= zg and zd >= dd):
                    self.results.append(LogicValidationResult(
                        category="缠论",
                        item="中枢区间",
                        level=ValidationLevel.ERROR,
                        message="中枢区间关系错误",
                        theory="GG >= ZG > ZD >= DD",
                        calculation="GG=最高点, DD=最低点",
                        expected="GG >= ZG > ZD >= DD",
                        actual=f"GG={gg}, ZG={zg}, ZD={zd}, DD={dd}",
                        evidence="区间关系不成立"
                    ))

    def validate_decision(self, decision_data: str, current_price: float) -> List[LogicValidationResult]:
        """验证决策逻辑"""
        self.results = []

        try:
            decision = json.loads(decision_data)

            # 1. 验证止盈止损方向
            self._validate_tp_sl_direction(decision, current_price)

            # 2. 验证决策与得分一致性
            self._validate_decision_score_consistency(decision)

            # 3. 验证盈亏比
            self._validate_risk_reward(decision)

        except Exception as e:
            self.results.append(LogicValidationResult(
                category="决策",
                item="整体",
                level=ValidationLevel.ERROR,
                message=f"决策验证失败: {e}",
                theory="",
                calculation="",
                expected="有效JSON",
                actual="解析失败",
                evidence=str(e)
            ))

        return [r for r in self.results if r.category == "决策"]

    def _validate_tp_sl_direction(self, decision: Dict, current_price: float):
        """验证止盈止损方向（关键！）"""
        trading_plan = decision.get('trading_plan', {})
        decision_type = decision.get('decision')
        entry = trading_plan.get('entry', current_price)

        take_profits = trading_plan.get('take_profit', [])
        stop_losses = trading_plan.get('stop_loss', [])

        # 验证做多
        if decision_type in ['买入', '偏多']:
            # 止盈必须高于现价
            for i, tp in enumerate(take_profits):
                tp_price = tp.get('price')
                if tp_price and tp_price <= entry:
                    self.results.append(LogicValidationResult(
                        category="决策",
                        item=f"止盈TP{i+1}",
                        level=ValidationLevel.CRITICAL,
                        message=f"做多时止盈TP{i+1}价格({tp_price}) <= 入场价({entry})，方向错误！",
                        theory="做多止盈：止盈价 > 入场价",
                        calculation="止盈价必须高于入场价",
                        expected=f"> {entry}",
                        actual=tp_price,
                        evidence=f"做多决策但TP{i+1}价格{tp_price} <= 入场价{entry}"
                    ))

            # 止损必须低于现价
            for i, sl in enumerate(stop_losses):
                sl_price = sl.get('price')
                if sl_price and sl_price >= entry:
                    self.results.append(LogicValidationResult(
                        category="决策",
                        item=f"止损SL{i+1}",
                        level=ValidationLevel.CRITICAL,
                        message=f"做多时止损SL{i+1}价格({sl_price}) >= 入场价({entry})，方向错误！",
                        theory="做多止损：止损价 < 入场价",
                        calculation="止损价必须低于入场价",
                        expected=f"< {entry}",
                        actual=sl_price,
                        evidence=f"做多决策但SL{i+1}价格{sl_price} >= 入场价{entry}"
                    ))

        # 验证做空
        elif decision_type in ['卖出', '偏空']:
            # 止盈必须低于现价
            for i, tp in enumerate(take_profits):
                tp_price = tp.get('price')
                if tp_price and tp_price >= entry:
                    self.results.append(LogicValidationResult(
                        category="决策",
                        item=f"止盈TP{i+1}",
                        level=ValidationLevel.CRITICAL,
                        message=f"做空时止盈TP{i+1}价格({tp_price}) >= 入场价({entry})，方向错误！",
                        theory="做空止盈：止盈价 < 入场价",
                        calculation="止盈价必须低于入场价",
                        expected=f"< {entry}",
                        actual=tp_price,
                        evidence=f"做空决策但TP{i+1}价格{tp_price} >= 入场价{entry}"
                    ))

            # 止损必须高于现价
            for i, sl in enumerate(stop_losses):
                sl_price = sl.get('price')
                if sl_price and sl_price <= entry:
                    self.results.append(LogicValidationResult(
                        category="决策",
                        item=f"止损SL{i+1}",
                        level=ValidationLevel.CRITICAL,
                        message=f"做空时止损SL{i+1}价格({sl_price}) <= 入场价({entry})，方向错误！",
                        theory="做空止损：止损价 > 入场价",
                        calculation="止损价必须高于入场价",
                        expected=f"> {entry}",
                        actual=sl_price,
                        evidence=f"做空决策但SL{i+1}价格{sl_price} <= 入场价{entry}"
                    ))

    def _validate_decision_score_consistency(self, decision: Dict):
        """验证决策与得分一致性"""
        score = decision.get('score', 0)
        decision_type = decision.get('decision')

        # 验证得分范围
        if not (0 <= score <= 100):
            self.results.append(LogicValidationResult(
                category="决策",
                item="得分范围",
                level=ValidationLevel.ERROR,
                message=f"综合得分{score}超出有效范围[0,100]",
                theory="综合得分 = 归一化后范围[0,100]",
                calculation="得分应在0-100之间",
                expected="0-100",
                actual=score,
                evidence="得分超出范围"
            ))

        # 验证决策与得分对应关系
        if decision_type == '买入' and score < 70:
            self.results.append(LogicValidationResult(
                category="决策",
                item="决策一致性",
                level=ValidationLevel.WARNING,
                message=f"决策为买入但得分{score} < 70，不一致",
                theory="买入: 得分 >= 70",
                calculation="得分 >= 70 -> 买入",
                expected=">= 70",
                actual=score,
                evidence=f"决策={decision_type}, 得分={score}"
            ))
        elif decision_type == '卖出' and score > 30:
            self.results.append(LogicValidationResult(
                category="决策",
                item="决策一致性",
                level=ValidationLevel.WARNING,
                message=f"决策为卖出但得分{score} > 30，不一致",
                theory="卖出: 得分 <= 30",
                calculation="得分 <= 30 -> 卖出",
                expected="<= 30",
                actual=score,
                evidence=f"决策={decision_type}, 得分={score}"
            ))

    def _validate_risk_reward(self, decision: Dict):
        """验证盈亏比"""
        trading_plan = decision.get('trading_plan', {})
        risk_reward = trading_plan.get('risk_reward_ratio', [])

        if risk_reward:
            rr = risk_reward[0]
            if rr < 1:
                self.results.append(LogicValidationResult(
                    category="决策",
                    item="盈亏比",
                    level=ValidationLevel.WARNING,
                    message=f"盈亏比{rr} < 1，风险过高",
                    theory="盈亏比 = 收益/风险",
                    calculation="盈亏比应该 >= 1",
                    expected=">= 1",
                    actual=rr,
                    evidence=f"盈亏比{rr}小于1"
                ))

    def get_summary(self) -> Dict[str, Any]:
        """获取验证摘要"""
        critical = sum(1 for r in self.results if r.level == ValidationLevel.CRITICAL)
        error = sum(1 for r in self.results if r.level == ValidationLevel.ERROR)
        warning = sum(1 for r in self.results if r.level == ValidationLevel.WARNING)
        pass_count = sum(1 for r in self.results if r.level == ValidationLevel.PASS)

        # 判断整体是否通过
        overall_pass = (critical == 0) and (error == 0)

        return {
            "overall_pass": overall_pass,
            "total": len(self.results),
            "critical": critical,
            "error": error,
            "warning": warning,
            "pass": pass_count,
            "can_proceed": overall_pass
        }

    def to_dict(self) -> List[Dict]:
        """转换为字典列表"""
        return [
            {
                "category": r.category,
                "item": r.item,
                "level": r.level.value,
                "message": r.message,
                "theory": r.theory,
                "calculation": r.calculation,
                "expected": str(r.expected),
                "actual": str(r.actual),
                "evidence": r.evidence
            }
            for r in self.results
        ]
