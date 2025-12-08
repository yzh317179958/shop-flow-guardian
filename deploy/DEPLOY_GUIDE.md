# Fiido Shop Flow Guardian - 阿里云ECS部署指南

> 版本: v3.1.0
> 适用环境: Ubuntu 22.04 (阿里云ECS 2核2G)
> 部署时间: 约10-15分钟

---

## 📋 目录

1. [准备工作](#1-准备工作)
2. [一键部署](#2-一键部署)
3. [配置说明](#3-配置说明)
4. [日常使用](#4-日常使用)
5. [维护指南](#5-维护指南)
6. [故障排查](#6-故障排查)

---

## 1. 准备工作

### 1.1 配置阿里云安全组

**必须先完成此步骤，否则无法访问Web界面！**

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com/)
2. 找到你的ECS实例，点击实例ID进入详情
3. 点击左侧菜单「安全组」
4. 点击「配置规则」→「手动添加」
5. 添加以下规则：

| 授权策略 | 优先级 | 协议类型 | 端口范围 | 授权对象 | 描述 |
|---------|-------|---------|---------|---------|------|
| 允许 | 1 | TCP | 5000/5000 | 0.0.0.0/0 | Web服务 |

6. 点击「确定」保存

### 1.2 SSH连接服务器

```bash
# 使用密钥登录 (将 your-key.pem 替换为你的密钥文件路径)
ssh -i your-key.pem root@223.4.251.97

# 如果提示密钥权限问题，先修改权限
chmod 400 your-key.pem
```

---

## 2. 一键部署

连接到服务器后，执行以下命令：

```bash
# 下载并执行安装脚本
curl -fsSL https://raw.githubusercontent.com/yzh317179958/shop-flow-guardian/main/deploy/install.sh | sudo bash
```

**或者分步执行：**

```bash
# 1. 下载安装脚本
wget https://raw.githubusercontent.com/yzh317179958/shop-flow-guardian/main/deploy/install.sh

# 2. 添加执行权限
chmod +x install.sh

# 3. 执行安装
sudo bash install.sh
```

安装过程约需10-15分钟，请耐心等待。

---

## 3. 配置说明

### 3.1 配置DeepSeek API Key（AI分析功能）

```bash
# 编辑环境配置
fiido env

# 或直接编辑
vim /opt/fiido-shop-flow-guardian/.env
```

修改以下内容：
```ini
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
```

> 💡 获取DeepSeek API Key: https://platform.deepseek.com/

配置完成后重启服务：
```bash
fiido restart
```

### 3.2 环境变量说明

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| DEEPSEEK_API_KEY | - | DeepSeek API密钥（AI分析必需） |
| FLASK_HOST | 0.0.0.0 | Web服务监听地址 |
| FLASK_PORT | 5000 | Web服务端口 |
| HEADLESS | true | 浏览器无头模式（服务器必须为true） |

---

## 4. 日常使用

### 4.1 访问Web界面

打开浏览器访问：
```
http://223.4.251.97:5000
```

### 4.2 Web界面功能

| 页面 | 功能 | 路径 |
|------|------|------|
| 概览 | 系统状态和统计数据 | `/` |
| 商品管理 | 查看/发现/管理商品 | `/products` |
| 测试执行 | 配置和运行测试 | `/tests` |
| 报告中心 | 查看测试报告和AI分析 | `/reports` |

### 4.3 管理命令

所有命令都可以使用 `fiido` 快捷方式：

```bash
# 启动服务
fiido start

# 停止服务
fiido stop

# 重启服务
fiido restart

# 查看服务状态
fiido status

# 查看实时日志
fiido logs

# 更新到最新版本
fiido update

# 编辑环境配置
fiido env

# 命令行运行测试
fiido test c21-gravel quick    # 快速测试
fiido test c21-gravel full     # 全面测试
```

### 4.4 运行测试的三种方式

**方式1: Web界面（推荐）**
1. 访问 http://223.4.251.97:5000/tests
2. 选择测试范围（所有商品/按分类/自定义/单个）
3. 点击「快速测试」或「全面测试」

**方式2: 命令行**
```bash
# 进入项目目录
cd /opt/fiido-shop-flow-guardian
source venv/bin/activate

# 单个商品测试
python scripts/run_product_test.py --product-id c21-gravel --mode quick

# 批量测试
python scripts/run_batch_test.py --category "Electric Bikes" --mode full
```

**方式3: 使用管理命令**
```bash
fiido test c21-gravel quick
```

---

## 5. 维护指南

### 5.1 更新代码

```bash
# 一键更新（推荐）
fiido update

# 或手动更新
cd /opt/fiido-shop-flow-guardian
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
fiido restart
```

### 5.2 备份数据

重要数据目录：
- `/opt/fiido-shop-flow-guardian/data/` - 商品数据
- `/opt/fiido-shop-flow-guardian/reports/` - 测试报告
- `/opt/fiido-shop-flow-guardian/.env` - 环境配置

```bash
# 备份命令
tar -czvf backup_$(date +%Y%m%d).tar.gz \
    /opt/fiido-shop-flow-guardian/data \
    /opt/fiido-shop-flow-guardian/reports \
    /opt/fiido-shop-flow-guardian/.env
```

### 5.3 日志管理

```bash
# 查看实时日志
fiido logs

# 查看最近100行日志
journalctl -u fiido-guardian -n 100

# 查看今天的日志
journalctl -u fiido-guardian --since today

# 清理旧日志（保留7天）
journalctl --vacuum-time=7d
```

### 5.4 磁盘空间管理

```bash
# 查看磁盘使用
df -h

# 查看项目占用空间
du -sh /opt/fiido-shop-flow-guardian/*

# 清理旧报告（保留最近30天）
find /opt/fiido-shop-flow-guardian/reports -name "*.json" -mtime +30 -delete
```

### 5.5 重启服务器后

服务会自动启动（已配置systemd自启动）。如果没有自动启动：
```bash
fiido start
```

---

## 6. 故障排查

### 6.1 服务无法启动

```bash
# 查看详细错误
journalctl -u fiido-guardian -n 50 --no-pager

# 检查端口占用
lsof -i :5000

# 手动运行测试
cd /opt/fiido-shop-flow-guardian
source venv/bin/activate
python web/app.py
```

### 6.2 无法访问Web界面

1. **检查服务状态**
   ```bash
   fiido status
   ```

2. **检查防火墙**
   ```bash
   ufw status
   # 如果启用了ufw，添加规则
   ufw allow 5000/tcp
   ```

3. **检查阿里云安全组**
   - 确保5000端口已开放
   - 确保授权对象是 `0.0.0.0/0`

4. **检查服务监听**
   ```bash
   netstat -tlnp | grep 5000
   ```

### 6.3 测试执行失败

```bash
# 检查Playwright浏览器
cd /opt/fiido-shop-flow-guardian
source venv/bin/activate
playwright install chromium
playwright install-deps chromium

# 测试浏览器是否正常
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); b = p.chromium.launch(headless=True); print('Browser OK'); b.close(); p.stop()"
```

### 6.4 AI分析不工作

```bash
# 检查API Key配置
cat /opt/fiido-shop-flow-guardian/.env | grep DEEPSEEK

# 测试API连接
cd /opt/fiido-shop-flow-guardian
source venv/bin/activate
python -c "
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv('DEEPSEEK_API_KEY'), base_url='https://api.deepseek.com')
response = client.chat.completions.create(model='deepseek-chat', messages=[{'role':'user','content':'Hello'}], max_tokens=10)
print('API OK:', response.choices[0].message.content)
"
```

### 6.5 内存不足（2G限制）

```bash
# 查看内存使用
free -h

# 创建交换空间（如果没有）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# 限制Chromium内存使用（已在代码中配置）
```

---

## 📞 常用信息速查

| 项目 | 信息 |
|------|------|
| Web访问地址 | http://223.4.251.97:5000 |
| 项目目录 | /opt/fiido-shop-flow-guardian |
| 配置文件 | /opt/fiido-shop-flow-guardian/.env |
| 服务名称 | fiido-guardian |
| 管理命令 | fiido {start\|stop\|restart\|status\|logs\|update} |

---

## 🔗 相关链接

- [GitHub仓库](https://github.com/yzh317179958/shop-flow-guardian)
- [DeepSeek API](https://platform.deepseek.com/)
- [Fiido官网](https://fiido.com)

---

*最后更新: 2025-12-08*
