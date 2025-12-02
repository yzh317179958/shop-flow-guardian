"""
CheckoutPage 单元测试

测试结账页面对象的各种方法。
"""

import pytest
from unittest.mock import Mock, MagicMock
from playwright.sync_api import Page, Locator

from pages.checkout_page import CheckoutPage


class TestCheckoutPage:
    """测试 CheckoutPage 类"""

    @pytest.fixture
    def mock_page(self):
        """创建 mock Page 对象"""
        page = Mock(spec=Page)
        page.locator = Mock(return_value=Mock(spec=Locator))
        page.wait_for_timeout = Mock()
        page.wait_for_load_state = Mock()
        return page

    @pytest.fixture
    def checkout_page(self, mock_page):
        """创建 CheckoutPage 实例"""
        return CheckoutPage(mock_page, base_url="https://test.com")

    def test_checkout_page_initialization(self, checkout_page, mock_page):
        """测试 CheckoutPage 初始化"""
        assert checkout_page.page == mock_page
        assert checkout_page.base_url == "https://test.com"

    def test_base_url_strips_trailing_slash(self, mock_page):
        """测试 base_url 自动去除尾部斜杠"""
        checkout_page = CheckoutPage(mock_page, base_url="https://test.com/")
        assert checkout_page.base_url == "https://test.com"

    def test_checkout_url_paths_constant(self):
        """测试结账 URL 路径常量"""
        assert "/checkout" in CheckoutPage.CHECKOUT_URL_PATHS
        assert isinstance(CheckoutPage.CHECKOUT_URL_PATHS, list)
        assert len(CheckoutPage.CHECKOUT_URL_PATHS) > 0

    def test_selectors_constant(self):
        """测试选择器常量定义"""
        # 验证关键选择器存在
        assert "email" in CheckoutPage.SELECTORS
        assert "first_name" in CheckoutPage.SELECTORS
        assert "submit_order" in CheckoutPage.SELECTORS
        assert "checkout_button" in CheckoutPage.SELECTORS or "continue_to_shipping" in CheckoutPage.SELECTORS
        assert "order_total" in CheckoutPage.SELECTORS
        assert isinstance(CheckoutPage.SELECTORS, dict)

    def test_navigate_success(self, checkout_page, mock_page):
        """测试成功导航到结账页面"""
        mock_page.goto = Mock()

        checkout_page.navigate()

        # 验证至少调用了一次 goto
        assert mock_page.goto.called
        # 验证调用的 URL 包含结账路径
        call_args = mock_page.goto.call_args[0][0]
        assert any(path in call_args for path in CheckoutPage.CHECKOUT_URL_PATHS)

    def test_navigate_with_custom_wait(self, checkout_page, mock_page):
        """测试使用自定义等待状态导航"""
        mock_page.goto = Mock()

        checkout_page.navigate(wait_until="networkidle", timeout=30000)

        # 验证 goto 被调用时使用了正确的参数
        call_kwargs = mock_page.goto.call_args[1]
        assert call_kwargs["wait_until"] == "networkidle"
        assert call_kwargs["timeout"] == 30000

    def test_fill_shipping_info_required_fields(self, checkout_page, mock_page):
        """测试填写必填配送信息"""
        # 创建 mock locator
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.fill = Mock()
        mock_locator.first.select_option = Mock()

        mock_page.locator = Mock(return_value=mock_locator)

        # 调用方法
        checkout_page.fill_shipping_info(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            address1="123 Main St",
            city="New York",
            zip_code="10001",
        )

        # 验证所有必填字段都被填写
        assert mock_locator.first.fill.called
        # 至少应该调用 6 次 fill（email, first_name, last_name, address1, city, zip）
        assert mock_locator.first.fill.call_count >= 6

    def test_fill_shipping_info_with_optional_fields(self, checkout_page, mock_page):
        """测试填写包含可选字段的配送信息"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.fill = Mock()
        mock_locator.first.select_option = Mock()

        mock_page.locator = Mock(return_value=mock_locator)

        # 调用方法（包含可选字段）
        checkout_page.fill_shipping_info(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            address1="123 Main St",
            city="New York",
            zip_code="10001",
            country="United States",
            province="New York",
            phone="1234567890",
            address2="Apt 4B",
        )

        # 验证 select_option 被调用（用于 country 和 province）
        assert mock_locator.first.select_option.called
        # 验证 fill 调用次数增加（包含 phone 和 address2）
        assert mock_locator.first.fill.call_count >= 8

    def test_select_shipping_method(self, checkout_page, mock_page):
        """测试选择配送方式"""
        # 创建 mock 配送方式列表
        mock_method1 = Mock(spec=Locator)
        mock_method1.is_visible = Mock(return_value=True)
        mock_method1.click = Mock()

        mock_method2 = Mock(spec=Locator)
        mock_method2.is_visible = Mock(return_value=True)
        mock_method2.click = Mock()

        mock_locator = Mock(spec=Locator)
        mock_locator.all = Mock(return_value=[mock_method1, mock_method2])

        mock_page.locator = Mock(return_value=mock_locator)

        # 选择第一个方式
        checkout_page.select_shipping_method(0)

        # 验证第一个方法被点击
        assert mock_method1.click.called
        assert not mock_method2.click.called

    def test_select_shipping_method_out_of_range(self, checkout_page, mock_page):
        """测试选择超出范围的配送方式"""
        mock_locator = Mock(spec=Locator)
        mock_locator.all = Mock(return_value=[])

        mock_page.locator = Mock(return_value=mock_locator)

        # 选择不存在的方法（不应抛出异常）
        checkout_page.select_shipping_method(5)

        # 验证没有抛出异常

    def test_continue_to_shipping(self, checkout_page, mock_page):
        """测试点击继续到配送按钮"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.click = Mock()

        mock_page.locator = Mock(return_value=mock_locator)

        checkout_page.continue_to_shipping()

        # 验证按钮被点击
        assert mock_locator.first.click.called

    def test_continue_to_payment(self, checkout_page, mock_page):
        """测试点击继续到支付按钮"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.click = Mock()

        mock_page.locator = Mock(return_value=mock_locator)

        checkout_page.continue_to_payment()

        # 验证按钮被点击
        assert mock_locator.first.click.called

    def test_fill_payment_info(self, checkout_page, mock_page):
        """测试填写支付信息"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.fill = Mock()

        mock_page.locator = Mock(return_value=mock_locator)

        checkout_page.fill_payment_info(
            card_number="4111111111111111",
            card_name="John Doe",
            expiry="12/25",
            cvv="123",
        )

        # 验证所有支付字段都被填写
        assert mock_locator.first.fill.call_count >= 4

    def test_apply_discount_code_success(self, checkout_page, mock_page):
        """测试成功应用折扣码"""
        mock_input = Mock(spec=Locator)
        mock_input.is_visible = Mock(return_value=True)
        mock_input.fill = Mock()

        mock_button = Mock(spec=Locator)
        mock_button.is_visible = Mock(return_value=True)
        mock_button.click = Mock()

        mock_locator = Mock(spec=Locator)
        mock_locator.first = mock_input

        def locator_side_effect(selector):
            if "discount_code" in selector or "discount" in selector:
                result = Mock(spec=Locator)
                result.first = mock_input
                return result
            elif "apply" in selector:
                result = Mock(spec=Locator)
                result.first = mock_button
                return result
            return mock_locator

        mock_page.locator = Mock(side_effect=locator_side_effect)

        result = checkout_page.apply_discount_code("SAVE10")

        # 验证折扣码被填写并点击应用
        assert mock_input.fill.called
        assert mock_button.click.called
        assert result is True

    def test_apply_discount_code_field_not_visible(self, checkout_page, mock_page):
        """测试折扣码字段不可见"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=False)

        mock_page.locator = Mock(return_value=mock_locator)

        result = checkout_page.apply_discount_code("SAVE10")

        # 验证返回 False
        assert result is False

    def test_submit_order(self, checkout_page, mock_page):
        """测试提交订单"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.click = Mock()

        mock_page.locator = Mock(return_value=mock_locator)

        checkout_page.submit_order()

        # 验证提交按钮被点击
        assert mock_locator.first.click.called

    def test_get_order_total(self, checkout_page, mock_page):
        """测试获取订单总计"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.inner_text = Mock(return_value="$123.45")

        mock_page.locator = Mock(return_value=mock_locator)

        total = checkout_page.get_order_total()

        # 验证解析出正确的价格
        assert total == 123.45

    def test_get_order_total_with_comma(self, checkout_page, mock_page):
        """测试获取带逗号的订单总计"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.inner_text = Mock(return_value="$1,234.56")

        mock_page.locator = Mock(return_value=mock_locator)

        total = checkout_page.get_order_total()

        # 验证正确处理逗号
        assert total == 1234.56

    def test_get_shipping_cost(self, checkout_page, mock_page):
        """测试获取运费"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.inner_text = Mock(return_value="$10.00")

        mock_page.locator = Mock(return_value=mock_locator)

        shipping = checkout_page.get_shipping_cost()

        assert shipping == 10.00

    def test_get_tax(self, checkout_page, mock_page):
        """测试获取税费"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.inner_text = Mock(return_value="$8.99")

        mock_page.locator = Mock(return_value=mock_locator)

        tax = checkout_page.get_tax()

        assert tax == 8.99

    def test_get_discount(self, checkout_page, mock_page):
        """测试获取折扣金额"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.inner_text = Mock(return_value="-$15.00")

        mock_page.locator = Mock(return_value=mock_locator)

        discount = checkout_page.get_discount()

        # 验证解析出折扣金额（负号会被忽略）
        assert discount == 15.00

    def test_get_price_returns_none_when_not_visible(self, checkout_page, mock_page):
        """测试价格元素不可见时返回 None"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=False)

        mock_page.locator = Mock(return_value=mock_locator)

        total = checkout_page.get_order_total()

        assert total is None

    def test_get_order_number(self, checkout_page, mock_page):
        """测试获取订单号"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_locator.first.inner_text = Mock(return_value="Order #12345")

        mock_page.locator = Mock(return_value=mock_locator)

        order_number = checkout_page.get_order_number()

        assert order_number == "Order #12345"

    def test_get_order_number_returns_none_when_not_visible(self, checkout_page, mock_page):
        """测试订单号元素不可见时返回 None"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=False)

        mock_page.locator = Mock(return_value=mock_locator)

        order_number = checkout_page.get_order_number()

        assert order_number is None

    def test_is_order_confirmed_true(self, checkout_page, mock_page):
        """测试订单已确认"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)

        mock_page.locator = Mock(return_value=mock_locator)

        is_confirmed = checkout_page.is_order_confirmed()

        assert is_confirmed is True

    def test_is_order_confirmed_false(self, checkout_page, mock_page):
        """测试订单未确认"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=False)

        mock_page.locator = Mock(return_value=mock_locator)

        is_confirmed = checkout_page.is_order_confirmed()

        assert is_confirmed is False

    def test_get_checkout_summary(self, checkout_page, mock_page):
        """测试获取结账摘要"""
        # Mock 所有价格方法
        checkout_page.get_order_total = Mock(return_value=123.45)
        checkout_page.get_shipping_cost = Mock(return_value=10.00)
        checkout_page.get_tax = Mock(return_value=8.99)
        checkout_page.get_discount = Mock(return_value=15.00)

        summary = checkout_page.get_checkout_summary()

        # 验证摘要包含所有字段
        assert summary["order_total"] == 123.45
        assert summary["shipping_cost"] == 10.00
        assert summary["tax"] == 8.99
        assert summary["discount"] == 15.00
        assert isinstance(summary, dict)
