#!/bin/bash
# 定期备份脚本
# 用途：每周备份重要文件到backup目录

echo "========================================="
echo "  定期备份脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32f'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 创建带时间戳的备份目录
BACKUP_DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/workspace/projects/backup/weekly_${BACKUP_DATE}"

echo -e "${BLUE}📦 开始备份...${NC}"
echo ""
echo "备份时间: $(date)"
echo "备份目录: $BACKUP_DIR"
echo ""

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份计数器
backup_count=0
error_count=0

# 1. 备份多智能体系统
echo "📁 备份多智能体系统..."
if [ -d "multi_agents" ]; then
    cp -r multi_agents "$BACKUP_DIR/"
    echo -e "${GREEN}  ✓ 已备份: multi_agents/${NC}"
    ((backup_count++))
else
    echo -e "${RED}  ✗ 错误: multi_agents/ 不存在${NC}"
    ((error_count++))
fi

# 2. 备份工具模块
echo ""
echo "📁 备份工具模块..."
if [ -d "src/tools" ]; then
    cp -r src/tools "$BACKUP_DIR/"
    echo -e "${GREEN}  ✓ 已备份: src/tools/${NC}"
    ((backup_count++))
else
    echo -e "${RED}  ✗ 错误: src/tools/ 不存在${NC}"
    ((error_count++))
fi

# 3. 备份运行脚本
echo ""
echo "📁 备份运行脚本..."
if [ -f "run_multi_agent_analysis.py" ]; then
    cp run_multi_agent_analysis.py "$BACKUP_DIR/"
    echo -e "${GREEN}  ✓ 已备份: run_multi_agent_analysis.py${NC}"
    ((backup_count++))
else
    echo -e "${RED}  ✗ 错误: run_multi_agent_analysis.py 不存在${NC}"
    ((error_count++))
fi

# 4. 备份配置文件
echo ""
echo "📁 备份配置文件..."
if [ -d "config" ]; then
    cp -r config "$BACKUP_DIR/"
    echo -e "${GREEN}  ✓ 已备份: config/${NC}"
    ((backup_count++))
else
    echo -e "${YELLOW}  ⏭  跳过: config/ 不存在${NC}"
fi

# 5. 备份最新数据
echo ""
echo "📁 备份最新数据..."
if [ -f "data/BTCUSDT_4h_latest.csv" ]; then
    cp data/BTCUSDT_4h_latest.csv "$BACKUP_DIR/"
    echo -e "${GREEN}  ✓ 已备份: data/BTCUSDT_4h_latest.csv${NC}"
    ((backup_count++))
else
    echo -e "${YELLOW}  ⏭  跳过: data/BTCUSDT_4h_latest.csv 不存在${NC}"
fi

# 6. 备份文档
echo ""
echo "📁 备份文档..."
for doc in CHANLUN_README.md FILE_CLEANUP_REPORT.md FILE_CHECKLIST.md CLEANUP_EXECUTION_REPORT.md; do
    if [ -f "$doc" ]; then
        cp "$doc" "$BACKUP_DIR/"
        echo -e "${GREEN}  ✓ 已备份: $doc${NC}"
        ((backup_count++))
    fi
done

# 7. 创建备份清单
echo ""
echo "📋 创建备份清单..."
cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
备份清单
=========
备份时间: $(date)
备份目录: $BACKUP_DIR
备份类型: 每周备份

备份文件列表:
$(find "$BACKUP_DIR" -type f | sort)

备份统计:
- 备份文件数: $backup_count
- 错误数: $error_count
- 备份大小: $(du -sh "$BACKUP_DIR" | cut -f1)
EOF

echo -e "${GREEN}  ✓ 已创建: BACKUP_MANIFEST.txt${NC}"

# 8. 显示备份信息
echo ""
echo "========================================="
echo "  备份完成"
echo "========================================="
echo -e "${GREEN}✓ 成功备份: $backup_count 个文件/目录${NC}"
if [ $error_count -gt 0 ]; then
    echo -e "${RED}✗ 错误: $error_count 个${NC}"
fi
echo -e "${BLUE}📦 备份位置: $BACKUP_DIR${NC}"
echo -e "${BLUE}💾 备份大小: $(du -sh "$BACKUP_DIR" | cut -f1)${NC}"
echo ""

# 9. 显示所有备份目录
echo "📊 所有备份目录:"
ls -lt backup/ | head -6
echo ""

# 10. 下次备份提示
echo "📅 下次备份建议: $(date -d "+7 days" '+%Y-%m-%d %H:%M')"
echo ""
