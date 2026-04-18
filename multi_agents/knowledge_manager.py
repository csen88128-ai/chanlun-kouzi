#!/usr/bin/env python3
"""
知识库管理模块 - 管理各智能体的知识完整性
"""
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class KnowledgeStatus(Enum):
    """知识状态"""
    COMPLETE = "完整"
    PARTIAL = "部分"
    MISSING = "缺失"
    OUTDATED = "过时"


@dataclass
class KnowledgeItem:
    """知识项"""
    agent_type: str          # 智能体类型
    domain: str              # 知识领域
    concept: str             # 概念名称
    status: KnowledgeStatus  # 知识状态
    description: str         # 描述
    confidence: float        # 掌握程度（0-1）
    last_updated: str        # 最后更新时间
    evidence: str            # 实锤证据
    improvement_needed: str  # 改进建议
    learning_resources: List[str]  # 学习资源


class KnowledgeManager:
    """知识库管理器"""

    def __init__(self):
        self.knowledge_base: List[KnowledgeItem] = []
        self.knowledge_file = "/workspace/projects/data/knowledge_base.json"
        self._load_knowledge()

    def _load_knowledge(self):
        """加载知识库"""
        try:
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.knowledge_base = [KnowledgeItem(**item) for item in data]
        except FileNotFoundError:
            # 初始化知识库
            self._initialize_knowledge()
        except Exception as e:
            print(f"加载知识库失败: {e}")
            self._initialize_knowledge()

    def _save_knowledge(self):
        """保存知识库"""
        try:
            # 将枚举转换为字符串
            serializable_items = []
            for item in self.knowledge_base:
                item_dict = asdict(item)
                item_dict['status'] = item.status.value  # 转换枚举为字符串
                serializable_items.append(item_dict)

            with open(self.knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存知识库失败: {e}")

    def _initialize_knowledge(self):
        """初始化知识库"""
        self.knowledge_base = [
            # 数据采集智能体
            KnowledgeItem(
                agent_type="data_collector",
                domain="数据获取",
                concept="火币API调用",
                status=KnowledgeStatus.COMPLETE,
                description="使用火币API获取BTC K线数据",
                confidence=0.95,
                last_updated=datetime.now().isoformat(),
                evidence="成功获取200根K线数据",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="data_collector",
                domain="数据处理",
                concept="24小时涨跌幅计算",
                status=KnowledgeStatus.COMPLETE,
                description="计算真正的24小时涨跌幅（不是单根K线）",
                confidence=0.98,
                last_updated=datetime.now().isoformat(),
                evidence="使用24小时前价格计算",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="data_collector",
                domain="数据质量",
                concept="数据清洗",
                status=KnowledgeStatus.PARTIAL,
                description="处理缺失值、异常值、重复数据",
                confidence=0.7,
                last_updated=datetime.now().isoformat(),
                evidence="基础清洗",
                improvement_needed="需要加强异常值检测和处理逻辑",
                learning_resources=[
                    "Pandas数据清洗最佳实践",
                    "金融数据异常值检测算法"
                ]
            ),

            # 结构分析智能体（缠论）
            KnowledgeItem(
                agent_type="structure_analyzer",
                domain="缠论",
                concept="分型识别",
                status=KnowledgeStatus.COMPLETE,
                description="识别顶分型和底分型",
                confidence=0.9,
                last_updated=datetime.now().isoformat(),
                evidence="成功识别30个分型（14顶、16底）",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="structure_analyzer",
                domain="缠论",
                concept="笔识别",
                status=KnowledgeStatus.COMPLETE,
                description="识别向上笔和向下笔",
                confidence=0.85,
                last_updated=datetime.now().isoformat(),
                evidence="成功识别14笔",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="structure_analyzer",
                domain="缠论",
                concept="线段识别",
                status=KnowledgeStatus.PARTIAL,
                description="识别向上线段和向下线段",
                confidence=0.75,
                last_updated=datetime.now().isoformat(),
                evidence="识别4段线段",
                improvement_needed="算法较简单，需要优化复杂场景",
                learning_resources=[
                    "缠论线段识别高级算法",
                    "线段破坏判断标准"
                ]
            ),
            KnowledgeItem(
                agent_type="structure_analyzer",
                domain="缠论",
                concept="中枢识别",
                status=KnowledgeStatus.COMPLETE,
                description="识别中枢（ZG、ZD、GG、DD）",
                confidence=0.9,
                last_updated=datetime.now().isoformat(),
                evidence="成功识别1个中枢",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="structure_analyzer",
                domain="缠论",
                concept="买卖点识别",
                status=KnowledgeStatus.PARTIAL,
                description="识别一买、二买、三买、一卖、二卖、三卖",
                confidence=0.7,
                last_updated=datetime.now().isoformat(),
                evidence="识别6个买卖点",
                improvement_needed="背驰判断需要加强，多级别买卖点识别待实现",
                learning_resources=[
                    "缠论买卖点背驰判断标准",
                    "多级别缠论分析方法"
                ]
            ),

            # 动力学分析智能体
            KnowledgeItem(
                agent_type="dynamics_analyzer",
                domain="技术指标",
                concept="RSI计算",
                status=KnowledgeStatus.COMPLETE,
                description="计算14周期RSI",
                confidence=0.98,
                last_updated=datetime.now().isoformat(),
                evidence="计算结果与手动验证一致",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="dynamics_analyzer",
                domain="技术指标",
                concept="MACD计算",
                status=KnowledgeStatus.COMPLETE,
                description="计算MACD、Signal、Histogram",
                confidence=0.95,
                last_updated=datetime.now().isoformat(),
                evidence="金叉死叉判断正确",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="dynamics_analyzer",
                domain="技术指标",
                concept="波动率计算",
                status=KnowledgeStatus.COMPLETE,
                description="计算20周期标准差",
                confidence=0.9,
                last_updated=datetime.now().isoformat(),
                evidence="计算逻辑正确",
                improvement_needed="可考虑其他波动率指标（ATR）",
                learning_resources=[
                    "ATR（平均真实波幅）指标"
                ]
            ),

            # 决策制定智能体
            KnowledgeItem(
                agent_type="decision_maker",
                domain="交易决策",
                concept="止盈止损方向",
                status=KnowledgeStatus.COMPLETE,
                description="确保止盈止损方向正确",
                confidence=0.95,
                last_updated=datetime.now().isoformat(),
                evidence="已通过逻辑验证，方向正确",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="decision_maker",
                domain="交易决策",
                concept="综合评分",
                status=KnowledgeStatus.COMPLETE,
                description="基于6个因子综合评分",
                confidence=0.85,
                last_updated=datetime.now().isoformat(),
                evidence="评分逻辑清晰",
                improvement_needed="权重可能需要根据回测调整",
                learning_resources=[
                    "多因子权重优化方法",
                    "交易策略回测框架"
                ]
            ),
            KnowledgeItem(
                agent_type="decision_maker",
                domain="交易决策",
                concept="盈亏比",
                status=KnowledgeStatus.PARTIAL,
                description="计算风险收益比",
                confidence=0.8,
                last_updated=datetime.now().isoformat(),
                evidence="基础盈亏比计算",
                improvement_needed="需要动态调整止盈止损策略",
                learning_resources=[
                    "动态止盈止损策略",
                    "资金管理理论"
                ]
            ),

            # 市场情绪智能体
            KnowledgeItem(
                agent_type="sentiment_analyzer",
                domain="市场情绪",
                concept="恐惧贪婪指数",
                status=KnowledgeStatus.COMPLETE,
                description="获取Alternative.me的恐惧贪婪指数",
                confidence=0.98,
                last_updated=datetime.now().isoformat(),
                evidence="成功获取数据",
                improvement_needed="无",
                learning_resources=[]
            ),
            KnowledgeItem(
                agent_type="sentiment_analyzer",
                domain="市场情绪",
                concept="情绪解读",
                status=KnowledgeStatus.PARTIAL,
                description="解读情绪对价格的影响",
                confidence=0.7,
                last_updated=datetime.now().isoformat(),
                evidence="基础解读",
                improvement_needed="需要结合历史数据验证情绪指标有效性",
                learning_resources=[
                    "情绪指标与价格相关性研究",
                    "市场情绪量化分析方法"
                ]
            )
        ]

        self._save_knowledge()

    def get_agent_knowledge(self, agent_type: str) -> List[KnowledgeItem]:
        """获取智能体的知识库"""
        return [item for item in self.knowledge_base if item.agent_type == agent_type]

    def check_completeness(self, agent_type: str) -> Dict[str, Any]:
        """检查智能体知识完整性"""
        knowledge = self.get_agent_knowledge(agent_type)

        if not knowledge:
            return {
                "agent_type": agent_type,
                "total": 0,
                "complete": 0,
                "partial": 0,
                "missing": 0,
                "outdated": 0,
                "completeness_rate": 0,
                "needs_improvement": True
            }

        total = len(knowledge)
        complete = sum(1 for item in knowledge if item.status == KnowledgeStatus.COMPLETE)
        partial = sum(1 for item in knowledge if item.status == KnowledgeStatus.PARTIAL)
        missing = sum(1 for item in knowledge if item.status == KnowledgeStatus.MISSING)
        outdated = sum(1 for item in knowledge if item.status == KnowledgeStatus.OUTDATED)

        completeness_rate = (complete / total) * 100 if total > 0 else 0
        needs_improvement = (partial + missing + outdated) > 0

        return {
            "agent_type": agent_type,
            "total": total,
            "complete": complete,
            "partial": partial,
            "missing": missing,
            "outdated": outdated,
            "completeness_rate": round(completeness_rate, 2),
            "needs_improvement": needs_improvement,
            "improvement_items": [
                {
                    "concept": item.concept,
                    "status": item.status.value,
                    "confidence": item.confidence,
                    "improvement_needed": item.improvement_needed
                }
                for item in knowledge if item.status != KnowledgeStatus.COMPLETE
            ]
        }

    def identify_knowledge_gaps(self) -> List[Dict[str, Any]]:
        """识别所有智能体的知识缺口"""
        gaps = []

        for agent_type in ["data_collector", "structure_analyzer", "dynamics_analyzer", "decision_maker", "sentiment_analyzer"]:
            completeness = self.check_completeness(agent_type)
            if completeness["needs_improvement"]:
                gaps.append({
                    "agent_type": agent_type,
                    "completeness_rate": completeness["completeness_rate"],
                    "improvement_items": completeness["improvement_items"]
                })

        return gaps

    def update_knowledge(self, agent_type: str, concept: str, update_data: Dict[str, Any]):
        """更新知识项"""
        for item in self.knowledge_base:
            if item.agent_type == agent_type and item.concept == concept:
                if "status" in update_data:
                    item.status = KnowledgeStatus(update_data["status"])
                if "confidence" in update_data:
                    item.confidence = update_data["confidence"]
                if "improvement_needed" in update_data:
                    item.improvement_needed = update_data["improvement_needed"]
                if "evidence" in update_data:
                    item.evidence = update_data["evidence"]
                item.last_updated = datetime.now().isoformat()
                break

        self._save_knowledge()

    def get_summary(self) -> Dict[str, Any]:
        """获取知识库摘要"""
        all_agents = ["data_collector", "structure_analyzer", "dynamics_analyzer", "decision_maker", "sentiment_analyzer"]

        summaries = {}
        total_complete = 0
        total_partial = 0
        total_missing = 0
        total_outdated = 0

        for agent in all_agents:
            check = self.check_completeness(agent)
            summaries[agent] = check
            total_complete += check["complete"]
            total_partial += check["partial"]
            total_missing += check["missing"]
            total_outdated += check["outdated"]

        total_items = total_complete + total_partial + total_missing + total_outdated
        overall_completeness = (total_complete / total_items) * 100 if total_items > 0 else 0

        return {
            "total_agents": len(all_agents),
            "total_knowledge_items": total_items,
            "complete": total_complete,
            "partial": total_partial,
            "missing": total_missing,
            "outdated": total_outdated,
            "overall_completeness": round(overall_completeness, 2),
            "agent_summaries": summaries
        }
