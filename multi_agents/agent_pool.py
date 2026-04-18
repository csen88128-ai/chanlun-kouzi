"""
Agent池模块 - 实现Agent复用
"""
import logging
from typing import Dict, Any, Optional, Callable

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentPool:
    """Agent池，用于管理和复用Agent实例"""

    _instances: Dict[str, Any] = {}
    _configs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_agent(
        cls,
        agent_type: str,
        agent_builder: Optional[Callable] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        注册Agent构建器

        Args:
            agent_type: Agent类型标识
            agent_builder: Agent构建函数
            config: Agent配置
        """
        cls._configs[agent_type] = config or {}
        logger.info(f"注册Agent: {agent_type}")

    @classmethod
    def get_agent(cls, agent_type: str) -> Optional[Any]:
        """
        获取Agent实例（复用已创建的实例）

        Args:
            agent_type: Agent类型标识

        Returns:
            Agent实例，如果不存在则返回None
        """
        if agent_type not in cls._instances:
            logger.debug(f"Agent {agent_type} 尚未初始化")
            return None

        logger.debug(f"复用Agent实例: {agent_type}")
        return cls._instances[agent_type]

    @classmethod
    def create_agent(
        cls,
        agent_type: str,
        agent_builder: Callable,
        force_rebuild: bool = False
    ) -> Any:
        """
        创建或获取Agent实例

        Args:
            agent_type: Agent类型标识
            agent_builder: Agent构建函数
            force_rebuild: 是否强制重建

        Returns:
            Agent实例
        """
        # 如果已存在且不强制重建，直接返回
        if not force_rebuild and agent_type in cls._instances:
            logger.info(f"复用Agent实例: {agent_type}")
            return cls._instances[agent_type]

        # 创建新实例
        logger.info(f"构建Agent实例: {agent_type}")
        try:
            agent = agent_builder()
            cls._instances[agent_type] = agent
            cls.register_agent(agent_type, agent_builder)
            return agent
        except Exception as e:
            logger.error(f"构建Agent失败 {agent_type}: {e}")
            raise

    @classmethod
    def rebuild_agent(cls, agent_type: str, agent_builder: Callable) -> Any:
        """
        重建Agent实例

        Args:
            agent_type: Agent类型标识
            agent_builder: Agent构建函数

        Returns:
            新的Agent实例
        """
        logger.info(f"重建Agent: {agent_type}")
        return cls.create_agent(agent_type, agent_builder, force_rebuild=True)

    @classmethod
    def remove_agent(cls, agent_type: str):
        """
        移除Agent实例

        Args:
            agent_type: Agent类型标识
        """
        if agent_type in cls._instances:
            del cls._instances[agent_type]
            logger.info(f"移除Agent实例: {agent_type}")

    @classmethod
    def clear_all(cls):
        """清空所有Agent实例"""
        cls._instances.clear()
        cls._configs.clear()
        logger.info("清空所有Agent实例")

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取Agent池统计信息"""
        return {
            "total_agents": len(cls._instances),
            "agent_types": list(cls._instances.keys()),
            "configs": cls._configs
        }

    @classmethod
    def is_loaded(cls, agent_type: str) -> bool:
        """
        检查Agent是否已加载

        Args:
            agent_type: Agent类型标识

        Returns:
            True如果已加载，否则False
        """
        return agent_type in cls._instances


# 便捷函数
def get_or_create_agent(
    agent_type: str,
    agent_builder: Callable,
    force_rebuild: bool = False
) -> Any:
    """
    获取或创建Agent的便捷函数

    Args:
        agent_type: Agent类型标识
        agent_builder: Agent构建函数
        force_rebuild: 是否强制重建

    Returns:
        Agent实例
    """
    return AgentPool.create_agent(agent_type, agent_builder, force_rebuild)


def warm_up_agents(agent_builders: Dict[str, Callable]):
    """
    预加载所有Agent

    Args:
        agent_builders: Agent构建器字典 {agent_type: agent_builder}
    """
    logger.info("开始预加载Agent...")
    for agent_type, builder in agent_builders.items():
        try:
            get_or_create_agent(agent_type, builder)
        except Exception as e:
            logger.error(f"预加载Agent失败 {agent_type}: {e}")

    stats = AgentPool.get_stats()
    logger.info(f"预加载完成，共加载 {stats['total_agents']} 个Agent")
