"""
知识库管理工具
为各智能体提供知识查询和更新能力
"""
import json
import os
from typing import Dict, List, Optional
from datetime import datetime


class KnowledgeBase:
    """智能体知识库管理类"""

    def __init__(self, knowledge_file: str = "/workspace/projects/data/knowledge_base.json"):
        """
        初始化知识库

        Args:
            knowledge_file: 知识库文件路径
        """
        self.knowledge_file = knowledge_file
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self) -> List[Dict]:
        """加载知识库"""
        if not os.path.exists(self.knowledge_file):
            return []

        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载知识库失败: {e}")
            return []

    def _save_knowledge(self):
        """保存知识库"""
        try:
            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存知识库失败: {e}")

    def get_knowledge(self, agent_type: str, domain: str, concept: str) -> Optional[Dict]:
        """
        获取指定的知识项

        Args:
            agent_type: 智能体类型（如 data_collector, structure_analyzer）
            domain: 领域（如 缠论, 技术指标）
            concept: 概念（如 分型识别, RSI计算）

        Returns:
            知识项字典，如果不存在返回None
        """
        for item in self.knowledge:
            if (item.get("agent_type") == agent_type and
                item.get("domain") == domain and
                item.get("concept") == concept):
                return item
        return None

    def get_agent_knowledge(self, agent_type: str) -> List[Dict]:
        """
        获取指定智能体的所有知识

        Args:
            agent_type: 智能体类型

        Returns:
            该智能体的知识列表
        """
        return [item for item in self.knowledge if item.get("agent_type") == agent_type]

    def get_domain_knowledge(self, domain: str) -> List[Dict]:
        """
        获取指定领域的所有知识

        Args:
            domain: 领域名称

        Returns:
            该领域的知识列表
        """
        return [item for item in self.knowledge if item.get("domain") == domain]

    def update_knowledge(
        self,
        agent_type: str,
        domain: str,
        concept: str,
        status: str,
        description: str,
        confidence: float,
        evidence: str,
        improvement_needed: str,
        learning_resources: List[str]
    ):
        """
        更新或添加知识项

        Args:
            agent_type: 智能体类型
            domain: 领域
            concept: 概念
            status: 状态（完整/部分/待完善）
            description: 描述
            confidence: 置信度（0-1）
            evidence: 证据
            improvement_needed: 需要改进的地方
            learning_resources: 学习资源列表
        """
        # 查找是否已存在
        for item in self.knowledge:
            if (item.get("agent_type") == agent_type and
                item.get("domain") == domain and
                item.get("concept") == concept):
                # 更新现有知识
                item.update({
                    "status": status,
                    "description": description,
                    "confidence": confidence,
                    "evidence": evidence,
                    "improvement_needed": improvement_needed,
                    "learning_resources": learning_resources,
                    "last_updated": datetime.now().isoformat()
                })
                self._save_knowledge()
                return True

        # 添加新知识
        new_knowledge = {
            "agent_type": agent_type,
            "domain": domain,
            "concept": concept,
            "status": status,
            "description": description,
            "confidence": confidence,
            "evidence": evidence,
            "improvement_needed": improvement_needed,
            "learning_resources": learning_resources,
            "last_updated": datetime.now().isoformat()
        }
        self.knowledge.append(new_knowledge)
        self._save_knowledge()
        return True

    def get_knowledge_summary(self) -> Dict:
        """
        获取知识库摘要

        Returns:
            知识库统计信息
        """
        total = len(self.knowledge)
        complete = sum(1 for item in self.knowledge if item.get("status") == "完整")
        partial = sum(1 for item in self.knowledge if item.get("status") == "部分")
        avg_confidence = sum(item.get("confidence", 0) for item in self.knowledge) / total if total > 0 else 0

        # 按智能体统计
        agent_stats = {}
        for item in self.knowledge:
            agent_type = item.get("agent_type")
            if agent_type not in agent_stats:
                agent_stats[agent_type] = {"total": 0, "complete": 0, "avg_confidence": 0}
            agent_stats[agent_type]["total"] += 1
            if item.get("status") == "完整":
                agent_stats[agent_type]["complete"] += 1
            agent_stats[agent_type]["avg_confidence"] += item.get("confidence", 0)

        for agent_type in agent_stats:
            agent_stats[agent_type]["avg_confidence"] /= agent_stats[agent_type]["total"]

        return {
            "total": total,
            "complete": complete,
            "partial": partial,
            "incomplete": total - complete - partial,
            "completeness": (complete / total * 100) if total > 0 else 0,
            "avg_confidence": avg_confidence,
            "agent_stats": agent_stats
        }

    def get_improvement_suggestions(self) -> List[str]:
        """
        获取改进建议

        Returns:
            改进建议列表
        """
        suggestions = []
        for item in self.knowledge:
            if item.get("improvement_needed") and item.get("improvement_needed") != "无":
                suggestions.append(
                    f"[{item.get('agent_type')} - {item.get('domain')} - {item.get('concept')}] "
                    f"{item.get('improvement_needed')}"
                )
        return suggestions


# 全局知识库实例
_global_knowledge_base = None


def get_knowledge_base() -> KnowledgeBase:
    """获取全局知识库实例"""
    global _global_knowledge_base
    if _global_knowledge_base is None:
        _global_knowledge_base = KnowledgeBase()
    return _global_knowledge_base


if __name__ == "__main__":
    # 测试知识库
    print("=" * 60)
    print("知识库管理测试")
    print("=" * 60)

    kb = get_knowledge_base()

    # 1. 获取知识摘要
    print("\n[1] 知识库摘要:")
    summary = kb.get_knowledge_summary()
    print(f"  总数: {summary['total']}")
    print(f"  完整: {summary['complete']}")
    print(f"  部分: {summary['partial']}")
    print(f"  完整度: {summary['completeness']:.1f}%")
    print(f"  平均置信度: {summary['avg_confidence']:.1%}")

    print("\n  各智能体知识统计:")
    for agent_type, stats in summary["agent_stats"].items():
        print(f"    - {agent_type}: {stats['complete']}/{stats['total']} (置信度: {stats['avg_confidence']:.1%})")

    # 2. 获取缠论领域知识
    print("\n[2] 缠论领域知识:")
    chanlun_knowledge = kb.get_domain_knowledge("缠论")
    for item in chanlun_knowledge:
        print(f"  - {item['concept']}: {item['status']} (置信度: {item['confidence']:.1%})")

    # 3. 获取改进建议
    print("\n[3] 改进建议:")
    suggestions = kb.get_improvement_suggestions()
    for i, suggestion in enumerate(suggestions[:5], 1):
        print(f"  {i}. {suggestion}")
