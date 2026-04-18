#!/usr/bin/env python3
"""
历史数据分析模块 - 分析执行历史，验证改进效果
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum


@dataclass
class TrendMetrics:
    """趋势指标"""
    metric_name: str         # 指标名称
    current_value: float     # 当前值
    previous_value: float    # 前一次值
    change_percent: float    # 变化百分比
    change_trend: str        # 变化趋势（上升/下降/稳定）
    improvement_rate: float  # 改进率（正向为正）


@dataclass
class ComparisonResult:
    """对比结果"""
    agent_type: str              # 智能体类型
    metric_name: str             # 指标名称
    period1_value: float         # 第一时期值
    period2_value: float         # 第二时期值
    change: float                # 变化值
    change_percent: float        # 变化百分比
    trend: str                   # 趋势
    is_improvement: bool         # 是否为改进
    significance: str            # 显著性（显著/轻微/无）


class HistoryAnalyzer:
    """历史数据分析器"""

    def __init__(self):
        self.records_file = "/workspace/projects/data/execution_records.json"
        self.knowledge_file = "/workspace/projects/data/knowledge_base.json"
        self.skill_file = "/workspace/projects/data/skill_metrics.json"
        self.improvement_file = "/workspace/projects/data/improvement_actions.json"

    def _load_records(self) -> List[Dict]:
        """加载执行记录"""
        try:
            with open(self.records_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"加载执行记录失败: {e}")
            return []

    def _load_knowledge(self) -> List[Dict]:
        """加载知识库"""
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"加载知识库失败: {e}")
            return []

    def _load_skills(self) -> List[Dict]:
        """加载技能指标"""
        try:
            with open(self.skill_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except Exception as e:
            print(f"加载技能指标失败: {e}")
            return []

    def analyze_execution_trends(self, agent_type: str, days: int = 7) -> List[TrendMetrics]:
        """分析执行趋势"""
        records = self._load_records()
        agent_records = [r for r in records if r['agent_type'] == agent_type]

        if len(agent_records) < 2:
            return []

        # 按时间排序
        agent_records.sort(key=lambda x: x['timestamp'])

        # 获取最新的记录和几天前的记录
        latest_record = agent_records[-1]
        cutoff_date = datetime.now() - timedelta(days=days)
        previous_records = [r for r in agent_records
                           if datetime.fromisoformat(r['timestamp']) < cutoff_date]

        if not previous_records:
            previous_record = agent_records[0]
        else:
            previous_record = previous_records[-1]

        # 计算趋势指标
        trends = []

        # 1. 执行时间趋势
        current_time = latest_record['execution_time']
        previous_time = previous_record['execution_time']
        if previous_time > 0:
            change_percent = ((current_time - previous_time) / previous_time) * 100
            trend = "下降" if change_percent < -5 else "上升" if change_percent > 5 else "稳定"
            improvement_rate = -change_percent  # 时间减少是改进
        else:
            change_percent = 0
            trend = "稳定"
            improvement_rate = 0

        trends.append(TrendMetrics(
            metric_name="执行时间",
            current_value=current_time,
            previous_value=previous_time,
            change_percent=change_percent,
            change_trend=trend,
            improvement_rate=improvement_rate
        ))

        # 2. 质量得分趋势
        current_quality = latest_record['quality_score']
        previous_quality = previous_record['quality_score']
        if previous_quality > 0:
            change_percent = ((current_quality - previous_quality) / previous_quality) * 100
            trend = "上升" if change_percent > 5 else "下降" if change_percent < -5 else "稳定"
            improvement_rate = change_percent  # 质量提升是改进
        else:
            change_percent = 0
            trend = "稳定"
            improvement_rate = 0

        trends.append(TrendMetrics(
            metric_name="质量得分",
            current_value=current_quality,
            previous_value=previous_quality,
            change_percent=change_percent,
            change_trend=trend,
            improvement_rate=improvement_rate
        ))

        return trends

    def compare_periods(self, agent_type: str, period1_days: int = 14, period2_days: int = 7) -> List[ComparisonResult]:
        """对比两个时期的性能"""
        records = self._load_records()
        agent_records = [r for r in records if r['agent_type'] == agent_type]

        if len(agent_records) < 10:
            return []

        # 按时间排序
        agent_records.sort(key=lambda x: x['timestamp'])

        now = datetime.now()

        # 第一时期（较早）
        period1_end = now - timedelta(days=period2_days)
        period1_records = [r for r in agent_records
                          if datetime.fromisoformat(r['timestamp']) < period1_end]

        # 第二时期（较近）
        period1_records = period1_records[-period1_days:] if len(period1_records) > period1_days else period1_records

        period2_records = [r for r in agent_records
                          if datetime.fromisoformat(r['timestamp']) >= period1_end]
        period2_records = period2_records[:period2_days] if len(period2_records) > period2_days else period2_records

        if not period1_records or not period2_records:
            return []

        comparisons = []

        # 1. 对比平均执行时间
        period1_time = sum(r['execution_time'] for r in period1_records) / len(period1_records)
        period2_time = sum(r['execution_time'] for r in period2_records) / len(period2_records)

        change = period2_time - period1_time
        change_percent = (change / period1_time) * 100 if period1_time > 0 else 0

        trend = "上升" if change > 0.5 else "下降" if change < -0.5 else "稳定"
        is_improvement = change < 0  # 时间减少是改进
        significance = "显著" if abs(change_percent) > 10 else "轻微" if abs(change_percent) > 2 else "无"

        comparisons.append(ComparisonResult(
            agent_type=agent_type,
            metric_name="平均执行时间",
            period1_value=period1_time,
            period2_value=period2_time,
            change=change,
            change_percent=change_percent,
            trend=trend,
            is_improvement=is_improvement,
            significance=significance
        ))

        # 2. 对比平均质量得分
        period1_quality = sum(r['quality_score'] for r in period1_records) / len(period1_records)
        period2_quality = sum(r['quality_score'] for r in period2_records) / len(period2_records)

        change = period2_quality - period1_quality
        change_percent = (change / period1_quality) * 100 if period1_quality > 0 else 0

        trend = "上升" if change > 5 else "下降" if change < -5 else "稳定"
        is_improvement = change > 0  # 质量提升是改进
        significance = "显著" if abs(change_percent) > 10 else "轻微" if abs(change_percent) > 2 else "无"

        comparisons.append(ComparisonResult(
            agent_type=agent_type,
            metric_name="平均质量得分",
            period1_value=period1_quality,
            period2_value=period2_quality,
            change=change,
            change_percent=change_percent,
            trend=trend,
            is_improvement=is_improvement,
            significance=significance
        ))

        # 3. 对比成功率
        period1_success = sum(1 for r in period1_records if r['status'] in ['成功', 'SUCCESS']) / len(period1_records)
        period2_success = sum(1 for r in period2_records if r['status'] in ['成功', 'SUCCESS']) / len(period2_records)

        change = period2_success - period1_success
        change_percent = (change / period1_success) * 100 if period1_success > 0 else 0

        trend = "上升" if change > 0.05 else "下降" if change < -0.05 else "稳定"
        is_improvement = change > 0  # 成功率提升是改进
        significance = "显著" if abs(change_percent) > 10 else "轻微" if abs(change_percent) > 2 else "无"

        comparisons.append(ComparisonResult(
            agent_type=agent_type,
            metric_name="成功率",
            period1_value=period1_success * 100,
            period2_value=period2_success * 100,
            change=change * 100,
            change_percent=change_percent,
            trend=trend,
            is_improvement=is_improvement,
            significance=significance
        ))

        return comparisons

    def analyze_improvement_effectiveness(self) -> Dict[str, Any]:
        """分析改进措施的有效性"""
        records = self._load_records()
        skills = self._load_skills()
        knowledge = self._load_knowledge()

        if not records:
            return {
                "total_executions": 0,
                "analysis": "数据不足，无法分析改进效果"
            }

        # 按时间分段
        records.sort(key=lambda x: x['timestamp'])

        # 最近7天 vs 前14天
        now = datetime.now()
        recent_records = [r for r in records
                          if datetime.fromisoformat(r['timestamp']) >= now - timedelta(days=7)]
        previous_records = [r for r in records
                           if (now - timedelta(days=21)) <= datetime.fromisoformat(r['timestamp']) < now - timedelta(days=7)]

        analysis = {
            "total_executions": len(records),
            "recent_executions": len(recent_records),
            "previous_executions": len(previous_records),
            "period_comparison": {},
            "skill_improvements": {},
            "knowledge_improvements": {},
            "overall_assessment": ""
        }

        # 1. 时期对比
        if recent_records and previous_records:
            recent_avg_time = sum(r['execution_time'] for r in recent_records) / len(recent_records)
            previous_avg_time = sum(r['execution_time'] for r in previous_records) / len(previous_records)
            recent_avg_quality = sum(r['quality_score'] for r in recent_records) / len(recent_records)
            previous_avg_quality = sum(r['quality_score'] for r in previous_records) / len(previous_records)

            analysis["period_comparison"] = {
                "recent_avg_time": round(recent_avg_time, 2),
                "previous_avg_time": round(previous_avg_time, 2),
                "time_change_percent": round(((recent_avg_time - previous_avg_time) / previous_avg_time) * 100, 2),
                "recent_avg_quality": round(recent_avg_quality, 2),
                "previous_avg_quality": round(previous_avg_quality, 2),
                "quality_change_percent": round(((recent_avg_quality - previous_avg_quality) / previous_avg_quality) * 100, 2)
            }

        # 2. 技能改进
        if skills:
            skill_analysis = {}
            for skill in skills:
                agent_type = skill['agent_type']
                current_value = skill['current_value']
                target_value = skill['target_value']
                gap = target_value - current_value

                skill_analysis[agent_type] = {
                    "current": current_value,
                    "target": target_value,
                    "gap": gap,
                    "progress_percent": round(((current_value - 50) / (target_value - 50)) * 100, 2) if target_value > 50 else 0
                }

            analysis["skill_improvements"] = skill_analysis

        # 3. 知识改进
        if knowledge:
            knowledge_analysis = {}
            for item in knowledge:
                agent_type = item['agent_type']
                concept = item['concept']
                status = item['status']
                confidence = item['confidence']

                if agent_type not in knowledge_analysis:
                    knowledge_analysis[agent_type] = {
                        "complete": 0,
                        "partial": 0,
                        "missing": 0,
                        "outdated": 0,
                        "avg_confidence": 0,
                        "items": []
                    }

                knowledge_analysis[agent_type][status.lower()] += 1
                knowledge_analysis[agent_type]["items"].append({
                    "concept": concept,
                    "status": status,
                    "confidence": confidence
                })

            for agent_type, data in knowledge_analysis.items():
                if data["items"]:
                    data["avg_confidence"] = round(sum(item['confidence'] for item in data["items"]) / len(data["items"]), 2)
                del data["items"]

            analysis["knowledge_improvements"] = knowledge_analysis

        # 4. 总体评估
        assessment_parts = []

        # 执行时间评估
        if analysis["period_comparison"]:
            time_change = analysis["period_comparison"]["time_change_percent"]
            if time_change < -10:
                assessment_parts.append("执行时间显著优化")
            elif time_change < -2:
                assessment_parts.append("执行时间有所改善")
            elif time_change > 10:
                assessment_parts.append("执行时间有所增加，需要优化")

        # 质量评估
        if analysis["period_comparison"]:
            quality_change = analysis["period_comparison"]["quality_change_percent"]
            if quality_change > 5:
                assessment_parts.append("输出质量显著提升")
            elif quality_change > 0:
                assessment_parts.append("输出质量有所提升")
            elif quality_change < -5:
                assessment_parts.append("输出质量有所下降，需要关注")

        # 技能评估
        if analysis["skill_improvements"]:
            avg_progress = sum(data.get('progress_percent', 0) for data in analysis["skill_improvements"].values())
            if avg_progress > 80:
                assessment_parts.append("技能水平持续提升")
            elif avg_progress > 50:
                assessment_parts.append("技能水平稳步提升")
            elif avg_progress > 20:
                assessment_parts.append("技能水平有待提升")

        analysis["overall_assessment"] = "；".join(assessment_parts) if assessment_parts else "数据不足，无法评估"

        return analysis

    def generate_improvement_report(self) -> str:
        """生成改进效果报告"""
        analysis = self.analyze_improvement_effectiveness()

        report = f"""
===========================================
        改进效果分析报告
===========================================

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【执行概况】
- 总执行次数: {analysis['total_executions']}
- 近期执行次数: {analysis.get('recent_executions', 0)}
- 前期执行次数: {analysis.get('previous_executions', 0)}

【时期对比】
"""

        if "period_comparison" in analysis and analysis["period_comparison"]:
            pc = analysis["period_comparison"]
            report += f"""
- 近期平均执行时间: {pc.get('recent_avg_time', 0):.2f}秒
- 前期平均执行时间: {pc.get('previous_avg_time', 0):.2f}秒
- 执行时间变化: {pc.get('time_change_percent', 0):.2f}%

- 近期平均质量得分: {pc.get('recent_avg_quality', 0):.2f}
- 前期平均质量得分: {pc.get('previous_avg_quality', 0):.2f}
- 质量得分变化: {pc.get('quality_change_percent', 0):.2f}%
"""

        report += """

【技能改进】
"""
        if "skill_improvements" in analysis and analysis["skill_improvements"]:
            for agent, data in analysis["skill_improvements"].items():
                report += f"""
{agent}:
- 当前值: {data['current']:.2f}
- 目标值: {data['target']:.2f}
- 差距: {data['gap']:.2f}
- 进度: {data['progress_percent']:.2f}%
"""
        else:
            report += "暂无技能改进数据\n"

        report += """

【知识改进】
"""
        if "knowledge_improvements" in analysis and analysis["knowledge_improvements"]:
            for agent, data in analysis["knowledge_improvements"].items():
                report += f"""
{agent}:
- 完整: {data['complete']}
- 部分: {data['partial']}
- 缺失: {data['missing']}
- 过期: {data['outdated']}
- 平均置信度: {data['avg_confidence']:.2f}
"""
        else:
            report += "暂无知识改进数据\n"

        report += f"""

【总体评估】
{analysis['overall_assessment']}

【改进建议】
"""

        # 基于分析结果生成建议
        suggestions = []

        if "period_comparison" in analysis and analysis["period_comparison"]:
            time_change = analysis["period_comparison"].get("time_change_percent", 0)
            if time_change > 5:
                suggestions.append("1. 优化智能体执行时间，考虑并行执行或缓存机制")

            quality_change = analysis["period_comparison"].get("quality_change_percent", 0)
            if quality_change < 0:
                suggestions.append("2. 检查并优化验证逻辑，提升输出质量")

        if "skill_improvements" in analysis:
            for agent, data in analysis["skill_improvements"].items():
                if data["gap"] > 10:
                    suggestions.append(f"3. 提升{agent}的技能水平，缩小与目标的差距")

        if not suggestions:
            suggestions.append("当前系统运行良好，继续保持")

        report += "\n".join(suggestions)

        report += """

===========================================
"""

        return report


if __name__ == "__main__":
    analyzer = HistoryAnalyzer()

    print("=" * 60)
    print("改进效果分析")
    print("=" * 60)

    # 生成报告
    report = analyzer.generate_improvement_report()
    print(report)

    # 保存报告
    report_file = "/workspace/projects/data/improvement_effectiveness_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n报告已保存到: {report_file}")
