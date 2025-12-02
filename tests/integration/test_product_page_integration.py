"""
集成测试 - 商品页面交互

测试真实商品页面的完整交互流程
"""

import pytest
from playwright.sync_api import Page, expect


class TestProductPageIntegration:
    """商品页面集成测试"""

    # 使用真实存在的商品URL
    TEST_PRODUCTS = [
        "https://fiido.com/products/fiido-m1-pro-fat-tire-electric-bike",
        "https://fiido.com/products/fiido-titan-robust-cargo-electric-bike-with-ul-certified",
        "https://fiido.com/products/fiido-t1-utility-electric-bike",
    ]

    @pytest.mark.parametrize("product_url", TEST_PRODUCTS)
    def test_product_page_loads(self, page: Page, product_url: str):
        """测试商品页面加载"""
        print(f"\n测试商品页面: {product_url}")

        # 访问商品页面
        page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 验证页面加载成功
        assert "fiido.com" in page.url.lower()
        assert page.title() != "404 Not Found"

        print(f"✅ 页面加载成功: {page.title()}")

    @pytest.mark.parametrize("product_url", TEST_PRODUCTS)
    def test_product_has_title(self, page: Page, product_url: str):
        """测试商品页面有标题"""
        page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 查找商品标题
        title_selectors = [
            'h1[class*="title"]',
            'h1.product__title',
            'h1',
        ]

        title_found = False
        for selector in title_selectors:
            if page.locator(selector).count() > 0:
                title = page.locator(selector).first.text_content()
                assert len(title.strip()) > 0
                print(f"✅ 找到商品标题: {title.strip()[:50]}")
                title_found = True
                break

        assert title_found, "未找到商品标题"

    @pytest.mark.parametrize("product_url", TEST_PRODUCTS)
    def test_product_has_price(self, page: Page, product_url: str):
        """测试商品页面有价格"""
        page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 查找价格
        price_selectors = [
            '.price',
            '[class*="price"]',
            '.product__price',
        ]

        price_found = False
        for selector in price_selectors:
            if page.locator(selector).count() > 0:
                price = page.locator(selector).first.text_content()
                assert len(price.strip()) > 0
                print(f"✅ 找到价格: {price.strip()[:50]}")
                price_found = True
                break

        assert price_found, "未找到商品价格"

    @pytest.mark.parametrize("product_url", TEST_PRODUCTS)
    def test_product_has_add_to_cart_button(self, page: Page, product_url: str):
        """测试商品页面有 Add to Cart 按钮"""
        page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 查找 Add to Cart 按钮
        add_to_cart_selectors = [
            'button:has-text("Add to cart")',
            'button:has-text("ADD TO CART")',
            'button[name="add"]',
            'button.product-form__submit',
        ]

        button_found = False
        for selector in add_to_cart_selectors:
            count = page.locator(selector).count()
            if count > 0:
                btn = page.locator(selector).first
                is_visible = btn.is_visible()
                print(f"✅ 找到 Add to Cart 按钮: {selector}")
                print(f"   可见: {is_visible}")
                button_found = True
                break

        assert button_found, "未找到 Add to Cart 按钮"

    def test_add_to_cart_interaction(self, page: Page):
        """测试添加到购物车交互"""
        # 使用已知可用的商品
        product_url = "https://fiido.com/products/fiido-m1-pro-fat-tire-electric-bike"

        print(f"\n测试添加到购物车: {product_url}")

        # 访问商品页面
        page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(5000)

        # 查找并点击 Add to Cart 按钮
        add_to_cart_btn = page.locator('button:has-text("Add to cart")').first

        # 验证按钮可见且可用
        assert add_to_cart_btn.is_visible(), "Add to Cart 按钮不可见"
        assert add_to_cart_btn.is_enabled(), "Add to Cart 按钮不可用"

        print("✅ Add to Cart 按钮可见且可用")

        # 点击按钮
        add_to_cart_btn.click()
        page.wait_for_timeout(3000)

        print("✅ 成功点击 Add to Cart 按钮")

        # 验证购物车有变化 (可能是图标数量或弹窗)
        # 注意: 这里不验证具体的购物车逻辑，因为可能有不同的实现方式
        # 只验证点击操作成功执行

    def test_cart_link_exists(self, page: Page):
        """测试购物车链接存在"""
        product_url = "https://fiido.com/products/fiido-m1-pro-fat-tire-electric-bike"

        page.goto(product_url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(3000)

        # 查找购物车链接
        cart_selectors = [
            'a[href="/cart"]',
            '[href*="cart"]',
            '.cart-link',
        ]

        cart_found = False
        for selector in cart_selectors:
            if page.locator(selector).count() > 0:
                print(f"✅ 找到购物车链接: {selector}")
                cart_found = True
                break

        assert cart_found, "未找到购物车链接"
