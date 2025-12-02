# DeepSeek AI 报告快速开始指南

## 🚀 3 步开始使用

### 步骤 1: 获取 DeepSeek API Key (1分钟)

1. 访问 https://platform.deepseek.com/
2. 点击 "注册" (支持国内手机号)
3. 登录后进入 "API Keys" 页面
4. 点击 "创建新密钥"
5. 复制生成的 API Key (格式: `sk-...`)

### 步骤 2: 配置环境变量 (30秒)

编辑项目根目录的 `.env` 文件:

```bash
# DeepSeek API 配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx  # 粘贴你的 API Key
```

### 步骤 3: 测试并使用 (1分钟)

```bash
# 1. 测试 API 连接
./run.sh python scripts/test_deepseek_connection.py

# 2. 生成 AI 测试报告
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek
```

完成！🎉

---

## 📝 完整使用流程

### 1. 运行自动化测试

```bash
./run.sh pytest tests/ -v
```

### 2. 生成 AI 分析报告

```bash
# 完整报告 (包含详细分析)
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek

# 仅生成摘要 (快速查看)
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek --summary-only
```

### 3. 查看报告

```bash
cat reports/latest-ai-report.md
```

---

## 💡 报告内容

AI 报告包含:

1. **执行摘要** - 测试整体情况总结
2. **关键指标** - 通过率、失败数等统计
3. **失败分析** - 按优先级分类的问题分析
4. **趋势洞察** - 识别高失败率商品和共同模式
5. **修复建议** - 具体的问题修复方案

---

## ⚙️ 高级选项

### 自定义输出路径

```bash
./run.sh python scripts/generate_universal_ai_report.py \
  --provider deepseek \
  --output reports/sprint-3-report.md
```

### 指定测试结果文件

```bash
./run.sh python scripts/generate_universal_ai_report.py \
  --provider deepseek \
  --results reports/custom-results.json
```

### 使用 Claude (如果有官方 API Key)

```bash
# 在 .env 中配置
CLAUDE_API_KEY=sk-ant-api03-xxx

# 生成报告
./run.sh python scripts/generate_universal_ai_report.py --provider claude
```

---

## 🆘 常见问题

### API Key 无效

**问题**: `❌ 请先在 .env 文件中设置 DEEPSEEK_API_KEY`

**解决**:
1. 检查 `.env` 文件是否存在
2. 确认 `DEEPSEEK_API_KEY` 已设置
3. API Key 不要包含多余的空格或引号

### 网络连接错误

**问题**: `Connection error`

**解决**:
1. 检查网络连接
2. DeepSeek 在国内，不需要代理
3. 如果使用了代理，尝试关闭代理

### 依赖包缺失

**问题**: `No module named 'openai'`

**解决**:
```bash
./run.sh pip install openai python-dotenv
```

### 测试结果文件不存在

**问题**: `Test results not found`

**解决**:
1. 先运行测试生成结果文件
2. 或使用示例数据: `--results reports/test-results.json`

---

## 📊 成本和配额

### DeepSeek 免费额度

- **每天**: 500万 tokens
- **每次报告**: 约 5,000 tokens
- **每天可生成**: 1000+ 次报告

### 实际使用

一般项目每天:
- 运行测试: 5-10 次
- 生成报告: 5-10 次
- Token 消耗: 约 25,000-50,000

**完全在免费额度内！** ✅

---

## 📚 相关文档

- **详细使用指南**: `docs/ai-providers-guide.md`
- **开发总结**: `docs/sprint-3-final-summary.md`
- **API 文档**: https://platform.deepseek.com/docs

---

## 🎯 下一步

现在你可以:

1. ✅ 运行自动化测试
2. ✅ 生成 AI 智能分析报告
3. ✅ 快速识别和修复问题
4. ✅ 持续监控测试质量

**享受免费的 AI 驱动测试分析！** 🚀
