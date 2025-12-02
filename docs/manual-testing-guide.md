# 手动测试验证指南 - Fiido Shop Flow Guardian

**目标**: 验证 Sprint 0-3 所有功能的完整性和正确性

---

## 测试环境准备

### 前置条件检查

```bash
# 1. 检查 Python 版本 (需要 3.10+)
python3 --version

# 2. 检查虚拟环境
ls venv/

# 3. 检查依赖安装
./run.sh pip list | grep -E "playwright|pytest|anthropic|openai"
```

**成功指标**:
- ✅ Python 版本 >= 3.10
- ✅ venv 目录存在
- ✅ 所有关键依赖已安装

**失败指标**:
- ❌ Python 版本过低
- ❌ 虚拟环境不存在
- ❌ 缺少关键依赖

---

## 测试模块 1: 商品爬虫 (Sprint 1)

### 测试 1.1: 商品发现功能

**测试步骤**:

```bash
# 1. 运行商品发现脚本
./run.sh python scripts/discover_products.py

# 2. 查看生成的数据文件
ls -lh data/products.json

# 3. 查看数据内容
cat data/products.json | head -50
```

**原理**:
- 爬虫访问 fiido.com 首页
- 解析导航菜单获取分类链接
- 访问每个分类页面抓取商品列表
- 提取商品 ID、名称、价格、URL 等信息
- 保存为 JSON 格式

**成功指标**:
- ✅ `data/products.json` 文件存在
- ✅ 文件大小 > 1KB
- ✅ JSON 格式正确，包含商品数据
- ✅ 每个商品有以下字段:
  ```json
  {
    "product_id": "fiido-xxx",
    "name": "商品名称",
    "price": "价格",
    "url": "https://fiido.com/products/xxx",
    "category": "bike/scooter/accessory",
    "priority": "P0/P1/P2"
  }
  ```
- ✅ 控制台输出显示: `✅ 发现 X 个商品`

**失败指标**:
- ❌ 文件不存在或大小为 0
- ❌ JSON 格式错误
- ❌ 商品数量为 0
- ❌ 缺少必需字段
- ❌ 控制台显示错误信息

**故障排查**:
```bash
# 如果失败，查看详细错误
./run.sh python scripts/discover_products.py 2>&1 | tee logs/discover.log

# 检查网络连接
curl -I https://fiido.com

# 检查 Playwright 浏览器
./run.sh playwright --version
```

---

### 测试 1.2: 选择器管理器

**测试步骤**:

```bash
# 1. 运行单元测试
./run.sh pytest tests/unit/test_selector_manager.py -v

# 2. 查看测试结果
```

**原理**:
- SelectorManager 管理页面元素的选择器
- 支持多个备用选择器 (主选择器失败时自动尝试备用)
- 提供统一的元素查找接口

**成功指标**:
- ✅ 所有测试用例通过
- ✅ 控制台显示: `X passed`
- ✅ 没有 FAILED 或 ERROR

**失败指标**:
- ❌ 测试失败 (显示 FAILED)
- ❌ 导入错误或语法错误

---

## 测试模块 2: 页面对象 (Sprint 2)

### 测试 2.1: ProductPage (商品页面)

**测试步骤**:

```bash
# 1. 运行商品页面单元测试
./run.sh pytest tests/unit/test_product_page.py -v

# 2. 运行商品页面集成测试
./run.sh pytest tests/integration/test_product_page_integration.py -v
```

**原理**:
- ProductPage 封装商品详情页的所有操作
- 包括: 导航到商品页、获取商品信息、选择配置、添加到购物车
- 使用 Page Object Model (POM) 模式

**成功指标**:
- ✅ 所有单元测试通过
- ✅ 集成测试通过 (真实浏览器交互)
- ✅ 能成功导航到商品页
- ✅ 能正确获取商品标题、价格
- ✅ 能成功添加商品到购物车

**失败指标**:
- ❌ 测试失败
- ❌ 超时错误 (元素未找到)
- ❌ 断言错误 (数据不匹配)

**手动验证** (可选):
```bash
# 运行带界面的测试 (观察浏览器操作)
./run.sh pytest tests/integration/test_product_page_integration.py -v -s --headed
```

观察浏览器:
- ✅ 浏览器自动打开
- ✅ 自动导航到商品页
- ✅ 自动点击 "Add to Cart" 按钮
- ✅ 购物车图标显示数量变化

---

### 测试 2.2: CartPage (购物车页面)

**测试步骤**:

```bash
# 1. 运行购物车单元测试
./run.sh pytest tests/unit/test_cart_page.py -v

# 2. 运行购物车集成测试
./run.sh pytest tests/integration/test_cart_page_integration.py -v
```

**原理**:
- CartPage 封装购物车页面操作
- 功能: 查看购物车、验证商品、更新数量、删除商品、前往结账

**成功指标**:
- ✅ 能成功导航到购物车页面
- ✅ 能正确获取购物车商品列表
- ✅ 能验证商品信息 (名称、价格、数量)
- ✅ 能更新商品数量
- ✅ 能删除商品
- ✅ 能点击 "Checkout" 按钮

**失败指标**:
- ❌ 购物车为空时断言失败
- ❌ 商品信息不匹配
- ❌ 操作超时

---

### 测试 2.3: CheckoutPage (结账页面)

**测试步骤**:

```bash
# 1. 运行结账页面单元测试
./run.sh pytest tests/unit/test_checkout_page.py -v

# 2. 运行结账页面集成测试
./run.sh pytest tests/integration/test_checkout_page_integration.py -v
```

**原理**:
- CheckoutPage 封装结账流程操作
- 功能: 填写邮箱、地址、支付信息、提交订单

**成功指标**:
- ✅ 能成功进入结账页面
- ✅ 能填写客户信息 (邮箱)
- ✅ 能填写收货地址
- ✅ 能选择配送方式
- ✅ 能填写支付信息
- ✅ 表单验证正确

**失败指标**:
- ❌ 无法加载结账页面
- ❌ 表单字段无法填写
- ❌ 提交按钮不可点击

---

## 测试模块 3: E2E 测试 (Sprint 2)

### 测试 3.1: 完整购物流程

**测试步骤**:

```bash
# 1. 运行单个商品的完整流程测试
./run.sh pytest tests/e2e/test_shopping_flow.py::test_full_checkout_flow_us -v -s

# 2. 运行所有 E2E 测试
./run.sh pytest tests/e2e/ -v
```

**原理**:
- 模拟真实用户完整购物流程
- 步骤: 访问商品页 → 添加到购物车 → 查看购物车 → 进入结账 → 填写信息 → (测试环境不提交)

**成功指标**:
- ✅ 测试完整执行无报错
- ✅ 每个步骤都成功完成
- ✅ 控制台输出显示每个步骤的进度
- ✅ 截图文件生成 (如果失败)

**失败指标**:
- ❌ 任何步骤超时
- ❌ 元素未找到
- ❌ 断言失败
- ❌ 网络错误

**观察指标** (带界面模式):
```bash
# 运行带界面的测试
./run.sh pytest tests/e2e/test_shopping_flow.py::test_full_checkout_flow_us -v -s --headed --slowmo 1000
```

观察浏览器行为:
1. ✅ 自动打开商品页
2. ✅ 自动点击 "Add to Cart"
3. ✅ 自动导航到购物车页面
4. ✅ 自动点击 "Checkout"
5. ✅ 自动填写邮箱
6. ✅ 自动填写地址信息
7. ✅ 自动选择配送方式
8. ✅ 自动填写测试支付信息

**每一步预期结果**:
- 步骤 1-2: 购物车图标数字增加
- 步骤 3: URL 变为 `/cart`
- 步骤 4: URL 变为 `/checkout`
- 步骤 5-8: 表单字段自动填充

---

### 测试 3.2: 多商品并发测试

**测试步骤**:

```bash
# 运行所有商品的测试 (并发)
./run.sh pytest tests/e2e/ -v -n 4
```

**原理**:
- 使用 pytest-xdist 并发执行测试
- 每个测试在独立的浏览器实例中运行
- 验证系统在并发场景下的稳定性

**成功指标**:
- ✅ 所有测试通过
- ✅ 通过率 > 90%
- ✅ 无并发冲突错误

**失败指标**:
- ❌ 大量测试失败
- ❌ 并发错误 (锁、资源冲突)

---

## 测试模块 4: AI 报告生成 (Sprint 3)

### 测试 4.1: DeepSeek API 连接

**测试步骤**:

```bash
# 1. 检查 .env 配置
cat .env | grep DEEPSEEK_API_KEY

# 2. 测试 API 连接
./run.sh python scripts/test_deepseek_connection.py
```

**原理**:
- 使用 OpenAI SDK 连接 DeepSeek API
- 发送简单测试请求验证连接和认证
- 检查 API 响应和 token 消耗

**成功指标**:
- ✅ 控制台显示: `✅ DeepSeek API 连接成功!`
- ✅ 显示 AI 响应内容
- ✅ 显示 token 使用统计
- ✅ 无错误信息

**失败指标**:
- ❌ `❌ 请先在 .env 文件中设置 DEEPSEEK_API_KEY`
- ❌ 认证错误 (401 Unauthorized)
- ❌ 网络连接错误
- ❌ API 限流错误 (429 Too Many Requests)

**故障排查**:
```bash
# 检查 API Key 格式
cat .env | grep DEEPSEEK_API_KEY
# 应该显示: DEEPSEEK_API_KEY=sk-xxx

# 检查网络连接
curl https://api.deepseek.com

# 检查依赖
./run.sh pip show openai
```

---

### 测试 4.2: 测试结果收集

**测试步骤**:

```bash
# 1. 运行测试并收集结果
./run.sh pytest tests/e2e/ -v --json-report --json-report-file=reports/test-results.json

# 2. 检查生成的 JSON 文件
ls -lh reports/test-results.json

# 3. 查看 JSON 内容
cat reports/test-results.json | python3 -m json.tool | head -100
```

**原理**:
- pytest 插件自动收集测试结果
- TestResultCollector 整理成结构化格式
- 保存为 JSON 文件供 AI 分析

**成功指标**:
- ✅ `reports/test-results.json` 文件存在
- ✅ 文件大小 > 500 bytes
- ✅ JSON 格式正确
- ✅ 包含以下字段:
  ```json
  {
    "summary": {
      "total": X,
      "passed": X,
      "failed": X,
      "skipped": X,
      "pass_rate": X.XX,
      "duration": X.XX
    },
    "failures": [...],
    "failures_by_product": {...}
  }
  ```

**失败指标**:
- ❌ 文件不存在
- ❌ JSON 格式错误
- ❌ 缺少必需字段

---

### 测试 4.3: AI 报告生成 (完整流程)

**测试步骤**:

```bash
# 1. 生成简短摘要
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek --summary-only

# 2. 生成完整报告
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek

# 3. 查看生成的报告
cat reports/latest-ai-report.md

# 4. 验证报告内容
ls -lh reports/latest-ai-report.md
```

**原理**:
1. 加载 `reports/test-results.json`
2. 构建详细的提示词 (包含测试统计、失败详情)
3. 调用 DeepSeek API 生成分析
4. 格式化为 Markdown 报告
5. 保存到文件

**成功指标**:

**步骤 1 (摘要):**
- ✅ 控制台显示: `✅ DeepSeek API 初始化成功`
- ✅ 控制台显示: `✅ 已加载测试结果`
- ✅ 控制台显示: `📝 正在生成失败摘要...`
- ✅ 输出 3-5 句话的摘要
- ✅ 摘要包含:
  - 主要问题原因
  - 影响的功能
  - 修复建议

**步骤 2 (完整报告):**
- ✅ 控制台显示: `✅ AI 报告生成成功`
- ✅ 控制台显示: `✅ 报告已保存: reports/latest-ai-report.md`
- ✅ 控制台显示报告预览

**步骤 3 (报告内容验证):**
- ✅ 报告文件存在且大小 > 2KB
- ✅ 报告包含以下章节:
  1. **执行摘要** (3-5 句话总结)
  2. **关键指标** (表格格式)
  3. **失败分析** (按 P0/P1/P2 分类)
  4. **趋势洞察** (高失败率商品、共同模式)
  5. **行动建议** (立即/高优先级/中长期)

**报告质量检查**:
```bash
# 检查报告结构
grep "## " reports/latest-ai-report.md

# 应该看到:
# ## 1. 执行摘要
# ## 2. 关键指标
# ## 3. 失败分析
# ## 4. 趋势洞察
# ## 5. 行动建议
```

**失败指标**:
- ❌ API 连接失败
- ❌ 报告文件未生成
- ❌ 报告内容不完整 (缺少章节)
- ❌ 报告内容无意义 (乱码或错误)
- ❌ Token 配额耗尽

---

## 完整系统测试 (端到端验证)

### 完整流程测试

**测试步骤**:

```bash
# 1. 发现商品
./run.sh python scripts/discover_products.py

# 2. 运行测试
./run.sh pytest tests/e2e/ -v --json-report --json-report-file=reports/test-results.json

# 3. 生成 AI 报告
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek

# 4. 查看完整报告
cat reports/latest-ai-report.md
```

**原理**:
完整模拟真实使用场景:
1. 爬取最新商品数据
2. 执行自动化测试
3. 收集测试结果
4. AI 分析生成报告

**成功指标** (整个流程):

**阶段 1 (商品发现):**
- ✅ 发现 X 个商品 (X > 0)
- ✅ `data/products.json` 生成

**阶段 2 (测试执行):**
- ✅ 至少运行 10+ 个测试
- ✅ 通过率 > 70%
- ✅ `reports/test-results.json` 生成
- ✅ 测试时长合理 (< 5 分钟)

**阶段 3 (AI 报告):**
- ✅ API 连接成功
- ✅ 报告生成成功
- ✅ 报告质量高 (有意义的分析和建议)

**阶段 4 (验证):**
- ✅ 报告准确识别失败的测试
- ✅ 报告给出合理的修复建议
- ✅ 报告分析了失败趋势

**失败指标**:
- ❌ 任何阶段中断
- ❌ 通过率过低 (< 50%)
- ❌ 报告质量差

---

## 性能测试

### 测试 5.1: 并发测试性能

**测试步骤**:

```bash
# 不同并发度测试
time ./run.sh pytest tests/e2e/ -v -n 1  # 串行
time ./run.sh pytest tests/e2e/ -v -n 2  # 2 并发
time ./run.sh pytest tests/e2e/ -v -n 4  # 4 并发
```

**成功指标**:
- ✅ 并发执行时间 < 串行执行时间
- ✅ 加速比合理 (n=4 应该快 2-3 倍)
- ✅ 无并发错误

**失败指标**:
- ❌ 并发比串行更慢
- ❌ 大量并发错误

---

### 测试 5.2: AI 报告生成性能

**测试步骤**:

```bash
# 测试报告生成时间
time ./run.sh python scripts/generate_universal_ai_report.py --provider deepseek --summary-only

time ./run.sh python scripts/generate_universal_ai_report.py --provider deepseek
```

**成功指标**:
- ✅ 摘要生成 < 10 秒
- ✅ 完整报告生成 < 30 秒
- ✅ Token 消耗合理 (< 10,000 tokens)

**失败指标**:
- ❌ 生成时间过长 (> 60 秒)
- ❌ Token 消耗过高 (> 50,000 tokens)

---

## 稳定性测试

### 测试 6.1: 连续运行测试

**测试步骤**:

```bash
# 连续运行 3 次
for i in 1 2 3; do
  echo "===== Run $i ====="
  ./run.sh pytest tests/e2e/ -v
done
```

**成功指标**:
- ✅ 3 次运行结果一致
- ✅ 通过率稳定 (波动 < 10%)
- ✅ 无新增失败

**失败指标**:
- ❌ 每次结果差异大
- ❌ 通过率不稳定
- ❌ 随机失败 (flaky tests)

---

## 错误恢复测试

### 测试 7.1: 网络错误恢复

**测试步骤**:

```bash
# 1. 断开网络
# (在测试过程中暂时断网)

# 2. 运行测试观察错误处理
./run.sh pytest tests/e2e/test_shopping_flow.py -v

# 3. 恢复网络重试
```

**成功指标**:
- ✅ 明确的错误信息 (不是崩溃)
- ✅ 错误信息有意义
- ✅ 恢复网络后测试可以正常运行

**失败指标**:
- ❌ 程序崩溃
- ❌ 错误信息不清晰
- ❌ 无法恢复

---

## 测试报告检查清单

### 最终验证清单

```
□ 商品发现功能正常
□ 所有单元测试通过
□ 所有集成测试通过
□ E2E 测试通过率 > 90%
□ DeepSeek API 连接正常
□ 测试结果收集正常
□ AI 报告生成正常
□ 报告内容准确有意义
□ 并发测试无错误
□ 性能指标达标
□ 稳定性测试通过
□ 错误恢复正常
```

---

## 快速验证脚本

创建一个快速验证脚本:

```bash
#!/bin/bash
# 文件: verify_all.sh

echo "=========================================="
echo "Fiido Shop Flow Guardian 完整验证"
echo "=========================================="

echo ""
echo "[1/7] 测试商品发现..."
./run.sh python scripts/discover_products.py
if [ $? -eq 0 ]; then
  echo "✅ 商品发现成功"
else
  echo "❌ 商品发现失败"
  exit 1
fi

echo ""
echo "[2/7] 测试单元测试..."
./run.sh pytest tests/unit/ -v
if [ $? -eq 0 ]; then
  echo "✅ 单元测试通过"
else
  echo "❌ 单元测试失败"
  exit 1
fi

echo ""
echo "[3/7] 测试集成测试..."
./run.sh pytest tests/integration/ -v
if [ $? -eq 0 ]; then
  echo "✅ 集成测试通过"
else
  echo "❌ 集成测试失败"
  exit 1
fi

echo ""
echo "[4/7] 测试 E2E 测试..."
./run.sh pytest tests/e2e/ -v --json-report --json-report-file=reports/test-results.json
if [ $? -eq 0 ]; then
  echo "✅ E2E 测试通过"
else
  echo "⚠️ E2E 测试部分失败 (继续验证报告生成)"
fi

echo ""
echo "[5/7] 测试 DeepSeek API..."
./run.sh python scripts/test_deepseek_connection.py
if [ $? -eq 0 ]; then
  echo "✅ DeepSeek API 连接成功"
else
  echo "❌ DeepSeek API 连接失败"
  exit 1
fi

echo ""
echo "[6/7] 生成 AI 摘要..."
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek --summary-only
if [ $? -eq 0 ]; then
  echo "✅ AI 摘要生成成功"
else
  echo "❌ AI 摘要生成失败"
  exit 1
fi

echo ""
echo "[7/7] 生成完整 AI 报告..."
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek
if [ $? -eq 0 ]; then
  echo "✅ AI 报告生成成功"
else
  echo "❌ AI 报告生成失败"
  exit 1
fi

echo ""
echo "=========================================="
echo "✅ 所有验证完成！"
echo "=========================================="
echo ""
echo "查看报告:"
echo "  cat reports/latest-ai-report.md"
```

保存并运行:

```bash
chmod +x verify_all.sh
./verify_all.sh
```

---

## 常见问题诊断

### 问题 1: pytest 找不到测试

**现象**: `collected 0 items`

**诊断**:
```bash
# 检查测试文件
ls tests/e2e/test_*.py

# 检查 pytest 配置
cat pytest.ini
```

**解决**:
- 确保测试文件以 `test_` 开头
- 确保测试函数以 `test_` 开头

---

### 问题 2: Playwright 浏览器错误

**现象**: `Executable doesn't exist`

**诊断**:
```bash
./run.sh playwright --version
```

**解决**:
```bash
./run.sh playwright install chromium
```

---

### 问题 3: DeepSeek API 失败

**现象**: `401 Unauthorized`

**诊断**:
```bash
cat .env | grep DEEPSEEK_API_KEY
```

**解决**:
- 检查 API Key 格式正确
- 确认 API Key 已激活
- 检查配额是否用完

---

### 问题 4: 报告内容质量差

**现象**: 报告内容不准确或无意义

**诊断**:
```bash
# 检查测试结果数据
cat reports/test-results.json | python3 -m json.tool
```

**解决**:
- 确保测试结果数据完整
- 增加失败测试的详细信息
- 调整提示词 (在 generate_universal_ai_report.py)

---

## 总结

### 核心验证流程

```
1. 环境检查
   ↓
2. 商品发现测试
   ↓
3. 单元测试
   ↓
4. 集成测试
   ↓
5. E2E 测试
   ↓
6. AI 连接测试
   ↓
7. AI 报告生成
   ↓
8. 报告质量验证
```

### 关键成功指标汇总

| 模块 | 关键指标 | 目标值 |
|------|---------|--------|
| 商品发现 | 发现商品数 | > 0 |
| 单元测试 | 通过率 | 100% |
| 集成测试 | 通过率 | 100% |
| E2E 测试 | 通过率 | > 90% |
| AI 连接 | 连接成功 | 是 |
| AI 报告 | 生成成功 | 是 |
| 报告质量 | 包含 5 个章节 | 是 |
| 性能 | 完整流程时间 | < 5 分钟 |

---

**验证完成后，您的系统应该**:
- ✅ 能自动发现商品
- ✅ 能运行自动化测试
- ✅ 能生成测试结果
- ✅ 能连接 AI 服务
- ✅ 能生成智能分析报告
- ✅ 报告内容准确有价值
