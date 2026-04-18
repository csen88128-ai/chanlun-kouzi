#!/bin/bash
# 定期清理脚本
# 用途：定期清理data目录中的旧数据文件

echo "========================================="
echo "  定期清理脚本"
echo "========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查参数
if [ $# -eq 0 ]; then
    echo "使用方法："
    echo "  ./regular_cleanup.sh daily    # 清理7天前的文件"
    echo "  ./regular_cleanup.sh weekly   # 清理30天前的文件"
    echo "  ./regular_cleanup.sh monthly  # 清理90天前的文件"
    echo ""
    exit 1
fi

MODE=$1
DAYS=7

case $MODE in
    daily)
        DAYS=7
        echo "模式: 每日清理 (清理 ${DAYS} 天前的文件)"
        ;;
    weekly)
        DAYS=30
        echo "模式: 每周清理 (清理 ${DAYS} 天前的文件)"
        ;;
    monthly)
        DAYS=90
        echo "模式: 每月清理 (清理 ${DAYS} 天前的文件)"
        ;;
    *)
        echo -e "${RED}错误: 未知模式 '$MODE'${NC}"
        echo "可用模式: daily, weekly, monthly"
        exit 1
        ;;
esac

echo ""
echo "开始清理..."
echo ""

# 清理计数器
deleted_count=0
skipped_count=0

# 1. 清理旧的CSV数据文件
echo "📁 清理旧数据文件..."
for file in data/BTCUSDT_*.csv; do
    if [ -f "$file" ] && [ "$file" != "data/BTCUSDT_4h_latest.csv" ]; then
        file_age=$(find "$file" -mtime +$DAYS -print)
        if [ -n "$file_age" ]; then
            rm "$file"
            echo -e "${GREEN}  ✓ 已删除: $file (${DAYS}天前)${NC}"
            ((deleted_count++))
        else
            echo -e "${YELLOW}  ⏭  跳过: $file (未超过${DAYS}天)${NC}"
            ((skipped_count++))
        fi
    fi
done

# 2. 清理旧的备份目录
echo ""
echo "📁 清理旧备份目录..."
for backup_dir in backup/*/; do
    if [ -d "$backup_dir" ]; then
        dir_age=$(find "$backup_dir" -type d -mtime +$DAYS -print)
        if [ -n "$dir_age" ]; then
            echo -e "${YELLOW}  ⚠️  发现旧备份: $backup_dir${NC}"
            read -p "  是否删除? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                rm -rf "$backup_dir"
                echo -e "${GREEN}  ✓ 已删除: $backup_dir${NC}"
                ((deleted_count++))
            else
                echo -e "${YELLOW}  ⏭  跳过: $backup_dir${NC}"
                ((skipped_count++))
            fi
        else
            echo -e "${YELLOW}  ⏭  跳过: $backup_dir (未超过${DAYS}天)${NC}"
            ((skipped_count++))
        fi
    fi
done

# 3. 显示当前状态
echo ""
echo "📊 当前状态："
echo "  数据文件数量: $(ls -1 data/*.csv 2>/dev/null | wc -l)"
echo "  备份目录数量: $(ls -1d backup/*/ 2>/dev/null | wc -l)"
echo "  数据目录大小: $(du -sh data/ 2>/dev/null | cut -f1)"
echo "  备份目录大小: $(du -sh backup/ 2>/dev/null | cut -f1)"

# 总结
echo ""
echo "========================================="
echo "  清理完成"
echo "========================================="
echo -e "${GREEN}✓ 已删除: $deleted_count 个文件/目录${NC}"
echo -e "${YELLOW}⏭  跳过: $skipped_count 个文件/目录${NC}"
echo ""
echo "下次清理建议:"
echo "  - 每日: $(date -d "+7 days" +%Y-%m-%d)"
echo "  - 每周: $(date -d "+30 days" +%Y-%m-%d)"
echo "  - 每月: $(date -d "+90 days" +%Y-%m-%d)"
echo ""
