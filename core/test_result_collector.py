"""
测试结果收集器

用于收集 pytest 测试结果并生成结构化的 JSON 报告。
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    """单个测试用例结果"""
    test_id: str
    test_name: str
    product_id: Optional[str]
    status: str  # passed, failed, skipped
    duration: float
    error_message: Optional[str] = None
    screenshot_path: Optional[str] = None
    traceback: Optional[str] = None


@dataclass
class TestSummary:
    """测试摘要统计"""
    total: int
    passed: int
    failed: int
    skipped: int
    duration: float
    pass_rate: float
    start_time: str
    end_time: str


class TestResultCollector:
    """测试结果收集器"""

    def __init__(self, output_path: str = "reports/test-results.json"):
        """初始化测试结果收集器

        Args:
            output_path: 输出 JSON 文件路径
        """
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        self.test_cases: List[TestCase] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

        logger.info(f"TestResultCollector initialized: {output_path}")

    def start_session(self):
        """开始测试会话"""
        self.start_time = datetime.now()
        self.test_cases = []
        logger.info("Test session started")

    def end_session(self):
        """结束测试会话"""
        self.end_time = datetime.now()
        logger.info("Test session ended")

    def add_test_result(
        self,
        test_id: str,
        test_name: str,
        status: str,
        duration: float,
        product_id: Optional[str] = None,
        error_message: Optional[str] = None,
        screenshot_path: Optional[str] = None,
        traceback: Optional[str] = None,
    ):
        """添加测试结果

        Args:
            test_id: 测试唯一标识
            test_name: 测试名称
            status: 测试状态 (passed/failed/skipped)
            duration: 执行时间(秒)
            product_id: 关联的商品 ID
            error_message: 错误消息
            screenshot_path: 失败截图路径
            traceback: 错误堆栈
        """
        test_case = TestCase(
            test_id=test_id,
            test_name=test_name,
            product_id=product_id,
            status=status,
            duration=duration,
            error_message=error_message,
            screenshot_path=screenshot_path,
            traceback=traceback,
        )

        self.test_cases.append(test_case)
        logger.debug(f"Added test result: {test_id} - {status}")

    def get_summary(self) -> TestSummary:
        """生成测试摘要

        Returns:
            TestSummary: 测试摘要对象
        """
        total = len(self.test_cases)
        passed = sum(1 for tc in self.test_cases if tc.status == "passed")
        failed = sum(1 for tc in self.test_cases if tc.status == "failed")
        skipped = sum(1 for tc in self.test_cases if tc.status == "skipped")

        total_duration = sum(tc.duration for tc in self.test_cases)
        pass_rate = (passed / total * 100) if total > 0 else 0.0

        return TestSummary(
            total=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            duration=total_duration,
            pass_rate=round(pass_rate, 2),
            start_time=self.start_time.isoformat() if self.start_time else "",
            end_time=self.end_time.isoformat() if self.end_time else "",
        )

    def get_failures(self) -> List[Dict]:
        """获取所有失败的测试

        Returns:
            List[Dict]: 失败测试列表
        """
        failures = [
            asdict(tc) for tc in self.test_cases
            if tc.status == "failed"
        ]
        return failures

    def get_failures_by_product(self) -> Dict[str, List[Dict]]:
        """按商品分组获取失败测试

        Returns:
            Dict[str, List[Dict]]: 商品ID -> 失败测试列表
        """
        failures_by_product = {}

        for tc in self.test_cases:
            if tc.status == "failed" and tc.product_id:
                if tc.product_id not in failures_by_product:
                    failures_by_product[tc.product_id] = []
                failures_by_product[tc.product_id].append(asdict(tc))

        return failures_by_product

    def save(self):
        """保存测试结果到 JSON 文件"""
        if not self.end_time:
            self.end_session()

        summary = self.get_summary()
        failures = self.get_failures()

        report = {
            "summary": asdict(summary),
            "test_cases": [asdict(tc) for tc in self.test_cases],
            "failures": failures,
            "failures_by_product": self.get_failures_by_product(),
            "metadata": {
                "generator": "Fiido Shop Flow Guardian",
                "version": "1.0",
                "generated_at": datetime.now().isoformat(),
            }
        }

        # 保存 JSON
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        logger.info(f"Test results saved to {self.output_path}")
        logger.info(f"Summary: {summary.passed}/{summary.total} passed ({summary.pass_rate}%)")

        return report

    def load_from_file(self, filepath: str) -> Dict:
        """从文件加载测试结果

        Args:
            filepath: JSON 文件路径

        Returns:
            Dict: 测试结果数据
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        logger.info(f"Loaded test results from {filepath}")
        return data


# Pytest 插件集成
def pytest_configure(config):
    """Pytest 配置钩子"""
    if not hasattr(config, '_result_collector'):
        config._result_collector = TestResultCollector()
        config._result_collector.start_session()


def pytest_runtest_logreport(report):
    """Pytest 测试报告钩子"""
    if report.when == 'call':
        collector = report.config._result_collector

        # 提取商品 ID
        product_id = None
        if hasattr(report, 'keywords'):
            for marker in report.keywords.get('parametrize', []):
                if 'product' in str(marker):
                    # 尝试从参数中提取 product_id
                    product_id = getattr(report, 'product_id', None)

        # 提取错误信息
        error_message = None
        traceback = None
        if report.failed:
            error_message = str(report.longrepr) if report.longrepr else "Unknown error"
            traceback = str(report.longrepr)

        # 提取截图路径
        screenshot_path = None
        if hasattr(report, 'screenshot_path'):
            screenshot_path = report.screenshot_path

        # 添加测试结果
        collector.add_test_result(
            test_id=report.nodeid,
            test_name=report.nodeid.split("::")[-1],
            status="passed" if report.passed else ("failed" if report.failed else "skipped"),
            duration=report.duration,
            product_id=product_id,
            error_message=error_message,
            screenshot_path=screenshot_path,
            traceback=traceback if report.failed else None,
        )


def pytest_sessionfinish(session, exitstatus):
    """Pytest 会话结束钩子"""
    if hasattr(session.config, '_result_collector'):
        collector = session.config._result_collector
        collector.save()


if __name__ == "__main__":
    # 示例用法
    collector = TestResultCollector("test-results.json")
    collector.start_session()

    # 模拟添加测试结果
    collector.add_test_result(
        test_id="tests/test_example.py::test_product_page",
        test_name="test_product_page",
        status="passed",
        duration=1.5,
        product_id="fiido-t1",
    )

    collector.add_test_result(
        test_id="tests/test_example.py::test_add_to_cart",
        test_name="test_add_to_cart",
        status="failed",
        duration=2.3,
        product_id="fiido-t1",
        error_message="Cart button not found",
        screenshot_path="screenshots/failure_cart.png",
    )

    # 保存结果
    report = collector.save()

    print(f"Total: {report['summary']['total']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Pass Rate: {report['summary']['pass_rate']}%")
