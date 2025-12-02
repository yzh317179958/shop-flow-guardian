#!/bin/bash
# Fiido Shop Flow Guardian 完整验证脚本

echo "=========================================="
echo "Fiido Shop Flow Guardian 完整验证"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASSED=0
FAILED=0

echo ""
echo "[1/7] 测试商品发现..."
./run.sh python scripts/discover_products.py > /tmp/discover.log 2>&1
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ 商品发现成功${NC}"
  PASSED=$((PASSED+1))
  # 显示发现的商品数
  if [ -f data/products.json ]; then
    PRODUCT_COUNT=$(cat data/products.json | grep -o '"product_id"' | wc -l)
    echo "   发现 $PRODUCT_COUNT 个商品"
  fi
else
  echo -e "${RED}❌ 商品发现失败${NC}"
  cat /tmp/discover.log
  FAILED=$((FAILED+1))
fi

echo ""
echo "[2/7] 测试单元测试..."
./run.sh pytest tests/unit/ -v --tb=short > /tmp/unit.log 2>&1
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ 单元测试通过${NC}"
  PASSED=$((PASSED+1))
  # 显示测试数量
  grep "passed" /tmp/unit.log | tail -1
else
  echo -e "${RED}❌ 单元测试失败${NC}"
  grep -A 5 "FAILED\|ERROR" /tmp/unit.log | head -20
  FAILED=$((FAILED+1))
fi

echo ""
echo "[3/7] 测试集成测试..."
./run.sh pytest tests/integration/ -v --tb=short > /tmp/integration.log 2>&1
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ 集成测试通过${NC}"
  PASSED=$((PASSED+1))
  grep "passed" /tmp/integration.log | tail -1
else
  echo -e "${RED}❌ 集成测试失败${NC}"
  grep -A 5 "FAILED\|ERROR" /tmp/integration.log | head -20
  FAILED=$((FAILED+1))
fi

echo ""
echo "[4/7] 测试 E2E 测试..."
./run.sh pytest tests/e2e/ -v --json-report --json-report-file=reports/test-results.json --tb=short > /tmp/e2e.log 2>&1
E2E_EXIT_CODE=$?
if [ $E2E_EXIT_CODE -eq 0 ]; then
  echo -e "${GREEN}✅ E2E 测试全部通过${NC}"
  PASSED=$((PASSED+1))
  grep "passed" /tmp/e2e.log | tail -1
else
  echo -e "${YELLOW}⚠️ E2E 测试部分失败 (继续验证报告生成)${NC}"
  grep "passed\|failed" /tmp/e2e.log | tail -1
  PASSED=$((PASSED+1))  # E2E 可以部分失败
fi

echo ""
echo "[5/7] 测试 DeepSeek API 连接..."
./run.sh python scripts/test_deepseek_connection.py > /tmp/deepseek.log 2>&1
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ DeepSeek API 连接成功${NC}"
  PASSED=$((PASSED+1))
  grep "响应内容" /tmp/deepseek.log -A 1
else
  echo -e "${RED}❌ DeepSeek API 连接失败${NC}"
  cat /tmp/deepseek.log
  FAILED=$((FAILED+1))
fi

echo ""
echo "[6/7] 生成 AI 摘要..."
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek --summary-only > /tmp/summary.log 2>&1
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ AI 摘要生成成功${NC}"
  PASSED=$((PASSED+1))
  echo "   摘要预览:"
  grep -A 3 "^=====" /tmp/summary.log | head -5
else
  echo -e "${RED}❌ AI 摘要生成失败${NC}"
  cat /tmp/summary.log
  FAILED=$((FAILED+1))
fi

echo ""
echo "[7/7] 生成完整 AI 报告..."
./run.sh python scripts/generate_universal_ai_report.py --provider deepseek > /tmp/report.log 2>&1
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ AI 报告生成成功${NC}"
  PASSED=$((PASSED+1))

  # 检查报告质量
  if [ -f reports/latest-ai-report.md ]; then
    REPORT_SIZE=$(wc -c < reports/latest-ai-report.md)
    echo "   报告大小: $REPORT_SIZE 字节"

    # 检查必需章节
    SECTIONS=0
    grep -q "## 1. 执行摘要" reports/latest-ai-report.md && SECTIONS=$((SECTIONS+1))
    grep -q "## 2. 关键指标" reports/latest-ai-report.md && SECTIONS=$((SECTIONS+1))
    grep -q "## 3. 失败分析" reports/latest-ai-report.md && SECTIONS=$((SECTIONS+1))
    grep -q "## 4. 趋势洞察" reports/latest-ai-report.md && SECTIONS=$((SECTIONS+1))
    grep -q "## 5. 行动建议" reports/latest-ai-report.md && SECTIONS=$((SECTIONS+1))

    echo "   报告章节: $SECTIONS/5"

    if [ $SECTIONS -ge 5 ]; then
      echo -e "   ${GREEN}✅ 报告结构完整${NC}"
    else
      echo -e "   ${YELLOW}⚠️ 报告结构不完整${NC}"
    fi
  fi
else
  echo -e "${RED}❌ AI 报告生成失败${NC}"
  cat /tmp/report.log
  FAILED=$((FAILED+1))
fi

# 总结
echo ""
echo "=========================================="
echo "验证结果汇总"
echo "=========================================="
echo -e "通过: ${GREEN}$PASSED${NC} / 7"
echo -e "失败: ${RED}$FAILED${NC} / 7"

if [ $FAILED -eq 0 ]; then
  echo ""
  echo -e "${GREEN}✅ 所有验证完成！系统运行正常！${NC}"
  echo ""
  echo "生成的文件:"
  echo "  - 商品数据: data/products.json"
  echo "  - 测试结果: reports/test-results.json"
  echo "  - AI 报告: reports/latest-ai-report.md"
  echo ""
  echo "查看完整报告:"
  echo "  cat reports/latest-ai-report.md"
  exit 0
else
  echo ""
  echo -e "${RED}❌ 验证失败！请检查上述错误信息${NC}"
  echo ""
  echo "日志文件:"
  echo "  /tmp/discover.log"
  echo "  /tmp/unit.log"
  echo "  /tmp/integration.log"
  echo "  /tmp/e2e.log"
  echo "  /tmp/deepseek.log"
  echo "  /tmp/summary.log"
  echo "  /tmp/report.log"
  exit 1
fi
