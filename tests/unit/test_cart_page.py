"""
CartPage 单元测试

测试购物车页面对象的各种方法。
"""

import pytest
from unittest.mock import Mock, MagicMock
from playwright.sync_api import Page, Locator

from pages.cart_page import CartPage, CartItem


class TestCartItem:
    """测试 CartItem 数据类"""

    def test_cart_item_creation(self):
        """测试 CartItem 创建"""
        locator = Mock(spec=Locator)
        item = CartItem(
            name="Test Product",
            quantity=2,
            price=99.99,
            locator=locator,
        )

        assert item.name == "Test Product"
        assert item.quantity == 2
        assert item.price == 99.99
        assert item.locator == locator

    def test_cart_item_subtotal(self):
        """测试小计计算"""
        locator = Mock(spec=Locator)
        item = CartItem(
            name="Test Product",
            quantity=3,
            price=50.00,
            locator=locator,
        )

        assert item.subtotal == 150.00

    def test_cart_item_repr(self):
        """测试字符串表示"""
        locator = Mock(spec=Locator)
        item = CartItem(
            name="Test Product",
            quantity=1,
            price=99.99,
            locator=locator,
        )

        repr_str = repr(item)
        assert "CartItem" in repr_str
        assert "Test Product" in repr_str
        assert "99.99" in repr_str


class TestCartPage:
    """测试 CartPage 类"""

    @pytest.fixture
    def mock_page(self):
        """创建 mock Page 对象"""
        page = Mock(spec=Page)
        page.locator = Mock(return_value=Mock(spec=Locator))
        return page

    @pytest.fixture
    def cart_page(self, mock_page):
        """创建 CartPage 实例"""
        return CartPage(mock_page, base_url="https://test.com")

    def test_cart_page_initialization(self, cart_page, mock_page):
        """测试 CartPage 初始化"""
        assert cart_page.page == mock_page
        assert cart_page.base_url == "https://test.com"

    def test_base_url_strips_trailing_slash(self, mock_page):
        """测试 base_url 自动去除尾部斜杠"""
        cart_page = CartPage(mock_page, base_url="https://test.com/")
        assert cart_page.base_url == "https://test.com"

    def test_navigate_success(self, cart_page, mock_page):
        """测试成功导航到购物车页面"""
        mock_page.goto = Mock()

        cart_page.navigate()

        # 验证至少调用了一次 goto
        assert mock_page.goto.called
        # 验证调用的 URL 包含购物车路径
        call_args = mock_page.goto.call_args[0][0]
        assert any(path in call_args for path in CartPage.CART_URL_PATHS)

    def test_cart_url_paths_constant(self):
        """测试购物车 URL 路径常量"""
        assert "/cart" in CartPage.CART_URL_PATHS
        assert isinstance(CartPage.CART_URL_PATHS, list)
        assert len(CartPage.CART_URL_PATHS) > 0

    def test_selectors_constant(self):
        """测试选择器常量定义"""
        assert "cart_items" in CartPage.SELECTORS
        assert "checkout_button" in CartPage.SELECTORS
        assert "total" in CartPage.SELECTORS
        assert isinstance(CartPage.SELECTORS, dict)

    def test_is_empty_with_empty_message(self, cart_page, mock_page):
        """测试空购物车检测（有空消息提示）"""
        mock_locator = Mock(spec=Locator)
        mock_locator.first = Mock(spec=Locator)
        mock_locator.first.is_visible = Mock(return_value=True)
        mock_page.locator = Mock(return_value=mock_locator)

        assert cart_page.is_empty() is True

    def test_is_empty_with_no_items(self, cart_page, mock_page):
        """测试空购物车检测（无商品）"""
        # 空消息不可见
        mock_empty_msg = Mock(spec=Locator)
        mock_empty_msg.first = Mock(spec=Locator)
        mock_empty_msg.first.is_visible = Mock(return_value=False)

        # 无购物车商品
        mock_items = Mock(spec=Locator)
        mock_items.all = Mock(return_value=[])

        def locator_side_effect(selector):
            if "empty" in selector:
                return mock_empty_msg
            return mock_items

        mock_page.locator = Mock(side_effect=locator_side_effect)

        assert cart_page.is_empty() is True

    def test_get_item_count(self, cart_page):
        """测试获取商品数量"""
        # Mock get_cart_items 返回
        cart_page.get_cart_items = Mock(return_value=[
            Mock(spec=CartItem),
            Mock(spec=CartItem),
        ])

        assert cart_page.get_item_count() == 2

    def test_get_cart_summary(self, cart_page):
        """测试获取购物车摘要"""
        # Mock 方法返回
        mock_item1 = Mock(spec=CartItem)
        mock_item1.name = "Product 1"
        mock_item1.quantity = 2
        mock_item1.price = 50.0

        cart_page.get_cart_items = Mock(return_value=[mock_item1])
        cart_page.get_subtotal = Mock(return_value=100.0)
        cart_page.get_total = Mock(return_value=110.0)
        cart_page.is_empty = Mock(return_value=False)

        summary = cart_page.get_cart_summary()

        assert summary["item_count"] == 1
        assert summary["subtotal"] == 100.0
        assert summary["total"] == 110.0
        assert summary["is_empty"] is False
        assert len(summary["items"]) == 1
        assert summary["items"][0]["name"] == "Product 1"
