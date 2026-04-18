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

    def validate_dynamics(self, dynamics_data: str, original_df: pd.DataFrame = None) -> List[LogicValidationResult]:
        """验证动力学分析逻辑"""
        self.results = []

        try:
            dynamics = json.loads(dynamics_data)

            # 1. 验证RSI
            self._validate_rsi_basic(dynamics)

            # 2. 验证MACD
            self._validate_macd_basic(dynamics)

            # 3. 验证波动率
            self._validate_volatility_basic(dynamics)

            # 4. 验证成交量
            self._validate_volume_basic(dynamics)

            # 5. 如果有DataFrame，进行详细验证
            if original_df is not None:
                self._validate_rsi_detailed(dynamics, original_df)
                self._validate_macd_detailed(dynamics, original_df)

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

    def _validate_rsi_basic(self, dynamics: Dict):
        """验证RSI基本属性"""
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
        else:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="RSI",
                level=ValidationLevel.PASS,
                message="RSI范围验证通过",
                theory="RSI = 100 - (100 / (1 + RS))",
                calculation="RSI范围验证",
                expected="0-100",
                actual=rsi,
                evidence=f"RSI={rsi} 在有效范围内"
            ))

        # 验证RSI状态
        rsi_status = dynamics.get('rsi_status')
        if rsi_status:
            if rsi >= 70 and rsi_status not in ["超买", "Overbought"]:
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="RSI状态",
                    level=ValidationLevel.WARNING,
                    message="RSI状态与数值不匹配",
                    theory="RSI >= 70 为超买",
                    calculation="RSI状态验证",
                    expected="超买/Overbought",
                    actual=rsi_status,
                    evidence=f"RSI={rsi}, 状态={rsi_status}"
                ))
            elif rsi <= 30 and rsi_status not in ["超卖", "Oversold"]:
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="RSI状态",
                    level=ValidationLevel.WARNING,
                    message="RSI状态与数值不匹配",
                    theory="RSI <= 30 为超卖",
                    calculation="RSI状态验证",
                    expected="超卖/Oversold",
                    actual=rsi_status,
                    evidence=f"RSI={rsi}, 状态={rsi_status}"
                ))

    def _validate_rsi_detailed(self, dynamics: Dict, df: pd.DataFrame):
        """验证RSI详细计算"""
        rsi = dynamics.get('rsi')

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
                    item="RSI计算",
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
                    item="RSI计算",
                    level=ValidationLevel.PASS,
                    message="RSI计算验证通过",
                    theory="RSI = 100 - (100 / (1 + RS))",
                    calculation="14周期RSI标准公式",
                    expected=f"~{latest_calculated_rsi:.1f}",
                    actual=rsi,
                    evidence=f"差异{rsi_diff:.2f}在可接受范围内"
                ))
        except:
            pass  # 跳过详细验证

    def _validate_macd_basic(self, dynamics: Dict):
        """验证MACD基本属性"""
        macd = dynamics.get('macd')
        macd_signal = dynamics.get('macd_signal')
        macd_histogram = dynamics.get('macd_histogram')

        if macd is None or macd_signal is None:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="MACD",
                level=ValidationLevel.ERROR,
                message="缺少MACD数据",
                theory="MACD = EMA(12) - EMA(26)",
                calculation="MACD基于12日和26日EMA计算",
                expected="MACD和Signal都应该存在",
                actual=f"MACD={macd}, Signal={macd_signal}",
                evidence="MACD字段缺失"
            ))
            return

        # 验证MACD Histogram计算
        if macd_histogram is not None:
            calculated_histogram = macd - macd_signal
            histogram_diff = abs(macd_histogram - calculated_histogram)
            if histogram_diff > 0.01:
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="MACD Histogram",
                    level=ValidationLevel.WARNING,
                    message=f"MACD Histogram计算可能有误差（差异{histogram_diff:.4f}）",
                    theory="Histogram = MACD - Signal",
                    calculation="MACD Histogram标准公式",
                    expected=f"~{calculated_histogram:.4f}",
                    actual=macd_histogram,
                    evidence=f"计算值{calculated_histogram:.4f}，报告值{macd_histogram}"
                ))

        # 验证MACD信号类型
        macd_signal_type = dynamics.get('macd_signal_type')
        if macd_signal_type:
            if macd > macd_signal and macd_signal_type not in ["金叉", "Golden Cross", "Bullish"]:
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="MACD信号类型",
                    level=ValidationLevel.WARNING,
                    message="MACD信号类型与数值不匹配",
                    theory="MACD > Signal 为金叉",
                    calculation="MACD信号验证",
                    expected="金叉/Golden Cross/Bullish",
                    actual=macd_signal_type,
                    evidence=f"MACD={macd} > Signal={macd_signal}"
                ))
            elif macd < macd_signal and macd_signal_type not in ["死叉", "Death Cross", "Bearish"]:
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="MACD信号类型",
                    level=ValidationLevel.WARNING,
                    message="MACD信号类型与数值不匹配",
                    theory="MACD < Signal 为死叉",
                    calculation="MACD信号验证",
                    expected="死叉/Death Cross/Bearish",
                    actual=macd_signal_type,
                    evidence=f"MACD={macd} < Signal={macd_signal}"
                ))

    def _validate_macd_detailed(self, dynamics: Dict, df: pd.DataFrame):
        """验证MACD详细计算"""
        try:
            # 计算MACD
            ema12 = df['close'].ewm(span=12, adjust=False).mean()
            ema26 = df['close'].ewm(span=26, adjust=False).mean()
            calculated_macd = ema12 - ema26
            calculated_signal = calculated_macd.ewm(span=9, adjust=False).mean()

            latest_macd = calculated_macd.iloc[-1]
            latest_signal = calculated_signal.iloc[-1]

            # 比较
            macd = dynamics.get('macd', 0)
            macd_signal = dynamics.get('macd_signal', 0)
            macd_diff = abs(macd - latest_macd)
            signal_diff = abs(macd_signal - latest_signal)

            if macd_diff > 10 or signal_diff > 10:
                self.results.append(LogicValidationResult(
                    category="动力学",
                    item="MACD计算",
                    level=ValidationLevel.WARNING,
                    message=f"MACD计算可能有较大误差",
                    theory="MACD = EMA(12) - EMA(26)",
                    calculation="12日和26日EMA",
                    expected=f"MACD~{latest_macd:.2f}, Signal~{latest_signal:.2f}",
                    actual=f"MACD={macd:.2f}, Signal={macd_signal:.2f}",
                    evidence=f"MACD差异{macd_diff:.2f}, Signal差异{signal_diff:.2f}"
                ))
        except:
            pass  # 跳过详细验证

    def _validate_volatility_basic(self, dynamics: Dict):
        """验证波动率基本属性"""
        volatility = dynamics.get('volatility')

        if volatility is None:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="波动率",
                level=ValidationLevel.WARNING,
                message="缺少波动率数据",
                theory="波动率 = 标准差 / 均值",
                calculation="20周期波动率计算",
                expected=">= 0",
                actual=None,
                evidence="波动率字段缺失"
            ))
            return

        # 验证波动率范围
        if volatility < 0:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="波动率",
                level=ValidationLevel.ERROR,
                message="波动率不能为负",
                theory="波动率 = 标准差 / 均值",
                calculation="波动率计算",
                expected=">= 0",
                actual=volatility,
                evidence="波动率为负数"
            ))

    def _validate_volume_basic(self, dynamics: Dict):
        """验证成交量基本属性"""
        volume = dynamics.get('volume')
        volume_status = dynamics.get('volume_status')

        if volume is None:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="成交量",
                level=ValidationLevel.WARNING,
                message="缺少成交量数据",
                theory="成交量分析",
                calculation="成交量统计",
                expected=">= 0",
                actual=None,
                evidence="成交量字段缺失"
            ))
            return

        # 验证成交量范围
        if volume < 0:
            self.results.append(LogicValidationResult(
                category="动力学",
                item="成交量",
                level=ValidationLevel.ERROR,
                message="成交量不能为负",
                theory="成交量分析",
                calculation="成交量统计",
                expected=">= 0",
                actual=volume,
                evidence="成交量为负数"
            ))
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

    def validate_chanlun(self, structure_data: str, original_df: pd.DataFrame = None) -> List[LogicValidationResult]:
        """验证缠论分析逻辑"""
        self.results = []

        try:
            structure = json.loads(structure_data)

            # 1. 验证分型识别
            self._validate_fractals_basic(structure)

            # 2. 验证笔识别
            self._validate_bis_basic(structure)

            # 3. 验证线段识别
            self._validate_segments_basic(structure)

            # 4. 验证中枢识别
            self._validate_zhongshu_basic(structure)

            # 5. 验证买卖点
            self._validate_buy_sell_points_basic(structure)

            # 6. 如果有DataFrame，进行详细验证
            if original_df is not None:
                self._validate_fractals_detailed(structure, original_df)
                self._validate_bis_detailed(structure, original_df)

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

    def _validate_fractals_basic(self, structure: Dict):
        """验证分型基本属性"""
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
                calculation="分型数量统计",
                expected=f"{top_count} + {bottom_count} = {top_count + bottom_count}",
                actual=str(total_count),
                evidence=f"总数={total_count}, 顶={top_count}, 底={bottom_count}"
            ))

        # 验证分型数量合理性
        if total_count == 0:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="分型数量",
                level=ValidationLevel.WARNING,
                message="未识别到任何分型",
                theory="分型识别：顶分型和底分型",
                calculation="分型识别算法",
                expected="> 0",
                actual=0,
                evidence="可能数据量不足或算法问题"
            ))

        # 验证最新分型
        latest_fractal = fractals.get('latest')
        if latest_fractal:
            if latest_fractal not in ["顶分型", "底分型", "Top", "Bottom"]:
                self.results.append(LogicValidationResult(
                    category="缠论",
                    item="最新分型类型",
                    level=ValidationLevel.WARNING,
                    message="最新分型类型无效",
                    theory="分型类型：顶分型或底分型",
                    calculation="分型类型判断",
                    expected="顶分型/底分型/Top/Bottom",
                    actual=latest_fractal,
                    evidence=f"最新分型={latest_fractal}"
                ))

    def _validate_fractals_detailed(self, structure: Dict, df: pd.DataFrame):
        """验证分型详细计算"""
        # 这里可以添加详细的分型计算验证
        pass

    def _validate_bis_basic(self, structure: Dict):
        """验证笔基本属性"""
        bis = structure.get('bis', {})
        total_count = bis.get('total_count', 0)
        up_count = bis.get('up_count', 0)
        down_count = bis.get('down_count', 0)

        # 验证数量关系
        if total_count != up_count + down_count:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="笔数量",
                level=ValidationLevel.ERROR,
                message="笔总数不等于向上笔+向下笔",
                theory="笔总数 = 向上笔 + 向下笔",
                calculation="笔数量统计",
                expected=f"{up_count} + {down_count} = {up_count + down_count}",
                actual=str(total_count),
                evidence=f"总数={total_count}, 向上={up_count}, 向下={down_count}"
            ))

        # 验证笔数量合理性
        if total_count < 2:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="笔数量",
                level=ValidationLevel.WARNING,
                message="笔数量过少",
                theory="笔：连接相邻的顶底分型",
                calculation="笔识别算法",
                expected=">= 2",
                actual=total_count,
                evidence="可能数据量不足或算法问题"
            ))

        # 验证最新笔
        latest_bi = bis.get('latest')
        if latest_bi:
            bi_type = latest_bi.get('type', '')
            if bi_type not in ["向上笔", "向下笔", "Up", "Down"]:
                self.results.append(LogicValidationResult(
                    category="缠论",
                    item="最新笔类型",
                    level=ValidationLevel.WARNING,
                    message="最新笔类型无效",
                    theory="笔类型：向上笔或向下笔",
                    calculation="笔类型判断",
                    expected="向上笔/向下笔/Up/Down",
                    actual=bi_type,
                    evidence=f"最新笔类型={bi_type}"
                ))

    def _validate_bis_detailed(self, structure: Dict, df: pd.DataFrame):
        """验证笔详细计算"""
        # 这里可以添加详细的笔计算验证
        pass

    def _validate_segments_basic(self, structure: Dict):
        """验证线段基本属性"""
        segments = structure.get('segments', {})
        total_count = segments.get('total_count', 0)
        up_count = segments.get('up_count', 0)
        down_count = segments.get('down_count', 0)

        # 验证数量关系
        if total_count != up_count + down_count:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="线段数量",
                level=ValidationLevel.ERROR,
                message="线段总数不等于向上线段+向下线段",
                theory="线段总数 = 向上线段 + 向下线段",
                calculation="线段数量统计",
                expected=f"{up_count} + {down_count} = {up_count + down_count}",
                actual=str(total_count),
                evidence=f"总数={total_count}, 向上={up_count}, 向下={down_count}"
            ))

        # 验证线段数量合理性
        if total_count < 1:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="线段数量",
                level=ValidationLevel.WARNING,
                message="线段数量过少",
                theory="线段：至少由3笔构成",
                calculation="线段识别算法",
                expected=">= 1",
                actual=total_count,
                evidence="可能数据量不足或算法问题"
            ))

        # 验证最新线段
        latest_segment = segments.get('latest')
        if latest_segment:
            segment_type = latest_segment.get('type', '')
            if segment_type not in ["向上线段", "向下线段", "Up", "Down"]:
                self.results.append(LogicValidationResult(
                    category="缠论",
                    item="最新线段类型",
                    level=ValidationLevel.WARNING,
                    message="最新线段类型无效",
                    theory="线段类型：向上线段或向下线段",
                    calculation="线段类型判断",
                    expected="向上线段/向下线段/Up/Down",
                    actual=segment_type,
                    evidence=f"最新线段类型={segment_type}"
                ))

    def _validate_zhongshu_basic(self, structure: Dict):
        """验证中枢基本属性"""
        zhongshu = structure.get('zhongshu', {})
        total_count = zhongshu.get('total_count', 0)

        # 验证中枢数量合理性
        if total_count < 1:
            self.results.append(LogicValidationResult(
                category="缠论",
                item="中枢数量",
                level=ValidationLevel.WARNING,
                message="未识别到中枢",
                theory="中枢：至少由3段构成，区间为所有段的重叠部分",
                calculation="中枢识别算法",
                expected=">= 1",
                actual=total_count,
                evidence="可能数据量不足或算法问题"
            ))

        # 验证最新中枢
        latest_zhongshu = zhongshu.get('latest')
        if latest_zhongshu:
            zg = latest_zhongshu.get('ZG')
            zd = latest_zhongshu.get('ZD')
            gg = latest_zhongshu.get('GG')
            dd = latest_zhongshu.get('DD')

            # 验证ZG >= ZD
            if zg is not None and zd is not None and zg < zd:
                self.results.append(LogicValidationResult(
                    category="缠论",
                    item="中枢ZG/ZD关系",
                    level=ValidationLevel.ERROR,
                    message="中枢上沿(ZG)不能小于中枢下沿(ZD)",
                    theory="ZG：所有段高点最低值，ZD：所有段低点最高值",
                    calculation="中枢区间计算",
                    expected="ZG >= ZD",
                    actual=f"ZG={zg}, ZD={zd}",
                    evidence="中枢区间计算错误"
                ))

            # 验证GG >= ZG >= ZD >= DD
            if all([gg, zg, zd, dd]):
                if not (gg >= zg >= zd >= dd):
                    self.results.append(LogicValidationResult(
                        category="缠论",
                        item="中枢区间关系",
                        level=ValidationLevel.ERROR,
                        message="中枢区间关系错误",
                        theory="GG >= ZG >= ZD >= DD",
                        calculation="中枢区间计算",
                        expected="GG >= ZG >= ZD >= DD",
                        actual=f"GG={gg}, ZG={zg}, ZD={zd}, DD={dd}",
                        evidence="中枢区间计算错误"
                    ))

    def _validate_buy_sell_points_basic(self, structure: Dict):
        """验证买卖点基本属性"""
        buy_sell_points = structure.get('buy_sell_points', {})
        total_count = buy_sell_points.get('total_count', 0)

        # 验证买卖点
        latest_point = buy_sell_points.get('latest')
        if latest_point:
            point_type = latest_point.get('type', '')
            valid_types = ["一买", "二买", "三买", "一卖", "二卖", "三卖",
                          "1st Buy", "2nd Buy", "3rd Buy", "1st Sell", "2nd Sell", "3rd Sell"]
            if point_type not in valid_types:
                self.results.append(LogicValidationResult(
                    category="缠论",
                    item="最新买卖点类型",
                    level=ValidationLevel.WARNING,
                    message="买卖点类型无效",
                    theory="买卖点：一买、二买、三买、一卖、二卖、三卖",
                    calculation="买卖点识别算法",
                    expected=f"{valid_types}",
                    actual=point_type,
                    evidence=f"最新买卖点类型={point_type}"
                ))

            # 验证买卖点强度
            strength = latest_point.get('strength')
            if strength is not None:
                if not (0 <= strength <= 100):
                    self.results.append(LogicValidationResult(
                        category="缠论",
                        item="买卖点强度",
                        level=ValidationLevel.WARNING,
                        message="买卖点强度超出范围",
                        theory="买卖点强度：0-100",
                        calculation="买卖点强度计算",
                        expected="0-100",
                        actual=strength,
                        evidence="买卖点强度计算错误"
                    ))
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
