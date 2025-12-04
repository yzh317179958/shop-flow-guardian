#!/usr/bin/env python3
"""
测试改进后的商品发现功能

测试内容：
1. 从www.fiido.com主页发现所有分类
2. 验证去重机制
3. 验证分类信息保留
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.crawler import ProductCrawler
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def test_discover_collections():
    """测试分类发现功能"""
    print("\n" + "=" * 60)
    print("测试 1: 从主页发现所有分类")
    print("=" * 60)

    crawler = ProductCrawler(base_url="https://www.fiido.com")

    try:
        collections = crawler.discover_collections()

        print(f"\n✅ 成功发现 {len(collections)} 个分类:")
        for i, collection in enumerate(collections, 1):
            print(f"  {i}. {collection}")

        return collections

    except Exception as e:
        print(f"\n❌ 失败: {e}")
        return []
    finally:
        crawler.close()


def test_discover_products(collection_paths):
    """测试商品发现和去重功能"""
    print("\n" + "=" * 60)
    print("测试 2: 发现商品并测试去重机制")
    print("=" * 60)

    if not collection_paths:
        print("❌ 没有分类可测试")
        return

    crawler = ProductCrawler(base_url="https://www.fiido.com")

    try:
        # 只测试前2个分类
        test_collections = collection_paths[:min(2, len(collection_paths))]

        # 使用字典来跟踪商品ID
        all_products = {}
        duplicate_count = 0

        for collection_path in test_collections:
            print(f"\n🔍 正在爬取: {collection_path}")

            products = crawler.discover_products(collection_path, limit=5)

            for product in products:
                if product.id in all_products:
                    duplicate_count += 1
                    print(f"  ⚠️  发现重复商品: {product.name} (ID: {product.id})")
                else:
                    all_products[product.id] = product
                    print(f"  ✅ {product.name}")
                    print(f"     - 分类: {product.category}")
                    print(f"     - 价格: ${product.price_min} - ${product.price_max}")
                    if 'collection_path' in product.metadata:
                        print(f"     - 分类路径: {product.metadata['collection_path']}")

        print(f"\n📊 统计:")
        print(f"  总商品数: {len(all_products)}")
        print(f"  重复商品数: {duplicate_count}")

        if duplicate_count == 0:
            print("  ✅ 去重机制工作正常，未发现重复商品")

    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        crawler.close()


def test_category_formatting():
    """测试分类名称格式化"""
    print("\n" + "=" * 60)
    print("测试 3: 分类名称格式化")
    print("=" * 60)

    crawler = ProductCrawler()

    test_cases = [
        ('electric-bikes', 'Electric Bikes'),
        ('cargo-bikes', 'Cargo Bikes'),
        ('accessories', 'Accessories'),
        ('spare-parts', 'Spare Parts'),
        ('e-bikes', 'E-Bikes'),
    ]

    all_passed = True

    for slug, expected in test_cases:
        result = crawler._format_category_name(slug)
        passed = result == expected

        if passed:
            print(f"  ✅ '{slug}' -> '{result}'")
        else:
            print(f"  ❌ '{slug}' -> '{result}' (期望: '{expected}')")
            all_passed = False

    crawler.close()

    if all_passed:
        print("\n✅ 所有分类格式化测试通过")
    else:
        print("\n⚠️  部分测试失败")


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🧪 商品发现功能改进测试")
    print("=" * 60)

    # 测试1: 发现分类
    collections = test_discover_collections()

    # 测试2: 发现商品和去重
    if collections:
        test_discover_products(collections)

    # 测试3: 分类名称格式化
    test_category_formatting()

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()
