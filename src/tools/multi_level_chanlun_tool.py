"""
多级别缠论分析工具
供结构分析智能体调用
"""
import json
import sys
import os
from typing import Dict, Any
from langchain.tools import tool

# 添加路径
sys.path.insert(0, '/workspace/projects')
sys.path.insert(0, '/workspace/projects/src')

from multi_agents.multi_level_chanlun_analyzer import MultiLevelChanLunAnalyzer


@tool
def analyze_multi_level_chanlun(symbol: str = "btcusdt", levels: str = "5m,30m,4h,1d") -> str:
    """
    进行多级别缠论分析，包括5m、30m、4h、1d四个级别的完整分析

    参数:
        symbol: 交易对，如 "btcusdt"
        levels: 需要分析的级别，如 "5m,30m,4h,1d"

    返回:
        JSON格式的多级别缠论分析结果，包含：
        - 各级别的缠论结构（分型、笔、线段、中枢、买卖点）
        - 级别递归验证
        - 高阶缠论理论（小转大、九段升级、区间套）
        - 综合决策建议

    使用场景:
        - 需要进行多级别缠论分析时
        - 需要识别不同级别的买卖点时
        - 需要验证级别递归关系时
        - 需要检测高阶缠论理论（小转大、九段升级、区间套）时
    """
    try:
        print(f"开始多级别缠论分析: {symbol}, 级别: {levels}")

        # 创建分析器
        analyzer = MultiLevelChanLunAnalyzer(symbol=symbol)

        # 1. 采集所有级别数据
        all_data = analyzer.collect_all_levels_data()

        # 2. 分析所有级别
        all_analysis = analyzer.analyze_all_levels()

        # 3. 高阶理论分析
        advanced_theory = analyzer.analyze_advanced_theory()

        # 4. 生成综合报告
        report = analyzer.generate_comprehensive_report()

        # 5. 构造返回结果
        result = {
            "status": "success",
            "symbol": symbol,
            "levels_analyzed": levels.split(","),
            "analysis": {
                "level_details": {},
                "advanced_theory": advanced_theory,
                "comprehensive_decision": report["comprehensive_decision"]
            }
        }

        # 添加各级别的详细信息
        for level in report["level_analysis"]:
            if report["level_analysis"][level]:
                level_info = {
                    "level": level,
                    "level_name": report["level_analysis"][level]["level_name"],
                    "kline_count": report["level_analysis"][level]["kline_count"],
                    "fractals": report["level_analysis"][level]["fractals"],
                    "bi": report["level_analysis"][level]["bi"],
                    "segment": report["level_analysis"][level]["segment"],
                    "zhongshu": report["level_analysis"][level]["zhongshu"],
                    "buy_sell_points": report["level_analysis"][level]["buy_sell_points"],
                    "trend": report["level_analysis"][level]["trend"],
                    "divergence": report["level_analysis"][level]["divergence"]
                }
                result["analysis"]["level_details"][level] = level_info

        print(f"多级别缠论分析完成")

        return json.dumps(result, ensure_ascii=False, indent=2)

    except Exception as e:
        error_result = {
            "status": "error",
            "message": f"多级别缠论分析失败: {str(e)}"
        }
        print(f"多级别缠论分析失败: {e}")
        import traceback
        traceback.print_exc()
        return json.dumps(error_result, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 测试工具
    print("=" * 80)
    print("测试多级别缠论分析工具")
    print("=" * 80)

    result = analyze_multi_level_chanlun(symbol="btcusdt", levels="30m,4h,1d")
    print(result)
