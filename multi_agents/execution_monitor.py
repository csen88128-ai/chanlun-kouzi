#!/usr/bin/env python3
"""
执行监控模块 - 监控各智能体的执行情况
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class ExecutionStatus(Enum):
    """执行状态"""
    SUCCESS = "成功"
    FAILURE = "失败"
    WARNING = "警告"
    TIMEOUT = "超时"
    VALIDATION_FAILED = "验证失败"


@dataclass
class ExecutionRecord:
    """执行记录"""
    agent_type: str                  # 智能体类型
    execution_id: str                # 执行ID
    timestamp: str                   # 时间戳
    status: ExecutionStatus          # 执行状态
    execution_time: float            # 执行时间（秒）
    input_data: str                  # 输入数据摘要
    output_data: str                 # 输出数据摘要
    validation_result: Dict[str, Any]  # 验证结果
    errors: List[str]                # 错误列表
    warnings: List[str]              # 警告列表
    quality_score: float             # 质量得分（0-100）
    improvement_notes: str           # 改进笔记


class ExecutionMonitor:
    """执行监控器"""

    def __init__(self):
        self.records: List[ExecutionRecord] = []
        self.records_file = "/workspace/projects/data/execution_records.json"
        self.max_records = 1000  # 最多保存1000条记录
        self._load_records()

    def _load_records(self):
        """加载执行记录"""
        try:
            with open(self.records_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 将字符串状态转换为枚举
                self.records = []
                for item in data:
                    # 创建一个副本，将status字符串转换为枚举
                    item_copy = item.copy()
                    if 'status' in item_copy and isinstance(item_copy['status'], str):
                        # 根据字符串值创建枚举
                        status_map = {
                            "成功": ExecutionStatus.SUCCESS,
                            "失败": ExecutionStatus.FAILURE,
                            "警告": ExecutionStatus.WARNING,
                            "超时": ExecutionStatus.TIMEOUT,
                            "验证失败": ExecutionStatus.VALIDATION_FAILED
                        }
                        item_copy['status'] = status_map.get(item_copy['status'], ExecutionStatus.FAILURE)
                    self.records.append(ExecutionRecord(**item_copy))
        except FileNotFoundError:
            self.records = []
        except Exception as e:
            print(f"加载执行记录失败: {e}")
            self.records = []

    def _save_records(self):
        """保存执行记录"""
        try:
            # 只保留最近的记录
            records_to_save = self.records[-self.max_records:]
            # 将枚举转换为字符串
            serializable_records = []
            for record in records_to_save:
                record_dict = asdict(record)
                record_dict['status'] = record.status.value  # 转换枚举为字符串
                serializable_records.append(record_dict)

            with open(self.records_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存执行记录失败: {e}")

    def record_execution(
        self,
        agent_type: str,
        status: ExecutionStatus,
        execution_time: float,
        input_data: str,
        output_data: str,
        validation_result: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None
    ) -> ExecutionRecord:
        """记录执行情况"""
        execution_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        # 计算质量得分
        quality_score = self._calculate_quality_score(status, validation_result, errors, warnings)

        record = ExecutionRecord(
            agent_type=agent_type,
            execution_id=execution_id,
            timestamp=datetime.now().isoformat(),
            status=status,
            execution_time=execution_time,
            input_data=input_data[:200] + "..." if len(input_data) > 200 else input_data,
            output_data=output_data[:200] + "..." if len(output_data) > 200 else output_data,
            validation_result=validation_result or {},
            errors=errors or [],
            warnings=warnings or [],
            quality_score=quality_score,
            improvement_notes=""
        )

        self.records.append(record)
        self._save_records()

        return record

    def _calculate_quality_score(
        self,
        status: ExecutionStatus,
        validation_result: Optional[Dict[str, Any]],
        errors: Optional[List[str]],
        warnings: Optional[List[str]]
    ) -> float:
        """计算质量得分"""
        score = 100

        # 状态扣分
        if status == ExecutionStatus.FAILURE:
            score -= 50
        elif status == ExecutionStatus.TIMEOUT:
            score -= 40
        elif status == ExecutionStatus.VALIDATION_FAILED:
            score -= 60
        elif status == ExecutionStatus.WARNING:
            score -= 20

        # 验证结果扣分
        if validation_result:
            if validation_result.get('critical', 0) > 0:
                score -= 30
            if validation_result.get('error', 0) > 0:
                score -= 15
            if validation_result.get('warning', 0) > 0:
                score -= 5

        # 错误扣分
        if errors:
            score -= len(errors) * 10

        # 警告扣分
        if warnings:
            score -= len(warnings) * 3

        return max(0, min(100, score))

    def get_agent_stats(self, agent_type: str, limit: int = 10) -> Dict[str, Any]:
        """获取智能体的执行统计"""
        agent_records = [r for r in self.records if r.agent_type == agent_type]

        if not agent_records:
            return {
                "agent_type": agent_type,
                "total_executions": 0,
                "success_rate": 0,
                "average_time": 0,
                "average_quality": 0,
                "recent_records": []
            }

        # 只取最近的记录
        recent_records = agent_records[-limit:]

        # 统计
        total_executions = len(recent_records)
        success_count = sum(1 for r in recent_records if r.status == ExecutionStatus.SUCCESS)
        success_rate = (success_count / total_executions) * 100 if total_executions > 0 else 0

        average_time = sum(r.execution_time for r in recent_records) / total_executions
        average_quality = sum(r.quality_score for r in recent_records) / total_executions

        # 错误统计
        all_errors = [e for r in recent_records for e in r.errors]
        error_summary = {}
        for error in all_errors:
            error_summary[error] = error_summary.get(error, 0) + 1

        return {
            "agent_type": agent_type,
            "total_executions": total_executions,
            "success_rate": round(success_rate, 2),
            "average_time": round(average_time, 2),
            "average_quality": round(average_quality, 2),
            "error_summary": error_summary,
            "recent_records": [
                {
                    "execution_id": r.execution_id,
                    "timestamp": r.timestamp,
                    "status": r.status.value,
                    "execution_time": r.execution_time,
                    "quality_score": r.quality_score,
                    "errors": r.errors,
                    "warnings": r.warnings
                }
                for r in recent_records[-5:]
            ]
        }

    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有智能体的执行统计"""
        all_agents = ["data_collector", "structure_analyzer", "dynamics_analyzer", "decision_maker", "sentiment_analyzer"]

        stats = {}
        total_success = 0
        total_executions = 0

        for agent in all_agents:
            agent_stat = self.get_agent_stats(agent)
            stats[agent] = agent_stat
            total_success += int(agent_stat["success_rate"] * agent_stat["total_executions"] / 100)
            total_executions += agent_stat["total_executions"]

        overall_success_rate = (total_success / total_executions) * 100 if total_executions > 0 else 0

        return {
            "total_agents": len(all_agents),
            "total_executions": total_executions,
            "overall_success_rate": round(overall_success_rate, 2),
            "agent_stats": stats
        }

    def identify_trends(self, agent_type: str) -> Dict[str, Any]:
        """识别智能体的执行趋势"""
        agent_records = [r for r in self.records if r.agent_type == agent_type]

        if len(agent_records) < 5:
            return {
                "agent_type": agent_type,
                "insufficient_data": True,
                "message": "数据不足，无法分析趋势"
            }

        # 取最近10条记录
        recent = agent_records[-10:]

        # 计算趋势
        recent_success_rate = sum(1 for r in recent if r.status == ExecutionStatus.SUCCESS) / len(recent)
        recent_quality_avg = sum(r.quality_score for r in recent) / len(recent)

        # 与历史对比（取前10-20条）
        if len(agent_records) >= 20:
            historical = agent_records[-20:-10]
            historical_success_rate = sum(1 for r in historical if r.status == ExecutionStatus.SUCCESS) / len(historical)
            historical_quality_avg = sum(r.quality_score for r in historical) / len(historical)

            success_rate_trend = "上升" if recent_success_rate > historical_success_rate else "下降"
            quality_trend = "上升" if recent_quality_avg > historical_quality_avg else "下降"
        else:
            success_rate_trend = "稳定"
            quality_trend = "稳定"

        return {
            "agent_type": agent_type,
            "recent_success_rate": round(recent_success_rate * 100, 2),
            "recent_quality_avg": round(recent_quality_avg, 2),
            "success_rate_trend": success_rate_trend,
            "quality_trend": quality_trend,
            "insufficient_data": False
        }

    def get_improvement_candidates(self) -> List[Dict[str, Any]]:
        """获取需要改进的智能体"""
        candidates = []

        for agent_type in ["data_collector", "structure_analyzer", "dynamics_analyzer", "decision_maker", "sentiment_analyzer"]:
            stats = self.get_agent_stats(agent_type)

            # 判断是否需要改进
            needs_improvement = False
            reasons = []

            if stats["success_rate"] < 90:
                needs_improvement = True
                reasons.append(f"成功率低({stats['success_rate']}%)")

            if stats["average_quality"] < 80:
                needs_improvement = True
                reasons.append(f"质量得分低({stats['average_quality']})")

            if stats["error_summary"]:
                needs_improvement = True
                reasons.append(f"存在错误: {list(stats['error_summary'].keys())}")

            if needs_improvement:
                candidates.append({
                    "agent_type": agent_type,
                    "success_rate": stats["success_rate"],
                    "average_quality": stats["average_quality"],
                    "reasons": reasons,
                    "priority": "高" if stats["success_rate"] < 80 else "中" if stats["success_rate"] < 90 else "低"
                })

        # 按优先级排序
        candidates.sort(key=lambda x: x["priority"], reverse=True)

        return candidates
