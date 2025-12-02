# Fiido 测试系统 - 内部服务器部署指南

**版本**: v1.4.0
**目标**: 部署到公司内部服务器，提供 Web 工作台界面
**用户**: 内部测试人员（非技术背景）
**完成时间**: 预计 2-3 小时

---

## 📋 部署前准备清单

### 1. 服务器要求

**硬件要求**：
- CPU: 2 核以上
- 内存: 4GB 以上（推荐 8GB）
- 硬盘: 20GB 可用空间

**软件要求**：
- 操作系统: Ubuntu 22.04 LTS（推荐）或 Ubuntu 20.04
- 访问权限: sudo 权限
- 网络: 能被公司内网访问

**可选但推荐**：
- 固定内网 IP 地址
- 域名（如 `fiido-test.company.com`）

### 2. 获取必要信息

需要准备：
- [ ] 服务器 IP 地址: `_____________`
- [ ] 服务器 SSH 登录账号: `_____________`
- [ ] DeepSeek API Key（免费）: `_____________`
  - 注册地址: https://platform.deepseek.com/
  - 用途: AI 报告生成

### 3. 本地准备

- [ ] 项目代码已下载
- [ ] 有服务器 SSH 访问权限
- [ ] 了解服务器基本操作

---

## 🚀 部署步骤

### 阶段 1：清理项目结构（本地操作）

**目标**: 删除开发过程文件，保留生产必需文件

```bash
# 1. 进入项目目录
cd fiido-shop-flow-guardian

# 2. 创建归档目录
mkdir -p archive

# 3. 归档开发文档
mv claude.md development-lifecycle-guide.md FIIDO_WORKBENCH_DEVELOPMENT_LIFECYCLE.md archive/

# 4. 归档 Sprint 总结文档
cd docs
mkdir -p archive
mv sprint-*-summary.md archive/
cd ..

# 5. 清理测试截图（可选，节省空间）
# 注意：如果想保留失败截图用于分析，可以跳过此步
# rm -rf screenshots/*.png

# 6. 清理 HTML 覆盖率报告（可选）
rm -rf htmlcov/

# 7. 验证清理结果
tree -L 2 -I 'venv|__pycache__|*.pyc|node_modules|.git|screenshots|archive'
```

**清理后的标准项目结构**：

```
fiido-shop-flow-guardian/
├── .github/              # GitHub Actions 配置
│   └── workflows/
├── config/               # 配置文件
│   ├── alert_config.json
│   └── selectors.json
├── core/                 # 核心框架
│   ├── crawler.py
│   ├── models.py
│   ├── selector_manager.py
│   └── ...
├── pages/                # 页面对象
│   ├── product_page.py
│   ├── cart_page.py
│   └── checkout_page.py
├── scripts/              # 工具脚本
│   ├── discover_products.py
│   ├── detect_product_changes.py
│   ├── analyze_trends.py
│   ├── generate_dashboard.py
│   ├── check_test_health.py
│   ├── collect_test_results.py
│   ├── send_alerts.py
│   └── ...
├── tests/                # 测试套件
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                 # 用户文档
│   ├── 购物流程AI自动化检测方案_Fiido独立站.md
│   ├── quickstart-deepseek.md
│   ├── alert-setup-guide.md
│   ├── testing-checklist.md
│   └── ...
├── data/                 # 数据目录（运行时生成）
├── reports/              # 报告目录（运行时生成）
├── .env.example          # 环境变量模板
├── requirements.txt      # Python 依赖
├── run.sh                # 运行脚本
├── run_tests.sh          # 测试脚本
└── README.md             # 主文档
```

---

### 阶段 2：上传代码到服务器

**选项 A：使用 Git（推荐）**

```bash
# 在服务器上执行
cd /opt  # 或者你希望的安装目录
sudo mkdir -p fiido-test
sudo chown $USER:$USER fiido-test
cd fiido-test

# 克隆代码
git clone https://github.com/yzh317179958/fiido-shop-flow-guardian.git
cd fiido-shop-flow-guardian
```

**选项 B：使用 SCP 上传**

```bash
# 在本地执行
cd /path/to/fiido-shop-flow-guardian
tar -czf fiido-test.tar.gz \
  --exclude='venv' \
  --exclude='__pycache__' \
  --exclude='.git' \
  --exclude='screenshots' \
  --exclude='archive' \
  .

# 上传到服务器
scp fiido-test.tar.gz user@server-ip:/tmp/

# 在服务器上解压
ssh user@server-ip
cd /opt
sudo mkdir -p fiido-test
sudo chown $USER:$USER fiido-test
cd fiido-test
tar -xzf /tmp/fiido-test.tar.gz
```

---

### 阶段 3：安装依赖环境

```bash
# SSH 登录到服务器
ssh user@server-ip

# 进入项目目录
cd /opt/fiido-test/fiido-shop-flow-guardian

# 1. 更新系统
sudo apt update

# 2. 安装 Python 3.11+
sudo apt install -y python3.11 python3.11-venv python3-pip

# 3. 安装系统依赖
sudo apt install -y \
  wget \
  curl \
  git \
  nginx \
  supervisor

# 4. 创建 Python 虚拟环境
python3.11 -m venv venv

# 5. 激活虚拟环境
source venv/bin/activate

# 6. 升级 pip
pip install --upgrade pip

# 7. 安装 Python 依赖
pip install -r requirements.txt

# 8. 安装额外的 Web 框架依赖
pip install flask flask-cors gunicorn

# 9. 安装 Playwright 浏览器
playwright install chromium
playwright install-deps chromium  # 安装浏览器依赖
```

---

### 阶段 4：配置环境变量

```bash
# 1. 复制环境变量模板
cp .env.example .env

# 2. 编辑环境变量
nano .env
```

**`.env` 文件内容**：

```bash
# AI 服务配置（必需）
DEEPSEEK_API_KEY=your-deepseek-api-key-here

# 可选：告警配置
# SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
# SMTP_USER=your-email@gmail.com
# SMTP_PASSWORD=your-app-password
```

**获取 DeepSeek API Key**：
1. 访问 https://platform.deepseek.com/
2. 注册账号（支持国内手机号）
3. 进入 API Keys 页面
4. 创建新的 API Key
5. 复制到 `.env` 文件

---

### 阶段 5：创建 Web 应用

**创建 Web 应用目录和文件**：

```bash
# 在项目根目录创建 web 目录
mkdir -p web/templates web/static

# 创建后端 Flask 应用
nano web/app.py
```

**提示**: 将以下 Python 代码粘贴到 `web/app.py` 文件中

<details>
<summary>点击查看完整的 app.py 代码（约 400 行）</summary>

```python
#!/usr/bin/env python3
"""
Fiido 测试工作台 Web 应用
提供简单易用的 UI 界面，非技术人员可以通过浏览器使用测试系统。
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# 当前运行的任务
running_tasks = {}


def run_command(command, task_id=None):
    """执行命令并返回结果"""
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600
        )

        output = {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }

        if task_id:
            running_tasks[task_id] = {
                'status': 'completed' if result.returncode == 0 else 'failed',
                'result': output,
                'completed_at': datetime.now().isoformat()
            }

        return output
    except Exception as e:
        error = {'success': False, 'error': str(e)}
        if task_id:
            running_tasks[task_id] = {
                'status': 'error',
                'result': error,
                'completed_at': datetime.now().isoformat()
            }
        return error


@app.route('/')
def index():
    """首页"""
    return render_template('index.html')


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/products/discover', methods=['POST'])
def discover_products():
    """发现商品"""
    task_id = f"discover_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.now().isoformat()
    }

    def run_discovery():
        command = ['./run.sh', 'python3', 'scripts/discover_products.py']
        run_command(command, task_id)

    thread = threading.Thread(target=run_discovery)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started'})


@app.route('/api/products/list')
def list_products():
    """获取商品列表"""
    products_file = DATA_DIR / 'products.json'

    if not products_file.exists():
        return jsonify({'products': [], 'total': 0})

    try:
        with open(products_file) as f:
            products = json.load(f)
        return jsonify({'products': products, 'total': len(products)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tests/run', methods=['POST'])
def run_tests():
    """运行测试"""
    data = request.json or {}

    command = ['./run_tests.sh']

    if data.get('priority'):
        command.append(f"--priority={data['priority']}")

    if data.get('category'):
        command.append(f"--category={data['category']}")

    if data.get('product_id'):
        command.append(f"--product-id={data['product_id']}")

    task_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.now().isoformat(),
        'params': data
    }

    def run_test():
        run_command(command, task_id)

    thread = threading.Thread(target=run_test)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started'})


@app.route('/api/tests/status/<task_id>')
def test_status(task_id):
    """查询任务状态"""
    if task_id not in running_tasks:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify(running_tasks[task_id])


@app.route('/api/reports/latest')
def latest_report():
    """获取最新报告"""
    result_file = REPORTS_DIR / 'test_results.json'

    if not result_file.exists():
        return jsonify({'error': 'No reports found'}), 404

    try:
        with open(result_file) as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/generate', methods=['POST'])
def generate_dashboard():
    """生成质量看板"""
    command = ['./run.sh', 'python3', 'scripts/generate_dashboard.py']
    result = run_command(command)

    if result['success']:
        return jsonify({'status': 'success', 'url': '/dashboard'})
    else:
        return jsonify({'error': result.get('stderr', 'Unknown error')}), 500


@app.route('/dashboard')
def view_dashboard():
    """查看质量看板"""
    dashboard_file = REPORTS_DIR / 'dashboard.html'

    if not dashboard_file.exists():
        return "Dashboard not found. Please generate it first.", 404

    return send_file(dashboard_file)


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Fiido 测试工作台启动中...")
    print("=" * 60)
    print(f"📁 项目目录: {PROJECT_ROOT}")
    print(f"📊 数据目录: {DATA_DIR}")
    print(f"📈 报告目录: {REPORTS_DIR}")
    print("=" * 60)
    print("✅ 服务已启动！")
    print("🌐 访问地址: http://localhost:5000")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5000, debug=False)
```

</details>

保存后，设置执行权限：

```bash
chmod +x web/app.py
```

---

### 阶段 6：创建前端界面

```bash
# 创建首页 HTML
nano web/templates/index.html
```

**提示**: 将前端 HTML 代码粘贴到此文件（下一步提供完整代码）

---

### 阶段 7：配置 Nginx 反向代理

**目的**: 让用户通过服务器 IP 或域名直接访问，而不是加端口号

```bash
# 1. 创建 Nginx 配置文件
sudo nano /etc/nginx/sites-available/fiido-test
```

**Nginx 配置内容**：

```nginx
server {
    listen 80;
    server_name your-server-ip;  # 替换为实际 IP 或域名

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件
    location /static {
        alias /opt/fiido-test/fiido-shop-flow-guardian/web/static;
        expires 30d;
    }

    # 日志
    access_log /var/log/nginx/fiido-test-access.log;
    error_log /var/log/nginx/fiido-test-error.log;
}
```

```bash
# 2. 启用站点
sudo ln -s /etc/nginx/sites-available/fiido-test /etc/nginx/sites-enabled/

# 3. 测试 Nginx 配置
sudo nginx -t

# 4. 重启 Nginx
sudo systemctl restart nginx
```

---

### 阶段 8：配置自动启动（Supervisor）

**目的**: 服务器重启后自动启动 Web 应用

```bash
# 1. 创建 Supervisor 配置
sudo nano /etc/supervisor/conf.d/fiido-test.conf
```

**Supervisor 配置内容**：

```ini
[program:fiido-test]
command=/opt/fiido-test/fiido-shop-flow-guardian/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 web.app:app
directory=/opt/fiido-test/fiido-shop-flow-guardian
user=your-username  # 替换为实际用户名
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/fiido-test-error.log
stdout_logfile=/var/log/fiido-test.log
environment=PATH="/opt/fiido-test/fiido-shop-flow-guardian/venv/bin"
```

```bash
# 2. 更新 Supervisor 配置
sudo supervisorctl reread
sudo supervisorctl update

# 3. 启动服务
sudo supervisorctl start fiido-test

# 4. 检查状态
sudo supervisorctl status fiido-test
```

---

### 阶段 9：测试验证

```bash
# 1. 检查服务状态
sudo supervisorctl status fiido-test
# 输出应该是: fiido-test   RUNNING   pid xxx, uptime x:xx:xx

# 2. 检查 Nginx 状态
sudo systemctl status nginx

# 3. 测试本地访问
curl http://localhost:5000/api/health
# 输出应该是: {"status": "ok", "timestamp": "..."}

# 4. 测试外部访问（在浏览器）
# 访问: http://your-server-ip
```

---

## ✅ 部署完成检查清单

- [ ] 服务器依赖已安装（Python, Nginx, Supervisor）
- [ ] 项目代码已上传
- [ ] Python 虚拟环境已创建
- [ ] 依赖包已安装
- [ ] Playwright 浏览器已安装
- [ ] `.env` 文件已配置
- [ ] Web 应用文件已创建
- [ ] Nginx 配置已生效
- [ ] Supervisor 配置已生效
- [ ] 服务正常运行
- [ ] 可以通过浏览器访问

---

## 🎯 使用指南

### 访问工作台

浏览器打开：`http://your-server-ip`

### 基本操作

1. **发现商品**
   - 点击"发现商品"按钮
   - 等待爬虫自动抓取所有商品信息
   - 查看商品列表

2. **运行测试**
   - 选择测试范围（全部/按优先级/按分类）
   - 点击"运行测试"
   - 查看实时进度

3. **查看报告**
   - 测试完成后，点击"查看报告"
   - 查看通过率、失败详情
   - 下载截图

4. **生成 AI 报告**
   - 点击"生成 AI 报告"
   - AI 自动分析失败原因
   - 提供修复建议

5. **质量看板**
   - 点击"质量看板"
   - 查看 30 天趋势
   - 查看性能指标

---

## 🔧 常见问题

### 问题 1: 无法访问 Web 界面

**解决方案**：

```bash
# 检查服务状态
sudo supervisorctl status fiido-test

# 如果显示 STOPPED，重启服务
sudo supervisorctl start fiido-test

# 检查日志
sudo tail -f /var/log/fiido-test.log
sudo tail -f /var/log/nginx/fiido-test-error.log
```

### 问题 2: 测试运行失败

**解决方案**：

```bash
# 检查 Playwright 浏览器
source venv/bin/activate
playwright install chromium
playwright install-deps chromium
```

### 问题 3: AI 报告生成失败

**检查**：

```bash
# 验证 API Key
cat .env | grep DEEPSEEK_API_KEY

# 测试 API 连接
./run.sh python3 scripts/test_deepseek_connection.py
```

---

## 📞 维护与更新

### 更新代码

```bash
# SSH 登录服务器
ssh user@server-ip

# 进入项目目录
cd /opt/fiido-test/fiido-shop-flow-guardian

# 拉取最新代码
git pull origin main

# 重启服务
sudo supervisorctl restart fiido-test
```

### 查看日志

```bash
# 应用日志
sudo tail -f /var/log/fiido-test.log

# Nginx 日志
sudo tail -f /var/log/nginx/fiido-test-access.log
sudo tail -f /var/log/nginx/fiido-test-error.log
```

### 备份数据

```bash
# 备份商品数据和测试报告
cd /opt/fiido-test/fiido-shop-flow-guardian
tar -czf backup_$(date +%Y%m%d).tar.gz data/ reports/

# 下载到本地
scp user@server-ip:/opt/fiido-test/fiido-shop-flow-guardian/backup_*.tar.gz ./
```

---

## 📊 下一步计划

部署完成后，建议：

1. **培训测试人员**: 演示如何使用工作台
2. **配置定时任务**: 设置每日自动测试
3. **配置告警**: 设置邮件/企业微信告警
4. **完善前端**: 根据反馈优化界面

---

## 🎉 总结

完成以上步骤后，你将拥有：

- ✅ 一个稳定运行的测试服务器
- ✅ 一个简单易用的 Web 工作台
- ✅ 自动化测试和 AI 报告系统
- ✅ 质量看板和趋势分析

**关键价值**：
- 测试人员无需懂技术，点击按钮即可使用
- 7x24 小时自动运行
- 所有人共享同一份数据和报告

**部署时间**: 约 2-3 小时

**维护成本**: 极低，基本无需日常维护

---

**文档版本**: v1.0
**创建日期**: 2025-12-02
**适用版本**: Fiido Shop Flow Guardian v1.4.0
