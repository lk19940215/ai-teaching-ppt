#!/bin/bash
# 单进程生产环境启动脚本
# 解决 uvicorn --reload 多进程导致的 SSE/网络异常问题

cd "$(dirname "$0")"

# 确保端口未被占用
echo "【环境清理】检查并释放 8000 端口..."
lsof -ti :8000 | xargs kill -9 2>/dev/null || true
sleep 1

# 使用单进程模式启动（无 reload，适合生产/测试）
echo "【启动】uvicorn 单进程模式..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --no-access-log
