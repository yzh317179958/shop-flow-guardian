#!/bin/bash
# Fiido 测试工作台 Web 服务启动脚本

set -e

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "============================================================"
echo "🚀 Fiido 测试工作台 Web 服务"
echo "============================================================"

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ 错误: 需要 Python $required_version 或更高版本"
    echo "   当前版本: $python_version"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "⚠️  虚拟环境不存在，正在创建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "✅ 虚拟环境已激活"

# 检查依赖
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask 未安装，正在安装依赖..."
    pip install -r requirements.txt
fi

# 检查端口
if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  端口 5000 已被占用"
    echo "   请选择操作："
    echo "   1) 杀死占用进程并继续"
    echo "   2) 退出"
    read -p "请输入选择 [1-2]: " choice

    case $choice in
        1)
            echo "正在杀死占用进程..."
            lsof -ti:5000 | xargs kill -9 2>/dev/null || true
            sleep 2
            ;;
        2)
            echo "退出"
            exit 0
            ;;
        *)
            echo "无效选择，退出"
            exit 1
            ;;
    esac
fi

# 启动服务
echo "============================================================"
echo "🌐 正在启动 Web 服务..."
echo "============================================================"

python3 web/app.py
