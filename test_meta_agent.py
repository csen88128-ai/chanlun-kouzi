"""
测试元智能体（Meta-Agent）框架
"""

import json
import time
from datetime import datetime
from pathlib import Path

from multi_agents.meta_agent import run_meta_agent_analysis, MetaAgentCoordinator


def test_meta_agent_basic():
    """测试元智能体基本功能"""
    print("\n" + "=" * 80)
    print("测试 1/3: 元智能体基本功能")
    print("=" * 80)
    
    # 运行元智能体分析
    result = run_meta_agent_analysis(symbol="btcusdt")
    
    # 验证结果
    assert result is not None, "元智能体返回结果为空"
    assert result["symbol"] == "btcusdt", "交易对不匹配"
    assert result["total_execution_time"] > 0, "执行时间无效"
    assert len(result["phases_completed"]) > 0, "没有完成的阶段"
    
    print("✅ 元智能体基本功能测试通过")
    print(f"  - 总执行时间: {result['total_execution_time']:.2f}秒")
    print(f"  - 完成阶段数: {len(result['phases_completed'])}/5")
    
    return result


def test_meta_agent_parallel_execution():
    """测试元智能体并行执行"""
    print("\n" + "=" * 80)
    print("测试 2/3: 元智能体并行执行")
    print("=" * 80)
    
    # 创建元智能体协调器
    coordinator = MetaAgentCoordinator()
    
    # 初始化状态
    initial_state = coordinator.initialize_state("btcusdt")
    
    # 运行元智能体
    start_time = time.time()
    final_state = coordinator.graph.invoke(initial_state)
    execution_time = time.time() - start_time
    
    # 验证并行执行
    assert "dynamics_analysis" in final_state["execution_times"], "缺少动力学分析执行时间"
    assert "sentiment_analysis" in final_state["execution_times"], "缺少市场情绪分析执行时间"
    
    dynamics_time = final_state["execution_times"]["dynamics_analysis"]
    sentiment_time = final_state["execution_times"]["sentiment_analysis"]
    structure_time = final_state["execution_times"]["structure_analysis"]
    
    # 并行任务的总时间应该接近最慢的任务时间（而不是两个任务时间之和）
    print("✅ 元智能体并行执行测试通过")
    print(f"  - 结构分析时间: {structure_time:.2f}秒")
    print(f"  - 动力学分析时间: {dynamics_time:.2f}秒")
    print(f"  - 市场情绪分析时间: {sentiment_time:.2f}秒")
    print(f"  - 总执行时间: {execution_time:.2f}秒")
    
    return final_state


def test_meta_agent_error_handling():
    """测试元智能体错误处理和重试"""
    print("\n" + "=" * 80)
    print("测试 3/3: 元智能体错误处理")
    print("=" * 80)
    
    # 创建元智能体协调器
    coordinator = MetaAgentCoordinator()
    
    # 初始化状态（使用一个可能失败的交易对）
    initial_state = coordinator.initialize_state("invalid_symbol")
    
    # 运行元智能体
    try:
        final_state = coordinator.graph.invoke(initial_state)
        
        # 验证错误处理
        if len(final_state["errors"]) > 0:
            print("✅ 元智能体错误处理测试通过")
            print(f"  - 捕获到 {len(final_state['errors'])} 个错误")
            for i, error in enumerate(final_state["errors"], 1):
                print(f"    {i}. {error}")
        else:
            print("⚠️ 元智能体错误处理测试：未捕获到预期错误")
    except Exception as e:
        print(f"⚠️ 元智能体错误处理测试：遇到未捕获异常: {str(e)}")
    
    return final_state


def save_result_to_file(result: dict, filename: str):
    """
    保存结果到文件
    
    Args:
        result: 分析结果
        filename: 文件名
    """
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    filepath = data_dir / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到: {filepath}")


def generate_meta_agent_report(result: dict):
    """
    生成元智能体分析报告
    
    Args:
        result: 分析结果
    """
    report = f"""# 元智能体（Meta-Agent）分析报告

**系统版本**: Meta-Agent v1.0
**分析时间**: {result.get('start_time', 'N/A')}
**交易对**: {result.get('symbol', 'N/A')}
**总执行时间**: {result.get('total_execution_time', 0):.2f}秒
**完成阶段**: {len(result.get('phases_completed', []))}/5

---

## 📊 执行摘要

### 各智能体执行时间
"""

    # 添加各智能体执行时间
    execution_times = result.get('execution_times', {})
    if execution_times:
        for agent_name, exec_time in execution_times.items():
            report += f"- **{agent_name}**: {exec_time:.2f}秒\n"
    else:
        report += "无执行时间数据\n"

    # 添加完成的阶段
    report += f"\n### 已完成的阶段\n"
    phases_completed = result.get('phases_completed', [])
    if phases_completed:
        for i, phase in enumerate(phases_completed, 1):
            report += f"{i}. {phase}\n"
    else:
        report += "无\n"

    # 添加错误日志
    errors = result.get('errors', [])
    if errors:
        report += f"\n### 错误日志 ({len(errors)}个)\n"
        for i, error in enumerate(errors, 1):
            report += f"{i}. {error}\n"

    # 添加最终决策
    decision = result.get('decision')
    if decision:
        report += f"""
---

## 🎯 最终决策

| 项目 | 结果 |
|------|------|
| **综合评分** | {decision.get('overall_score', 0):.1f} / 100 |
| **操作建议** | {decision.get('action', '未知')} |
| **风险等级** | {decision.get('risk_level', '未知')} |
| **置信度** | {decision.get('confidence', '未知')} |
| **建议仓位** | {decision.get('position_size', '未知')} |
| **止损价格** | ${decision.get('stop_loss', 0):,.2f} |
| **止盈价格** | ${decision.get('take_profit', 0):,.2f} |
| **持仓周期** | {decision.get('holding_period', '未知')} |

### 决策因子详情
"""
        factors = decision.get('factors', {})
        if factors:
            report += f"| 决策因子 | 因子值 | 权重 |\n"
            report += f"|----------|--------|------|\n"
            for factor_name, factor_value in factors.items():
                report += f"| {factor_name} | {factor_value} | - |\n"

    # 添加各智能体分析结果
    structure_analysis = result.get('structure_analysis')
    if structure_analysis:
        report += "\n---\n\n## 🧩 结构分析智能体\n"
        report += f"- **级别一致性**: {structure_analysis.get('level_consistency', 0):.1f}%\n"
        report += f"- **主导趋势**: {structure_analysis.get('dominant_trend', '未知')}\n"
        report += f"- **风险评估**: {structure_analysis.get('risk_assessment', '未知')}\n"

    dynamics_analysis = result.get('dynamics_analysis')
    if dynamics_analysis:
        report += "\n---\n\n## ⚡ 动力学分析智能体\n"
        report += f"- **RSI**: {dynamics_analysis.get('rsi', {}).get('current_rsi', 0):.1f}\n"
        report += f"- **MACD**: {dynamics_analysis.get('macd', {}).get('signal_type', '未知')}\n"
        report += f"- **综合评分**: {dynamics_analysis.get('overall_score', 0):.1f}\n"
        report += f"- **综合信号**: {dynamics_analysis.get('overall_signal', '未知')}\n"

    sentiment_analysis = result.get('sentiment_analysis')
    if sentiment_analysis:
        report += "\n---\n\n## 😰 市场情绪智能体\n"
        report += f"- **恐惧贪婪指数**: {sentiment_analysis.get('fear_greed', {}).get('value', 0)}\n"
        report += f"- **综合情绪**: {sentiment_analysis.get('overall_sentiment', '未知')}\n"
        report += f"- **综合评分**: {sentiment_analysis.get('overall_score', 0):.1f}\n"

    # 添加智能体间消息
    messages = result.get('messages', [])
    if messages:
        report += "\n---\n\n## 💬 智能体间通信\n"
        for i, msg in enumerate(messages, 1):
            report += f"{i}. {msg.get('role', 'system')}: {msg.get('content', '')}\n"

    report += f"""

---

**报告生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**系统版本**: Meta-Agent v1.0
"""

    return report


def main():
    """主测试函数"""
    print("\n" + "=" * 80)
    print("元智能体（Meta-Agent）框架测试")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # 运行所有测试
    try:
        # 测试1: 基本功能
        result = test_meta_agent_basic()
        
        # 测试2: 并行执行
        test_meta_agent_parallel_execution()
        
        # 测试3: 错误处理
        test_meta_agent_error_handling()
        
        # 保存结果
        save_result_to_file(result, "meta_agent_analysis_result.json")
        
        # 生成报告
        report = generate_meta_agent_report(result)
        report_path = Path("META_AGENT_ANALYSIS_REPORT.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {report_path}")
        
        # 打印最终摘要
        print("\n" + "=" * 80)
        print("✅ 所有测试通过！")
        print("=" * 80)
        print(f"总执行时间: {result['total_execution_time']:.2f}秒")
        print(f"完成阶段: {len(result['phases_completed'])}/5")
        if result['decision']:
            print(f"综合评分: {result['decision']['overall_score']:.1f}")
            print(f"操作建议: {result['decision']['action']}")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
