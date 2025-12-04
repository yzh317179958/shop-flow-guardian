# Fiido Shop Flow Guardian - 系统架构

## 系统概览

```
┌─────────────────────────────────────────────────────────────────┐
│                    Fiido Shop Flow Guardian                       │
│                   电商自动化测试平台 v1.4.0                         │
└─────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                        用户界面层                                   │
├─────────────────────┬─────────────────────┬───────────────────────┤
│    CLI 命令行工具     │    Web 界面          │   GitHub Actions    │
│   (技术人员使用)      │  (所有人使用)         │   (自动化运行)       │
│                     │                      │                      │
│  • discover_products │  • 概览仪表板        │  • daily-test.yml   │
│  • run_tests.sh     │  • 商品管理          │  • hourly-p0.yml    │
│  • generate_report  │  • 测试执行          │  • pr-test.yml      │
│  • analyze_trends   │  • 报告中心          │                      │
└─────────────────────┴─────────────────────┴───────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────────┐
│                        API 服务层                                   │
│                     Flask Web Application                          │
├───────────────────────────────────────────────────────────────────┤
│  Products API    │  Tests API     │  Reports API  │  Analytics    │
│  • discover      │  • run         │  • list       │  • trends     │
│  • list          │  • status      │  • latest     │  • changes    │
│                  │                │  • ai/generate│  • dashboard  │
└───────────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────────┐
│                        业务逻辑层                                   │
├─────────────────────┬─────────────────────┬───────────────────────┤
│   商品爬虫模块        │   测试执行引擎        │   分析报告模块        │
│                     │                      │                      │
│  ProductCrawler     │  Pytest Framework    │  AI Report Generator│
│  • Shopify API     │  • Page Objects      │  • DeepSeek         │
│  • HTML Parser     │  • Test Fixtures     │  • Claude           │
│  • Cache Manager   │  • Smart Waiter      │  Trend Analyzer     │
│  • Selector Mgr    │  • Result Collector  │  Change Detector    │
└─────────────────────┴─────────────────────┴───────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────────┐
│                        数据存储层                                   │
├─────────────────────┬─────────────────────┬───────────────────────┤
│   商品数据           │   测试结果           │   配置文件            │
│                     │                      │                      │
│  data/             │  reports/            │  config/             │
│  • products.json   │  • test_results.json │  • selectors.json    │
│  • history/        │  • dashboard.html    │  • alert_config.json │
│  • changes.json    │  • trend_analysis    │  • pytest.ini        │
└─────────────────────┴─────────────────────┴───────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────────┐
│                        外部服务                                     │
├─────────────────────┬─────────────────────┬───────────────────────┤
│   测试目标站点        │   AI 服务            │   告警通知            │
│                     │                      │                      │
│  • Fiido 独立站     │  • DeepSeek API     │  • Slack            │
│  • Shopify 平台     │  • Claude API       │  • Email            │
│  • 其他电商站点      │                      │  • 企业微信          │
└─────────────────────┴─────────────────────┴───────────────────────┘
```

## 核心组件详解

### 1. 商品爬虫模块 (core/crawler.py)

**职责**: 从电商网站发现和提取商品信息

**核心功能**:
- Shopify JSON API 解析
- HTML 页面解析（BeautifulSoup）
- 商品变体提取
- 缓存管理（24小时TTL）
- 智能重试机制

**输入**: 网站URL
**输出**: products.json

### 2. 测试执行引擎

**职责**: 执行端到端自动化测试

**核心组件**:
- **Page Objects** (pages/)
  - ProductPage: 商品详情页操作
  - CartPage: 购物车页操作
  - CheckoutPage: 结账流程操作

- **Test Fixtures** (conftest.py)
  - 浏览器配置
  - 测试参数化
  - 增量测试支持

- **Smart Waiter** (core/smart_wait.py)
  - 三阶段等待策略
  - 网络空闲检测
  - 智能超时优化

**输入**: 商品列表 + 测试配置
**输出**: test_results.json

### 3. 分析报告模块

**职责**: 生成智能分析和可视化报告

**核心功能**:
- **AI 报告生成**
  - DeepSeek API 集成
  - Claude API 集成
  - 失败原因分析
  - 改进建议

- **趋势分析**
  - 30天历史数据
  - 通过率趋势
  - 高频失败分析

- **质量看板**
  - HTML 可视化
  - Chart.js 图表
  - 性能指标

**输入**: test_results.json + 历史数据
**输出**: AI报告 + 趋势分析 + 看板

### 4. Web 界面

**职责**: 提供用户友好的操作界面

**技术栈**:
- Flask (后端框架)
- Bootstrap 5.3 (UI组件)
- Chart.js 4.4 (数据可视化)
- 原生JavaScript (前端交互)

**页面**:
- 概览仪表板
- 商品管理
- 测试执行
- 报告中心

## 数据流图

### 完整测试流程

```
1. 发现商品
   └─→ ProductCrawler.discover_products()
       └─→ Shopify API / HTML Parser
           └─→ data/products.json

2. 运行测试
   └─→ pytest (run_tests.sh)
       └─→ conftest.py (参数化商品)
           └─→ Page Objects (测试执行)
               └─→ Playwright (浏览器自动化)
                   └─→ reports/test_results.json

3. 生成报告
   └─→ AI Report Generator
       ├─→ DeepSeek/Claude API
       │   └─→ AI 分析报告
       ├─→ Trend Analyzer
       │   └─→ 趋势分析报告
       └─→ Dashboard Generator
           └─→ HTML 质量看板

4. 告警通知
   └─→ Alert System
       ├─→ Slack Webhook
       ├─→ SMTP Email
       └─→ 企业微信 API
```

## 目录结构

```
fiido-shop-flow-guardian/
│
├── core/                      # 核心框架
│   ├── crawler.py            # 商品爬虫
│   ├── models.py             # 数据模型
│   ├── selector_manager.py   # 选择器管理
│   ├── cache.py              # 缓存管理
│   ├── smart_wait.py         # 智能等待
│   └── test_result_collector.py
│
├── pages/                     # 页面对象
│   ├── product_page.py
│   ├── cart_page.py
│   └── checkout_page.py
│
├── scripts/                   # 工具脚本
│   ├── discover_products.py
│   ├── generate_universal_ai_report.py
│   ├── analyze_trends.py
│   ├── detect_product_changes.py
│   ├── generate_dashboard.py
│   └── send_alerts.py
│
├── tests/                     # 测试套件
│   ├── e2e/                  # 端到端测试
│   ├── unit/                 # 单元测试
│   └── integration/          # 集成测试
│
├── web/                       # Web 应用
│   ├── app.py                # Flask 应用
│   ├── templates/            # HTML 模板
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── products.html
│   │   ├── tests.html
│   │   └── reports.html
│   └── static/               # 静态资源
│       ├── css/style.css
│       └── js/main.js
│
├── config/                    # 配置文件
│   ├── selectors.json
│   └── alert_config.json
│
├── data/                      # 数据目录
│   ├── products.json
│   ├── product_changes.json
│   └── history/
│
├── reports/                   # 报告目录
│   ├── test_results.json
│   ├── trend_analysis.json
│   ├── dashboard.html
│   └── test_health.json
│
├── docs/                      # 文档
│   ├── README.md
│   ├── WEB_UI_GUIDE.md       # Web界面指南
│   ├── WEB_UI_IMPLEMENTATION.md
│   ├── ARCHITECTURE.md       # 本文件
│   └── ...
│
├── .github/workflows/         # CI/CD
│   ├── daily-test.yml
│   ├── hourly-p0-test.yml
│   └── pr-test.yml
│
├── conftest.py               # Pytest 配置
├── pytest.ini
├── requirements.txt
├── run.sh                    # 通用启动器
├── run_tests.sh              # 测试运行器
└── start_web.sh              # Web 启动器
```

## 技术栈总览

### 后端技术
- **Python 3.11+** - 主要编程语言
- **Flask** - Web 框架
- **Playwright** - 浏览器自动化
- **Pytest** - 测试框架
- **BeautifulSoup** - HTML 解析
- **Pydantic** - 数据验证

### 前端技术
- **Bootstrap 5.3** - UI 框架
- **Chart.js 4.4** - 图表库
- **Bootstrap Icons** - 图标库
- **JavaScript ES6** - 前端逻辑

### AI 服务
- **DeepSeek** - AI 分析（推荐）
- **Claude** - AI 分析（备选）

### DevOps
- **GitHub Actions** - CI/CD
- **Systemd** - 服务管理
- **Nginx** - 反向代理（可选）
- **Gunicorn** - WSGI 服务器（可选）

## 部署架构

### 开发环境

```
开发机器
├── Python 3.11+
├── 虚拟环境 (venv)
├── Flask 开发服务器 (localhost:5000)
└── 本地浏览器测试
```

### 生产环境 (推荐)

```
Linux 服务器
├── Nginx (反向代理)
│   └─→ localhost:80/443 → localhost:5000
├── Gunicorn (WSGI 服务器)
│   ├─→ 4 worker 进程
│   └─→ localhost:5000
├── Systemd (服务管理)
│   └─→ 自动启动/重启
└── Playwright 浏览器
    └─→ Chromium/Firefox/WebKit
```

## 扩展性设计

### 支持新站点
1. 配置新的 `selectors.json`
2. 实现站点特定的 Crawler（如需要）
3. 无需修改测试逻辑

### 添加新测试场景
1. 在 `tests/e2e/` 添加新测试文件
2. 使用现有 Page Objects
3. Pytest 自动发现并执行

### 集成新 AI 服务
1. 在 `scripts/generate_universal_ai_report.py` 添加新 provider
2. 实现 API 调用逻辑
3. Web 界面自动支持

### 添加新告警渠道
1. 在 `scripts/send_alerts.py` 添加新通道
2. 配置 `config/alert_config.json`
3. 自动发送告警

## 性能考量

### 爬虫性能
- 并发请求控制
- 缓存机制（24小时）
- 智能重试（3次）

### 测试性能
- 并行测试（pytest-xdist）
- 智能等待策略
- 增量测试支持

### Web性能
- CDN 加速（Bootstrap、Chart.js）
- 静态资源缓存
- 异步任务处理

## 安全考量

### API 安全
- CORS 配置
- 输入验证
- 错误处理

### 数据安全
- 环境变量存储敏感信息（.env）
- .gitignore 排除敏感文件
- 数据文件权限控制

### 生产建议
- 启用 HTTPS
- 配置防火墙
- 添加认证系统
- 日志审计

## 监控与维护

### 日志
- Flask 日志
- Pytest 输出
- 浏览器控制台

### 健康检查
- `/api/health` 端点
- 系统状态监控
- 定期健康检查

### 备份
- 数据文件定期备份
- 历史数据归档
- 配置文件版本控制

## 总结

Fiido Shop Flow Guardian 是一个**企业级**的电商自动化测试平台，具有：

✅ **模块化架构** - 松耦合，易扩展
✅ **多层次设计** - 清晰的职责划分
✅ **双界面支持** - CLI + Web
✅ **智能分析** - AI 驱动
✅ **完整监控** - 7x24 自动化
✅ **生产就绪** - 经过充分测试

**适用场景**:
- 电商网站功能测试
- 购物流程监控
- 性能基线追踪
- 多站点批量测试
- AI 辅助分析
