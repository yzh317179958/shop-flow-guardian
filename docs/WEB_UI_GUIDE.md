# Fiido 测试工作台 - Web界面使用指南

## 简介

Fiido 测试工作台提供了一个友好的Web界面，让非技术人员也能轻松使用自动化测试系统。

## 启动Web服务

### 方式一：直接启动

```bash
cd /home/yzh/fiido-shop-flow-guardian
python3 web/app.py
```

### 方式二：使用虚拟环境

```bash
cd /home/yzh/fiido-shop-flow-guardian
source venv/bin/activate
python3 web/app.py
```

启动后，访问：**http://localhost:5000**

## 页面功能说明

### 1. 📊 概览页面 (/)

**功能**：
- 系统状态监控
- 关键指标展示（总商品数、通过率、失败数、健康度）
- 快速操作按钮
- 最新测试结果预览
- 通过率趋势图表
- 最近活动时间线

**快速操作**：
- 发现商品
- 运行所有测试
- 运行P0测试
- 生成AI报告

### 2. 📦 商品管理页面 (/products)

**功能**：
- 查看所有已发现的商品
- 按优先级/分类筛选商品
- 搜索商品（按名称或ID）
- 查看商品详情（变体、价格等）
- 测试单个商品

**统计信息**：
- 总商品数
- P0/P1/P2商品分布

**操作**：
- 点击"发现商品"按钮重新爬取商品
- 点击商品卡片查看详情
- 在详情弹窗中点击"测试此商品"

### 3. 🧪 测试执行页面 (/tests)

**功能**：
- 配置测试范围（全部/优先级/分类/单个商品）
- 运行自动化测试
- 实时查看测试状态
- 查看测试历史记录

**测试配置选项**：
- **所有商品**：测试全部商品
- **按优先级**：只测试指定优先级（P0/P1/P2）
- **按分类**：只测试指定分类的商品
- **单个商品**：只测试选中的商品

**快速测试**：
- P0快速测试（核心商品）
- P1快速测试（重要商品）
- 全量测试

### 4. 📄 报告中心页面 (/reports)

**功能**：
- 查看最新测试报告
- AI智能分析报告
- 历史趋势分析
- 商品变更检测

**选项卡**：

#### 最新报告
- 测试结果概览（总数、通过、失败、跳过）
- 通过率进度条
- 详细测试结果表格

#### AI分析
- 选择AI提供商（DeepSeek推荐/Claude）
- 生成智能分析报告
- 自动失败原因分析

#### 趋势分析
- 选择时间范围（7/14/30天）
- 查看历史趋势数据
- 通过率变化曲线

#### 商品变更
- 检测商品变更
- 增量测试建议

### 5. 📈 质量看板 (/dashboard)

**功能**：
- 可视化质量看板
- 通过率趋势图
- 高频失败商品排行
- 地区性能对比

## API端点说明

### 商品相关
- `POST /api/products/discover` - 发现商品
- `GET /api/products/list` - 获取商品列表

### 测试相关
- `POST /api/tests/run` - 运行测试
- `GET /api/tests/status/<task_id>` - 查询测试状态

### 报告相关
- `GET /api/reports/list` - 获取报告列表
- `GET /api/reports/latest` - 获取最新报告
- `POST /api/reports/ai/generate` - 生成AI报告

### 分析相关
- `POST /api/changes/detect` - 检测商品变更
- `GET /api/changes/latest` - 获取最新变更
- `POST /api/trends/analyze` - 分析历史趋势
- `GET /api/trends/latest` - 获取最新趋势

### 系统相关
- `GET /api/health` - 健康检查
- `GET /api/config` - 获取系统配置
- `POST /api/dashboard/generate` - 生成质量看板
- `GET /dashboard` - 查看质量看板

## 技术栈

### 后端
- **Flask** - Web框架
- **Flask-CORS** - 跨域支持
- **Python threading** - 后台任务

### 前端
- **Bootstrap 5.3** - UI框架
- **Bootstrap Icons** - 图标库
- **Chart.js 4.4** - 图表库
- **原生JavaScript** - 交互逻辑

### 特点
- 响应式设计，支持移动端
- 实时状态更新
- 任务轮询机制
- Toast通知提示
- 加载动画

## 使用流程

### 首次使用

1. **启动Web服务**
   ```bash
   python3 web/app.py
   ```

2. **访问首页**
   打开浏览器访问 http://localhost:5000

3. **发现商品**
   - 点击首页的"发现商品"按钮
   - 或访问商品管理页面，点击"发现商品"
   - 等待任务完成（通常需要几分钟）

4. **运行测试**
   - 访问测试执行页面
   - 选择测试范围
   - 点击"运行测试"
   - 等待测试完成

5. **查看报告**
   - 访问报告中心页面
   - 查看测试结果
   - 可选：生成AI报告获取智能分析

### 日常使用

1. **监控测试状态**
   - 打开概览页面
   - 查看关键指标和最新结果

2. **快速测试P0商品**
   - 点击"运行P0测试"
   - 或访问测试页面，选择P0快速测试

3. **查看趋势**
   - 访问报告中心
   - 点击"趋势分析"选项卡
   - 选择时间范围并分析

## 注意事项

1. **任务执行时间**
   - 商品发现：2-5分钟
   - 全量测试：10-30分钟（取决于商品数量）
   - P0测试：2-5分钟
   - AI报告生成：1-2分钟

2. **超时设置**
   - 所有后台任务默认超时时间为10分钟
   - 如果任务超时，会自动标记为失败

3. **数据存储**
   - 商品数据：`data/products.json`
   - 测试结果：`reports/test_results.json`
   - 变更检测：`data/product_changes.json`
   - 趋势分析：`reports/trend_analysis.json`

4. **浏览器兼容性**
   - 推荐使用Chrome、Firefox、Edge最新版本
   - 不支持IE浏览器

## 故障排查

### Web服务无法启动

```bash
# 检查端口是否被占用
lsof -i :5000

# 杀死占用进程
kill -9 <PID>
```

### API请求失败

1. 检查后端服务是否运行
2. 查看浏览器控制台错误信息
3. 检查网络连接

### 任务一直显示运行中

1. 刷新页面重新查询状态
2. 检查后台任务是否真的在运行
3. 查看服务器日志

## 生产部署建议

### 使用Gunicorn（推荐）

```bash
pip install gunicorn

# 启动4个worker进程
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
```

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /path/to/fiido-shop-flow-guardian/web/static;
    }
}
```

### 使用Systemd自动启动

创建 `/etc/systemd/system/fiido-web.service`:

```ini
[Unit]
Description=Fiido Test Workbench
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/yzh/fiido-shop-flow-guardian
ExecStart=/usr/bin/python3 /home/yzh/fiido-shop-flow-guardian/web/app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable fiido-web
sudo systemctl start fiido-web
```

## 更多帮助

- 项目主文档：`README.md`
- 测试文档：`docs/TESTING.md`
- 部署文档：`docs/DEPLOYMENT.md`
- GitHub Issues: https://github.com/anthropics/fiido-shop-flow-guardian/issues
