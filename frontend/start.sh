#!/bin/bash

# claw-ex React UI 启动脚本
# 同时启动后端 API 和前端开发服务器

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEBUI_DIR="$SCRIPT_DIR/claw-ex-webui"
REACT_UI_DIR="$SCRIPT_DIR/claw-ex-react-ui"

echo "🐾 claw-ex React UI 启动脚本"
echo "================================"

# 检查后端目录
if [ ! -d "$WEBUI_DIR" ]; then
    echo "❌ 错误：claw-ex-webui 目录不存在"
    exit 1
fi

# 检查前端目录
if [ ! -d "$REACT_UI_DIR" ]; then
    echo "❌ 错误：claw-ex-react-ui 目录不存在"
    exit 1
fi

# 启动后端
echo ""
echo "📡 启动后端 API 服务器..."
cd "$WEBUI_DIR"
python3 server.py &
BACKEND_PID=$!
echo "✅ 后端已启动 (PID: $BACKEND_PID)"

# 等待后端启动
sleep 2

# 启动前端
echo ""
echo "🎨 启动前端开发服务器..."
cd "$REACT_UI_DIR"

# 检查 node_modules
if [ ! -d "node_modules" ]; then
    echo "⚠️  未检测到 node_modules，正在安装依赖..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "✅ 前端已启动 (PID: $FRONTEND_PID)"

echo ""
echo "================================"
echo "🌐 访问地址:"
echo "   前端：http://localhost:5173"
echo "   后端：http://localhost:8000"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "================================"

# 捕获退出信号
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# 等待
wait
