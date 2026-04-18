"""
缠论买卖点识别模块
实现第一类买卖点、第二类买卖点、第三类买卖点的识别

缠论买卖点定义：
1. 第一类买点（一买）：某级别下跌趋势中，最后一个中枢下沿出现背驰
2. 第二类买点（二买）：一买之后，向上笔突破最后一个中枢上沿后回抽不破下沿
3. 第三类买点（三买）：某级别上涨趋势中，向上笔突破最后一个中枢上沿后回抽不破下沿
4. 第一类卖点（一卖）：某级别上涨趋势中，最后一个中枢上沿出现背驰
5. 第二类卖点（二卖）：一卖之后，向下笔跌破最后一个中枢下沿后反弹不破上沿
6. 第三类卖点（三卖）：某级别下跌趋势中，向下笔跌破最后一个中枢下沿后反弹不破上沿
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum
import pandas as pd


class BuySellType(Enum):
    """买卖点类型"""
    FIRST_BUY = "一买"  # 第一类买点
    SECOND_BUY = "二买"  # 第二类买点
    THIRD_BUY = "三买"  # 第三类买点
    FIRST_SELL = "一卖"  # 第一类卖点
    SECOND_SELL = "二卖"  # 第二类卖点
    THIRD_SELL = "三卖"  # 第三类卖点


class BuySellDirection(Enum):
    """买卖点方向"""
    BUY = "买"  # 买入点
    SELL = "卖"  # 卖出点


@dataclass
class BuySellPoint:
    """买卖点数据结构"""
    type: BuySellType  # 买卖点类型
    direction: BuySellDirection  # 买卖方向
    index: int  # K线索引
    price: float  # 价格
    level: int  # 缠论级别（1级、2级、3级、4级）
    reliability: str  # 可靠性（高、中、低）
    description: str  # 描述
    zhongshu_index: int  # 关联的中枢索引
    divergence: Optional[bool] = None  # 是否有背驰
    macd_strength: Optional[float] = None  # MACD背驰强度


@dataclass
class BuySellAnalysisResult:
    """买卖点分析结果"""
    buy_points: List[BuySellPoint] = field(default_factory=list)
    sell_points: List[BuySellPoint] = field(default_factory=list)
    latest_buy_point: Optional[BuySellPoint] = None
    latest_sell_point: Optional[BuySellPoint] = None
    trend: str = "未知"  # 当前趋势
    next_buy_level: int = 0  # 下一个买入点的级别
    next_sell_level: int = 0  # 下一个卖出点的级别


class BuySellPointAnalyzer:
    """买卖点识别器"""

    def __init__(self, df: pd.DataFrame, bi: List[Any], segment: List[Any], zhongshu: Any):
        """
        初始化买卖点识别器

        Args:
            df: K线数据
            bi: 笔列表
            segment: 线段列表
            zhongshu: 中枢对象
        """
        self.df = df
        self.bi = bi
        self.segment = segment
        self.zhongshu = zhongshu

    def identify_all_buy_sell_points(self) -> BuySellAnalysisResult:
        """
        识别所有买卖点

        Returns:
            买卖点分析结果
        """
        result = BuySellAnalysisResult()

        # 获取中枢信息
        zhongshu_info = self._get_zhongshu_info()
        if not zhongshu_info:
            return result

        # 识别第一类买点
        result.buy_points.extend(self._identify_first_buy(zhongshu_info))

        # 识别第二类买点
        result.buy_points.extend(self._identify_second_buy(zhongshu_info))

        # 识别第三类买点
        result.buy_points.extend(self._identify_third_buy(zhongshu_info))

        # 识别第一类卖点
        result.sell_points.extend(self._identify_first_sell(zhongshu_info))

        # 识别第二类卖点
        result.sell_points.extend(self._identify_second_sell(zhongshu_info))

        # 识别第三类卖点
        result.sell_points.extend(self._identify_third_sell(zhongshu_info))

        # 获取最新的买卖点
        if result.buy_points:
            result.latest_buy_point = result.buy_points[-1]
        if result.sell_points:
            result.latest_sell_point = result.sell_points[-1]

        # 判断趋势
        result.trend = self._determine_trend(zhongshu_info)

        # 设置下一个买卖点的级别
        result.next_buy_level = self._get_next_buy_level(zhongshu_info)
        result.next_sell_level = self._get_next_sell_level(zhongshu_info)

        return result

    def _get_zhongshu_info(self) -> Dict[str, Any]:
        """
        获取中枢信息

        Returns:
            中枢信息字典
        """
        if self.zhongshu is None or not hasattr(self.zhongshu, '__dict__'):
            return {}

        try:
            if hasattr(self.zhongshu, 'high') and hasattr(self.zhongshu, 'low'):
                return {
                    'high': self.zhongshu.high,
                    'low': self.zhongshu.low,
                    'high_point': self.zhongshu.high_point if hasattr(self.zhongshu, 'high_point') else self.zhongshu.high,
                    'low_point': self.zhongshu.low_point if hasattr(self.zhongshu, 'low_point') else self.zhongshu.low,
                    'level': self.zhongshu.level if hasattr(self.zhongshu, 'level') else 1,
                    'start_index': self.zhongshu.start_index if hasattr(self.zhongshu, 'start_index') else 0,
                    'end_index': self.zhongshu.end_index if hasattr(self.zhongshu, 'end_index') else len(self.df) - 1,
                }
        except Exception as e:
            pass

        return {}

    def _identify_first_buy(self, zhongshu_info: Dict[str, Any]) -> List[BuySellPoint]:
        """
        识别第一类买点

        定义：某级别下跌趋势中，最后一个中枢下沿出现背驰

        Args:
            zhongshu_info: 中枢信息

        Returns:
            第一类买点列表
        """
        points = []

        # 检查是否在下跌趋势
        if self._is_downtrend():
            # 检查是否在中枢下沿附近
            latest_price = self.df['close'].iloc[-1]
            if latest_price <= zhongshu_info['low'] * 1.02:  # 允许2%的误差
                # 检查是否有背驰
                has_divergence = self._check_divergence(direction='down')

                point = BuySellPoint(
                    type=BuySellType.FIRST_BUY,
                    direction=BuySellDirection.BUY,
                    index=len(self.df) - 1,
                    price=latest_price,
                    level=zhongshu_info['level'],
                    reliability="高" if has_divergence else "中",
                    description="下跌趋势中，中枢下沿出现背驰" if has_divergence else "下跌趋势中，中枢下沿",
                    zhongshu_index=0,
                    divergence=has_divergence,
                    macd_strength=self._calculate_macd_divergence_strength() if has_divergence else None
                )
                points.append(point)

        return points

    def _identify_second_buy(self, zhongshu_info: Dict[str, Any]) -> List[BuySellPoint]:
        """
        识别第二类买点

        定义：一买之后，向上笔突破最后一个中枢上沿后回抽不破下沿

        Args:
            zhongshu_info: 中枢信息

        Returns:
            第二类买点列表
        """
        points = []

        # 检查是否有第一类买点
        if not self._has_first_buy():
            return points

        # 检查是否向上突破中枢上沿
        latest_price = self.df['close'].iloc[-1]
        if latest_price >= zhongshu_info['high']:
            # 检查是否回抽不破下沿
            if self._check_pullback(zhongshu_info['low']):
                point = BuySellPoint(
                    type=BuySellType.SECOND_BUY,
                    direction=BuySellDirection.BUY,
                    index=len(self.df) - 1,
                    price=latest_price,
                    level=zhongshu_info['level'],
                    reliability="高",
                    description="向上突破中枢上沿后回抽不破下沿，确认趋势反转",
                    zhongshu_index=0,
                    divergence=False
                )
                points.append(point)

        return points

    def _identify_third_buy(self, zhongshu_info: Dict[str, Any]) -> List[BuySellPoint]:
        """
        识别第三类买点

        定义：某级别上涨趋势中，向上笔突破最后一个中枢上沿后回抽不破下沿

        Args:
            zhongshu_info: 中枢信息

        Returns:
            第三类买点列表
        """
        points = []

        # 检查是否在上涨趋势
        if self._is_uptrend():
            # 检查是否向上突破中枢上沿
            latest_price = self.df['close'].iloc[-1]
            if latest_price >= zhongshu_info['high']:
                # 检查是否回抽不破下沿
                if self._check_pullback(zhongshu_info['low']):
                    point = BuySellPoint(
                        type=BuySellType.THIRD_BUY,
                        direction=BuySellDirection.BUY,
                        index=len(self.df) - 1,
                        price=latest_price,
                        level=zhongshu_info['level'],
                        reliability="中",
                        description="上涨趋势中，向上突破中枢上沿后回抽不破下沿，趋势延续",
                        zhongshu_index=0,
                        divergence=False
                    )
                    points.append(point)

        return points

    def _identify_first_sell(self, zhongshu_info: Dict[str, Any]) -> List[BuySellPoint]:
        """
        识别第一类卖点

        定义：某级别上涨趋势中，最后一个中枢上沿出现背驰

        Args:
            zhongshu_info: 中枢信息

        Returns:
            第一类卖点列表
        """
        points = []

        # 检查是否在上涨趋势
        if self._is_uptrend():
            # 检查是否在中枢上沿附近
            latest_price = self.df['close'].iloc[-1]
            if latest_price >= zhongshu_info['high'] * 0.98:  # 允许2%的误差
                # 检查是否有背驰
                has_divergence = self._check_divergence(direction='up')

                point = BuySellPoint(
                    type=BuySellType.FIRST_SELL,
                    direction=BuySellDirection.SELL,
                    index=len(self.df) - 1,
                    price=latest_price,
                    level=zhongshu_info['level'],
                    reliability="高" if has_divergence else "中",
                    description="上涨趋势中，中枢上沿出现背驰" if has_divergence else "上涨趋势中，中枢上沿",
                    zhongshu_index=0,
                    divergence=has_divergence,
                    macd_strength=self._calculate_macd_divergence_strength() if has_divergence else None
                )
                points.append(point)

        return points

    def _identify_second_sell(self, zhongshu_info: Dict[str, Any]) -> List[BuySellPoint]:
        """
        识别第二类卖点

        定义：一卖之后，向下笔跌破最后一个中枢下沿后反弹不破上沿

        Args:
            zhongshu_info: 中枢信息

        Returns:
            第二类卖点列表
        """
        points = []

        # 检查是否有第一类卖点
        if not self._has_first_sell():
            return points

        # 检查是否向下跌破中枢下沿
        latest_price = self.df['close'].iloc[-1]
        if latest_price <= zhongshu_info['low']:
            # 检查是否反弹不破上沿
            if self._check_bounce(zhongshu_info['high']):
                point = BuySellPoint(
                    type=BuySellType.SECOND_SELL,
                    direction=BuySellDirection.SELL,
                    index=len(self.df) - 1,
                    price=latest_price,
                    level=zhongshu_info['level'],
                    reliability="高",
                    description="向下跌破中枢下沿后反弹不破上沿，确认趋势反转",
                    zhongshu_index=0,
                    divergence=False
                )
                points.append(point)

        return points

    def _identify_third_sell(self, zhongshu_info: Dict[str, Any]) -> List[BuySellPoint]:
        """
        识别第三类卖点

        定义：某级别下跌趋势中，向下笔跌破最后一个中枢下沿后反弹不破上沿

        Args:
            zhongshu_info: 中枢信息

        Returns:
            第三类卖点列表
        """
        points = []

        # 检查是否在下跌趋势
        if self._is_downtrend():
            # 检查是否向下跌破中枢下沿
            latest_price = self.df['close'].iloc[-1]
            if latest_price <= zhongshu_info['low']:
                # 检查是否反弹不破上沿
                if self._check_bounce(zhongshu_info['high']):
                    point = BuySellPoint(
                        type=BuySellType.THIRD_SELL,
                        direction=BuySellDirection.SELL,
                        index=len(self.df) - 1,
                        price=latest_price,
                        level=zhongshu_info['level'],
                        reliability="中",
                        description="下跌趋势中，向下跌破中枢下沿后反弹不破上沿，趋势延续",
                        zhongshu_index=0,
                        divergence=False
                    )
                    points.append(point)

        return points

    def _is_uptrend(self) -> bool:
        """判断是否上涨趋势"""
        if not self.segment or len(self.segment) < 2:
            return False

        # 检查最后两段线段的方向
        last_segment = self.segment[-1]
        if hasattr(last_segment, 'direction'):
            return last_segment.direction == 'up'

        return False

    def _is_downtrend(self) -> bool:
        """判断是否下跌趋势"""
        if not self.segment or len(self.segment) < 2:
            return False

        # 检查最后两段线段的方向
        last_segment = self.segment[-1]
        if hasattr(last_segment, 'direction'):
            return last_segment.direction == 'down'

        return False

    def _has_first_buy(self) -> bool:
        """检查是否有第一类买点"""
        # 简化判断：检查最近是否有向上突破中枢下沿的信号
        return self._is_uptrend()

    def _has_first_sell(self) -> bool:
        """检查是否有第一类卖点"""
        # 简化判断：检查最近是否有向下跌破中枢上沿的信号
        return self._is_downtrend()

    def _check_pullback(self, zhongshu_low: float) -> bool:
        """
        检查是否回抽不破下沿

        Args:
            zhongshu_low: 中枢下沿

        Returns:
            是否回抽不破下沿
        """
        # 检查最近几根K线的最低价是否高于中枢下沿
        recent_lows = self.df['low'].tail(10)
        return all(low > zhongshu_low for low in recent_lows)

    def _check_bounce(self, zhongshu_high: float) -> bool:
        """
        检查是否反弹不破上沿

        Args:
            zhongshu_high: 中枢上沿

        Returns:
            是否反弹不破上沿
        """
        # 检查最近几根K线的最高价是否低于中枢上沿
        recent_highs = self.df['high'].tail(10)
        return all(high < zhongshu_high for high in recent_highs)

    def _check_divergence(self, direction: str) -> bool:
        """
        检查是否有背驰

        Args:
            direction: 方向（'up'或'down'）

        Returns:
            是否有背驰
        """
        # 简化判断：基于MACD
        try:
            # 计算MACD
            df = self.df.copy()
            df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema12'] - df['ema26']
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['histogram'] = df['macd'] - df['signal']

            # 检查价格创新高/新低，但MACD没有创新高/新低
            if direction == 'up':
                # 检查顶背驰
                recent_prices = df['close'].tail(20)
                recent_macd = df['macd'].tail(20)

                price_new_high = recent_prices.iloc[-1] == recent_prices.max()
                macd_not_new_high = recent_macd.iloc[-1] < recent_macd.max()

                return price_new_high and macd_not_new_high
            else:
                # 检查底背驰
                recent_prices = df['close'].tail(20)
                recent_macd = df['macd'].tail(20)

                price_new_low = recent_prices.iloc[-1] == recent_prices.min()
                macd_not_new_low = recent_macd.iloc[-1] > recent_macd.min()

                return price_new_low and macd_not_new_low

        except Exception as e:
            return False

    def _calculate_macd_divergence_strength(self) -> float:
        """
        计算MACD背驰强度

        Returns:
            背驰强度（0-100）
        """
        try:
            df = self.df.copy()
            df['ema12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema26'] = df['close'].ewm(span=26, adjust=False).mean()
            df['macd'] = df['ema12'] - df['ema26']
            df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['histogram'] = df['macd'] - df['signal']

            # 计算MACD的绝对值
            macd_abs = abs(df['macd'].iloc[-1])

            # 转换为0-100的强度
            strength = min(100, macd_abs * 1000)
            return strength

        except Exception as e:
            return 0.0

    def _determine_trend(self, zhongshu_info: Dict[str, Any]) -> str:
        """
        判断趋势

        Args:
            zhongshu_info: 中枢信息

        Returns:
            趋势（向上、向下、盘整）
        """
        if self._is_uptrend():
            return "向上"
        elif self._is_downtrend():
            return "向下"
        else:
            return "盘整"

    def _get_next_buy_level(self, zhongshu_info: Dict[str, Any]) -> int:
        """
        获取下一个买入点的级别

        Args:
            zhongshu_info: 中枢信息

        Returns:
            级别（0表示无）
        """
        # 简化判断：如果在下跌趋势，返回中枢级别
        if self._is_downtrend():
            return zhongshu_info.get('level', 1)
        return 0

    def _get_next_sell_level(self, zhongshu_info: Dict[str, Any]) -> int:
        """
        获取下一个卖出点的级别

        Args:
            zhongshu_info: 中枢信息

        Returns:
            级别（0表示无）
        """
        # 简化判断：如果在上涨趋势，返回中枢级别
        if self._is_uptrend():
            return zhongshu_info.get('level', 1)
        return 0


def identify_buy_sell_points(df: pd.DataFrame, bi: List[Any], segment: List[Any], zhongshu: Any) -> Dict[str, Any]:
    """
    识别买卖点（便捷函数）

    Args:
        df: K线数据
        bi: 笔列表
        segment: 线段列表
        zhongshu: 中枢对象

    Returns:
        买卖点分析结果（字典格式）
    """
    analyzer = BuySellPointAnalyzer(df, bi, segment, zhongshu)
    result = analyzer.identify_all_buy_sell_points()

    # 转换为字典格式
    return {
        'buy_points': [
            {
                'type': point.type.value,
                'direction': point.direction.value,
                'index': point.index,
                'price': point.price,
                'level': point.level,
                'reliability': point.reliability,
                'description': point.description,
                'zhongshu_index': point.zhongshu_index,
                'divergence': point.divergence,
                'macd_strength': point.macd_strength
            }
            for point in result.buy_points
        ],
        'sell_points': [
            {
                'type': point.type.value,
                'direction': point.direction.value,
                'index': point.index,
                'price': point.price,
                'level': point.level,
                'reliability': point.reliability,
                'description': point.description,
                'zhongshu_index': point.zhongshu_index,
                'divergence': point.divergence,
                'macd_strength': point.macd_strength
            }
            for point in result.sell_points
        ],
        'latest_buy_point': {
            'type': result.latest_buy_point.type.value,
            'direction': result.latest_buy_point.direction.value,
            'index': result.latest_buy_point.index,
            'price': result.latest_buy_point.price,
            'level': result.latest_buy_point.level,
            'reliability': result.latest_buy_point.reliability,
            'description': result.latest_buy_point.description,
            'zhongshu_index': result.latest_buy_point.zhongshu_index,
            'divergence': result.latest_buy_point.divergence,
            'macd_strength': result.latest_buy_point.macd_strength
        } if result.latest_buy_point else None,
        'latest_sell_point': {
            'type': result.latest_sell_point.type.value,
            'direction': result.latest_sell_point.direction.value,
            'index': result.latest_sell_point.index,
            'price': result.latest_sell_point.price,
            'level': result.latest_sell_point.level,
            'reliability': result.latest_sell_point.reliability,
            'description': result.latest_sell_point.description,
            'zhongshu_index': result.latest_sell_point.zhongshu_index,
            'divergence': result.latest_sell_point.divergence,
            'macd_strength': result.latest_sell_point.macd_strength
        } if result.latest_sell_point else None,
        'trend': result.trend,
        'next_buy_level': result.next_buy_level,
        'next_sell_level': result.next_sell_level,
        'total_buy_points': len(result.buy_points),
        'total_sell_points': len(result.sell_points)
    }
