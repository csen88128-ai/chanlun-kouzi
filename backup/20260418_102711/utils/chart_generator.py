"""
可视化图表模块
生成K线图并标注结构（笔、线段、中枢）
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd


class ChartGenerator:
    """图表生成器"""

    def __init__(self):
        pass

    def generate_ascii_chart(
        self,
        df: pd.DataFrame,
        structure_data: Optional[Dict[str, Any]] = None,
        last_n: int = 30
    ) -> str:
        """
        生成ASCII格式的K线图

        Args:
            df: K线数据
            structure_data: 结构分析数据
            last_n: 显示最后N根K线

        Returns:
            ASCII格式的图表
        """
        # 获取最后N根K线
        df_subset = df.tail(last_n).copy()

        # 计算价格范围
        high_max = df_subset['high'].max()
        low_min = df_subset['low'].min()
        price_range = high_max - low_min

        # 如果价格范围太小，使用最小范围
        if price_range < 1:
            price_range = 1

        # 图表高度
        chart_height = 20

        # 生成图表
        lines = []
        lines.append(f"\n{'=' * 80}")
        lines.append(f"K线图表 (最近{last_n}根)")
        lines.append(f"价格范围: {low_min:.2f} - {high_max:.2f}")
        lines.append(f"{'=' * 80}\n")

        # 生成价格轴和K线
        for i in range(chart_height, 0, -1):
            price = low_min + (price_range * i / chart_height)

            # 价格标签
            price_label = f"{price:.2f}"
            line = f"{price_label:10} |"

            # 绘制K线
            for _, row in df_subset.iterrows():
                high = row['high']
                low = row['low']
                open_price = row['open']
                close = row['close']

                # 判断K线颜色
                if close >= open_price:
                    color = "█"  # 阳线
                else:
                    color = "▓"  # 阴线

                # 绘制K线
                if high >= price >= low:
                    line += color
                else:
                    line += " "

            lines.append(line)

        # 时间轴
        lines.append(f"{'':10} |")
        time_line = f"{'':10} |"
        for i in range(0, len(df_subset), 5):
            time_line += f"{df_subset.iloc[i]['timestamp'][-8:-3]:^5}"
        lines.append(time_line)
        lines.append("")

        # 添加标注
        if structure_data:
            lines.append("--- 结构标注 ---")
            lines.append(f"最后价格: {df_subset['close'].iloc[-1]:.2f}")
            lines.append(f"最高价: {high_max:.2f}")
            lines.append(f"最低价: {low_min:.2f}")
            lines.append("")

        return "\n".join(lines)

    def generate_chart_description(
        self,
        df: pd.DataFrame,
        structure_data: Optional[Dict[str, Any]] = None,
        dynamics_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        生成图表描述文本

        Args:
            df: K线数据
            structure_data: 结构分析数据
            dynamics_data: 动力学分析数据

        Returns:
            图表描述
        """
        description = []

        # 基本信息
        description.append("## K线图表说明")
        description.append("")
        description.append(f"### 数据概览")
        description.append(f"- K线数量: {len(df)}")
        description.append(f"- 时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
        description.append(f"- 最新价格: {df['close'].iloc[-1]:.2f}")
        description.append(f"- 最高价: {df['high'].max():.2f}")
        description.append(f"- 最低价: {df['low'].min():.2f}")
        description.append("")

        # 结构标注
        if structure_data:
            algorithm_result = structure_data.get('algorithm_result', {})
            description.append(f"### 结构标注")
            description.append(f"- 分型数量: {algorithm_result.get('fractals', {}).get('count', 0)}")
            description.append(f"- 笔数量: {algorithm_result.get('bis', {}).get('count', 0)}")
            description.append(f"- 线段数量: {algorithm_result.get('segments', {}).get('count', 0)}")
            description.append(f"- 中枢数量: {algorithm_result.get('zhongshu', {}).get('count', 0)}")
            description.append("")

            # 最后一笔
            last_bi = algorithm_result.get('bis', {}).get('last_bi')
            if last_bi:
                description.append(f"### 最后一笔")
                description.append(f"- 方向: {last_bi.get('direction', '未知')}")
                description.append(f"- 起始价格: {last_bi.get('start_price', 0):.2f}")
                description.append(f"- 结束价格: {last_bi.get('end_price', 0):.2f}")
                description.append(f"- 高点: {last_bi.get('high', 0):.2f}")
                description.append(f"- 低点: {last_bi.get('low', 0):.2f}")
                description.append("")

        # 动力学标注
        if dynamics_data:
            algorithm_result = dynamics_data.get('algorithm_result', {})
            macd = algorithm_result.get('macd', {})
            divergences = algorithm_result.get('divergences', {})

            description.append(f"### 动力学标注")
            description.append(f"- MACD状态: {macd.get('macd_state', '未知')}")
            description.append(f"- DIF值: {macd.get('dif', 0):.4f}")
            description.append(f"- DEA值: {macd.get('dea', 0):.4f}")
            description.append(f"- MACD柱: {macd.get('macd', 0):.4f}")
            description.append(f"- 交叉类型: {macd.get('cross_type', '无')}")
            description.append(f"- 力度: {macd.get('strength', 0):.2f}")
            description.append("")
            description.append(f"### 背驰信号")
            description.append(f"- 背驰数量: {divergences.get('count', 0)}")
            if divergences.get('latest'):
                latest_div = divergences['latest']
                description.append(f"- 最新背驰: {latest_div.get('type', '未知')}")
                description.append(f"- 背驰强度: {latest_div.get('strength', '未知')}")
                description.append(f"- 价格区间: {latest_div.get('start_price', 0):.2f} - {latest_div.get('end_price', 0):.2f}")
            description.append("")

        # 图表解读
        description.append(f"### 图表解读")
        description.append(f"价格走势:")
        change = (df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0] * 100
        if change > 5:
            description.append(f"- 整体呈上涨趋势，涨幅 {change:.2f}%")
        elif change < -5:
            description.append(f"- 整体呈下跌趋势，跌幅 {abs(change):.2f}%")
        else:
            description.append(f"- 整体呈震荡走势，涨跌 {change:.2f}%")
        description.append("")

        # 波动性
        volatility = df['high'].max() - df['low'].min()
        avg_price = df['close'].mean()
        volatility_percent = (volatility / avg_price) * 100
        description.append(f"波动性:")
        if volatility_percent > 10:
            description.append(f"- 波动性较高，价格波动范围 {volatility:.2f} ({volatility_percent:.2f}%)")
        elif volatility_percent > 5:
            description.append(f"- 波动性适中，价格波动范围 {volatility:.2f} ({volatility_percent:.2f}%)")
        else:
            description.append(f"- 波动性较低，价格波动范围 {volatility:.2f} ({volatility_percent:.2f}%)")
        description.append("")

        return "\n".join(description)

    def generate_structure_annotations(
        self,
        df: pd.DataFrame,
        bis: List,
        segments: List,
        zhongshu_list: List
    ) -> List[Dict[str, Any]]:
        """
        生成结构标注数据（用于图表绘制）

        Args:
            df: K线数据
            bis: 笔列表
            segments: 线段列表
            zhongshu_list: 中枢列表

        Returns:
            标注数据列表
        """
        annotations = []

        # 笔标注
        for bi in bis[-5:]:  # 只标注最后5笔
            annotations.append({
                "type": "bi",
                "direction": bi.direction.value,
                "start_index": bi.start_index,
                "end_index": bi.end_index,
                "start_price": bi.start_price,
                "end_price": bi.end_price,
                "label": f"笔({bi.direction.value})"
            })

        # 线段标注
        for segment in segments[-3:]:  # 只标注最后3条线段
            annotations.append({
                "type": "segment",
                "direction": segment.direction.value,
                "start_price": segment.start_price,
                "end_price": segment.end_price,
                "label": f"线段({segment.direction.value})"
            })

        # 中枢标注
        for zhongshu in zhongshu_list[-2:]:  # 只标注最后2个中枢
            annotations.append({
                "type": "zhongshu",
                "high": zhongshu.high,
                "low": zhongshu.low,
                "high_point": zhongshu.high_point,
                "low_point": zhongshu.low_point,
                "label": f"中枢[{zhongshu.low:.2f}, {zhongshu.high:.2f}]"
            })

        return annotations

    def save_chart_description(
        self,
        description: str,
        symbol: str = "BTCUSDT",
        interval: str = "1h"
    ) -> str:
        """
        保存图表描述到文件

        Args:
            description: 图表描述
            symbol: 交易对
            interval: K线周期

        Returns:
            保存路径
        """
        workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
        reports_dir = os.path.join(workspace_path, "reports")
        os.makedirs(reports_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{symbol}_{interval}_chart_{timestamp}.md"
        save_path = os.path.join(reports_dir, filename)

        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(description)

        return save_path


# 全局实例
_chart_generator = ChartGenerator()


def generate_chart(
    df: pd.DataFrame,
    structure_data: Optional[Dict[str, Any]] = None,
    dynamics_data: Optional[Dict[str, Any]] = None,
    chart_type: str = "description",
    symbol: str = "BTCUSDT",
    interval: str = "1h"
) -> Dict[str, Any]:
    """
    生成图表

    Args:
        df: K线数据
        structure_data: 结构分析数据
        dynamics_data: 动力学分析数据
        chart_type: 图表类型 (ascii, description)
        symbol: 交易对
        interval: K线周期

    Returns:
        图表结果
    """
    result = {
        "chart_type": chart_type,
        "symbol": symbol,
        "interval": interval,
        "timestamp": datetime.now().isoformat()
    }

    if chart_type == "ascii":
        content = _chart_generator.generate_ascii_chart(df, structure_data)
        result["content"] = content
    elif chart_type == "description":
        content = _chart_generator.generate_chart_description(
            df, structure_data, dynamics_data
        )
        save_path = _chart_generator.save_chart_description(
            content, symbol, interval
        )
        result["content"] = content
        result["save_path"] = save_path
    else:
        result["error"] = f"Unsupported chart type: {chart_type}"

    return result
