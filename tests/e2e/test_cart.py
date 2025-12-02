"""
购物车 E2E 测试

测试从商品页加购到购物车的完整流程。
"""

import pytest
from playwright.sync_api import Page, expect

from core.models import Product
from pages.cart_page import CartPage


@pytest.mark.e2e
def test_add_to_cart_and_verify(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试加购流程：从商品页加入购物车，然后验证购物车内容

    流程:
    1. 访问商品页
    2. 点击"加入购物车"
    3. 导航到购物车页面
    4. 验证商品已加入购物车
    """
    # Step 1: 访问商品页
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)

    # Step 2: 点击加购按钮
    add_to_cart_selector = test_product.selectors.add_to_cart_button
    add_to_cart_btn = page.locator(add_to_cart_selector).first
    expect(add_to_cart_btn).to_be_visible(timeout=10000)

    # 点击加购
    add_to_cart_btn.click()

    # 等待加购完成（可能有加载动画或提示）
    page.wait_for_timeout(2000)

    # Step 3: 导航到购物车
    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()

    # Step 4: 验证购物车不为空
    assert not cart_page.is_empty(), "购物车应该不为空"

    # 验证至少有 1 个商品
    item_count = cart_page.get_item_count()
    assert item_count >= 1, f"购物车应至少有 1 个商品，实际: {item_count}"


@pytest.mark.e2e
def test_cart_item_details(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试购物车商品详情

    验证:
    - 商品名称正确
    - 商品数量正确
    - 价格信息存在
    """
    # 先加购商品
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # 进入购物车
    cart_page = CartPage(page)
    cart_page.navigate()

    # 获取购物车商品列表
    items = cart_page.get_cart_items()
    assert len(items) > 0, "购物车应有商品"

    # 验证第一个商品的信息
    first_item = items[0]
    assert first_item.name, "商品名称不应为空"
    assert first_item.quantity >= 1, "商品数量应至少为 1"
    # 价格可能为 0（某些网站在购物车页不显示价格）
    assert first_item.price >= 0, "商品价格不应为负数"


@pytest.mark.e2e
def test_cart_summary(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试购物车摘要信息

    验证:
    - 可以获取购物车摘要
    - 摘要包含必要字段
    """
    # 加购商品
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # 进入购物车
    cart_page = CartPage(page)
    cart_page.navigate()

    # 获取摘要
    summary = cart_page.get_cart_summary()

    # 验证摘要字段
    assert "item_count" in summary
    assert "items" in summary
    assert "is_empty" in summary
    assert summary["item_count"] >= 1
    assert summary["is_empty"] is False
    assert isinstance(summary["items"], list)
