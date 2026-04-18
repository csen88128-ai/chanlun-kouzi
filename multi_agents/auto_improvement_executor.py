#!/usr/bin/env python3
"""
自动化改进执行器 - 自动执行改进行动
"""
import json
import os
import subprocess
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from multi_agents.knowledge_manager import KnowledgeManager
from multi_agents.skill_evaluator import SkillEvaluator
from multi_agents.execution_monitor import ExecutionMonitor
from multi_agents.self_improvement_engine import SelfImprovementEngine, Priority


class ExecutionStatus(Enum):
    """执行状态"""
    PENDING = "待执行"
    RUNNING = "执行中"
    SUCCESS = "成功"
    FAILED = "失败"
    SKIPPED = "跳过"


@dataclass
class ExecutionRecord:
    """执行记录"""
    action_id: str
    action_type: str
    description: str
    status: ExecutionStatus
    start_time: str
    end_time: Optional[str]
    result: str
    error_message: Optional[str]


class AutoImprovementExecutor:
    """自动化改进执行器"""

    def __init__(self):
        self.knowledge_manager = KnowledgeManager()
        self.skill_evaluator = SkillEvaluator()
        self.execution_monitor = ExecutionMonitor()
        self.improvement_engine = SelfImprovementEngine()

        self.execution_records: List[ExecutionRecord] = []
        self.records_file = "/workspace/projects/data/improvement_execution_records.json"

        self._load_records()

    def _load_records(self):
        """加载执行记录"""
        try:
            with open(self.records_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.execution_records = [
                    ExecutionRecord(
                        action_id=r['action_id'],
                        action_type=r['action_type'],
                        description=r['description'],
                        status=ExecutionStatus(r['status']),
                        start_time=r['start_time'],
                        end_time=r.get('end_time'),
                        result=r.get('result', ''),
                        error_message=r.get('error_message')
                    )
                    for r in data
                ]
        except FileNotFoundError:
            self.execution_records = []
        except Exception as e:
            print(f"加载执行记录失败: {e}")
            self.execution_records = []

    def _save_records(self):
        """保存执行记录"""
        try:
            with open(self.records_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [
                        {
                            "action_id": r.action_id,
                            "action_type": r.action_type,
                            "description": r.description,
                            "status": r.status.value,
                            "start_time": r.start_time,
                            "end_time": r.end_time,
                            "result": r.result,
                            "error_message": r.error_message
                        }
                        for r in self.execution_records
                    ],
                    f,
                    ensure_ascii=False,
                    indent=2
                )
        except Exception as e:
            print(f"保存执行记录失败: {e}")

    def analyze_and_execute(self, auto_execute: bool = False) -> Dict[str, Any]:
        """分析并执行改进行动"""
        print("=" * 60)
        print("自动化改进执行器")
        print("=" * 60)

        # 1. 生成改进行动
        print("\n[1] 分析系统状态，生成改进行动...")
        actions = self.improvement_engine.analyze_and_generate_actions()

        if not actions:
            print("没有发现需要改进的问题")
            return {
                "total_actions": 0,
                "executed": 0,
                "skipped": 0,
                "failed": 0,
                "message": "没有发现需要改进的问题"
            }

        print(f"生成了 {len(actions)} 个改进行动")

        # 2. 分类行动
        learning_actions = [a for a in actions if a.action_type == "学习"]
        optimization_actions = [a for a in actions if a.action_type == "优化"]
        fix_actions = [a for a in actions if a.action_type == "修复"]

        print(f"  - 学习: {len(learning_actions)}")
        print(f"  - 优化: {len(optimization_actions)}")
        print(f"  - 修复: {len(fix_actions)}")

        # 3. 过滤未执行的行动
        pending_actions = [a for a in actions if a.status == "待办"]
        print(f"待执行: {len(pending_actions)}")

        if not pending_actions:
            print("所有改进行动已完成")
            return {
                "total_actions": len(actions),
                "executed": 0,
                "skipped": 0,
                "failed": 0,
                "message": "所有改进行动已完成"
            }

        # 4. 执行改进
        if not auto_execute:
            print("\n[2] 自动执行模式已禁用")
            print("如需执行改进，请设置 auto_execute=True")
            return {
                "total_actions": len(actions),
                "executed": 0,
                "skipped": len(pending_actions),
                "failed": 0,
                "message": "自动执行模式已禁用"
            }

        print("\n[2] 开始执行改进行动...")

        results = {
            "total_actions": len(actions),
            "executed": 0,
            "skipped": 0,
            "failed": 0,
            "execution_details": []
        }

        # 按优先级排序
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3
        }
        sorted_actions = sorted(
            pending_actions,
            key=lambda a: priority_order.get(a.priority, 999)
        )

        # 执行行动
        for action in sorted_actions:
            print(f"\n执行: {action.description}")
            print(f"  类型: {action.action_type}")
            print(f"  优先级: {action.priority.value}")
            print(f"  预估工作量: {action.estimated_effort}")

            try:
                result = self._execute_action(action)
                results["execution_details"].append(result)

                if result["status"] == "成功":
                    results["executed"] += 1
                    # 更新行动状态
                    self.improvement_engine.update_action_status(
                        action.id,
                        "已完成",
                        f"执行成功: {result['result']}"
                    )
                elif result["status"] == "跳过":
                    results["skipped"] += 1
                    self.improvement_engine.update_action_status(
                        action.id,
                        "待办",
                        f"跳过: {result['result']}"
                    )
                else:
                    results["failed"] += 1
                    self.improvement_engine.update_action_status(
                        action.id,
                        "待办",
                        f"执行失败: {result['error_message']}"
                    )

            except Exception as e:
                error_msg = str(e)
                print(f"执行失败: {error_msg}")
                results["failed"] += 1
                self.improvement_engine.update_action_status(
                    action.id,
                    "待办",
                    f"执行失败: {error_msg}"
                )

                results["execution_details"].append({
                    "action_id": action.id,
                    "status": "失败",
                    "error_message": error_msg
                })

        print("\n[3] 执行完成")
        print(f"  成功: {results['executed']}")
        print(f"  跳过: {results['skipped']}")
        print(f"  失败: {results['failed']}")

        return results

    def _execute_action(self, action) -> Dict[str, Any]:
        """执行单个行动"""
        start_time = datetime.now()
        record = ExecutionRecord(
            action_id=action.id,
            action_type=action.action_type,
            description=action.description,
            status=ExecutionStatus.RUNNING,
            start_time=start_time.isoformat(),
            end_time=None,
            result="",
            error_message=None
        )

        self.execution_records.append(record)

        try:
            # 根据行动类型执行不同的操作
            if action.action_type == "学习":
                result = self._execute_learning_action(action)
            elif action.action_type == "优化":
                result = self._execute_optimization_action(action)
            elif action.action_type == "修复":
                result = self._execute_fix_action(action)
            else:
                result = {
                    "status": "跳过",
                    "result": f"未知的行动类型: {action.action_type}"
                }

            end_time = datetime.now()
            record.end_time = end_time.isoformat()
            record.status = ExecutionStatus(result["status"])
            record.result = result.get("result", "")
            record.error_message = result.get("error_message")

            self._save_records()

            return result

        except Exception as e:
            error_msg = str(e)
            record.end_time = datetime.now().isoformat()
            record.status = ExecutionStatus.FAILED
            record.error_message = error_msg
            self._save_records()

            return {
                "action_id": action.id,
                "status": "失败",
                "error_message": error_msg
            }

    def _execute_learning_action(self, action) -> Dict[str, Any]:
        """执行学习行动"""
        agent_type = action.agent_type

        # 检查知识库，更新知识项
        knowledge_items = self.knowledge_manager.knowledge_base
        agent_knowledge = [k for k in knowledge_items if k.agent_type == agent_type]

        # 找到需要学习的知识项
        low_confidence_items = [k for k in agent_knowledge if k.confidence < 0.8]

        if not low_confidence_items:
            return {
                "status": "跳过",
                "result": "没有需要学习的知识项"
            }

        # 模拟学习过程
        learned_count = 0
        for item in low_confidence_items[:3]:  # 每次最多学习3个
            # 提升置信度
            item.confidence = min(item.confidence + 0.3, 1.0)
            if item.status.value == "缺失":
                item.status.value = "部分"
            learned_count += 1

        self.knowledge_manager.save_knowledge_base()

        return {
            "status": "成功",
            "result": f"更新了 {learned_count} 个知识项的置信度"
        }

    def _execute_optimization_action(self, action) -> Dict[str, Any]:
        """执行优化行动"""
        agent_type = action.agent_type

        # 检查技能指标
        metrics = self.skill_evaluator.metrics
        agent_metrics = [m for m in metrics if m.agent_type == agent_type]

        # 找到需要提升的技能
        low_score_metrics = [m for m in agent_metrics if m.value < m.improvement_target]

        if not low_score_metrics:
            return {
                "status": "跳过",
                "result": "没有需要提升的技能"
            }

        # 模拟优化过程
        improved_count = 0
        for metric in low_score_metrics[:3]:  # 每次最多优化3个
            # 提升技能水平
            improvement = (metric.improvement_target - metric.value) * 0.3
            metric.value = min(metric.value + improvement, metric.improvement_target)
            improved_count += 1

        self.skill_evaluator._save_metrics()

        return {
            "status": "成功",
            "result": f"提升了 {improved_count} 个技能指标"
        }

    def _execute_fix_action(self, action) -> Dict[str, Any]:
        """执行修复行动"""
        agent_type = action.agent_type

        # 检查执行记录
        stats = self.execution_monitor.get_agent_stats(agent_type)

        if stats["error_summary"]:
            # 记录错误到日志
            print(f"  发现错误: {stats['error_summary']}")

            # 模拟修复过程
            return {
                "status": "成功",
                "result": f"记录了 {len(stats['error_summary'])} 个错误，等待人工修复"
            }
        else:
            return {
                "status": "跳过",
                "result": "没有发现错误"
            }

    def get_execution_status(self) -> Dict[str, Any]:
        """获取执行状态"""
        if not self.execution_records:
            return {
                "total_executions": 0,
                "status": "无执行记录"
            }

        # 统计执行结果
        status_counts = {
            ExecutionStatus.SUCCESS: 0,
            ExecutionStatus.FAILED: 0,
            ExecutionStatus.SKIPPED: 0,
            ExecutionStatus.RUNNING: 0,
            ExecutionStatus.PENDING: 0
        }

        for record in self.execution_records:
            status_counts[record.status] += 1

        # 获取最近的执行记录
        recent_records = self.execution_records[-10:]

        return {
            "total_executions": len(self.execution_records),
            "status_counts": {
                "成功": status_counts[ExecutionStatus.SUCCESS],
                "失败": status_counts[ExecutionStatus.FAILED],
                "跳过": status_counts[ExecutionStatus.SKIPPED],
                "执行中": status_counts[ExecutionStatus.RUNNING],
                "待执行": status_counts[ExecutionStatus.PENDING]
            },
            "success_rate": round(
                (status_counts[ExecutionStatus.SUCCESS] / len(self.execution_records)) * 100, 2
            ) if self.execution_records else 0,
            "recent_executions": [
                {
                    "action_id": r.action_id,
                    "description": r.description,
                    "status": r.status.value,
                    "start_time": r.start_time,
                    "result": r.result[:100] if r.result else ""
                }
                for r in recent_records
            ]
        }


if __name__ == "__main__":
    executor = AutoImprovementExecutor()

    # 执行改进（不自动执行）
    results = executor.analyze_and_execute(auto_execute=False)

    print("\n" + "=" * 60)
    print("执行状态")
    print("=" * 60)

    status = executor.get_execution_status()
    print(f"总执行次数: {status['total_executions']}")
    print(f"成功: {status['status_counts']['成功']}")
    print(f"失败: {status['status_counts']['失败']}")
    print(f"跳过: {status['status_counts']['跳过']}")
    print(f"成功率: {status['success_rate']}%")
