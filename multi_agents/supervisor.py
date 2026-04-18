#!/usr/bin/env python3
"""
监督智能体 - 综合验证所有智能体的输出
确保数据有实锤依据，逻辑有理论支撑，输出真实有效
"""
import json
import sys
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from multi_agents.data_validator import DataValidator, ValidationLevel
from multi_agents.logic_validator import LogicValidator, LogicValidationResult


class ApprovalStatus(Enum):
    """审批状态"""
    APPROVED = "通过"
    REJECTED = "拒绝"
    WARNING = "警告"
    PENDING = "待定"


@dataclass
class SupervisionReport:
    """监督报告"""
    timestamp: str
    overall_status: ApprovalStatus
    data_validation: Dict[str, Any]
    logic_validation: Dict[str, Any]
    critical_issues: List[str]
    error_issues: List[str]
    warning_issues: List[str]
    can_proceed: bool
    reasoning: str


class Supervisor:
    """监督智能体"""

    def __init__(self):
        self.data_validator = DataValidator()
        self.logic_validator = LogicValidator()
        self.reports: List[SupervisionReport] = []

    def supervise_data_collection(self, data_result: str) -> SupervisionReport:
        """监督数据采集"""
        timestamp = datetime.now().isoformat()

        # 数据验证
        data_validation = validate_api_response(data_result)
        data_summary = data_validation.get('validation', {}).get('summary', {})

        # 检查数据来源和实锤依据
        if not data_summary.get('overall_pass', False):
            return SupervisionReport(
                timestamp=timestamp,
                overall_status=ApprovalStatus.REJECTED,
                data_validation=data_validation,
                logic_validation={},
                critical_issues=[],
                error_issues=[],
                warning_issues=[],
                can_proceed=False,
                reasoning=f"数据验证未通过，无法继续。严重错误{data_summary.get('critical', 0)}个，错误{data_summary.get('error', 0)}个"
            )

        # 提取关键信息
        validation_results = data_validation.get('validation', {}).get('results', [])
        critical_issues = [r['message'] for r in validation_results if r['level'] == '严重错误']
        error_issues = [r['message'] for r in validation_results if r['level'] == '错误']
        warning_issues = [r['message'] for r in validation_results if r['level'] == '警告']

        # 判断是否通过
        overall_status = ApprovalStatus.APPROVED if data_summary.get('overall_pass') else ApprovalStatus.WARNING
        can_proceed = overall_status == ApprovalStatus.APPROVED

        reasoning = self._generate_reasoning("数据采集", data_validation, can_proceed)

        report = SupervisionReport(
            timestamp=timestamp,
            overall_status=overall_status,
            data_validation=data_validation,
            logic_validation={},
            critical_issues=critical_issues,
            error_issues=error_issues,
            warning_issues=warning_issues,
            can_proceed=can_proceed,
            reasoning=reasoning
        )

        self.reports.append(report)
        return report

    def supervise_structure_analysis(self, structure_result: str) -> SupervisionReport:
        """监督结构分析（缠论）"""
        timestamp = datetime.now().isoformat()

        # 读取原始数据用于验证
        try:
            df = pd.read_csv("/workspace/projects/data/BTCUSDT_4h_latest.csv")
        except Exception as e:
            return SupervisionReport(
                timestamp=timestamp,
                overall_status=ApprovalStatus.REJECTED,
                data_validation={},
                logic_validation={},
                critical_issues=[f"无法读取原始数据: {e}"],
                error_issues=[],
                warning_issues=[],
                can_proceed=False,
                reasoning="无法读取原始数据进行逻辑验证"
            )

        # 逻辑验证
        logic_results = self.logic_validator.validate_chanlun(structure_result, df)
        logic_summary = self.logic_validator.get_summary()

        # 提取关键信息
        critical_issues = [r.message for r in logic_results if r.level == ValidationLevel.CRITICAL]
        error_issues = [r.message for r in logic_results if r.level == ValidationLevel.ERROR]
        warning_issues = [r.message for r in logic_results if r.level == ValidationLevel.WARNING]

        # 判断是否通过
        overall_status = ApprovalStatus.APPROVED if logic_summary.get('overall_pass') else ApprovalStatus.WARNING
        can_proceed = overall_status == ApprovalStatus.APPROVED

        reasoning = self._generate_reasoning("结构分析（缠论）", logic_results, can_proceed)

        report = SupervisionReport(
            timestamp=timestamp,
            overall_status=overall_status,
            data_validation={},
            logic_validation={"summary": logic_summary, "results": self.logic_validator.to_dict()},
            critical_issues=critical_issues,
            error_issues=error_issues,
            warning_issues=warning_issues,
            can_proceed=can_proceed,
            reasoning=reasoning
        )

        self.reports.append(report)
        return report

    def supervise_dynamics_analysis(self, dynamics_result: str) -> SupervisionReport:
        """监督动力学分析"""
        timestamp = datetime.now().isoformat()

        # 读取原始数据用于验证
        try:
            df = pd.read_csv("/workspace/projects/data/BTCUSDT_4h_latest.csv")
        except Exception as e:
            return SupervisionReport(
                timestamp=timestamp,
                overall_status=ApprovalStatus.REJECTED,
                data_validation={},
                logic_validation={},
                critical_issues=[f"无法读取原始数据: {e}"],
                error_issues=[],
                warning_issues=[],
                can_proceed=False,
                reasoning="无法读取原始数据进行逻辑验证"
            )

        # 逻辑验证
        logic_results = self.logic_validator.validate_dynamics(dynamics_result, df)
        logic_summary = self.logic_validator.get_summary()

        # 提取关键信息
        critical_issues = [r.message for r in logic_results if r.level == ValidationLevel.CRITICAL]
        error_issues = [r.message for r in logic_results if r.level == ValidationLevel.ERROR]
        warning_issues = [r.message for r in logic_results if r.level == ValidationLevel.WARNING]

        # 判断是否通过
        overall_status = ApprovalStatus.APPROVED if logic_summary.get('overall_pass') else ApprovalStatus.WARNING
        can_proceed = overall_status == ApprovalStatus.APPROVED

        reasoning = self._generate_reasoning("动力学分析", logic_results, can_proceed)

        report = SupervisionReport(
            timestamp=timestamp,
            overall_status=overall_status,
            data_validation={},
            logic_validation={"summary": logic_summary, "results": self.logic_validator.to_dict()},
            critical_issues=critical_issues,
            error_issues=error_issues,
            warning_issues=warning_issues,
            can_proceed=can_proceed,
            reasoning=reasoning
        )

        self.reports.append(report)
        return report

    def supervise_sentiment_analysis(self, sentiment_result: str) -> SupervisionReport:
        """监督市场情绪分析"""
        timestamp = datetime.now().isoformat()

        try:
            sentiment = json.loads(sentiment_result)

            # 验证数据来源
            status = sentiment.get('status')
            fgi = sentiment.get('fear_greed_index')

            issues = []

            if status != 'success':
                issues.append(f"情绪数据获取失败: {sentiment.get('error', '未知错误')}")

            if fgi is None:
                issues.append("缺少恐惧贪婪指数")

            if fgi is not None and not (0 <= fgi <= 100):
                issues.append(f"恐惧贪婪指数{fgi}超出有效范围[0,100]")

            # 判断是否通过
            can_proceed = len(issues) == 0
            overall_status = ApprovalStatus.APPROVED if can_proceed else ApprovalStatus.REJECTED

            reasoning = self._generate_reasoning("市场情绪分析", issues, can_proceed)

            report = SupervisionReport(
                timestamp=timestamp,
                overall_status=overall_status,
                data_validation={},
                logic_validation={},
                critical_issues=[],
                error_issues=issues,
                warning_issues=[],
                can_proceed=can_proceed,
                reasoning=reasoning
            )

            self.reports.append(report)
            return report

        except Exception as e:
            return SupervisionReport(
                timestamp=timestamp,
                overall_status=ApprovalStatus.REJECTED,
                data_validation={},
                logic_validation={},
                critical_issues=[f"情绪分析验证失败: {e}"],
                error_issues=[],
                warning_issues=[],
                can_proceed=False,
                reasoning=f"情绪数据解析失败: {e}"
            )

    def supervise_decision(self, decision_result: str, current_price: float) -> SupervisionReport:
        """监督决策制定（关键！）"""
        timestamp = datetime.now().isoformat()

        # 逻辑验证
        logic_results = self.logic_validator.validate_decision(decision_result, current_price)
        logic_summary = self.logic_validator.get_summary()

        # 提取关键信息
        critical_issues = [r.message for r in logic_results if r.level == ValidationLevel.CRITICAL]
        error_issues = [r.message for r in logic_results if r.level == ValidationLevel.ERROR]
        warning_issues = [r.message for r in logic_results if r.level == ValidationLevel.WARNING]

        # 关键：止盈止损方向错误必须拒绝
        if critical_issues:
            overall_status = ApprovalStatus.REJECTED
            can_proceed = False
        elif error_issues:
            overall_status = ApprovalStatus.WARNING
            can_proceed = False  # 有错误也不允许输出
        elif warning_issues:
            overall_status = ApprovalStatus.WARNING
            can_proceed = True  # 有警告可以输出
        else:
            overall_status = ApprovalStatus.APPROVED
            can_proceed = True

        reasoning = self._generate_reasoning("决策制定", logic_results, can_proceed)

        report = SupervisionReport(
            timestamp=timestamp,
            overall_status=overall_status,
            data_validation={},
            logic_validation={"summary": logic_summary, "results": self.logic_validator.to_dict()},
            critical_issues=critical_issues,
            error_issues=error_issues,
            warning_issues=warning_issues,
            can_proceed=can_proceed,
            reasoning=reasoning
        )

        self.reports.append(report)
        return report

    def supervise_final_decision(self, all_reports: List[SupervisionReport]) -> SupervisionReport:
        """监督最终决策（综合审批）"""
        timestamp = datetime.now().isoformat()

        # 收集所有问题
        all_critical = []
        all_errors = []
        all_warnings = []

        for report in all_reports:
            all_critical.extend(report.critical_issues)
            all_errors.extend(report.error_issues)
            all_warnings.extend(report.warning_issues)

        # 判断是否可以输出
        has_critical = len(all_critical) > 0
        has_error = len(all_errors) > 0

        if has_critical:
            overall_status = ApprovalStatus.REJECTED
            can_proceed = False
        elif has_error:
            overall_status = ApprovalStatus.REJECTED
            can_proceed = False
        elif all_warnings:
            overall_status = ApprovalStatus.WARNING
            can_proceed = True
        else:
            overall_status = ApprovalStatus.APPROVED
            can_proceed = True

        # 生成综合理由
        reasoning_parts = []
        reasoning_parts.append(f"共检查{len(all_reports)}个智能体输出")

        if all_critical:
            reasoning_parts.append(f"发现{len(all_critical)}个严重错误")
            reasoning_parts.append(f"严重错误：{'; '.join(all_critical[:3])}")

        if all_errors:
            reasoning_parts.append(f"发现{len(all_errors)}个错误")
            reasoning_parts.append(f"错误：{'; '.join(all_errors[:3])}")

        if all_warnings:
            reasoning_parts.append(f"发现{len(all_warnings)}个警告")

        if can_proceed:
            reasoning_parts.append("所有验证通过，可以输出最终研判")
        else:
            reasoning_parts.append("验证未通过，拒绝输出最终研判")

        reasoning = " | ".join(reasoning_parts)

        report = SupervisionReport(
            timestamp=timestamp,
            overall_status=overall_status,
            data_validation={},
            logic_validation={},
            critical_issues=all_critical,
            error_issues=all_errors,
            warning_issues=all_warnings,
            can_proceed=can_proceed,
            reasoning=reasoning
        )

        self.reports.append(report)
        return report

    def _generate_reasoning(self, stage: str, validation_results: Any, can_proceed: bool) -> str:
        """生成验证理由"""
        if can_proceed:
            return f"{stage}验证通过，所有检查项符合要求，有实锤依据和理论支撑"
        else:
            if isinstance(validation_results, list):
                issues = [r.message for r in validation_results if r.level in [ValidationLevel.CRITICAL, ValidationLevel.ERROR]]
                if issues:
                    return f"{stage}验证未通过：{'; '.join(issues[:3])}"
            return f"{stage}验证未通过，存在实锤依据或逻辑错误"

    def get_validation_chain(self) -> List[Dict]:
        """获取完整的验证链条"""
        chain = []
        for i, report in enumerate(self.reports):
            chain.append({
                "step": i + 1,
                "timestamp": report.timestamp,
                "status": report.overall_status.value,
                "can_proceed": report.can_proceed,
                "critical": len(report.critical_issues),
                "error": len(report.error_issues),
                "warning": len(report.warning_issues),
                "reasoning": report.reasoning
            })
        return chain

    def export_report(self) -> Dict[str, Any]:
        """导出完整报告"""
        return {
            "timestamp": datetime.now().isoformat(),
            "supervisor_report": {
                "total_steps": len(self.reports),
                "final_status": self.reports[-1].overall_status.value if self.reports else "未完成",
                "can_proceed": self.reports[-1].can_proceed if self.reports else False,
                "validation_chain": self.get_validation_chain()
            },
            "details": [
                {
                    "timestamp": r.timestamp,
                    "status": r.overall_status.value,
                    "can_proceed": r.can_proceed,
                    "critical_issues": r.critical_issues,
                    "error_issues": r.error_issues,
                    "warning_issues": r.warning_issues,
                    "reasoning": r.reasoning
                }
                for r in self.reports
            ]
        }
