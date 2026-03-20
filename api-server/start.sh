#!/bin/bash
# claw-ex API Server 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 claw-ex API Server 启动脚本"
echo "================================"

# 检查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 python3"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python 版本：$PYTHON_VERSION"

# 检查依赖
echo ""
echo "📦 检查依赖..."
if [ ! -f "venv/bin/activate" ]; then
    echo "  创建虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo "✓ 依赖安装完成"

# 启动服务器
echo ""
echo "🌐 启动 API 服务器..."
echo "   Swagger UI: http://localhost:8000/docs"
echo "   健康检查：http://localhost:8000/health"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

python3 main.py
