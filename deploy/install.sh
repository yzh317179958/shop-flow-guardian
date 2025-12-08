#!/bin/bash
# ============================================
# Fiido Shop Flow Guardian - 一键部署脚本
# 适用于: Ubuntu 22.04 (阿里云ECS)
# 版本: v3.1.0
# ============================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# 配置变量
APP_NAME="fiido-shop-flow-guardian"
APP_DIR="/opt/${APP_NAME}"
REPO_URL="https://github.com/yzh317179958/shop-flow-guardian.git"
PYTHON_VERSION="3.10"
WEB_PORT=5000

echo ""
echo "============================================"
echo "  Fiido Shop Flow Guardian 部署脚本"
echo "  版本: v3.1.0"
echo "============================================"
echo ""

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    error "请使用 root 用户运行此脚本: sudo bash install.sh"
fi

# 步骤1: 系统更新
info "步骤 1/8: 更新系统包..."
apt-get update -qq
apt-get upgrade -y -qq
success "系统更新完成"

# 步骤2: 安装基础依赖
info "步骤 2/8: 安装基础依赖..."
apt-get install -y -qq \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    git \
    curl \
    wget \
    vim \
    htop \
    unzip \
    build-essential \
    libssl-dev \
    libffi-dev \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgtk-3-0
success "基础依赖安装完成"

# 步骤3: 克隆项目代码
info "步骤 3/8: 克隆项目代码..."
if [ -d "$APP_DIR" ]; then
    warn "目录已存在，正在更新代码..."
    cd "$APP_DIR"
    git fetch --all
    git reset --hard origin/main
else
    git clone "$REPO_URL" "$APP_DIR"
    cd "$APP_DIR"
fi
success "项目代码已准备就绪: $APP_DIR"

# 步骤4: 创建Python虚拟环境
info "步骤 4/8: 创建Python虚拟环境..."
cd "$APP_DIR"
python${PYTHON_VERSION} -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
success "Python虚拟环境创建完成"

# 步骤5: 安装Python依赖
info "步骤 5/8: 安装Python依赖..."
pip install -r requirements.txt -q
success "Python依赖安装完成"

# 步骤6: 安装Playwright浏览器
info "步骤 6/8: 安装Playwright浏览器 (这可能需要几分钟)..."
playwright install chromium
playwright install-deps chromium
success "Playwright浏览器安装完成"

# 步骤7: 创建环境配置文件
info "步骤 7/8: 创建环境配置..."
if [ ! -f "$APP_DIR/.env" ]; then
    cat > "$APP_DIR/.env" << 'ENVEOF'
# Fiido Shop Flow Guardian 环境配置
# 请填写你的 DeepSeek API Key (用于AI分析功能)
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Web服务配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=false

# 测试配置
TEST_TIMEOUT=60000
HEADLESS=true
ENVEOF
    warn "已创建 .env 文件，请稍后编辑填写 DeepSeek API Key"
else
    success ".env 文件已存在，跳过创建"
fi

# 步骤8: 创建systemd服务
info "步骤 8/8: 创建系统服务..."
cat > /etc/systemd/system/fiido-guardian.service << SERVICEEOF
[Unit]
Description=Fiido Shop Flow Guardian Web Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
Environment=PATH=${APP_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=${APP_DIR}/venv/bin/python web/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICEEOF

systemctl daemon-reload
systemctl enable fiido-guardian
success "系统服务创建完成"

# 创建管理脚本
info "创建管理脚本..."
cat > "$APP_DIR/manage.sh" << 'MANAGEEOF'
#!/bin/bash
# Fiido Shop Flow Guardian 管理脚本

APP_DIR="/opt/fiido-shop-flow-guardian"
SERVICE_NAME="fiido-guardian"

case "$1" in
    start)
        echo "启动服务..."
        systemctl start $SERVICE_NAME
        systemctl status $SERVICE_NAME
        ;;
    stop)
        echo "停止服务..."
        systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "重启服务..."
        systemctl restart $SERVICE_NAME
        systemctl status $SERVICE_NAME
        ;;
    status)
        systemctl status $SERVICE_NAME
        ;;
    logs)
        journalctl -u $SERVICE_NAME -f
        ;;
    update)
        echo "更新代码..."
        cd $APP_DIR
        git fetch --all
        git reset --hard origin/main
        source venv/bin/activate
        pip install -r requirements.txt -q
        systemctl restart $SERVICE_NAME
        echo "更新完成！"
        ;;
    test)
        echo "运行测试..."
        cd $APP_DIR
        source venv/bin/activate
        python scripts/run_product_test.py --product-id "$2" --mode "${3:-quick}"
        ;;
    env)
        echo "编辑环境配置..."
        vim $APP_DIR/.env
        echo "配置已修改，请运行 'manage.sh restart' 使配置生效"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|update|test|env}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动Web服务"
        echo "  stop    - 停止Web服务"
        echo "  restart - 重启Web服务"
        echo "  status  - 查看服务状态"
        echo "  logs    - 查看实时日志"
        echo "  update  - 从GitHub更新代码"
        echo "  test    - 运行测试 (例: manage.sh test c21-gravel quick)"
        echo "  env     - 编辑环境配置"
        exit 1
        ;;
esac
MANAGEEOF
chmod +x "$APP_DIR/manage.sh"
ln -sf "$APP_DIR/manage.sh" /usr/local/bin/fiido

success "管理脚本创建完成，可使用 'fiido' 命令管理服务"

echo ""
echo "============================================"
echo -e "${GREEN}  部署完成！${NC}"
echo "============================================"
echo ""
echo "📋 后续步骤:"
echo ""
echo "1. 配置 DeepSeek API Key (用于AI分析功能):"
echo "   fiido env"
echo "   # 或直接编辑: vim /opt/fiido-shop-flow-guardian/.env"
echo ""
echo "2. 启动服务:"
echo "   fiido start"
echo ""
echo "3. 访问Web界面:"
echo "   http://$(curl -s ifconfig.me):${WEB_PORT}"
echo ""
echo "4. 常用命令:"
echo "   fiido start    # 启动服务"
echo "   fiido stop     # 停止服务"
echo "   fiido restart  # 重启服务"
echo "   fiido status   # 查看状态"
echo "   fiido logs     # 查看日志"
echo "   fiido update   # 更新代码"
echo ""
echo "============================================"
