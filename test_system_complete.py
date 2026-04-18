#!/usr/bin/env python3
"""
完整系统测试 - 测试所有优化后的功能
"""
import os
import sys
import time
import json
from datetime import datetime

sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.knowledge_manager import KnowledgeManager
from multi_agents.skill_evaluator import SkillEvaluator
from multi_agents.execution_monitor import ExecutionMonitor
from multi_agents.self_improvement_engine import SelfImprovementEngine
from multi_agents.meta_agent import MetaAgent
from multi_agents.data_validator import DataValidator
from multi_agents.logic_validator import LogicValidator
from multi_agents.auto_improvement_executor import AutoImprovementExecutor
from multi_agents.history_analyzer import HistoryAnalyzer
from multi_agents.workflow_optimized_v2 import OptimizedWorkflow


def test_knowledge_manager():
    """测试知识库管理器"""
    print("\n" + "=" * 60)
    print("测试1: 知识库管理器")
    print("=" * 60)

    km = KnowledgeManager()

    # 获取摘要
    summary = km.get_summary()
    print(f"知识项总数: {summary['total_knowledge_items']}")
    print(f"整体完整度: {summary['overall_completeness']:.1f}%")
    print(f"完整: {summary['complete']}, 部分: {summary['partial']}, 缺失: {summary['missing']}, 过期: {summary['outdated']}")

    # 检查单个智能体
    completeness = km.check_completeness("data_collector")
    print(f"\ndata_collector 完整度: {completeness['completeness_rate']:.1f}%")

    return True


def test_skill_evaluator():
    """测试技能评估器"""
    print("\n" + "=" * 60)
    print("测试2: 技能评估器")
    print("=" * 60)

    se = SkillEvaluator()

    # 获取所有评估
    evaluations = se.get_all_evaluations()
    print(f"平均得分: {evaluations['overall_average']:.1f}")
    print(f"需要改进: {evaluations['needs_improvement']}")

    # 评估单个智能体
    evaluation = se.evaluate_agent("decision_maker")
    print(f"\ndecision_maker 评估:")
    print(f"  等级: {evaluation['level']}")
    print(f"  平均分: {evaluation['average_score']:.1f}")
    print(f"  需要改进: {evaluation['needs_improvement']}")

    return True


def test_execution_monitor():
    """测试执行监控器"""
    print("\n" + "=" * 60)
    print("测试3: 执行监控器")
    print("=" * 60)

    em = ExecutionMonitor()

    # 记录一次执行
    print("记录模拟执行...")
    record = em.record_execution(
        agent_type="test_agent",
        status=em.ExecutionStatus.SUCCESS,
        execution_time=5.5,
        input_data="测试输入",
        output_data="测试输出",
        validation_result={"pass": 5, "warning": 0, "error": 0},
        errors=[],
        warnings=[]
    )

    print(f"执行ID: {record.execution_id}")
    print(f"质量得分: {record.quality_score:.1f}")

    # 获取统计
    stats = em.get_agent_stats("test_agent")
    print(f"\ntest_agent 统计:")
    print(f"  总执行次数: {stats['total_executions']}")
    print(f"  成功率: {stats['success_rate']:.1f}%")
    print(f"  平均质量: {stats['average_quality']:.1f}")

    return True


def test_self_improvement_engine():
    """测试自我改进引擎"""
    print("\n" + "=" * 60)
    print("测试4: 自我改进引擎")
    print("=" * 60)

    sie = SelfImprovementEngine()

    # 生成系统报告
    report = sie.generate_system_report()
    print(f"系统健康度: {report['overall_health']}")
    print(f"知识库完整度: {report['knowledge']['overall_completeness']:.1f}%")
    print(f"技能平均分: {report['skills']['overall_average']:.1f}")
    print(f"系统成功率: {report['execution']['overall_success_rate']:.1f}%")
    print(f"待改进项: {report['improvements']['pending']}")

    # 生成学习计划
    learning_plan = sie.get_learning_plan("structure_analyzer")
    print(f"\nstructure_analyzer 学习计划:")
    print(f"  待行动数: {learning_plan['pending_actions_count']}")
    print(f"  总工作量: {learning_plan['total_effort_hours']}小时")
    print(f"  预计天数: {learning_plan['estimated_days']}天")

    return True


def test_meta_agent():
    """测试元智能体"""
    print("\n" + "=" * 60)
    print("测试5: 元智能体")
    print("=" * 60)

    ma = MetaAgent()

    # 检查系统状态
    status_str = ma._check_system_status()
    status = json.loads(status_str)
    print(f"系统健康度: {status['overall_health']}")
    print(f"知识库完整度: {status['knowledge_completeness']:.1f}%")
    print(f"技能得分: {status['skill_score']:.1f}")
    print(f"成功率: {status['success_rate']:.1f}%")

    # 检查单个智能体状态
    agent_status_str = ma._check_agent_status("decision_maker")
    agent_status = json.loads(agent_status_str)
    print(f"\ndecision_maker 状态:")
    print(f"  知识完整度: {agent_status['knowledge']['completeness']:.1f}%")
    print(f"  技能得分: {agent_status['skills']['score']:.1f}")
    print(f"  成功率: {agent_status['execution']['success_rate']:.1f}%")

    return True


def test_validators():
    """测试验证器"""
    print("\n" + "=" * 60)
    print("测试6: 验证器")
    print("=" * 60)

    # 测试数据验证器
    dv = DataValidator()
    test_data = json.dumps({
        "status": "success",
        "latest_price": 77000,
        "highest": 78000,
        "lowest": 76000,
        "h24_change": 2.5,
        "timestamp": datetime.now().isoformat()
    })

    data_validation = dv.validate_data(test_data, "data_collector")
    print(f"数据验证状态: {data_validation['status']}")
    print(f"验证通过: {data_validation['pass']}, 警告: {data_validation['warning']}, 错误: {data_validation['error']}")

    # 测试逻辑验证器
    lv = LogicValidator()
    test_dynamics = json.dumps({
        "rsi": 65,
        "rsi_status": "正常",
        "macd": 150,
        "macd_signal": 140,
        "macd_histogram": 10,
        "macd_signal_type": "金叉",
        "volatility": 0.05,
        "volume": 1000,
        "volume_status": "正常"
    })

    dynamics_validation = lv.validate_dynamics(test_dynamics, None)
    pass_count = sum(1 for v in dynamics_validation if v.level.value == "通过")
    warning_count = sum(1 for v in dynamics_validation if v.level.value == "警告")
    print(f"\n动力学验证: 通过 {pass_count}, 警告 {warning_count}")

    return True


def test_auto_improvement_executor():
    """测试自动化改进执行器"""
    print("\n" + "=" * 60)
    print("测试7: 自动化改进执行器")
    print("=" * 60)

    aie = AutoImprovementExecutor()

    # 分析但不执行
    results = aie.analyze_and_execute(auto_execute=False)
    print(f"总行动数: {results['total_actions']}")
    print(f"已执行: {results['executed']}, 跳过: {results['skipped']}, 失败: {results['failed']}")

    # 获取执行状态
    status = aie.get_execution_status()
    print(f"\n执行状态:")
    print(f"  总执行次数: {status['total_executions']}")
    print(f"  成功: {status['status_counts']['成功']}")
    print(f"  失败: {status['status_counts']['失败']}")
    print(f"  成功率: {status['success_rate']}%")

    return True


def test_history_analyzer():
    """测试历史分析器"""
    print("\n" + "=" * 60)
    print("测试8: 历史分析器")
    print("=" * 60)

    ha = HistoryAnalyzer()

    # 分析改进效果
    analysis = ha.analyze_improvement_effectiveness()
    print(f"总执行次数: {analysis['total_executions']}")
    print(f"近期执行次数: {analysis.get('recent_executions', 0)}")
    print(f"总体评估: {analysis['overall_assessment']}")

    # 分析趋势
    trends = ha.analyze_execution_trends("test_agent", days=7)
    if trends:
        print(f"\ntest_agent 趋势:")
        for trend in trends:
            print(f"  {trend.metric_name}: {trend.change_trend} ({trend.change_percent:+.1f}%)")

    return True


def test_optimized_workflow():
    """测试优化版工作流"""
    print("\n" + "=" * 60)
    print("测试9: 优化版工作流")
    print("=" * 60)

    print("初始化优化版工作流...")
    workflow = OptimizedWorkflow()

    print("运行工作流（数据采集+并行分析+验证+监督）...")

    start_time = time.time()

    # 运行工作流
    result = workflow.run("分析BTCUSDT 4小时K线，制定交易决策")

    end_time = time.time()

    print(f"\n工作流执行完成，耗时: {end_time - start_time:.2f}秒")

    # 统计结果
    print("\n执行时间统计:")
    for agent, exec_time in result.get("execution_times", {}).items():
        print(f"  {agent}: {exec_time:.2f}秒")

    print(f"\n验证结果:")
    for agent, validation in result.get("validation_results", {}).items():
        print(f"  {agent}: {validation.get('status', 'UNKNOWN')}")

    print(f"\n元智能体报告:")
    meta_report = result.get("meta_report", {})
    system_status = meta_report.get("system_status", {})
    print(f"  系统健康度: {system_status.get('overall_health', '未知')}")
    print(f"  知识库完整度: {system_status.get('knowledge_completeness', 0):.1f}%")
    print(f"  技能得分: {system_status.get('skill_score', 0):.1f}")
    print(f"  成功率: {system_status.get('success_rate', 0):.1f}%")

    return True


def generate_final_report():
    """生成最终测试报告"""
    print("\n" + "=" * 60)
    print("生成最终测试报告")
    print("=" * 60)

    # 历史分析
    ha = HistoryAnalyzer()
    report = ha.generate_improvement_report()

    print(report)

    # 保存报告
    report_file = "/workspace/projects/data/system_test_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n报告已保存到: {report_file}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("完整系统测试")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    test_results = []

    # 运行测试
    tests = [
        ("知识库管理器", test_knowledge_manager),
        ("技能评估器", test_skill_evaluator),
        ("执行监控器", test_execution_monitor),
        ("自我改进引擎", test_self_improvement_engine),
        ("元智能体", test_meta_agent),
        ("验证器", test_validators),
        ("自动化改进执行器", test_auto_improvement_executor),
        ("历史分析器", test_history_analyzer),
        ("优化版工作流", test_optimized_workflow),
    ]

    for test_name, test_func in tests:
        try:
            print(f"\n开始测试: {test_name}")
            result = test_func()
            test_results.append((test_name, "成功", ""))
            print(f"✓ {test_name} 测试通过")
        except Exception as e:
            error_msg = str(e)
            test_results.append((test_name, "失败", error_msg))
            print(f"✗ {test_name} 测试失败: {error_msg}")

    # 生成测试摘要
    print("\n" + "=" * 60)
    print("测试摘要")
    print("=" * 60)

    passed = sum(1 for _, status, _ in test_results if status == "成功")
    failed = sum(1 for _, status, _ in test_results if status == "失败")

    print(f"总测试数: {len(test_results)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {(passed / len(test_results) * 100):.1f}%")

    print("\n详细结果:")
    for test_name, status, error in test_results:
        symbol = "✓" if status == "成功" else "✗"
        print(f"  {symbol} {test_name}: {status}")
        if error:
            print(f"    错误: {error}")

    # 生成最终报告
    try:
        generate_final_report()
    except Exception as e:
        print(f"\n生成最终报告失败: {e}")

    print("\n" + "=" * 60)
    print(f"测试完成")
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
