#!/bin/bash
# 开发环境启动脚本（带 reload，但限制为单进程）
# 避免多进程导致的网络/SSE 问题

cd "$(dirname "$0")"

# 确保端口未被占用
echo "【环境清理】检查并释放 8000 端口..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
sleep 1

# 使用单进程 + reload 模式（适合开发）
echo "【启动】uvicorn 开发模式（单进程 + reload）..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --workers 1
