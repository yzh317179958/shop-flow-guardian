#!/bin/bash
# 快速健康检查脚本 (30秒快速验证)

echo "🔍 快速健康检查..."
echo ""

# 1. 环境检查
echo -n "1. Python 环境... "
if ./run.sh python --version > /dev/null 2>&1; then
  echo "✅"
else
  echo "❌"
  exit 1
fi

# 2. 依赖检查
echo -n "2. 核心依赖... "
if ./run.sh pip show playwright pytest openai > /dev/null 2>&1; then
  echo "✅"
else
  echo "❌"
  exit 1
fi

# 3. 商品数据
echo -n "3. 商品数据... "
if [ -f data/products.json ] && [ -s data/products.json ]; then
  PRODUCTS=$(cat data/products.json | grep -o '"product_id"' | wc -l)
  echo "✅ ($PRODUCTS 个商品)"
else
  echo "⚠️ (未发现，运行: ./run.sh python scripts/discover_products.py)"
fi

# 4. DeepSeek API
echo -n "4. DeepSeek API... "
if grep -q "DEEPSEEK_API_KEY=sk-" .env 2>/dev/null; then
  echo "✅"
else
  echo "❌ (未配置)"
  exit 1
fi

# 5. API 连接测试
echo -n "5. API 连接... "
if ./run.sh python scripts/test_deepseek_connection.py > /dev/null 2>&1; then
  echo "✅"
else
  echo "❌"
  exit 1
fi

# 6. 快速单元测试
echo -n "6. 核心功能... "
if ./run.sh pytest tests/unit/test_selector_manager.py -q > /dev/null 2>&1; then
  echo "✅"
else
  echo "❌"
  exit 1
fi

echo ""
echo "✅ 系统健康状态良好！"
echo ""
echo "运行完整验证: ./verify_all.sh"
