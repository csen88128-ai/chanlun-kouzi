#!/usr/bin/env python3
"""
数据验证器 - 验证所有数据来源和完整性
"""
import json
import pandas as pd
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationLevel(Enum):
    """验证级别"""
    PASS = "通过"
    WARNING = "警告"
    ERROR = "错误"
    CRITICAL = "严重错误"


@dataclass
class ValidationResult:
    """验证结果"""
    item: str                 # 验证项
    level: ValidationLevel    # 验证级别
    message: str              # 验证消息
    expected: Any             # 期望值
    actual: Any               # 实际值
    evidence: str             # 证据（实锤依据）


class DataValidator:
    """数据验证器"""

    def __init__(self):
        self.results: List[ValidationResult] = []

    def validate_data(self, output: str, agent_type: str) -> Dict[str, Any]:
        """验证智能体的输出数据"""
        try:
            data = json.loads(output)
        except:
            return {
                "status": "ERROR",
                "message": "无法解析JSON输出",
                "validations": []
            }

        validations = self.validate_all(data)

        # 统计验证结果
        status_counts = {
            "通过": 0,
            "警告": 0,
            "错误": 0,
            "严重错误": 0
        }

        for v in validations:
            level_value = v.level.value
            if level_value in status_counts:
                status_counts[level_value] += 1

        # 确定整体状态
        if status_counts["严重错误"] > 0:
            overall_status = "CRITICAL"
        elif status_counts["错误"] > 0:
            overall_status = "ERROR"
        elif status_counts["警告"] > 0:
            overall_status = "WARNING"
        else:
            overall_status = "PASS"

        return {
            "status": overall_status,
            "agent_type": agent_type,
            "message": f"验证完成: {status_counts['通过']}通过, {status_counts['警告']}警告, {status_counts['错误']}错误, {status_counts['严重错误']}严重",
            "validations": [
                {
                    "item": v.item,
                    "level": v.level.value,
                    "message": v.message,
                    "expected": str(v.expected),
                    "actual": str(v.actual),
                    "evidence": v.evidence
                }
                for v in validations
            ],
            "counts": status_counts,
            "pass": status_counts["通过"],
            "warning": status_counts["警告"],
            "error": status_counts["错误"],
            "critical": status_counts["严重错误"]
        }

    def validate_all(self, data: Dict[str, Any]) -> List[ValidationResult]:
        """验证所有数据"""
        self.results = []

        # 1. 验证数据来源
        self._validate_data_source(data)

        # 2. 验证价格数据
        self._validate_price_data(data)

        # 3. 验证涨跌幅
        self._validate_change_data(data)

        # 4. 验证数据完整性
        self._validate_completeness(data)

        # 5. 验证数据时效性
        self._validate_freshness(data)

        return self.results

    def _validate_data_source(self, data: Dict[str, Any]):
        """验证数据来源"""
        status = data.get('status')

        if status != 'success':
            self.results.append(ValidationResult(
                item="数据来源",
                level=ValidationLevel.ERROR,
                message=f"数据获取失败: {data.get('error', '未知错误')}",
                expected="success",
                actual=status,
                evidence=f"API返回状态: {status}"
            ))
        else:
            # 检查是否有文件路径证明
            file_path = data.get('file_path')
            if file_path:
                self.results.append(ValidationResult(
                    item="数据来源",
                    level=ValidationLevel.PASS,
                    message="数据来源验证通过",
                    expected="文件存储",
                    actual=file_path,
                    evidence=f"数据已保存到: {file_path}"
                ))
            else:
                self.results.append(ValidationResult(
                    item="数据来源",
                    level=ValidationLevel.WARNING,
                    message="数据来源未提供文件路径",
                    expected="文件存储",
                    actual="未知",
                    evidence="只有状态信息，无文件证据"
                ))

    def _validate_price_data(self, data: Dict[str, Any]):
        """验证价格数据"""
        latest_price = data.get('latest_price')
        highest = data.get('highest')
        lowest = data.get('lowest')

        # 检查价格合理性
        if latest_price is None or latest_price <= 0:
            self.results.append(ValidationResult(
                item="最新价格",
                level=ValidationLevel.ERROR,
                message="最新价格无效",
                expected="> 0",
                actual=latest_price,
                evidence=f"最新价格: {latest_price}"
            ))

        if highest is not None and lowest is not None:
            if highest < lowest:
                self.results.append(ValidationResult(
                    item="价格区间",
                    level=ValidationLevel.ERROR,
                    message="最高价不能低于最低价",
                    expected="highest >= lowest",
                    actual=f"highest={highest}, lowest={lowest}",
                    evidence="价格数据矛盾"
                ))

            if latest_price > highest or latest_price < lowest:
                self.results.append(ValidationResult(
                    item="最新价格",
                    level=ValidationLevel.WARNING,
                    message="最新价格超出区间范围",
                    expected=f"lowest <= price <= highest",
                    actual=f"price={latest_price}",
                    evidence=f"区间: [{lowest}, {highest}]"
                ))

    def _validate_change_data(self, data: Dict[str, Any]):
        """验证涨跌幅"""
        h24_change = data.get('h24_change')

        if h24_change is None:
            self.results.append(ValidationResult(
                item="24小时涨跌幅",
                level=ValidationLevel.WARNING,
                message="缺少24小时涨跌幅数据",
                expected="数字",
                actual=None,
                evidence="数据字段缺失"
            ))

        # 检查涨跌幅是否合理（不能超过100%单日涨跌）
        if h24_change is not None:
            if abs(h24_change) > 100:
                self.results.append(ValidationResult(
                    item="24小时涨跌幅",
                    level=ValidationLevel.WARNING,
                    message="24小时涨跌幅超过100%",
                    expected="[-100%, 100%]",
                    actual=f"{h24_change}%",
                    evidence=f"涨跌幅异常: {h24_change}%"
                ))

    def _validate_completeness(self, data: Dict[str, Any]):
        """验证数据完整性"""
        required_fields = ['latest_price', 'highest', 'lowest', 'h24_change', 'volume']

        for field in required_fields:
            if field not in data or data[field] is None:
                self.results.append(ValidationResult(
                    item=f"数据字段",
                    level=ValidationLevel.WARNING,
                    message=f"缺少必填字段: {field}",
                    expected=f"{field}存在",
                    actual="缺失",
                    evidence=f"字段检查失败"
                ))

    def _validate_freshness(self, data: Dict[str, Any]):
        """验证数据时效性"""
        timestamp = data.get('timestamp')

        if timestamp:
            # 检查数据是否超过5分钟
            from datetime import datetime
            import time

            try:
                data_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                now = datetime.now(data_time.tzinfo)
                age_seconds = (now - data_time).total_seconds()

                if age_seconds > 300:  # 5分钟
                    self.results.append(ValidationResult(
                        item="数据时效性",
                        level=ValidationLevel.WARNING,
                        message=f"数据已过期 ({age_seconds/60:.1f}分钟前)",
                        expected="< 5分钟",
                        actual=f"{age_seconds/60:.1f}分钟",
                        evidence=f"数据时间戳: {timestamp}"
                    ))
                else:
                    self.results.append(ValidationResult(
                        item="数据时效性",
                        level=ValidationLevel.PASS,
                        message="数据时效性验证通过",
                        expected="< 5分钟",
                        actual=f"{age_seconds:.1f}秒",
                        evidence=f"数据时间戳: {timestamp}"
                    ))
            except:
                self.results.append(ValidationResult(
                    item="数据时效性",
                    level=ValidationLevel.WARNING,
                    message="无法解析时间戳",
                    expected="有效的ISO时间戳",
                    actual=timestamp,
                    evidence="时间戳格式错误"
                ))
