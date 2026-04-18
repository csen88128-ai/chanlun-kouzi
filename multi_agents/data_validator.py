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
                evidence=f"latest_price = {latest_price}"
            ))

        # 检查价格关系
        if highest < lowest:
            self.results.append(ValidationResult(
                item="价格关系",
                level=ValidationLevel.ERROR,
                message="最高价低于最低价，数据错误",
                expected="highest >= lowest",
                actual=f"highest={highest}, lowest={lowest}",
                evidence="价格关系不成立"
            ))

        # 检查现价是否在合理范围内
        if latest_price and highest and lowest:
            if latest_price > highest * 1.1:
                self.results.append(ValidationResult(
                    item="价格范围",
                    level=ValidationLevel.ERROR,
                    message="现价超过历史最高价10%以上，数据异常",
                    expected=f"<= {highest * 1.1}",
                    actual=latest_price,
                    evidence=f"现价{latest_price} 远高于历史最高{highest}"
                ))
            elif latest_price < lowest * 0.9:
                self.results.append(ValidationResult(
                    item="价格范围",
                    level=ValidationLevel.ERROR,
                    message="现价低于历史最低价10%以上，数据异常",
                    expected=f">= {lowest * 0.9}",
                    actual=latest_price,
                    evidence=f"现价{latest_price} 远低于历史最低{lowest}"
                ))

    def _validate_change_data(self, data: Dict[str, Any]):
        """验证涨跌幅数据"""
        h24_change = data.get('24h_change')

        if h24_change is None:
            self.results.append(ValidationResult(
                item="涨跌幅",
                level=ValidationLevel.ERROR,
                message="缺少24小时涨跌幅数据",
                expected="数值",
                actual=None,
                evidence="24h_change字段缺失"
            ))
        elif abs(h24_change) > 50:  # 超过50%异常
            self.results.append(ValidationResult(
                item="涨跌幅",
                level=ValidationLevel.WARNING,
                message="24小时涨跌幅超过50%，可能数据异常",
                expected="-50 ~ 50",
                actual=h24_change,
                evidence=f"涨跌幅{h24_change}%异常"
            ))

    def _validate_completeness(self, data: Dict[str, Any]):
        """验证数据完整性"""
        required_fields = ['latest_price', 'highest', 'lowest', '24h_change', 'data_count']

        for field in required_fields:
            if field not in data or data[field] is None:
                self.results.append(ValidationResult(
                    item="数据完整性",
                    level=ValidationLevel.ERROR,
                    message=f"缺少必要字段: {field}",
                    expected="存在",
                    actual="缺失",
                    evidence=f"字段 {field} 不存在"
                ))

        # 验证数据数量
        data_count = data.get('data_count')
        if data_count and data_count < 10:
            self.results.append(ValidationResult(
                item="数据数量",
                level=ValidationLevel.WARNING,
                message="数据数量过少，可能影响分析准确性",
                expected=">= 100",
                actual=data_count,
                evidence=f"只有{data_count}根K线"
            ))

    def _validate_freshness(self, data: Dict[str, Any]):
        """验证数据时效性"""
        file_path = data.get('file_path')
        if not file_path:
            return

        try:
            # 检查文件修改时间
            import os
            import time
            mtime = os.path.getmtime(file_path)
            age_minutes = (time.time() - mtime) / 60

            if age_minutes > 60:
                self.results.append(ValidationResult(
                    item="数据时效性",
                    level=ValidationLevel.WARNING,
                    message="数据超过1小时未更新",
                    expected="< 60分钟",
                    actual=f"{age_minutes:.1f}分钟",
                    evidence=f"文件修改时间: {age_minutes:.1f}分钟前"
                ))
            else:
                self.results.append(ValidationResult(
                    item="数据时效性",
                    level=ValidationLevel.PASS,
                    message="数据时效性验证通过",
                    expected="< 60分钟",
                    actual=f"{age_minutes:.1f}分钟",
                    evidence=f"数据于{age_minutes:.1f}分钟前更新"
                ))
        except Exception as e:
            self.results.append(ValidationResult(
                item="数据时效性",
                level=ValidationLevel.ERROR,
                message=f"无法验证数据时效性: {e}",
                expected="文件存在",
                actual="验证失败",
                evidence=str(e)
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
                "item": r.item,
                "level": r.level.value,
                "message": r.message,
                "expected": str(r.expected),
                "actual": str(r.actual),
                "evidence": r.evidence
            }
            for r in self.results
        ]


def validate_api_response(response: str) -> Dict[str, Any]:
    """
    验证API响应数据

    Args:
        response: API响应字符串（JSON格式）

    Returns:
        验证结果
    """
    try:
        data = json.loads(response)
        validator = DataValidator()
        results = validator.validate_all(data)

        return {
            "status": "success",
            "data": data,
            "validation": {
                "summary": validator.get_summary(),
                "results": validator.to_dict()
            }
        }
    except json.JSONDecodeError as e:
        return {
            "status": "error",
            "message": "JSON解析失败",
            "error": str(e)
        }
