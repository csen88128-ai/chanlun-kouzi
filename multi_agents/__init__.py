"""
多智能体协作系统 - 优化版本
"""

from .cache import DataCache, get_global_cache
from .error_handling import retry, safe_execute, timeout, safe_with_retry
from .agent_pool import AgentPool, get_or_create_agent, warm_up_agents
from .json_utils import (
    safe_extract_json,
    extract_json_with_fallback,
    validate_json,
    JSONParser
)
from .config_manager import Config, get_config, get, set, reload_config

__all__ = [
    # 缓存
    "DataCache",
    "get_global_cache",

    # 错误处理
    "retry",
    "safe_execute",
    "timeout",
    "safe_with_retry",

    # Agent池
    "AgentPool",
    "get_or_create_agent",
    "warm_up_agents",

    # JSON工具
    "safe_extract_json",
    "extract_json_with_fallback",
    "validate_json",
    "JSONParser",

    # 配置管理
    "Config",
    "get_config",
    "get",
    "set",
    "reload_config",
]
