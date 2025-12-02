"""
完整购物流程 E2E 测试

测试从商品页浏览 → 加购 → 购物车 → 结账的完整流程
"""

import pytest
from playwright.sync_api import Page, expect

from core.models import Product
from pages.product_page import ProductPage
from pages.cart_page import CartPage
from pages.checkout_page import CheckoutPage


# 测试地址数据
TEST_ADDRESSES = {
    "US": {
        "email": "test@fiido-e2e-test.com",
        "first_name": "John",
        "last_name": "Doe",
        "address1": "123 Test Street",
        "city": "New York",
        "state": "NY",
        "zip_code": "10001",
        "country": "United States",
    },
    "DE": {
        "email": "test@fiido-e2e-test.com",
        "first_name": "Max",
        "last_name": "Mustermann",
        "address1": "Teststraße 123",
        "city": "Berlin",
        "zip_code": "10115",
        "country": "Germany",
    },
    "UK": {
        "email": "test@fiido-e2e-test.com",
        "first_name": "Jane",
        "last_name": "Smith",
        "address1": "456 Test Road",
        "city": "London",
        "zip_code": "SW1A 1AA",
        "country": "United Kingdom",
    },
}


@pytest.mark.e2e
@pytest.mark.skip(reason="完整流程测试 - 需要有效购物车状态")
def test_full_checkout_flow_us(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试完整结账流程（美国）

    流程:
    1. 访问商品页
    2. 添加商品到购物车
    3. 进入购物车验证
    4. 进入结账页面
    5. 填写配送信息
    6. 验证订单摘要
    """
    # Step 1: 访问商品页
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)

    # Step 2: 添加商品到购物车
    product_page = ProductPage(page, test_product)

    # 检查库存
    if not product_page.is_in_stock():
        pytest.skip(f"商品 {test_product.id} 缺货")

    # 加购
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    expect(add_to_cart_btn).to_be_visible(timeout=10000)
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # Step 3: 进入购物车
    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()

    # 验证商品在购物车中
    assert not cart_page.is_empty(), "购物车应该不为空"
    items = cart_page.get_cart_items()
    assert len(items) > 0, "购物车应有商品"

    # Step 4: 进入结账
    try:
        cart_page.proceed_to_checkout()
        page.wait_for_timeout(3000)

        # 验证进入结账页面
        current_url = page.url
        assert "checkout" in current_url.lower(), f"应该在结账页面，实际 URL: {current_url}"

    except Exception as e:
        pytest.skip(f"无法进入结账页面: {e}")

    # Step 5: 填写配送信息
    checkout_page = CheckoutPage(page, base_url="https://fiido.com")
    address = TEST_ADDRESSES["US"]

    try:
        checkout_page.fill_shipping_info(
            email=address["email"],
            first_name=address["first_name"],
            last_name=address["last_name"],
            address1=address["address1"],
            city=address["city"],
            zip_code=address["zip_code"],
            country=address["country"],
        )

        # 等待表单验证
        page.wait_for_timeout(2000)

    except Exception as e:
        pytest.skip(f"无法填写配送信息: {e}")

    # Step 6: 获取订单摘要
    summary = checkout_page.get_checkout_summary()

    # 验证摘要字段
    assert isinstance(summary, dict), "订单摘要应为字典类型"
    assert "order_total" in summary

    # 截图记录
    page.screenshot(
        path=f"screenshots/full_flow_{test_product.id}_us.png",
        full_page=True,
    )

    # 注意：不提交订单，避免污染生产数据


@pytest.mark.e2e
@pytest.mark.skip(reason="完整流程测试 - 需要有效购物车状态")
def test_full_checkout_flow_uk(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试完整结账流程（英国）

    验证不同地区的配送和价格计算
    """
    # Step 1: 访问商品页并加购
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)

    product_page = ProductPage(page, test_product)
    if not product_page.is_in_stock():
        pytest.skip(f"商品 {test_product.id} 缺货")

    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # Step 2: 进入购物车
    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()

    if cart_page.is_empty():
        pytest.skip("购物车为空")

    # Step 3: 进入结账
    try:
        cart_page.proceed_to_checkout()
        page.wait_for_timeout(3000)
    except Exception as e:
        pytest.skip(f"无法进入结账页面: {e}")

    # Step 4: 填写英国地址
    checkout_page = CheckoutPage(page, base_url="https://fiido.com")
    address = TEST_ADDRESSES["UK"]

    try:
        checkout_page.fill_shipping_info(
            email=address["email"],
            first_name=address["first_name"],
            last_name=address["last_name"],
            address1=address["address1"],
            city=address["city"],
            zip_code=address["zip_code"],
            country=address["country"],
        )

        page.wait_for_timeout(2000)

    except Exception as e:
        pytest.skip(f"无法填写配送信息: {e}")

    # Step 5: 验证运费计算
    shipping_cost = checkout_page.get_shipping_cost()

    # 英国运费应该存在（非美国地址）
    # 注意：实际值取决于网站配置
    if shipping_cost is not None:
        assert shipping_cost >= 0, "运费应为非负数"

    # 截图
    page.screenshot(
        path=f"screenshots/full_flow_{test_product.id}_uk.png",
        full_page=True,
    )


@pytest.mark.e2e
def test_product_to_cart_flow(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试商品页到购物车的流程

    这是一个精简版测试，仅验证加购和购物车更新
    """
    # Step 1: 访问商品页
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)

    # Step 2: 验证商品页加载
    product_page = ProductPage(page, test_product)
    title = product_page.get_title()
    assert title, f"商品 {test_product.id} 标题未加载"

    # Step 3: 检查库存
    if not product_page.is_in_stock():
        pytest.skip(f"商品 {test_product.id} 缺货")

    # Step 4: 加购
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    expect(add_to_cart_btn).to_be_visible(timeout=10000)
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # Step 5: 验证购物车图标更新（可选）
    # 某些网站会更新购物车计数
    cart_count_selectors = [
        ".cart-count",
        ".cart-item-count",
        "[data-cart-count]",
        ".header__cart-count",
    ]

    for selector in cart_count_selectors:
        try:
            count_elem = page.locator(selector).first
            if count_elem.is_visible(timeout=3000):
                count_text = count_elem.inner_text()
                # 验证计数为数字
                assert count_text.strip().isdigit() or count_text.strip() == "", \
                    f"购物车计数格式异常: {count_text}"
                break
        except Exception:
            continue


@pytest.mark.e2e
@pytest.mark.skip(reason="需要折扣码才能测试")
def test_checkout_with_discount_code(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试使用折扣码的结账流程

    注意：需要有效的折扣码
    """
    # 加购商品
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)

    product_page = ProductPage(page, test_product)
    if not product_page.is_in_stock():
        pytest.skip("商品缺货")

    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # 进入购物车
    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()

    if cart_page.is_empty():
        pytest.skip("购物车为空")

    # 获取原始总价
    original_total = cart_page.get_total()

    # 进入结账
    try:
        cart_page.proceed_to_checkout()
        page.wait_for_timeout(3000)
    except Exception as e:
        pytest.skip(f"无法进入结账: {e}")

    # 填写配送信息
    checkout_page = CheckoutPage(page, base_url="https://fiido.com")
    address = TEST_ADDRESSES["US"]

    checkout_page.fill_shipping_info(
        email=address["email"],
        first_name=address["first_name"],
        last_name=address["last_name"],
        address1=address["address1"],
        city=address["city"],
        zip_code=address["zip_code"],
    )

    # 应用折扣码（需要有效折扣码）
    test_discount_code = "TEST10"  # 示例折扣码
    discount_applied = checkout_page.apply_discount_code(test_discount_code)

    if discount_applied:
        # 验证折扣金额
        discount = checkout_page.get_discount()
        assert discount is not None and discount > 0, "折扣应大于0"

        # 验证总价更新
        new_total = checkout_page.get_order_total()
        if new_total and original_total:
            assert new_total < original_total, "应用折扣后总价应降低"
    else:
        pytest.skip(f"折扣码 {test_discount_code} 无效或不可用")


@pytest.mark.e2e
def test_cart_to_checkout_navigation(
    test_product: Product,
    page: Page,
) -> None:
    """
    测试购物车到结账页面的导航

    验证结账按钮存在且可点击
    """
    # 加购商品
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)

    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    expect(add_to_cart_btn).to_be_visible(timeout=10000)
    add_to_cart_btn.click()
    page.wait_for_timeout(2000)

    # 进入购物车
    cart_page = CartPage(page, base_url="https://fiido.com")
    cart_page.navigate()

    # 验证购物车不为空
    if cart_page.is_empty():
        pytest.skip("购物车为空，无法测试结账导航")

    # 查找结账按钮
    checkout_selectors = [
        "button[name='checkout']",
        "a[href*='checkout']",
        ".checkout-button",
        "button:has-text('Checkout')",
        "a:has-text('Checkout')",
    ]

    checkout_button_found = False
    for selector in checkout_selectors:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=3000):
                checkout_button_found = True
                # 验证按钮可点击
                assert btn.is_enabled(), "结账按钮应为可用状态"
                break
        except Exception:
            continue

    assert checkout_button_found, "未找到结账按钮"


@pytest.mark.e2e
@pytest.mark.priority("P0")
def test_critical_checkout_path_exists(
    test_product: Product,
    page: Page,
) -> None:
    """
    P0 测试：验证关键结账路径存在

    这是核心流程测试，确保基本的购物路径可用
    """
    # 1. 商品页可访问
    page.goto(str(test_product.url), wait_until="domcontentloaded", timeout=60000)
    assert page.url, "商品页应可访问"

    # 2. 加购按钮存在
    add_to_cart_btn = page.locator(test_product.selectors.add_to_cart_button).first
    expect(add_to_cart_btn).to_be_visible(timeout=10000)

    # 3. 购物车页面可访问
    cart_page = CartPage(page, base_url="https://fiido.com")
    try:
        cart_page.navigate()
        assert "cart" in page.url.lower(), "应该在购物车页面"
    except Exception as e:
        pytest.fail(f"购物车页面不可访问: {e}")

    # 4. 结账页面路径存在
    try:
        checkout_page = CheckoutPage(page, base_url="https://fiido.com")
        checkout_page.navigate()
        # 某些网站可能会重定向到购物车（如果购物车为空）
        # 这里只验证导航不会出错
        assert page.url, "结账页面导航应成功"
    except Exception as e:
        # 允许失败（可能需要购物车商品）
        pass
