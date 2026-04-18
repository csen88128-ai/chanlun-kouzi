"""
增强的JSON解析模块
"""
import json
import re
import logging
from typing import Any, Optional, Union, List, Dict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JSONParseError(Exception):
    """JSON解析错误"""
    pass


def safe_extract_json(text: str) -> Dict[str, Any]:
    """
    安全提取JSON，支持多种格式

    Args:
        text: 包含JSON的文本

    Returns:
        解析后的字典

    Raises:
        JSONParseError: 如果无法提取有效的JSON
    """
    if not text or not isinstance(text, str):
        raise JSONParseError("输入文本为空或不是字符串")

    text = text.strip()

    # 1. 尝试直接解析
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
        elif isinstance(data, list):
            return {"data": data}
    except json.JSONDecodeError:
        pass

    # 2. 尝试提取Markdown代码块中的JSON
    markdown_pattern = r'```(?:json)?\s*\n?([\s\S]*?)\n?```'
    matches = re.findall(markdown_pattern, text)
    for match in matches:
        try:
            data = json.loads(match.strip())
            if isinstance(data, dict):
                return data
            elif isinstance(data, list):
                return {"data": data}
        except json.JSONDecodeError:
            continue

    # 3. 尝试提取JSON对象（支持嵌套）
    json_pattern = r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}'
    matches = re.findall(json_pattern, text, re.DOTALL)

    # 按长度排序，优先尝试最长的（可能是完整的JSON）
    matches.sort(key=len, reverse=True)

    for match in matches:
        try:
            data = json.loads(match)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            continue

    # 4. 尝试提取JSON数组
    array_pattern = r'\[(?:[^\[\]]|(?:\[[^\[\]]*\]))*\]'
    matches = re.findall(array_pattern, text, re.DOTALL)
    matches.sort(key=len, reverse=True)

    for match in matches:
        try:
            data = json.loads(match)
            if isinstance(data, list):
                return {"data": data}
        except json.JSONDecodeError:
            continue

    # 如果所有方法都失败，抛出错误
    raise JSONParseError(
        f"无法从文本中提取有效的JSON数据。"
        f"文本前500字符: {text[:500]}"
    )


def extract_json_with_fallback(
    text: str,
    fallback_value: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    提取JSON，失败时返回默认值

    Args:
        text: 包含JSON的文本
        fallback_value: 失败时返回的默认值

    Returns:
        解析后的字典或默认值
    """
    try:
        return safe_extract_json(text)
    except JSONParseError as e:
        logger.warning(f"JSON解析失败，使用默认值: {e}")
        return fallback_value or {"error": "json_parse_failed", "raw_text": text[:500]}


def validate_json(data: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    验证JSON数据是否包含必需的键

    Args:
        data: JSON数据
        required_keys: 必需的键列表

    Returns:
        True如果包含所有必需的键，否则False
    """
    if not isinstance(data, dict):
        return False

    missing_keys = [key for key in required_keys if key not in data]
    if missing_keys:
        logger.warning(f"JSON缺少必需的键: {missing_keys}")
        return False

    return True


def safe_get_nested(
    data: Dict[str, Any],
    *keys: str,
    default: Any = None
) -> Any:
    """
    安全获取嵌套字典的值

    Args:
        data: 字典数据
        *keys: 键路径
        default: 默认值

    Returns:
        嵌套值或默认值
    """
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def clean_json_string(text: str) -> str:
    """
    清理JSON字符串，移除注释和多余空白

    Args:
        text: JSON字符串

    Returns:
        清理后的JSON字符串
    """
    # 移除单行注释
    text = re.sub(r'//.*?\n', '\n', text)
    # 移除多行注释
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    # 移除多余的空白
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def pretty_json(data: Union[Dict, List], indent: int = 2) -> str:
    """
    格式化JSON为美化字符串

    Args:
        data: JSON数据
        indent: 缩进空格数

    Returns:
        美化的JSON字符串
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except Exception as e:
        logger.error(f"JSON序列化失败: {e}")
        return str(data)


def merge_json(*json_dicts: Dict[str, Any], deep: bool = False) -> Dict[str, Any]:
    """
    合并多个JSON字典

    Args:
        *json_dicts: 要合并的字典
        deep: 是否深度合并

    Returns:
        合并后的字典
    """
    if not json_dicts:
        return {}

    if len(json_dicts) == 1:
        return json_dicts[0].copy()

    if deep:
        result = {}
        for d in json_dicts:
            for key, value in d.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = merge_json(result[key], value, deep=True)
                else:
                    result[key] = value
        return result
    else:
        result = {}
        for d in json_dicts:
            result.update(d)
        return result


class JSONParser:
    """JSON解析器类"""

    def __init__(self, fallback_on_error: bool = True):
        """
        初始化解析器

        Args:
            fallback_on_error: 错误时是否返回默认值
        """
        self.fallback_on_error = fallback_on_error
        self.parse_count = 0
        self.error_count = 0

    def parse(self, text: str) -> Optional[Dict[str, Any]]:
        """
        解析JSON

        Args:
            text: 包含JSON的文本

        Returns:
            解析后的字典，失败时返回None或默认值
        """
        self.parse_count += 1
        try:
            return safe_extract_json(text)
        except JSONParseError as e:
            self.error_count += 1
            if self.fallback_on_error:
                logger.warning(f"JSON解析失败: {e}")
                return {"error": "parse_failed"}
            else:
                raise

    def get_success_rate(self) -> float:
        """获取解析成功率"""
        if self.parse_count == 0:
            return 0.0
        return ((self.parse_count - self.error_count) / self.parse_count) * 100

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_parses": self.parse_count,
            "successful_parses": self.parse_count - self.error_count,
            "failed_parses": self.error_count,
            "success_rate": f"{self.get_success_rate():.2f}%"
        }
