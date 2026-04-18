# 📋 缠论分析文件清单（快速参考）

## 🟢 必须保留（核心功能）

| 文件 | 大小 | 说明 | 重要性 |
|------|------|------|--------|
| multi_agents/__init__.py | - | 多智能体模块初始化 | ⭐⭐⭐⭐⭐ |
| multi_agents/data_collector_agent.py | - | 数据采集智能体 | ⭐⭐⭐⭐⭐ |
| multi_agents/structure_analyzer_agent.py | - | 结构分析智能体 | ⭐⭐⭐⭐⭐ |
| multi_agents/dynamics_analyzer_agent.py | - | 动力学分析智能体 | ⭐⭐⭐⭐⭐ |
| multi_agents/sentiment_analyzer_agent.py | - | 市场情绪智能体 | ⭐⭐⭐⭐⭐ |
| multi_agents/decision_maker_agent.py | - | 决策制定智能体 | ⭐⭐⭐⭐⭐ |
| multi_agents/workflow.py | - | 协作工作流 | ⭐⭐⭐⭐⭐ |
| src/tools/huobi_tools.py | - | 火币API工具 | ⭐⭐⭐⭐⭐ |
| run_multi_agent_analysis.py | 248B | 主运行脚本 | ⭐⭐⭐⭐⭐ |
| data/BTCUSDT_4h_latest.csv | 25KB | 最新数据 | ⭐⭐⭐⭐⭐ |

---

## 🟡 可选保留（备用/测试）

| 文件 | 大小 | 说明 | 建议 |
|------|------|------|------|
| src/utils/chanlun_structure.py | - | 缠论结构算法 | 📦 保留备用 |
| src/utils/chanlun_dynamics.py | - | 缠论动力学算法 | 📦 保留备用 |
| src/utils/chanlun_algorithms_v2.py | - | 缠论算法V2 | 📦 保留备用 |
| btc_chanlun_analysis.py | 5.3KB | 简化缠论分析 | 🗑️ 可删除 |
| btc_market_analysis.py | 7.2KB | 简化市场分析 | 🗑️ 可删除 |
| CHANLUN_README.md | 27KB | 缠论文档 | 📚 参考保留 |

### 旧智能体系统（可删除）

| 目录/文件 | 说明 | 建议 |
|----------|------|------|
| src/agents/data_collector/ | 旧版数据采集 | 🗑️ 可删除 |
| src/agents/structure_analyzer/ | 旧版结构分析 | 🗑️ 可删除 |
| src/agents/dynamics_analyzer/ | 旧版动力学分析 | 🗑️ 可删除 |
| src/agents/sentiment_analyzer/ | 旧版市场情绪 | 🗑️ 可删除 |
| src/agents/decision_maker/ | 旧版决策制定 | 🗑️ 可删除 |
| src/agents/practical_theory/ | 实战理论智能体 | 🗑️ 可删除 |
| src/agents/risk_manager/ | 风险管理智能体 | 🗑️ 可删除 |
| src/agents/cross_market_analyzer/ | 跨市场分析智能体 | 🗑️ 可删除 |
| src/agents/onchain_analyzer/ | 链上数据分析智能体 | 🗑️ 可删除 |
| src/agents/system_monitor/ | 系统监控智能体 | 🗑️ 可删除 |
| src/agents/simulation/ | 模拟盘智能体 | 🗑️ 可删除 |
| src/agents/report_generator/ | 报告生成智能体 | 🗑️ 可删除 |
| src/graphs/chanlun_graph.py | 旧版图工作流 | 🗑️ 可删除 |

### 测试脚本（可删除）

| 文件 | 大小 | 说明 |
|------|------|------|
| test_chanlun.py | 2.3KB | 基础缠论测试 |
| test_algorithms.py | 6.2KB | 算法测试 |
| test_algorithm_optimization.py | 12KB | 算法优化测试 |
| test_advanced_features.py | 13KB | 高级功能测试 |
| test_output_optimization.py | 8.9KB | 输出优化测试 |

---

## 🔴 可以删除（重复/废弃）

| 文件 | 大小 | 说明 | 操作 |
|------|------|------|------|
| data/BTCUSDT_1h_huobi_20260417_154108.csv | 56KB | 重复数据 | ❌ 删除 |
| data/BTCUSDT_1h_huobi_20260417_154112.csv | 56KB | 重复数据 | ❌ 删除 |
| data/BTCUSDT_1h_huobi_20260417_154415.csv | 56KB | 重复数据 | ❌ 删除 |
| data/BTCUSDT_1h_huobi_20260417_154417.csv | 56KB | 重复数据 | ❌ 删除 |
| data/BTCUSDT_1h_huobi_20260417_154453.csv | 56KB | 重复数据 | ❌ 删除 |
| /workspace/chanson-feishu/ | - | 旧项目目录 | ❌ 删除 |

---

## 📊 统计总结

| 类别 | 文件数 | 说明 |
|------|--------|------|
| 🔴 必须保留 | 10个 | 核心功能，不可删除 |
| 🟡 可选保留 | 24个 | 备用/测试，根据需要处理 |
| 🔵 可以删除 | 11个 | 重复/废弃，建议删除 |

---

## 🗑️ 一键清理

### 方式1：使用清理脚本（推荐）
```bash
chmod +x cleanup_files.sh
./cleanup_files.sh
```

### 方式2：手动删除重复文件
```bash
# 删除重复数据
rm data/BTCUSDT_1h_huobi_20260417_*.csv

# 删除测试脚本
rm test_*.py

# 删除简化版脚本
rm btc_chanlun_analysis.py
rm btc_market_analysis.py

# 删除旧目录
rm -rf /workspace/chanson-feishu
```

### 方式3：深度清理（删除旧智能体系统）
```bash
# ⚠️ 确保新系统正常工作后再执行
rm -rf src/agents/
rm -rf src/graphs/
```

---

## ✅ 清理后的最小结构

```
/workspace/projects/
├── multi_agents/              ← 核心系统
│   ├── __init__.py
│   ├── data_collector_agent.py
│   ├── structure_analyzer_agent.py
│   ├── dynamics_analyzer_agent.py
│   ├── sentiment_analyzer_agent.py
│   ├── decision_maker_agent.py
│   └── workflow.py
│
├── src/
│   └── tools/
│       └── huobi_tools.py     ← 数据工具
│
├── data/
│   └── BTCUSDT_4h_latest.csv  ← 最新数据
│
├── run_multi_agent_analysis.py ← 主入口
└── FILE_CLEANUP_REPORT.md      ← 本文档
```

---

**📝 提示**: 清理前建议先备份整个项目目录！
