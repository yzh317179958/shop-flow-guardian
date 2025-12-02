"""
Pytest 配置和 Fixtures

提供全局 fixtures 和配置，包括增量测试支持。
"""

import json
import pytest
from pathlib import Path
from typing import List, Dict


def pytest_addoption(parser):
    """添加自定义命令行选项"""
    parser.addoption(
        "--incremental",
        action="store_true",
        default=False,
        help="启用增量测试（仅测试变更的商品）"
    )
    parser.addoption(
        "--changed-products",
        action="store",
        default="data/product_changes.json",
        help="变更检测报告文件路径"
    )
    parser.addoption(
        "--priority",
        action="store",
        default=None,
        help="按优先级过滤测试（P0/P1/P2）"
    )


def pytest_configure(config):
    """配置 pytest"""
    # 注册自定义标记
    config.addinivalue_line(
        "markers",
        "incremental: 支持增量测试的测试用例"
    )


def pytest_collection_modifyitems(config, items):
    """
    根据增量测试配置修改测试集合

    如果启用增量测试，仅保留变更商品的测试
    """
    if not config.getoption("--incremental"):
        return

    # 加载变更报告
    changes_file = Path(config.getoption("--changed-products"))
    if not changes_file.exists():
        print(f"\n⚠️ 变更报告不存在: {changes_file}")
        print("请先运行: python scripts/detect_product_changes.py")
        return

    with open(changes_file) as f:
        changes = json.load(f)

    # 提取需要测试的商品 ID
    test_targets = changes.get('test_targets', [])

    if not test_targets:
        print("\n✅ 无商品变更，跳过所有测试")
        items.clear()
        return

    changed_product_ids = {target['id'] for target in test_targets}
    priority_filter = config.getoption("--priority")

    # 如果指定了优先级，进一步过滤
    if priority_filter:
        changed_product_ids = {
            target['id'] for target in test_targets
            if target.get('priority') == priority_filter
        }

    print(f"\n🎯 增量测试模式已启用")
    print(f"   变更商品数: {len(test_targets)}")
    if priority_filter:
        print(f"   优先级过滤: {priority_filter}")
        print(f"   测试目标数: {len(changed_product_ids)}")

    # 过滤测试项
    selected = []
    deselected = []

    for item in items:
        # 检查测试是否针对特定商品
        product_id = None

        # 方法1: 从 pytest 标记中获取商品 ID
        product_id_marker = item.get_closest_marker("product_id")
        if product_id_marker:
            product_id = product_id_marker.args[0] if product_id_marker.args else None

        # 方法2: 从测试参数中获取商品 ID
        if not product_id and hasattr(item, 'callspec'):
            params = item.callspec.params
            if 'product' in params:
                product_obj = params['product']
                if isinstance(product_obj, dict):
                    product_id = product_obj.get('id')
                elif hasattr(product_obj, 'id'):
                    product_id = product_obj.id
            elif 'product_id' in params:
                product_id = params['product_id']

        # 判断是否保留此测试
        if product_id and product_id in changed_product_ids:
            selected.append(item)
        elif not product_id:
            # 如果无法确定商品 ID，保留测试（如单元测试）
            # 但如果测试被标记为 incremental，则跳过
            if item.get_closest_marker("incremental"):
                deselected.append(item)
            else:
                selected.append(item)
        else:
            deselected.append(item)

    # 更新测试集合
    items[:] = selected

    if deselected:
        config.hook.pytest_deselected(items=deselected)

    print(f"   已选择测试: {len(selected)}")
    print(f"   已跳过测试: {len(deselected)}")


@pytest.fixture(scope="session")
def product_changes(request):
    """
    提供商品变更信息的 fixture

    Returns:
        商品变更报告字典
    """
    changes_file = Path(request.config.getoption("--changed-products"))

    if not changes_file.exists():
        return {
            'test_targets': [],
            'changes': {'added': [], 'modified': [], 'removed': []},
            'summary': {}
        }

    with open(changes_file) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def changed_product_ids(product_changes):
    """
    提供变更商品 ID 列表的 fixture

    Returns:
        变更商品 ID 集合
    """
    return {target['id'] for target in product_changes.get('test_targets', [])}


@pytest.fixture
def skip_if_unchanged(request, changed_product_ids):
    """
    装饰器 fixture: 如果商品未变更则跳过测试

    使用方法:
        @pytest.mark.product_id("fiido-d11")
        def test_product(skip_if_unchanged):
            ...
    """
    product_id_marker = request.node.get_closest_marker("product_id")

    if product_id_marker and request.config.getoption("--incremental"):
        product_id = product_id_marker.args[0] if product_id_marker.args else None

        if product_id and product_id not in changed_product_ids:
            pytest.skip(f"商品 {product_id} 未变更，跳过测试")
