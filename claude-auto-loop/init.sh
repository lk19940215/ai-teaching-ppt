#!/bin/bash
set -e

echo "=== AI 教学 PPT 生成器环境初始化 ==="

# 检查 Python 环境
if [ -d ".venv" ]; then
    echo "Python 虚拟环境 .venv 已存在"
else
    echo "创建 Python 虚拟环境 .venv"
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate
echo "Python 虚拟环境已激活"

# 安装 Python 依赖（如果存在 requirements.txt）
if [ -f "backend/requirements.txt" ]; then
    echo "安装 Python 依赖..."
    pip install -r backend/requirements.txt
elif [ -f "requirements.txt" ]; then
    echo "安装 Python 依赖..."
    pip install -r requirements.txt
else
    echo "未找到 requirements.txt，跳过 Python 依赖安装"
fi

# 检查 Node.js 版本
if command -v node &> /dev/null; then
    node_version=$(node --version | cut -d'v' -f2)
    echo "Node.js 版本: $node_version"
else
    echo "警告: Node.js 未安装，请安装 Node.js 20+"
    exit 1
fi

# 检查 pnpm
if command -v pnpm &> /dev/null; then
    echo "pnpm 已安装"
else
    echo "安装 pnpm..."
    npm install -g pnpm
fi

# 安装前端依赖（如果存在 package.json）
if [ -f "frontend/package.json" ]; then
    echo "安装前端依赖..."
    cd frontend
    pnpm install
    cd ..
else
    echo "未找到 frontend/package.json，跳过前端依赖安装"
fi

echo "=== 环境初始化完成 ==="
echo "如需启动服务，请参考 README.md 中的启动命令"