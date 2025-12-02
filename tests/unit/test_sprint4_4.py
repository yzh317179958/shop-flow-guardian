#!/usr/bin/env python3
"""
Sprint 4.4 单元测试

测试以下功能:
- 商品变更检测
- 历史趋势分析
- 质量看板生成
"""

import unittest
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.detect_product_changes import ProductChangeDetector
from scripts.analyze_trends import TrendAnalyzer
from scripts.generate_dashboard import DashboardGenerator


class TestProductChangeDetector(unittest.TestCase):
    """测试商品变更检测器"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # 创建测试数据目录
        self.data_dir = self.temp_path / "data"
        self.history_dir = self.data_dir / "history"
        self.history_dir.mkdir(parents=True, exist_ok=True)

        # 创建当前商品数据
        self.current_products_file = self.data_dir / "products.json"
        self.current_products = [
            {
                "id": "product-1",
                "name": "Product 1",
                "url": "https://example.com/product-1",
                "price_min": 100,
                "price_max": 100,
                "variants": [],
                "selectors": {},
                "metadata": {"available": True}
            },
            {
                "id": "product-2",
                "name": "Product 2",
                "url": "https://example.com/product-2",
                "price_min": 200,
                "price_max": 250,
                "variants": [{"color": "red"}, {"color": "blue"}],
                "selectors": {},
                "metadata": {"available": True}
            }
        ]

        with open(self.current_products_file, 'w') as f:
            json.dump(self.current_products, f)

        # 创建历史商品数据
        self.history_file = self.history_dir / "products_20240101_120000.json"
        self.history_products = [
            {
                "id": "product-1",
                "name": "Product 1 Old",
                "url": "https://example.com/product-1",
                "price_min": 90,
                "price_max": 90,
                "variants": [],
                "selectors": {},
                "metadata": {"available": True}
            },
            {
                "id": "product-3",
                "name": "Product 3",
                "url": "https://example.com/product-3",
                "price_min": 300,
                "price_max": 300,
                "variants": [],
                "selectors": {},
                "metadata": {"available": True}
            }
        ]

        with open(self.history_file, 'w') as f:
            json.dump(self.history_products, f)

        # 初始化检测器
        self.detector = ProductChangeDetector(
            current_products_file=str(self.current_products_file),
            history_dir=str(self.history_dir),
            changes_file=str(self.data_dir / "product_changes.json")
        )

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_products(self):
        """测试加载商品数据"""
        products = self.detector._load_products(self.current_products_file)
        self.assertEqual(len(products), 2)
        self.assertIn("product-1", products)
        self.assertIn("product-2", products)

    def test_detect_added_products(self):
        """测试检测新增商品"""
        report = self.detector.detect_changes()
        added = report['changes']['added']

        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]['id'], 'product-2')

    def test_detect_removed_products(self):
        """测试检测删除商品"""
        report = self.detector.detect_changes()
        removed = report['changes']['removed']

        self.assertEqual(len(removed), 1)
        self.assertEqual(removed[0]['id'], 'product-3')

    def test_detect_modified_products(self):
        """测试检测修改商品"""
        report = self.detector.detect_changes()
        modified = report['changes']['modified']

        self.assertEqual(len(modified), 1)
        self.assertEqual(modified[0]['id'], 'product-1')
        self.assertIn('price_changed', modified[0]['reason'])
        self.assertIn('name_changed', modified[0]['reason'])

    def test_generate_test_targets(self):
        """测试生成测试目标"""
        report = self.detector.detect_changes()
        test_targets = report['test_targets']

        # 应该包含新增和修改的商品
        self.assertEqual(len(test_targets), 2)

        # 新增商品应该是 P0
        added_target = next(t for t in test_targets if t['id'] == 'product-2')
        self.assertEqual(added_target['priority'], 'P0')

        # 价格变更应该是 P0
        modified_target = next(t for t in test_targets if t['id'] == 'product-1')
        self.assertEqual(modified_target['priority'], 'P0')


class TestTrendAnalyzer(unittest.TestCase):
    """测试历史趋势分析器"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # 创建测试报告目录
        self.reports_dir = self.temp_path / "reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        # 创建模拟测试报告
        for i in range(10):
            date = datetime.now() - timedelta(days=i)
            report_dir = self.reports_dir / f"report_{i}"
            report_dir.mkdir(exist_ok=True)

            test_results = {
                "timestamp": date.isoformat(),
                "summary": {
                    "total": 100,
                    "passed": 90 + i,  # 模拟通过率变化
                    "failed": 10 - i
                },
                "tests": [
                    {
                        "product_id": "product-1",
                        "product_name": "Product 1",
                        "status": "failed" if j < (10 - i) else "passed",
                        "error_type": "timeout" if j % 2 == 0 else "selector_not_found",
                        "region": "US" if j % 3 == 0 else "EU",
                        "metrics": {
                            "page_load_time": 2.0 + (j % 3) * 0.5,
                            "api_response_time": 0.5 + (j % 2) * 0.2
                        }
                    }
                    for j in range(100)
                ]
            }

            with open(report_dir / "test_results.json", 'w') as f:
                json.dump(test_results, f)

        # 初始化分析器
        self.analyzer = TrendAnalyzer(
            reports_dir=str(self.reports_dir),
            days=30,
            output_file=str(self.reports_dir / "trend_analysis.json")
        )

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_test_reports(self):
        """测试加载测试报告"""
        reports = self.analyzer._load_test_reports()
        self.assertEqual(len(reports), 10)

    def test_calculate_pass_rate_trend(self):
        """测试计算通过率趋势"""
        reports = self.analyzer._load_test_reports()
        pass_rate_trend = self.analyzer._calculate_pass_rate_trend(reports)

        self.assertIn('data', pass_rate_trend)
        self.assertIn('statistics', pass_rate_trend)

        stats = pass_rate_trend['statistics']
        self.assertIn('average_pass_rate', stats)
        self.assertIn('trend', stats)

        # 通过率应该是提升的（因为我们模拟了递增）
        self.assertEqual(stats['trend'], 'improving')

    def test_analyze_frequent_failures(self):
        """测试分析高频失败"""
        reports = self.analyzer._load_test_reports()
        frequent_failures = self.analyzer._analyze_frequent_failures(reports)

        self.assertIn('total_unique_failures', frequent_failures)
        self.assertIn('top_failures', frequent_failures)

        # 应该有失败记录
        self.assertGreater(frequent_failures['total_unique_failures'], 0)

    def test_analyze_regional_performance(self):
        """测试分析地区性能"""
        reports = self.analyzer._load_test_reports()
        regional_performance = self.analyzer._analyze_regional_performance(reports)

        self.assertIn('total_regions', regional_performance)
        self.assertIn('regions', regional_performance)

        # 应该有 US 和 EU 两个地区
        self.assertEqual(regional_performance['total_regions'], 2)

    def test_full_analysis(self):
        """测试完整分析"""
        report = self.analyzer.analyze()

        self.assertIn('pass_rate_trend', report)
        self.assertIn('frequent_failures', report)
        self.assertIn('regional_performance', report)
        self.assertIn('performance_trends', report)
        self.assertIn('insights', report)


class TestDashboardGenerator(unittest.TestCase):
    """测试质量看板生成器"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

        # 创建模拟报告文件
        self.trend_report_file = self.temp_path / "trend_analysis.json"
        self.test_results_file = self.temp_path / "test_results.json"
        self.health_report_file = self.temp_path / "test_health.json"

        # 创建模拟数据
        trend_report = {
            "pass_rate_trend": {
                "data": [
                    {"date": "2024-01-01", "pass_rate": 95.0},
                    {"date": "2024-01-02", "pass_rate": 96.0}
                ],
                "statistics": {
                    "average_pass_rate": 95.5,
                    "trend": "improving"
                }
            },
            "frequent_failures": {
                "top_failures": [
                    {
                        "product_id": "product-1",
                        "product_name": "Product 1",
                        "failure_count": 10,
                        "failure_days": 5,
                        "main_error_type": "timeout"
                    }
                ]
            },
            "regional_performance": {
                "regions": [
                    {"region": "US", "pass_rate": 96.0, "total_tests": 100},
                    {"region": "EU", "pass_rate": 94.0, "total_tests": 100}
                ]
            },
            "performance_trends": {
                "data": [
                    {"date": "2024-01-01", "avg_page_load_time": 2.0},
                    {"date": "2024-01-02", "avg_page_load_time": 2.1}
                ],
                "statistics": {
                    "avg_page_load_time": 2.05
                }
            },
            "insights": [
                {
                    "type": "positive",
                    "message": "测试通过率呈上升趋势",
                    "priority": "info"
                }
            ]
        }

        test_results = {
            "summary": {
                "total": 100,
                "passed": 95,
                "failed": 5
            }
        }

        health_report = {
            "status": "HEALTHY",
            "metrics": {
                "average_pass_rate": 95.5
            }
        }

        with open(self.trend_report_file, 'w') as f:
            json.dump(trend_report, f)

        with open(self.test_results_file, 'w') as f:
            json.dump(test_results, f)

        with open(self.health_report_file, 'w') as f:
            json.dump(health_report, f)

        # 初始化生成器
        self.generator = DashboardGenerator(
            trend_report_file=str(self.trend_report_file),
            test_results_file=str(self.test_results_file),
            health_report_file=str(self.health_report_file),
            output_file=str(self.temp_path / "dashboard.html")
        )

    def tearDown(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_load_json_files(self):
        """测试加载 JSON 文件"""
        trend_report = self.generator._load_json_file(self.trend_report_file)
        self.assertIn('pass_rate_trend', trend_report)

        test_results = self.generator._load_json_file(self.test_results_file)
        self.assertIn('summary', test_results)

    def test_generate_dashboard(self):
        """测试生成看板"""
        html = self.generator.generate_dashboard()

        # 检查 HTML 包含必要内容
        self.assertIn('<!DOCTYPE html>', html)
        self.assertIn('Fiido 测试质量看板', html)
        self.assertIn('HEALTHY', html)
        self.assertIn('95.5%', html)

    def test_save_dashboard(self):
        """测试保存看板"""
        self.generator.save_dashboard()

        # 检查文件是否创建
        self.assertTrue(self.generator.output_file.exists())

        # 检查文件内容
        with open(self.generator.output_file) as f:
            html = f.read()
            self.assertIn('<!DOCTYPE html>', html)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
