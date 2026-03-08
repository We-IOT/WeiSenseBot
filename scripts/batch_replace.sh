#!/bin/bash
# 批量替换脚本：将 weisensebot 替换为 weisensebot

set -e

echo "开始批量替换..."

# 1. 替换所有Python文件中的 from weisensebot. → from weisensebot.
echo "替换Python import语句..."
find . -type f -name "*.py" ! -path "./.git/*" ! -path "./.ruff_cache/*" ! -path "./__pycache__/*" ! -path "*/__pycache__/*" -exec sed -i '' 's/from weisensebot\./from weisensebot./g' {} +

# 2. 替换 import weisensebot → import weisensebot
find . -type f -name "*.py" ! -path "./.git/*" ! -path "./.ruff_cache/*" ! -path "./__pycache__/*" ! -path "*/__pycache__/*" -exec sed -i '' 's/import weisensebot/import weisensebot/g' {} +

# 3. 替换 "weisensebot" (文档字符串中的引用)
find . -type f -name "*.py" ! -path "./.git/*" ! -path "./.ruff_cache/*" ! -path "./__pycache__/*" ! -path "*/__pycache__/*" -exec sed -i '' 's/"weisensebot"/"weisensebot"/g' {} +

echo "✓ Python文件替换完成"

# 4. 替换配置文件和脚本文件
echo "替换配置和脚本文件..."
find . -type f \( -name "*.sh" -o -name "*.json" -o -name "*.toml" -o -name "*.yml" -o -name "*.yaml" \) ! -path "./.git/*" -exec sed -i '' 's/weisensebot/weisensebot/g' {} +

echo "✓ 配置和脚本文件替换完成"

# 5. 替换Markdown文档文件
echo "替换Markdown文档..."
find . -type f -name "*.md" ! -path "./.git/*" -exec sed -i '' 's/weisensebot/weisensebot/g' {} +

echo "✓ Markdown文档替换完成"

# 6. 替换TypeScript文件
echo "替换TypeScript文件..."
find ./bridge -type f -name "*.ts" ! -path "./.git/*" -exec sed -i '' 's/weisensebot/weisensebot/g' {} +

echo "✓ TypeScript文件替换完成"

echo ""
echo "🎉 批量替换完成！"
echo ""
echo "⚠️ 注意：请手动检查以下内容："
echo "   1. README.md 和 README_CN.md 中的logo图片引用"
echo "   2. LICENSE 文件中的版权信息"
echo "   3. 任何特殊的weisensebot引用（如logo、emoji等）"
