#!/bin/bash

# meseen 发布与部署脚本
# 用法: ./publish.sh "本次改动简述"

CHANGE_LOG=$1

if [ -z "$CHANGE_LOG" ]; then
    echo "请输入本次改动的简述:"
    read CHANGE_LOG
fi

echo "🚀 开始发布流程..."

# 1. Git 操作
echo "📦 提交代码到 GitHub..."
git add .
git commit -m "Update: $CHANGE_LOG"
git push origin main

# 2. 生成/更新 Release 文档
DATE=$(date "+%Y-%m-%d %H:%M:%S")
RELEASE_FILE="RELEASE_NOTES.md"

echo "📝 更新发行说明..."
if [ ! -f "$RELEASE_FILE" ]; then
    echo "# Meseen Release Notes" > "$RELEASE_FILE"
fi

# 在文件顶部插入新记录
TEMP_FILE=$(mktemp)
echo "## [$DATE] Update" > "$TEMP_FILE"
echo "- **变更描述**: $CHANGE_LOG" >> "$TEMP_FILE"
echo "- **部署状态**: 已推送到 GitHub Main 分支" >> "$TEMP_FILE"
echo "" >> "$TEMP_FILE"
cat "$RELEASE_FILE" >> "$TEMP_FILE"
mv "$TEMP_FILE" "$RELEASE_FILE"

echo "✅ 发布完成！"
echo "📄 Release 文档已更新: $RELEASE_FILE"
echo "🔗 GitHub 仓库: https://github.com/Sakee8848/meseen"
echo "🌐 部署预览: (等待 Vercel/GitHub Actions 自动构建)"
