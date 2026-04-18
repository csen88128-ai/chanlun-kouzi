#!/bin/bash
# 缠论分析文件清理脚本
# 使用说明：
# 1. chmod +x cleanup_files.sh
# 2. ./cleanup_files.sh

echo "========================================="
echo "  缠论分析文件清理脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 确认操作
echo -e "${YELLOW}⚠️  此脚本将删除重复和废弃的文件${NC}"
echo -e "${YELLOW}⚠️  请确保已备份重要文件${NC}"
echo ""
read -p "是否继续？(yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

echo ""
echo "开始清理..."
echo ""

# 清理计数器
deleted_count=0
skipped_count=0

# 1. 删除重复的数据文件
echo "📁 清理重复的数据文件..."
for file in data/BTCUSDT_1h_huobi_20260417_*.csv; do
    if [ -f "$file" ]; then
        rm "$file"
        echo -e "${GREEN}  ✓ 已删除: $file${NC}"
        ((deleted_count++))
    fi
done

# 2. 删除测试脚本
echo ""
echo "📁 清理测试脚本..."
for file in test_*.py; do
    if [ -f "$file" ]; then
        rm "$file"
        echo -e "${GREEN}  ✓ 已删除: $file${NC}"
        ((deleted_count++))
    fi
done

# 3. 删除简化版分析脚本
echo ""
echo "📁 清理简化版分析脚本..."
for file in btc_*.py; do
    if [ "$file" != "run_multi_agent_analysis.py" ]; then
        if [ -f "$file" ]; then
            rm "$file"
            echo -e "${GREEN}  ✓ 已删除: $file${NC}"
            ((deleted_count++))
        fi
    fi
done

# 4. 删除chanson-feishu目录
echo ""
echo "📁 清理chanson-feishu目录..."
if [ -d "/workspace/chanson-feishu" ]; then
    rm -rf /workspace/chanson-feishu
    echo -e "${GREEN}  ✓ 已删除: /workspace/chanson-feishu${NC}"
    ((deleted_count++))
else
    echo -e "${YELLOW}  ⏭  跳过: /workspace/chanson-feishu 不存在${NC}"
    ((skipped_count++))
fi

# 5. 清理旧的智能体系统（可选，需要手动确认）
echo ""
echo -e "${YELLOW}⚠️  是否删除旧的智能体系统 (src/agents/ 和 src/graphs/)？${NC}"
echo -e "${YELLOW}   注意：此操作不可恢复，新的multi_agents/系统已取代它们${NC}"
read -p "   是否删除旧智能体系统？(yes/no): " delete_old

if [ "$delete_old" = "yes" ]; then
    if [ -d "src/agents" ]; then
        rm -rf src/agents
        echo -e "${GREEN}  ✓ 已删除: src/agents/${NC}"
        ((deleted_count++))
    fi

    if [ -d "src/graphs" ]; then
        rm -rf src/graphs
        echo -e "${GREEN}  ✓ 已删除: src/graphs/${NC}"
        ((deleted_count++))
    fi
else
    echo -e "${YELLOW}  ⏭  跳过: 保留旧智能体系统${NC}"
fi

# 总结
echo ""
echo "========================================="
echo "  清理完成"
echo "========================================="
echo -e "${GREEN}✓ 已删除: $deleted_count 个文件/目录${NC}"
echo -e "${YELLOW}⏭  跳过: $skipped_count 个文件/目录${NC}"
echo ""
echo "📊 保留的核心文件："
echo "  - multi_agents/ (7个智能体文件)"
echo "  - src/tools/huobi_tools.py"
echo "  - run_multi_agent_analysis.py"
echo "  - data/BTCUSDT_4h_latest.csv"
echo ""
echo "📄 详细报告请查看: FILE_CLEANUP_REPORT.md"
echo ""
