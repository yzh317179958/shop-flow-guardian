# 告警系统配置指南

本指南帮助您配置 Fiido E2E 测试系统的自动告警功能。

## 目录

1. [告警功能概述](#告警功能概述)
2. [Slack 配置](#slack-配置)
3. [邮件配置](#邮件配置)
4. [企业微信配置](#企业微信配置)
5. [告警规则配置](#告警规则配置)
6. [测试告警功能](#测试告警功能)

---

## 告警功能概述

### 支持的告警渠道

| 渠道 | 国内可用 | 配置难度 | 推荐度 |
|------|---------|----------|--------|
| **Slack** | ❌ 需代理 | ⭐⭐ 简单 | ⭐⭐⭐⭐ |
| **邮件** | ✅ 可用 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ |
| **企业微信** | ✅ 可用 | ⭐ 很简单 | ⭐⭐⭐⭐⭐ |

### 告警触发条件

告警系统会在以下情况下自动触发：

1. **P0 核心商品测试失败** 🚨 (严重)
2. **测试通过率低于阈值** ⚠️ (高优先级)
3. **连续多次测试失败** ⚠️ (高优先级)
4. **失败数量突然增加** ℹ️ (中等优先级)

### 告警内容

每次告警包含以下信息：

- 测试通过率和统计数据
- 告警原因和严重程度
- 失败的商品列表（Top 5）
- 测试报告链接
- P0 失败特别提醒

---

## Slack 配置

### 1. 创建 Incoming Webhook

1. 访问 https://api.slack.com/messaging/webhooks
2. 点击 "Create your Slack app"
3. 选择 "From scratch"
4. 输入应用名称（如 "Fiido Test Alerts"）并选择工作区
5. 在左侧菜单选择 "Incoming Webhooks"
6. 开启 "Activate Incoming Webhooks"
7. 点击 "Add New Webhook to Workspace"
8. 选择要发送消息的频道
9. 复制生成的 Webhook URL

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXX
```

### 3. 测试 Slack 告警

```bash
# 创建测试结果文件
cat > reports/test-results.json << 'EOF'
{
  "pass_rate": 0.85,
  "total": 100,
  "passed": 85,
  "failed": 15,
  "skipped": 0,
  "timestamp": "2025-12-02T10:00:00",
  "summary": {
    "p0_failures": 1
  },
  "failures": [
    {
      "product_name": "Fiido D11",
      "priority": "P0",
      "error_message": "Add to cart button not found"
    }
  ]
}
EOF

# 测试发送告警
python scripts/send_alerts.py --channel slack --results-file reports/test-results.json
```

### 4. Slack 消息示例

<img src="docs/images/slack-alert-example.png" width="600" alt="Slack Alert Example">

告警消息包含：
- 🚨 醒目的标题
- 📊 关键指标卡片
- 📝 失败商品列表
- 🔗 报告链接按钮

---

## 邮件配置

### 1. 使用 Gmail (推荐)

#### 步骤 1: 开启两步验证

1. 访问 https://myaccount.google.com/security
2. 找到 "登录 Google" 部分
3. 点击 "两步验证" 并按提示开启

#### 步骤 2: 生成应用专用密码

1. 访问 https://myaccount.google.com/apppasswords
2. 在 "选择应用" 下拉菜单中选择 "其他（自定义名称）"
3. 输入名称（如 "Fiido Test Alerts"）
4. 点击 "生成"
5. 复制生成的 16 位密码

#### 步骤 3: 配置环境变量

在 `.env` 文件中添加：

```bash
# 发件人
ALERT_EMAIL_SENDER=your-email@gmail.com

# 收件人（多个用逗号分隔）
ALERT_EMAIL_RECIPIENTS=qa@company.com,dev@company.com

# SMTP 配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=生成的16位应用专用密码
```

### 2. 使用 Outlook/Office 365

```bash
SMTP_SERVER=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=your-email@outlook.com
SMTP_PASSWORD=your-password
```

### 3. 使用企业邮箱

咨询您的 IT 部门获取 SMTP 服务器配置：

```bash
SMTP_SERVER=smtp.yourcompany.com
SMTP_PORT=587  # 或 25, 465
SMTP_USER=your-email@yourcompany.com
SMTP_PASSWORD=your-password
```

### 4. 测试邮件告警

```bash
python scripts/send_alerts.py --channel email --results-file reports/test-results.json
```

### 5. 邮件示例

邮件内容包含：
- 📊 格式化的测试统计表格
- ⚠️ 告警原因说明
- 📋 失败商品列表
- 🔗 HTML 格式，美观易读

---

## 企业微信配置

### 1. 创建群机器人

1. 打开企业微信群聊
2. 点击右上角 "..." > "群设置"
3. 找到 "群机器人" > "添加机器人"
4. 输入机器人名称（如 "Fiido 测试告警"）
5. 复制生成的 Webhook 地址

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxxx
```

### 3. 启用企业微信通道

编辑 `config/alert_config.json`:

```json
{
  "channels": {
    "wechat": {
      "enabled": true,
      "webhook_env": "WECHAT_WEBHOOK_URL"
    }
  }
}
```

### 4. 测试企业微信告警

```bash
python scripts/send_alerts.py --channel wechat --results-file reports/test-results.json
```

---

## 告警规则配置

### 配置文件位置

`config/alert_config.json`

### 关键配置项

#### 1. 告警阈值

```json
{
  "thresholds": {
    "pass_rate": 0.90,              // 通过率阈值（90%）
    "consecutive_failures": 3,      // 连续失败次数
    "failure_spike_multiplier": 2.0, // 失败突增倍数
    "p0_failure_tolerance": 0,      // P0 失败容忍度（0表示不容忍）
    "p1_failure_tolerance": 2       // P1 失败容忍度
  }
}
```

#### 2. 静默时间

避免在休息时间发送非紧急告警：

```json
{
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "08:00",
    "timezone": "Asia/Shanghai",
    "suppress_non_critical": true  // 仅抑制非严重告警
  }
}
```

#### 3. 通道配置

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "webhook_env": "SLACK_WEBHOOK_URL",
      "mention_users": ["@qa-team"],
      "mention_on_p0_failure": true,  // P0 失败时 @ 用户
      "max_failures_to_show": 5       // 最多显示5个失败
    },
    "email": {
      "enabled": true,
      "include_html_report": true,
      "attach_screenshots": false     // 不附加截图（避免邮件过大）
    }
  }
}
```

---

## 测试告警功能

### 1. 本地测试

```bash
# 1. 创建测试数据
cat > reports/test-results.json << 'EOF'
{
  "pass_rate": 0.75,
  "total": 100,
  "passed": 75,
  "failed": 25,
  "skipped": 0,
  "timestamp": "2025-12-02T10:00:00",
  "summary": {"p0_failures": 2},
  "failures": [
    {"product_name": "Product A", "priority": "P0"},
    {"product_name": "Product B", "priority": "P1"}
  ]
}
EOF

# 2. 测试 Slack
python scripts/send_alerts.py --channel slack

# 3. 测试邮件
python scripts/send_alerts.py --channel email

# 4. 测试企业微信
python scripts/send_alerts.py --channel wechat

# 5. 测试所有渠道
python scripts/send_alerts.py --channel all
```

### 2. 在 GitHub Actions 中测试

将 Secrets 配置到 GitHub 仓库后，手动触发测试工作流：

1. 访问 Actions 页面
2. 选择 "Daily Test" 工作流
3. 点击 "Run workflow"
4. 测试完成后检查是否收到告警

### 3. 检查告警历史

```bash
# 查看告警历史
cat data/alert_history.json

# 健康检查
python scripts/check_test_health.py
```

---

## 常见问题

### Q1: Slack 告警发送失败

**可能原因**:
- Webhook URL 配置错误
- 网络连接问题（国内需要代理）

**解决方法**:
```bash
# 测试 Webhook 是否可访问
curl -X POST -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}' \
  YOUR_WEBHOOK_URL
```

### Q2: Gmail 邮件发送失败

**可能原因**:
- 未开启两步验证
- 使用了账号密码而非应用专用密码
- SMTP 端口被防火墙阻止

**解决方法**:
1. 确认已开启两步验证
2. 使用应用专用密码
3. 检查防火墙规则：`telnet smtp.gmail.com 587`

### Q3: 企业微信没有收到消息

**可能原因**:
- Webhook URL 过期
- 机器人被删除

**解决方法**:
1. 重新创建群机器人
2. 更新 Webhook URL

### Q4: 告警太频繁

**解决方法**:

调整 `config/alert_config.json` 中的阈值：

```json
{
  "thresholds": {
    "pass_rate": 0.80  // 降低阈值
  }
}
```

或启用静默时间：

```json
{
  "quiet_hours": {
    "enabled": true
  }
}
```

---

## 下一步

1. ✅ 配置至少一个告警渠道
2. ✅ 测试告警发送功能
3. ✅ 将 Secrets 添加到 GitHub
4. ✅ 运行一次完整测试验证告警
5. 📊 定期查看 `check_test_health.py` 输出

---

**需要帮助？**

查看完整文档：
- [测试指南](TESTING.md)
- [AI 配置指南](ai-providers-guide.md)
- [项目 README](../README.md)
