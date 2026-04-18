#!/usr/bin/env python3
"""
运行带元智能体的监督分析
"""
import os
import sys

sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.workflow_meta_supervised import MetaSupervisedWorkflow


def main():
    print("=" * 60)
    print("BTC缠论分析 - 元智能体监督版")
    print("=" * 60)

    workflow = MetaSupervisedWorkflow()

    print("\n开始执行分析流程...")
    result = workflow.run("分析BTCUSDT 4小时K线，制定交易决策")

    print("\n" + "=" * 60)
    print("分析完成")
    print("=" * 60)

    # 输出元智能体报告摘要
    meta_report = result.get("meta_report", {})
    if meta_report:
        print("\n【元智能体监督摘要】")

        system_status = meta_report.get("system_status", {})
        print(f"✓ 系统健康度: {system_status.get('overall_health', '未知')}")
        print(f"✓ 知识库完整度: {system_status.get('knowledge_completeness', 0):.1f}%")
        print(f"✓ 技能平均分: {system_status.get('skill_score', 0):.1f}")
        print(f"✓ 系统成功率: {system_status.get('success_rate', 0):.1f}%")

        improvements = meta_report.get("improvement_recommendations", {})
        print(f"✓ 改进候选数: {improvements.get('total_candidates', 0)}")

        learning_plans = meta_report.get("learning_plans", {})
        print(f"✓ 学习计划总数: {learning_plans.get('total_effort_hours', 0)}小时")

    # 输出验证结果
    validation_results = result.get("validation_results", {})
    if validation_results:
        print("\n【验证结果】")
        for agent, validation in validation_results.items():
            status = validation.get("status", "UNKNOWN")
            print(f"✓ {agent}: {status}")
            if status != "PASS":
                print(f"  - 消息: {validation.get('message', '')}")

    # 输出执行统计
    execution_times = result.get("execution_times", {})
    if execution_times:
        print("\n【执行时间统计】")
        total_time = 0
        for agent, exec_time in execution_times.items():
            print(f"✓ {agent}: {exec_time:.2f}秒")
            total_time += exec_time
        print(f"✓ 总执行时间: {total_time:.2f}秒")

    # 输出错误
    errors = result.get("errors", [])
    if errors:
        print("\n【执行错误】")
        for error in errors:
            print(f"✗ {error}")

    print("\n报告已保存到: /workspace/projects/data/btc_analysis_report.txt")


if __name__ == "__main__":
    main()
