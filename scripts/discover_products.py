#!/usr/bin/env python3
"""
商品发现命令行工具

从 Fiido 网站自动发现和抓取商品信息，保存为 JSON 文件供测试使用。

使用示例:
    # 发现所有商品
    python scripts/discover_products.py

    # 只发现特定分类
    python scripts/discover_products.py --collections bikes,accessories

    # 限制每个分类的商品数量
    python scripts/discover_products.py --limit 10

    # 增量更新（只抓取新商品）
    python scripts/discover_products.py --incremental

    # 指定输出文件
    python scripts/discover_products.py --output data/my_products.json
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.crawler import ProductCrawler
from core.models import Product


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_existing_products(file_path: Path) -> Dict[str, Dict[str, Any]]:
    """加载已存在的商品数据

    Args:
        file_path: 商品数据文件路径

    Returns:
        商品字典，key 为商品 ID
    """
    if not file_path.exists():
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return {p['id']: p for p in data.get('products', [])}
    except Exception as e:
        logger.warning(f"Failed to load existing products: {e}")
        return {}


def save_products(products: List[Product], file_path: Path, metadata: Dict[str, Any]):
    """保存商品数据到 JSON 文件

    Args:
        products: 商品列表
        file_path: 输出文件路径
        metadata: 元数据信息
    """
    # 确保输出目录存在
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 将 Pydantic 模型转换为字典
    products_data = [p.model_dump(mode='json') for p in products]

    output = {
        'metadata': metadata,
        'products': products_data
    }

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    logger.info(f"Products saved to {file_path}")


def print_statistics(
    total_collections: int,
    total_products: int,
    new_products: int,
    updated_products: int,
    duration: float
):
    """打印统计信息

    Args:
        total_collections: 扫描的分类总数
        total_products: 商品总数
        new_products: 新增商品数
        updated_products: 更新商品数
        duration: 执行耗时（秒）
    """
    print("\n" + "=" * 60)
    print("商品发现统计")
    print("=" * 60)
    print(f"扫描分类数: {total_collections}")
    print(f"商品总数: {total_products}")
    print(f"新增商品: {new_products}")
    print(f"更新商品: {updated_products}")
    print(f"执行耗时: {duration:.2f} 秒")
    print("=" * 60)


def discover_products_from_collections(
    crawler: ProductCrawler,
    collection_paths: List[str],
    limit_per_collection: int = None,
    existing_products: Dict[str, Dict[str, Any]] = None
) -> tuple[List[Product], int, int]:
    """从分类列表中发现商品

    Args:
        crawler: ProductCrawler 实例
        collection_paths: 分类路径列表
        limit_per_collection: 每个分类的商品数量限制
        existing_products: 已存在的商品字典

    Returns:
        (商品列表, 新增数量, 更新数量)
    """
    # 使用字典进行去重，key为商品ID
    products_dict = {}
    new_count = 0
    updated_count = 0
    duplicate_count = 0
    existing_products = existing_products or {}

    for i, collection_path in enumerate(collection_paths, 1):
        logger.info(f"[{i}/{len(collection_paths)}] Processing collection: {collection_path}")

        try:
            products = crawler.discover_products(collection_path, limit=limit_per_collection)

            for product in products:
                # 去重检查：如果商品ID已存在，跳过
                if product.id in products_dict:
                    duplicate_count += 1
                    logger.debug(f"  Skipping duplicate product: {product.name} (ID: {product.id})")
                    continue

                # 检查是新商品还是更新
                if product.id in existing_products:
                    # 更新已存在的商品
                    existing_product = existing_products[product.id]
                    # 保留原有的测试状态和最后测试时间
                    if 'test_status' in existing_product:
                        product.test_status = existing_product['test_status']
                    if 'last_tested' in existing_product and existing_product['last_tested']:
                        # 不覆盖 last_tested，保持原值
                        pass
                    updated_count += 1
                else:
                    # 新商品
                    new_count += 1

                # 添加到去重字典
                products_dict[product.id] = product

            logger.info(f"  Found {len(products)} products in {collection_path}")

        except Exception as e:
            logger.error(f"  Failed to process {collection_path}: {e}")
            continue

    # 转换为列表
    all_products = list(products_dict.values())

    if duplicate_count > 0:
        logger.info(f"📊 De-duplication: Removed {duplicate_count} duplicate products")

    return all_products, new_count, updated_count


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从 Fiido 网站发现和抓取商品信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--base-url',
        default='https://fiido.com',
        help='网站根 URL (默认: https://fiido.com)'
    )

    parser.add_argument(
        '--collections',
        type=str,
        help='指定要扫描的分类，用逗号分隔 (例如: bikes,accessories)。不指定则扫描所有分类'
    )

    parser.add_argument(
        '--limit',
        type=int,
        help='限制每个分类的商品数量'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/products.json'),
        help='输出文件路径 (默认: data/products.json)'
    )

    parser.add_argument(
        '--incremental',
        action='store_true',
        help='增量更新模式：只抓取新商品，保留已有商品的测试状态'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='请求超时时间（秒）(默认: 30)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='显示详细日志'
    )

    args = parser.parse_args()

    # 配置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 记录开始时间
    start_time = datetime.now()

    # 初始化爬虫
    logger.info(f"Initializing ProductCrawler for {args.base_url}")
    crawler = ProductCrawler(base_url=args.base_url, timeout=args.timeout)

    try:
        # 确定要扫描的分类
        if args.collections:
            # 用户指定分类
            collection_paths = [f'/collections/{c.strip()}' for c in args.collections.split(',')]
            logger.info(f"Scanning specified collections: {collection_paths}")
        else:
            # 自动发现所有分类
            logger.info("Discovering all collections...")
            collection_paths = crawler.discover_collections()
            logger.info(f"Found {len(collection_paths)} collections")

        if not collection_paths:
            logger.warning("No collections found!")
            return

        # 加载已存在的商品（如果是增量更新）
        existing_products = {}
        if args.incremental:
            logger.info(f"Loading existing products from {args.output}")
            existing_products = load_existing_products(args.output)
            logger.info(f"Loaded {len(existing_products)} existing products")

        # 从分类中发现商品
        logger.info(f"Starting product discovery from {len(collection_paths)} collections...")
        all_products, new_count, updated_count = discover_products_from_collections(
            crawler=crawler,
            collection_paths=collection_paths,
            limit_per_collection=args.limit,
            existing_products=existing_products if args.incremental else None
        )

        # 保存结果
        metadata = {
            'base_url': args.base_url,
            'discovered_at': datetime.now().isoformat(),
            'total_collections': len(collection_paths),
            'total_products': len(all_products),
            'new_products': new_count,
            'updated_products': updated_count,
            'incremental': args.incremental
        }

        save_products(all_products, args.output, metadata)

        # 打印统计信息
        duration = (datetime.now() - start_time).total_seconds()
        print_statistics(
            total_collections=len(collection_paths),
            total_products=len(all_products),
            new_products=new_count,
            updated_products=updated_count,
            duration=duration
        )

        logger.info("Product discovery completed successfully!")

    except KeyboardInterrupt:
        logger.warning("Product discovery interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Product discovery failed: {e}", exc_info=True)
        sys.exit(1)

    finally:
        crawler.close()


if __name__ == '__main__':
    main()
