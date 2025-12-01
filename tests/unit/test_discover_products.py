"""
discover_products 命令行工具单元测试

测试命令行参数解析、文件操作等功能。
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pytest

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.models import Product, Selectors
from scripts.discover_products import (
    load_existing_products,
    save_products,
    print_statistics,
    discover_products_from_collections
)


class TestLoadExistingProducts:
    """测试加载已存在商品"""

    def test_load_from_nonexistent_file(self, tmp_path):
        """测试从不存在的文件加载"""
        file_path = tmp_path / "nonexistent.json"
        result = load_existing_products(file_path)
        assert result == {}

    def test_load_from_valid_file(self, tmp_path):
        """测试从有效文件加载"""
        file_path = tmp_path / "products.json"
        data = {
            'metadata': {},
            'products': [
                {'id': '1', 'name': 'Product 1'},
                {'id': '2', 'name': 'Product 2'}
            ]
        }
        file_path.write_text(json.dumps(data), encoding='utf-8')

        result = load_existing_products(file_path)
        assert len(result) == 2
        assert '1' in result
        assert result['1']['name'] == 'Product 1'

    def test_load_from_invalid_json(self, tmp_path):
        """测试从无效 JSON 文件加载"""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("invalid json", encoding='utf-8')

        result = load_existing_products(file_path)
        assert result == {}


class TestSaveProducts:
    """测试保存商品"""

    def test_save_products_creates_directory(self, tmp_path):
        """测试保存时自动创建目录"""
        output_dir = tmp_path / "nested" / "dir"
        file_path = output_dir / "products.json"

        products = [
            Product(
                id="1",
                name="Test Product",
                url="https://fiido.com/products/test",
                category="Test",
                price_min=100.0,
                price_max=100.0,
                currency="USD",
                variants=[],
                selectors=Selectors()
            )
        ]

        metadata = {'test': 'data'}
        save_products(products, file_path, metadata)

        assert file_path.exists()
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert 'metadata' in data
        assert 'products' in data
        assert len(data['products']) == 1
        assert data['products'][0]['id'] == '1'

    def test_save_multiple_products(self, tmp_path):
        """测试保存多个商品"""
        file_path = tmp_path / "products.json"

        products = [
            Product(
                id=str(i),
                name=f"Product {i}",
                url=f"https://fiido.com/products/product-{i}",
                category="Test",
                price_min=100.0 * i,
                price_max=200.0 * i,
                currency="USD",
                variants=[],
                selectors=Selectors()
            )
            for i in range(1, 4)
        ]

        metadata = {'count': 3}
        save_products(products, file_path, metadata)

        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert len(data['products']) == 3
        assert data['metadata']['count'] == 3


class TestPrintStatistics:
    """测试打印统计信息"""

    def test_print_statistics(self, capsys):
        """测试统计信息打印格式"""
        print_statistics(
            total_collections=5,
            total_products=100,
            new_products=80,
            updated_products=20,
            duration=45.67
        )

        captured = capsys.readouterr()
        output = captured.out

        assert "商品发现统计" in output
        assert "扫描分类数: 5" in output
        assert "商品总数: 100" in output
        assert "新增商品: 80" in output
        assert "更新商品: 20" in output
        assert "执行耗时: 45.67 秒" in output


class TestDiscoverProductsFromCollections:
    """测试从分类发现商品"""

    def test_discover_from_single_collection(self):
        """测试从单个分类发现商品"""
        mock_crawler = Mock()
        mock_products = [
            Product(
                id="1",
                name="Product 1",
                url="https://fiido.com/products/product-1",
                category="Bikes",
                price_min=100.0,
                price_max=100.0,
                currency="USD",
                variants=[],
                selectors=Selectors()
            )
        ]
        mock_crawler.discover_products.return_value = mock_products

        products, new_count, updated_count = discover_products_from_collections(
            crawler=mock_crawler,
            collection_paths=['/collections/bikes']
        )

        assert len(products) == 1
        assert new_count == 1
        assert updated_count == 0
        mock_crawler.discover_products.assert_called_once_with('/collections/bikes', limit=None)

    def test_discover_with_existing_products(self):
        """测试增量更新模式"""
        mock_crawler = Mock()
        mock_products = [
            Product(
                id="1",
                name="Product 1",
                url="https://fiido.com/products/product-1",
                category="Bikes",
                price_min=100.0,
                price_max=100.0,
                currency="USD",
                variants=[],
                selectors=Selectors()
            ),
            Product(
                id="2",
                name="Product 2",
                url="https://fiido.com/products/product-2",
                category="Bikes",
                price_min=200.0,
                price_max=200.0,
                currency="USD",
                variants=[],
                selectors=Selectors()
            )
        ]
        mock_crawler.discover_products.return_value = mock_products

        existing_products = {
            '1': {'id': '1', 'test_status': 'passing', 'last_tested': '2025-01-01'}
        }

        products, new_count, updated_count = discover_products_from_collections(
            crawler=mock_crawler,
            collection_paths=['/collections/bikes'],
            existing_products=existing_products
        )

        assert len(products) == 2
        assert new_count == 1  # Product 2 is new
        assert updated_count == 1  # Product 1 is updated
        assert products[0].test_status == 'passing'  # Preserved from existing

    def test_discover_with_limit(self):
        """测试限制商品数量"""
        mock_crawler = Mock()
        mock_crawler.discover_products.return_value = []

        discover_products_from_collections(
            crawler=mock_crawler,
            collection_paths=['/collections/bikes'],
            limit_per_collection=10
        )

        mock_crawler.discover_products.assert_called_with('/collections/bikes', limit=10)

    def test_discover_handles_errors(self):
        """测试处理错误情况"""
        mock_crawler = Mock()
        mock_crawler.discover_products.side_effect = Exception("Network error")

        products, new_count, updated_count = discover_products_from_collections(
            crawler=mock_crawler,
            collection_paths=['/collections/bikes', '/collections/accessories']
        )

        # 即使有错误，也应继续处理其他分类
        assert len(products) == 0
        assert mock_crawler.discover_products.call_count == 2


class TestMainFunction:
    """测试主函数"""

    @patch('scripts.discover_products.ProductCrawler')
    def test_main_with_help(self, mock_crawler_class):
        """测试显示帮助信息"""
        with patch('sys.argv', ['discover_products.py', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                from scripts.discover_products import main
                main()
            assert exc_info.value.code == 0
