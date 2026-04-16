"""
测试输出优化功能
测试研报生成、图表生成、历史决策回溯
"""
import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from utils.report_generator import generate_report
from utils.chart_generator import generate_chart
from utils.decision_history import record_decision, get_decision_statistics, generate_decision_report


def generate_test_data():
    """生成测试数据"""
    np.random.seed(42)

    # 生成K线数据
    prices = []
    price = 50000

    for i in range(100):
        change = np.random.normal(0, 200)
        price += change

        high = price + abs(np.random.normal(0, 50))
        low = price - abs(np.random.normal(0, 50))
        close = price
        open_price = prices[-1]['open'] if prices else close

        prices.append({
            'timestamp': f"2026-04-16 {i:02d}:00:00",
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': abs(np.random.normal(1000, 200))
        })

    return pd.DataFrame(prices)


def test_report_generator():
    """测试研报生成器"""
    print("=" * 80)
    print("测试研报生成器")
    print("=" * 80)
    print()

    # 准备测试数据
    symbol = "BTCUSDT"
    interval = "1h"

    structure_data = {
        "agent_response": """
结构分析结果：
- 分型数量：45个（顶分型22个，底分型23个）
- 笔数量：12根（向上笔6根，向下笔6根）
- 线段数量：3条（向上线段2条，向下线段1条）
- 中枢数量：1个
- 当前走势：上涨中
- 关键支撑位：49500
- 关键阻力位：50500
"""
    }

    dynamics_data = {
        "agent_response": """
动力学分析结果：
- MACD状态：strong_bullish
- DIF值：125.5
- DEA值：98.3
- MACD柱：54.4
- 交叉类型：golden_cross
- 背驰信号：无
- 市场动量：强
"""
    }

    sentiment_data = {
        "agent_response": """
市场情绪分析：
- 恐慌贪婪指数：65（贪婪）
- 资金费率：0.01%（正费率）
- 爆仓数据：多单爆仓较多
- 持仓量：增加
"""
    }

    cross_market_data = {
        "agent_response": """
跨市场分析：
- 标普500：上涨0.5%
- 黄金：上涨0.2%
- 美元指数：下跌0.3%
- 综合判断：利好
"""
    }

    onchain_data = {
        "agent_response": """
链上数据：
- 交易所净流出：500 BTC
- 巨鲸活动：净买入
- 活跃地址：增加3%
- 算力：稳定
"""
    }

    decision_data = {
        "agent_response": """
交易决策：
- 交易方向：long（做多）
- 置信度：75%
- 入场价格：50000-50200
- 止损价格：49500
- 止盈目标：51000，52000
- 建议仓位：15%
- 风险等级：medium

分析逻辑：
1. 结构：上涨趋势，突破关键阻力位
2. 动力学：MACD金叉，无背驰
3. 情绪：贪婪但不过度
4. 跨市场：美股、黄金、美元都利好
5. 链上：净流出，长期持有信号
6. 模拟盘：胜率55%，策略有效

综合判断：做多，置信度75%
"""
    }

    # 生成研报
    print("正在生成研报...")
    result = generate_report(
        symbol=symbol,
        interval=interval,
        structure_data=structure_data,
        dynamics_data=dynamics_data,
        sentiment_data=sentiment_data,
        cross_market_data=cross_market_data,
        onchain_data=onchain_data,
        decision_data=decision_data
    )

    print(f"✓ 研报生成成功")
    print(f"  - 保存路径: {result['save_path']}")
    print(f"  - 决策ID: {result.get('decision_id', 'N/A')}")
    print()

    # 读取研报内容
    with open(result['save_path'], 'r', encoding='utf-8') as f:
        content = f.read()

    print("研报内容预览（前500字符）：")
    print("-" * 80)
    print(content[:500] + "...")
    print("-" * 80)
    print()

    return True


def test_chart_generator():
    """测试图表生成器"""
    print("=" * 80)
    print("测试图表生成器")
    print("=" * 80)
    print()

    # 生成测试数据
    df = generate_test_data()
    print(f"✓ 生成测试数据: {len(df)} 根K线")
    print()

    # 生成ASCII图表
    print("正在生成ASCII图表...")
    result = generate_chart(
        df=df,
        chart_type="ascii",
        symbol="BTCUSDT",
        interval="1h"
    )

    if "error" in result:
        print(f"✗ 图表生成失败: {result['error']}")
        return False

    print("✓ ASCII图表生成成功")
    print()
    print("图表内容：")
    print("-" * 80)
    print(result['content'])
    print("-" * 80)
    print()

    # 生成图表描述
    print("正在生成图表描述...")
    result = generate_chart(
        df=df,
        chart_type="description",
        symbol="BTCUSDT",
        interval="1h"
    )

    if "error" in result:
        print(f"✗ 图表描述生成失败: {result['error']}")
        return False

    print(f"✓ 图表描述生成成功")
    print(f"  - 保存路径: {result['save_path']}")
    print()

    # 读取图表描述
    with open(result['save_path'], 'r', encoding='utf-8') as f:
        content = f.read()

    print("图表描述预览（前500字符）：")
    print("-" * 80)
    print(content[:500] + "...")
    print("-" * 80)
    print()

    return True


def test_decision_history():
    """测试历史决策回溯"""
    print("=" * 80)
    print("测试历史决策回溯")
    print("=" * 80)
    print()

    # 准备测试数据
    symbol = "BTCUSDT"
    interval = "1h"

    decision_data = {
        "agent_response": """
交易决策：
- 交易方向：long（做多）
- 置信度：75%
- 入场价格：50000
- 止损价格：49500
- 止盈目标：51000，52000
- 建议仓位：15%
- 风险等级：medium

关键因素：
- 突破关键阻力位
- MACD金叉
- 交易所净流出
"""
    }

    analysis_results = {
        'structure_analysis': {"agent_response": "上涨趋势"},
        'dynamics_analysis': {"agent_response": "金叉信号"},
        'sentiment_analysis': {"agent_response": "贪婪指数65"},
        'cross_market_analysis': {"agent_response": "跨市场利好"},
        'onchain_analysis': {"agent_response": "净流出500 BTC"}
    }

    # 记录决策
    print("正在记录决策...")
    record = record_decision(
        symbol=symbol,
        interval=interval,
        decision_data=decision_data,
        analysis_results=analysis_results
    )

    print(f"✓ 决策记录成功")
    print(f"  - 决策ID: {record.decision_id}")
    print(f"  - 方向: {record.direction}")
    print(f"  - 置信度: {record.confidence}%")
    print()

    # 获取决策统计
    print("正在获取决策统计...")
    stats = get_decision_statistics(last_n=50)

    print(f"✓ 决策统计获取成功")
    print(f"  - 总决策数: {stats['total']}")
    print(f"  - 已执行: {stats['executed']}")
    print(f"  - 已平仓: {stats['closed']}")
    print(f"  - 胜率: {stats['pnl']['win_rate']}%")
    print(f"  - 总盈亏: {stats['pnl']['total_pnl']}")
    print()

    # 生成决策报告
    print("正在生成决策报告...")
    report = generate_decision_report(last_n=10)

    print(f"✓ 决策报告生成成功")
    print()
    print("决策报告预览（前500字符）：")
    print("-" * 80)
    print(report[:500] + "...")
    print("-" * 80)
    print()

    return True


def main():
    """主测试函数"""
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 25 + "输出优化功能测试" + " " * 40 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    # 测试研报生成
    try:
        success1 = test_report_generator()
    except Exception as e:
        print(f"✗ 研报生成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success1 = False

    print()

    # 测试图表生成
    try:
        success2 = test_chart_generator()
    except Exception as e:
        print(f"✗ 图表生成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success2 = False

    print()

    # 测试历史决策回溯
    try:
        success3 = test_decision_history()
    except Exception as e:
        print(f"✗ 历史决策回溯测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        success3 = False

    print()
    print("=" * 80)
    print("测试结果")
    print("=" * 80)
    print(f"研报生成: {'✓ 通过' if success1 else '✗ 失败'}")
    print(f"图表生成: {'✓ 通过' if success2 else '✗ 失败'}")
    print(f"历史决策回溯: {'✓ 通过' if success3 else '✗ 失败'}")
    print()
    print("=" * 80)

    return success1 and success2 and success3


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
