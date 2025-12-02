# 测试验证检查清单

**使用说明**: 按照此清单逐项验证系统功能

---

## 📋 快速验证 (5分钟)

### ☐ 运行健康检查

```bash
./health_check.sh
```

**预期输出**:
```
🔍 快速健康检查...

1. Python 环境... ✅
2. 核心依赖... ✅
3. 商品数据... ✅ (X 个商品)
4. DeepSeek API... ✅
5. API 连接... ✅
6. 核心功能... ✅

✅ 系统健康状态良好！
```

如果全部 ✅，说明系统基本正常。

---

## 📋 完整验证 (10-15分钟)

### ☐ 运行完整验证脚本

```bash
./verify_all.sh
```

**预期输出**:
```
==========================================
Fiido Shop Flow Guardian 完整验证
==========================================

[1/7] 测试商品发现...
✅ 商品发现成功
   发现 X 个商品

[2/7] 测试单元测试...
✅ 单元测试通过
   X passed

[3/7] 测试集成测试...
✅ 集成测试通过
   X passed

[4/7] 测试 E2E 测试...
✅ E2E 测试全部通过
   X passed

[5/7] 测试 DeepSeek API 连接...
✅ DeepSeek API 连接成功

[6/7] 生成 AI 摘要...
✅ AI 摘要生成成功

[7/7] 生成完整 AI 报告...
✅ AI 报告生成成功
   报告大小: XXXX 字节
   报告章节: 5/5
   ✅ 报告结构完整

==========================================
验证结果汇总
==========================================
通过: 7 / 7
失败: 0 / 7

✅ 所有验证完成！系统运行正常！
```

---

## 📋 逐项手动验证

### ☐ 1. 环境检查

```bash
# 检查 Python 版本
python3 --version
# 预期: Python 3.10 或更高

# 检查虚拟环境
ls venv/
# 预期: 存在 bin/, lib/, 等目录

# 检查依赖
./run.sh pip list | grep -E "playwright|pytest|openai|anthropic"
# 预期: 显示已安装的包版本
```

**✅ 通过标准**: 所有命令成功执行，版本符合要求

---

### ☐ 2. 商品爬虫功能

```bash
# 运行商品发现
./run.sh python scripts/discover_products.py

# 检查输出文件
ls -lh data/products.json

# 查看内容
cat data/products.json | python3 -m json.tool | head -50
```

**✅ 通过标准**:
- 控制台显示: `✅ 发现 X 个商品`
- `data/products.json` 文件存在且大小 > 1KB
- JSON 格式正确
- 每个商品包含: product_id, name, url, category, priority

**❌ 失败标志**:
- 文件不存在或为空
- JSON 格式错误
- 商品数量为 0

---

### ☐ 3. 单元测试

```bash
# 运行所有单元测试
./run.sh pytest tests/unit/ -v
```

**✅ 通过标准**:
- 所有测试 PASSED
- 控制台显示: `X passed`
- 无 FAILED 或 ERROR

**测试明细**:
- ☐ `test_selector_manager.py` - 选择器管理器
- ☐ `test_product_page.py` - 商品页面对象
- ☐ `test_cart_page.py` - 购物车页面对象
- ☐ `test_checkout_page.py` - 结账页面对象

---

### ☐ 4. 集成测试

```bash
# 运行集成测试
./run.sh pytest tests/integration/ -v
```

**✅ 通过标准**:
- 所有测试 PASSED
- 浏览器操作正常执行
- 无超时错误

**测试明细**:
- ☐ 商品页面导航
- ☐ 添加到购物车
- ☐ 购物车操作
- ☐ 结账页面加载

---

### ☐ 5. E2E 端到端测试

```bash
# 运行 E2E 测试
./run.sh pytest tests/e2e/ -v --json-report --json-report-file=reports/test-results.json
```

**✅ 通过标准**:
- 通过率 > 90%
- 核心流程测试通过
- 测试结果文件生成

**测试明细**:
- ☐ 完整购物流程 (US)
- ☐ 完整购物流程 (EU)
- ☐ 添加到购物车并验证
- ☐ 购物车商品详情
- ☐ 结账页面直接访问

**关键测试**:
```bash
# 测试单个完整流程 (带界面观察)
./run.sh pytest tests/e2e/test_shopping_flow.py::test_full_checkout_flow_us -v -s --headed --slowmo 1000
```

**观察清单**:
- ☐ 浏览器自动打开
- ☐ 导航到商品页面
- ☐ 点击 "Add to Cart"
- ☐ 购物车图标数量增加
- ☐ 导航到购物车页面
- ☐ 显示商品信息
- ☐ 点击 "Checkout"
- ☐ 进入结账页面
- ☐ 自动填写邮箱
- ☐ 自动填写地址
- ☐ 自动选择配送方式
- ☐ 填写测试支付信息

---

### ☐ 6. DeepSeek API 连接

```bash
# 测试 API 连接
./run.sh python scripts/test_deepseek_connection.py
```

**✅ 通过标准**:
```
✅ 已找到 API Key: sk-xxx...
🔌 正在连接 DeepSeek API...
📤 发送测试请求...
✅ DeepSeek API 连接成功!
📝 响应内容: [AI回复内容]
📊 使用情况:
   - Prompt Tokens: XX
   - Completion Tokens: XX
   - Total Tokens: XX
```

**❌ 失败标志**:
- `❌ 请先在 .env 文件中设置 DEEPSEEK_API_KEY`
- 认证错误 (401)
- 网络连接错误

---

### ☐ 7. 测试结果收集

```bash
# 检查测试结果文件
ls -lh reports/test-results.json

# 查看内容
cat reports/test-results.json | python3 -m json.tool
```

**✅ 通过标准**:
- 文件存在且大小 > 500 bytes
- JSON 格式正确
- 包含以下结构:
  ```json
  {
    "summary": {
      "total": X,
      "passed": X,
      "failed": X,
      "skipped": X,
      "pass_rate": XX.XX,
      "duration": XX.XX
    },
    "failures": [...],
    "failures_by_product": {...}
  }
  ```

---

### ☐ 8. AI 报告生成 (摘要)

```bash
# 生成摘要
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek --summary-only
```

**✅ 通过标准**:
```
✅ DeepSeek API 初始化成功
✅ 使用 AI 提供商: deepseek
✅ 已加载测试结果: reports/test-results.json

📝 正在生成失败摘要...

============================================================
[3-5句话的摘要内容]
- 主要问题原因
- 影响的功能
- 修复建议
============================================================

✅ AI 报告生成完成！
```

---

### ☐ 9. AI 报告生成 (完整)

```bash
# 生成完整报告
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek

# 查看报告
cat reports/latest-ai-report.md
```

**✅ 通过标准**:

**9.1 生成成功**:
```
✅ DeepSeek API 初始化成功
✅ 已加载测试结果
🤖 正在生成 AI 报告...
✅ AI 报告生成成功
✅ 报告已保存: reports/latest-ai-report.md
```

**9.2 报告结构**:
```bash
# 检查章节
grep "^## " reports/latest-ai-report.md
```

预期输出:
```
## 1. 执行摘要
## 2. 关键指标
## 3. 失败分析
## 4. 趋势洞察
## 5. 行动建议
```

**9.3 报告内容质量**:

报告应包含:
- ☐ **执行摘要**: 3-5句话总结测试情况
- ☐ **关键指标表格**: 包含通过率、失败数等统计
- ☐ **失败分析**:
  - P0 严重问题 (阻塞核心流程)
  - P1 高优先级 (影响重要功能)
  - 每个失败包含: 原因分析、影响范围、修复方案
- ☐ **趋势洞察**:
  - 高失败率商品识别
  - 共同失败模式
  - 可能的根本原因
- ☐ **行动建议**:
  - 立即行动项
  - 高优先级跟进
  - 中长期改进

**报告示例检查**:
```bash
# 检查是否包含关键词
grep -i "P0\|P1\|修复\|建议\|问题" reports/latest-ai-report.md | wc -l
# 预期: > 10 (说明分析详细)

# 检查表格
grep "|" reports/latest-ai-report.md | wc -l
# 预期: > 5 (说明有表格)
```

---

### ☐ 10. 性能测试

```bash
# 测试串行执行
time ./run.sh pytest tests/e2e/ -v -n 1

# 测试并发执行
time ./run.sh pytest tests/e2e/ -v -n 4
```

**✅ 通过标准**:
- 并发执行时间 < 串行执行时间
- 加速比合理 (n=4 应该快 2-3倍)
- 无并发错误

---

### ☐ 11. 稳定性测试

```bash
# 连续运行3次
for i in 1 2 3; do
  echo "===== Run $i ====="
  ./run.sh pytest tests/e2e/ -v
done
```

**✅ 通过标准**:
- 3次运行通过率一致 (波动 < 10%)
- 无新增失败
- 无随机失败 (flaky tests)

---

## 📋 报告质量评估清单

打开 `reports/latest-ai-report.md` 检查:

### ☐ 1. 基本信息
- ☐ 包含生成时间
- ☐ 标注分析引擎 (DEEPSEEK)
- ☐ 标注项目名称

### ☐ 2. 执行摘要
- ☐ 简洁明了 (3-5句话)
- ☐ 包含通过率
- ☐ 提到主要问题
- ☐ 中文表述

### ☐ 3. 关键指标
- ☐ 表格格式清晰
- ☐ 包含所有统计数据
- ☐ 数据准确 (与测试结果一致)

### ☐ 4. 失败分析
- ☐ 按优先级分类 (P0/P1/P2)
- ☐ 每个失败包含:
  - ☐ 测试名称
  - ☐ 失败原因分析
  - ☐ 影响范围
  - ☐ 修复方案
- ☐ 分析合理有见地

### ☐ 5. 趋势洞察
- ☐ 识别高失败率商品
- ☐ 识别共同失败模式
- ☐ 提出可能的根本原因
- ☐ 洞察有价值

### ☐ 6. 行动建议
- ☐ 按优先级分类 (立即/高优先级/中长期)
- ☐ 建议具体可执行
- ☐ 优先级合理

### ☐ 7. 整体质量
- ☐ Markdown 格式正确
- ☐ 无乱码或格式错误
- ☐ 中文表述流畅
- ☐ 有适当的 emoji 使用
- ☐ 内容有实际价值

---

## 📋 常见问题诊断

### 问题: pytest 找不到测试

**检查**:
```bash
ls tests/e2e/test_*.py
cat pytest.ini
```

**解决**: 确保测试文件和函数以 `test_` 开头

---

### 问题: Playwright 浏览器错误

**检查**:
```bash
./run.sh playwright --version
```

**解决**:
```bash
./run.sh playwright install chromium
```

---

### 问题: DeepSeek API 失败

**检查**:
```bash
cat .env | grep DEEPSEEK_API_KEY
```

**解决**: 确认 API Key 正确且已激活

---

### 问题: 测试结果文件不存在

**检查**:
```bash
ls -la reports/
```

**解决**: 确保运行测试时加上 `--json-report` 参数

---

### 问题: 报告内容质量差

**检查**:
```bash
cat reports/test-results.json | python3 -m json.tool
```

**解决**: 确保测试结果数据完整且包含失败信息

---

## ✅ 最终验证清单

### 系统功能
- ☐ 商品爬虫工作正常
- ☐ 单元测试全部通过
- ☐ 集成测试全部通过
- ☐ E2E 测试通过率 > 90%
- ☐ DeepSeek API 连接正常
- ☐ 测试结果收集正常
- ☐ AI 报告生成正常

### 报告质量
- ☐ 报告结构完整 (5个章节)
- ☐ 报告内容准确
- ☐ 分析有深度
- ☐ 建议可执行

### 性能和稳定性
- ☐ 并发测试无错误
- ☐ 连续运行结果一致
- ☐ 性能指标达标

### 文档和工具
- ☐ 使用文档完整
- ☐ 验证脚本可用
- ☐ 健康检查可用

---

## 🎯 验证成功标准

**所有项目 ✅ 时，系统完全就绪，可以投入使用！**

**部分项目 ⚠️ 时，记录问题并咨询开发团队。**

**任何项目 ❌ 时，系统存在问题，需要修复后再使用。**
