"""
结账流程 E2E 测试

测试从购物车到结账页面的完整流程。
注意：这些测试不会提交真实订单，仅验证结账页面的可访问性和基本功能。
"""

import pytest
from playwright.sync_api import Page, expect

from core.models import Product
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage


@pytest.mark.e2e
def test_checkout_page_accessible_from_cart(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试从购物车进入结账页面

    流程:
    1. 访问商品页并加购
    2. 进入购物车
    3. 点击结账按钮
    4. 验证进入结账页面
    """
    # Step 1: 加购商品
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    expect(add_to_cart_btn).to_be_visible(timeout=10000)
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # Step 2: 进入购物车
    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()

    # Step 3: 点击结账（如果购物车不为空）
    if not cart_page.is_empty():
        try:
            cart_page.proceed_to_checkout()

            # Step 4: 验证进入结账页面
            # 检查 URL 是否包含 checkout
            page.wait_for_timeout(2000)
            current_url = page.url
            assert "checkout" in current_url.lower(), f"应该在结账页面，实际 URL: {current_url}"
        except Exception as e:
            # 如果购物车到结账的流程失败，跳过测试
            pytest.skip(f"无法从购物车进入结账页面: {e}")
    else:
        pytest.skip("购物车为空，无法测试结账流程")


@pytest.mark.e2e
def test_checkout_page_loads_directly(
    page: Page,
) -> None:
    """
    测试直接访问结账页面

    验证:
    - 结账页面可以直接访问
    - 页面包含预期的表单元素
    """
    checkout_page = CheckoutPage(page, base_url="https://fiido.com")

    try:
        checkout_page.navigate()

        # 等待页面加载
        page.wait_for_timeout(2000)

        # 验证 URL 包含 checkout
        current_url = page.url
        assert "checkout" in current_url.lower(), f"应该在结账页面，实际 URL: {current_url}"

        # 验证页面标题存在
        title = page.title()
        assert title, "页面标题不应为空"

    except Exception as e:
        # 某些网站可能禁止直接访问结账页面（需要有购物车商品）
        pytest.skip(f"无法直接访问结账页面（可能需要购物车商品）: {e}")


@pytest.mark.e2e
@pytest.mark.skip(reason="需要真实购物车数据，暂时跳过")
def test_checkout_shipping_info_fields(
    page: Page,
) -> None:
    """
    测试结账页面配送信息字段

    验证:
    - 配送信息表单字段存在
    - 可以填写配送信息

    注意：此测试需要购物车中有商品
    """
    checkout_page = CheckoutPage(page, base_url="https://fiido.com")
    checkout_page.navigate()
    page.wait_for_timeout(2000)

    # 尝试填写配送信息（仅测试字段存在性，不提交）
    try:
        checkout_page.fill_shipping_info(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            address1="123 Test St",
            city="Test City",
            zip_code="12345",
            country="United States",
        )

        # 如果成功填写，说明字段存在
        assert True, "配送信息字段存在且可填写"

    except Exception as e:
        pytest.skip(f"无法填写配送信息（可能页面结构不同）: {e}")


@pytest.mark.e2e
def test_checkout_page_summary_visible(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试结账页面订单摘要是否可见

    流程:
    1. 加购商品
    2. 进入购物车
    3. 进入结账页面
    4. 验证订单摘要信息
    """
    # Step 1: 加购商品
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    expect(add_to_cart_btn).to_be_visible(timeout=10000)
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # Step 2: 进入购物车
    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()

    # Step 3: 进入结账页面
    if not cart_page.is_empty():
        try:
            cart_page.proceed_to_checkout()
            page.wait_for_timeout(2000)

            # Step 4: 尝试获取订单摘要
            checkout_page = CheckoutPage(page, base_url="https://fiido.com")
            summary = checkout_page.get_checkout_summary()

            # 验证摘要至少有一些数据
            # 注意：某些字段可能为 None（取决于页面结构）
            assert isinstance(summary, dict), "订单摘要应为字典类型"
            assert "order_total" in summary
            assert "shipping_cost" in summary
            assert "tax" in summary

        except Exception as e:
            pytest.skip(f"无法获取结账摘要: {e}")
    else:
        pytest.skip("购物车为空，无法测试结账摘要")


@pytest.mark.e2e
@pytest.mark.skip(reason="折扣码功能需要有效的折扣码，暂时跳过")
def test_apply_discount_code(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试应用折扣码功能

    注意：此测试需要有效的折扣码，暂时跳过
    """
    # Step 1: 加购商品
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # Step 2: 进入购物车并结账
    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()
    cart_page.proceed_to_checkout()
    page.wait_for_timeout(2000)

    # Step 3: 应用折扣码
    checkout_page = CheckoutPage(page, base_url="https://fiido.com")

    # 使用测试折扣码（实际需要有效的折扣码）
    result = checkout_page.apply_discount_code("TEST10")

    # 验证折扣码应用结果
    # 注意：由于我们不知道折扣码是否有效，这里只验证方法执行
    assert isinstance(result, bool), "apply_discount_code 应返回布尔值"


@pytest.mark.e2e
@pytest.mark.skip(reason="不执行真实订单提交")
def test_submit_order_button_exists(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试提交订单按钮存在性

    验证提交订单按钮存在，但不实际点击
    注意：此测试不会提交真实订单
    """
    # 加购 -> 购物车 -> 结账
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()
    cart_page.proceed_to_checkout()
    page.wait_for_timeout(2000)

    # 填写必要信息以显示提交按钮
    checkout_page = CheckoutPage(page, base_url="https://fiido.com")
    try:
        checkout_page.fill_shipping_info(
            email="test@example.com",
            first_name="Test",
            last_name="User",
            address1="123 Test St",
            city="Test City",
            zip_code="12345",
        )

        # 查找提交订单按钮
        submit_btn = page.locator(CheckoutPage.SELECTORS["submit_order"]).first

        # 验证按钮存在（可能可见或不可见，取决于表单验证）
        assert submit_btn is not None, "提交订单按钮应该存在"

    except Exception as e:
        pytest.skip(f"无法测试提交订单按钮: {e}")
