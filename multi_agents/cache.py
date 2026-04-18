"""
数据缓存模块
"""
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCache:
    """数据缓存类，支持TTL过期"""

    def __init__(self, default_ttl_minutes: int = 5):
        """
        初始化缓存

        Args:
            default_ttl_minutes: 默认缓存过期时间（分钟）
        """
        self.cache = {}  # {key: (value, timestamp, ttl)}
        self.default_ttl = timedelta(minutes=default_ttl_minutes)
        self.hits = 0
        self.misses = 0

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_str = "|".join(str(arg) for arg in args)
        key_str += "|" + "|".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存获取数据

        Args:
            key: 缓存键

        Returns:
            缓存的数据，如果不存在或已过期则返回None
        """
        if key not in self.cache:
            self.misses += 1
            return None

        value, timestamp, ttl = self.cache[key]

        # 检查是否过期
        if datetime.now() - timestamp > ttl:
            del self.cache[key]
            self.misses += 1
            logger.debug(f"缓存过期: {key}")
            return None

        self.hits += 1
        logger.debug(f"缓存命中: {key}")
        return value

    def set(self, key: str, value: Any, ttl_minutes: Optional[int] = None):
        """
        设置缓存

        Args:
            key: 缓存键
            value: 缓存的值
            ttl_minutes: 过期时间（分钟），如果为None则使用默认值
        """
        ttl = timedelta(minutes=ttl_minutes) if ttl_minutes else self.default_ttl
        self.cache[key] = (value, datetime.now(), ttl)
        logger.debug(f"缓存设置: {key}, TTL: {ttl}")

    def delete(self, key: str):
        """删除指定缓存"""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"缓存删除: {key}")

    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info("缓存已清空")

    def cleanup_expired(self):
        """清理过期缓存"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp, ttl) in self.cache.items()
            if now - timestamp > ttl
        ]

        for key in expired_keys:
            del self.cache[key]

        if expired_keys:
            logger.info(f"清理了 {len(expired_keys)} 个过期缓存")

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_keys": len(self.cache),
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%"
        }

    def __repr__(self) -> str:
        return f"DataCache(keys={len(self.cache)}, hits={self.hits}, misses={self.misses})"


# 全局缓存实例
_global_cache = None


def get_global_cache() -> DataCache:
    """获取全局缓存实例"""
    global _global_cache
    if _global_cache is None:
        _global_cache = DataCache(default_ttl_minutes=5)
    return _global_cache
