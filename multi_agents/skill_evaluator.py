#!/usr/bin/env python3
"""
技能评估模块 - 评估各智能体的技能水平
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class SkillLevel(Enum):
    """技能等级"""
    NOVICE = "新手"
    BEGINNER = "初级"
    INTERMEDIATE = "中级"
    ADVANCED = "高级"
    EXPERT = "专家"


@dataclass
class SkillMetric:
    """技能指标"""
    agent_type: str              # 智能体类型
    metric_name: str            # 指标名称
    value: float                # 指标值（0-100）
    level: SkillLevel           # 技能等级
    description: str            # 描述
    last_updated: str           # 最后更新时间
    evidence: str               # 证据
    improvement_target: float   # 改进目标
    improvement_action: str     # 改进行动


class SkillEvaluator:
    """技能评估器"""

    def __init__(self):
        self.metrics: List[SkillMetric] = []
        self.metrics_file = "/workspace/projects/data/skill_metrics.json"
        self._load_metrics()

    def _load_metrics(self):
        """加载技能指标"""
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.metrics = [SkillMetric(**item) for item in data]
        except FileNotFoundError:
            self._initialize_metrics()
        except Exception as e:
            print(f"加载技能指标失败: {e}")
            self._initialize_metrics()

    def _save_metrics(self):
        """保存技能指标"""
        try:
            # 将枚举转换为字符串
            serializable_metrics = []
            for metric in self.metrics:
                metric_dict = asdict(metric)
                metric_dict['level'] = metric.level.value  # 转换枚举为字符串
                serializable_metrics.append(metric_dict)

            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存技能指标失败: {e}")

    def _initialize_metrics(self):
        """初始化技能指标"""
        self.metrics = [
            # 数据采集智能体
            SkillMetric(
                agent_type="data_collector",
                metric_name="数据获取准确性",
                value=95,
                level=SkillLevel.EXPERT,
                description="成功获取数据且数据正确的比例",
                last_updated=datetime.now().isoformat(),
                evidence="多次测试成功，数据准确",
                improvement_target=98,
                improvement_action="优化异常处理逻辑"
            ),
            SkillMetric(
                agent_type="data_collector",
                metric_name="数据完整性",
                value=90,
                level=SkillLevel.ADVANCED,
                description="返回完整数据（包含所有必要字段）的比例",
                last_updated=datetime.now().isoformat(),
                evidence="基本完整，偶有字段缺失",
                improvement_target=95,
                improvement_action="增强数据验证"
            ),

            # 结构分析智能体
            SkillMetric(
                agent_type="structure_analyzer",
                metric_name="分型识别准确性",
                value=90,
                level=SkillLevel.ADVANCED,
                description="正确识别分型的比例",
                last_updated=datetime.now().isoformat(),
                evidence="人工验证准确率90%",
                improvement_target=95,
                improvement_action="优化分型判断算法"
            ),
            SkillMetric(
                agent_type="structure_analyzer",
                metric_name="线段识别准确性",
                value=75,
                level=SkillLevel.INTERMEDIATE,
                description="正确识别线段的比例",
                last_updated=datetime.now().isoformat(),
                evidence="算法较简单，复杂场景准确率低",
                improvement_target=85,
                improvement_action="实现更复杂的线段破坏判断"
            ),
            SkillMetric(
                agent_type="structure_analyzer",
                metric_name="买卖点识别准确性",
                value=70,
                level=SkillLevel.INTERMEDIATE,
                description="正确识别买卖点的比例",
                last_updated=datetime.now().isoformat(),
                evidence="背驰判断需要加强",
                improvement_target=80,
                improvement_action="实现更精确的背驰检测算法"
            ),

            # 动力学分析智能体
            SkillMetric(
                agent_type="dynamics_analyzer",
                metric_name="RSI计算准确性",
                value=98,
                level=SkillLevel.EXPERT,
                description="RSI计算与标准公式一致的比例",
                last_updated=datetime.now().isoformat(),
                evidence="与手动计算完全一致",
                improvement_target=99,
                improvement_action="优化计算精度"
            ),
            SkillMetric(
                agent_type="dynamics_analyzer",
                metric_name="MACD判断准确性",
                value=95,
                level=SkillLevel.EXPERT,
                description="金叉死叉判断正确的比例",
                last_updated=datetime.now().isoformat(),
                evidence="金叉死叉判断准确",
                improvement_target=98,
                improvement_action="增加趋势确认"
            ),

            # 决策制定智能体
            SkillMetric(
                agent_type="decision_maker",
                metric_name="止盈止损方向准确性",
                value=95,
                level=SkillLevel.EXPERT,
                description="止盈止损方向正确的比例",
                last_updated=datetime.now().isoformat(),
                evidence="已通过逻辑验证，方向正确",
                improvement_target=98,
                improvement_action="持续监控"
            ),
            SkillMetric(
                agent_type="decision_maker",
                metric_name="决策与得分一致性",
                value=85,
                level=SkillLevel.ADVANCED,
                description="决策与综合得分一致的比例",
                last_updated=datetime.now().isoformat(),
                evidence="基本一致，偶有边缘情况",
                improvement_target=90,
                improvement_action="优化决策阈值"
            ),
            SkillMetric(
                agent_type="decision_maker",
                metric_name="实锤数据支持度",
                value=90,
                level=SkillLevel.ADVANCED,
                description="输出有数据支持的比例",
                last_updated=datetime.now().isoformat(),
                evidence="大部分输出有数据支持",
                improvement_target=95,
                improvement_action="增强数据追溯能力"
            ),

            # 市场情绪智能体
            SkillMetric(
                agent_type="sentiment_analyzer",
                metric_name="数据获取准确性",
                value=98,
                level=SkillLevel.EXPERT,
                description="成功获取恐惧贪婪指数的比例",
                last_updated=datetime.now().isoformat(),
                evidence="API调用稳定",
                improvement_target=99,
                improvement_action="优化重试机制"
            ),
            SkillMetric(
                agent_type="sentiment_analyzer",
                metric_name="情绪解读准确性",
                value=70,
                level=SkillLevel.INTERMEDIATE,
                description="情绪解读与市场实际情况符合的程度",
                last_updated=datetime.now().isoformat(),
                evidence="缺乏历史验证",
                improvement_target=80,
                improvement_action="结合历史数据回测情绪指标有效性"
            )
        ]

        self._save_metrics()

    def get_agent_metrics(self, agent_type: str) -> List[SkillMetric]:
        """获取智能体的技能指标"""
        return [metric for metric in self.metrics if metric.agent_type == agent_type]

    def evaluate_agent(self, agent_type: str) -> Dict[str, Any]:
        """评估智能体的整体技能水平"""
        metrics = self.get_agent_metrics(agent_type)

        if not metrics:
            return {
                "agent_type": agent_type,
                "average_score": 0,
                "level": SkillLevel.NOVICE.value,
                "total_metrics": 0,
                "needs_improvement": True,
                "metrics": []
            }

        # 计算平均分
        avg_score = sum(m.value for m in metrics) / len(metrics)

        # 判断技能等级
        if avg_score >= 90:
            level = SkillLevel.EXPERT
        elif avg_score >= 80:
            level = SkillLevel.ADVANCED
        elif avg_score >= 70:
            level = SkillLevel.INTERMEDIATE
        elif avg_score >= 60:
            level = SkillLevel.BEGINNER
        else:
            level = SkillLevel.NOVICE

        # 判断是否需要改进
        needs_improvement = any(m.value < m.improvement_target for m in metrics)

        return {
            "agent_type": agent_type,
            "average_score": round(avg_score, 2),
            "level": level.value,
            "total_metrics": len(metrics),
            "needs_improvement": needs_improvement,
            "metrics": [
                {
                    "metric_name": m.metric_name,
                    "value": m.value,
                    "level": m.level.value,
                    "target": m.improvement_target,
                    "gap": m.improvement_target - m.value,
                    "action": m.improvement_action
                }
                for m in metrics
            ]
        }

    def update_metric(self, agent_type: str, metric_name: str, value: float, evidence: str):
        """更新技能指标"""
        for metric in self.metrics:
            if metric.agent_type == agent_type and metric.metric_name == metric_name:
                metric.value = value
                metric.evidence = evidence
                metric.last_updated = datetime.now().isoformat()

                # 更新技能等级
                if metric.value >= 90:
                    metric.level = SkillLevel.EXPERT
                elif metric.value >= 80:
                    metric.level = SkillLevel.ADVANCED
                elif metric.value >= 70:
                    metric.level = SkillLevel.INTERMEDIATE
                elif metric.value >= 60:
                    metric.level = SkillLevel.BEGINNER
                else:
                    metric.level = SkillLevel.NOVICE
                break

        self._save_metrics()

    def get_all_evaluations(self) -> Dict[str, Any]:
        """获取所有智能体的评估结果"""
        all_agents = ["data_collector", "structure_analyzer", "dynamics_analyzer", "decision_maker", "sentiment_analyzer"]

        evaluations = {}
        total_score = 0
        total_count = 0

        for agent in all_agents:
            evaluation = self.evaluate_agent(agent)
            evaluations[agent] = evaluation
            total_score += evaluation["average_score"]
            total_count += 1

        overall_average = total_score / total_count if total_count > 0 else 0

        return {
            "total_agents": total_count,
            "overall_average": round(overall_average, 2),
            "agent_evaluations": evaluations,
            "needs_improvement": any(e["needs_improvement"] for e in evaluations.values())
        }

    def get_improvement_priority(self) -> List[Dict[str, Any]]:
        """获取改进优先级"""
        improvements = []

        for metric in self.metrics:
            if metric.value < metric.improvement_target:
                gap = metric.improvement_target - metric.value
                improvements.append({
                    "agent_type": metric.agent_type,
                    "metric_name": metric.metric_name,
                    "current_value": metric.value,
                    "target_value": metric.improvement_target,
                    "gap": gap,
                    "priority": "高" if gap >= 20 else "中" if gap >= 10 else "低",
                    "action": metric.improvement_action
                })

        # 按差距大小排序
        improvements.sort(key=lambda x: x["gap"], reverse=True)

        return improvements
