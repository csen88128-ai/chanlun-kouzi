"""
配置管理模块
"""
import yaml
import os
import logging
from typing import Any, Dict, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Config:
    """配置管理类"""

    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化配置"""
        if not self._config:
            self._load_config()

    def _load_config(self, config_path: Optional[str] = None):
        """
        加载配置文件

        Args:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if config_path is None:
            # 默认配置文件路径
            workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
            config_path = os.path.join(workspace_path, "config.yaml")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
            logger.info(f"配置加载成功: {config_path}")
        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {config_path}，使用默认配置")
            self._load_default_config()
        except Exception as e:
            logger.error(f"配置加载失败: {e}，使用默认配置")
            self._load_default_config()

    def _load_default_config(self):
        """加载默认配置"""
        self._config = {
            "analysis": {
                "default_interval": "4h",
                "default_limit": 200,
                "symbol": "BTCUSDT"
            },
            "api": {
                "timeout": 10,
                "retries": 3,
                "retry_delay": 1.0
            },
            "cache": {
                "enabled": True,
                "ttl_minutes": 5
            },
            "scoring": {
                "weights": {
                    "trend": 0.30,
                    "rsi": 0.20,
                    "macd": 0.20,
                    "price_position": 0.15,
                    "sentiment": 0.15
                }
            },
            "workflow": {
                "execution_mode": "parallel"
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔的嵌套键（如 "analysis.default_interval"）
            default: 默认值

        Returns:
            配置值或默认值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        logger.debug(f"配置更新: {key} = {value}")

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()

    def reload(self, config_path: Optional[str] = None):
        """
        重新加载配置

        Args:
            config_path: 配置文件路径
        """
        self._config.clear()
        self._load_config(config_path)
        logger.info("配置已重新加载")

    def save(self, config_path: Optional[str] = None):
        """
        保存配置到文件

        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
            config_path = os.path.join(workspace_path, "config.yaml")

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            logger.info(f"配置已保存: {config_path}")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")

    def __getitem__(self, key: str) -> Any:
        """支持字典式访问"""
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        """支持字典式设置"""
        self.set(key, value)

    def __repr__(self) -> str:
        return f"Config({len(self._config)} sections)"


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


# 便捷函数
def get(key: str, default: Any = None) -> Any:
    """获取配置值"""
    return get_config().get(key, default)


def set(key: str, value: Any):
    """设置配置值"""
    get_config().set(key, value)


def reload_config(config_path: Optional[str] = None):
    """重新加载配置"""
    get_config().reload(config_path)
