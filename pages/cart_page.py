"""
购物车页面对象模块

提供购物车页面的 Page Object Model，封装购物车的所有交互操作。
"""

import logging
from typing import Optional, List, Dict
from playwright.sync_api import Page, Locator

logger = logging.getLogger(__name__)


class CartItem:
    """购物车商品项数据类"""

    def __init__(
        self,
        name: str,
        quantity: int,
        price: float,
        locator: Locator,
    ):
        """初始化购物车商品项

        Args:
            name: 商品名称
            quantity: 商品数量
            price: 单价
            locator: 商品项的 Playwright Locator
        """
        self.name = name
        self.quantity = quantity
        self.price = price
        self.locator = locator

    @property
    def subtotal(self) -> float:
        """计算小计"""
        return self.price * self.quantity

    def __repr__(self) -> str:
        return f"CartItem(name={self.name}, quantity={self.quantity}, price={self.price})"


class CartPage:
    """购物车页面对象

    封装购物车页面的所有交互操作，包括：
    - 页面导航
    - 获取购物车商品列表
    - 更新商品数量
    - 删除商品
    - 获取总价
    - 进入结账流程
    """

    # 购物车页面的常见 URL 路径
    CART_URL_PATHS = [
        "/cart",
        "/checkout/cart",
        "/shopping-cart",
    ]

    # 购物车选择器（通用选择器，适配 Shopify 等常见电商平台）
    SELECTORS = {
        "cart_items": ".cart-item, .cart__item, [data-cart-item]",
        "item_name": ".cart-item__name, .product-title, h3, h4",
        "item_quantity": "input[name*='quantity'], input[type='number']",
        "item_price": ".cart-item__price, .price, [data-price]",
        "remove_button": ".cart-item__remove, button[name='remove'], a[href*='remove']",
        "subtotal": ".cart-subtotal, [data-subtotal]",
        "total": ".cart-total, [data-total], .total-price",
        "checkout_button": "button[name='checkout'], a[href*='checkout'], .checkout-button",
        "empty_cart_message": ".cart-empty, .empty-cart, [data-empty-cart]",
        "quantity_increase": "button.qty-plus, button[aria-label*='Increase']",
        "quantity_decrease": "button.qty-minus, button[aria-label*='Decrease']",
    }

    def __init__(self, page: Page, base_url: str = "https://fiido.com"):
        """初始化购物车页面对象

        Args:
            page: Playwright Page 对象
            base_url: 网站基础 URL
        """
        self.page = page
        self.base_url = base_url.rstrip("/")
        logger.info("CartPage initialized")

    def navigate(self, wait_until: str = "domcontentloaded", timeout: int = 60000) -> None:
        """导航到购物车页面

        Args:
            wait_until: 等待状态 ('load', 'domcontentloaded', 'networkidle')
            timeout: 超时时间（毫秒）

        Raises:
            Exception: 页面导航失败
        """
        # 尝试常见的购物车 URL 路径
        for path in self.CART_URL_PATHS:
            cart_url = f"{self.base_url}{path}"
            try:
                logger.info(f"Navigating to cart page: {cart_url}")
                self.page.goto(cart_url, wait_until=wait_until, timeout=timeout)
                logger.debug("Cart page navigation completed")
                return
            except Exception as e:
                logger.warning(f"Failed to navigate to {cart_url}: {e}")
                continue

        raise Exception("Failed to navigate to cart page with any known URL pattern")

    def is_empty(self) -> bool:
        """检查购物车是否为空

        Returns:
            bool: True 如果购物车为空，False 如果有商品
        """
        # 方法 1: 检查空购物车提示消息
        empty_msg = self.page.locator(self.SELECTORS["empty_cart_message"]).first
        if empty_msg.is_visible():
            logger.info("Cart is empty (found empty message)")
            return True

        # 方法 2: 检查购物车商品数量
        items = self.page.locator(self.SELECTORS["cart_items"]).all()
        is_empty = len(items) == 0
        logger.info(f"Cart is {'empty' if is_empty else f'not empty ({len(items)} items)'}")
        return is_empty

    def get_cart_items(self) -> List[CartItem]:
        """获取购物车中所有商品

        Returns:
            List[CartItem]: 购物车商品列表
        """
        items: List[CartItem] = []
        item_locators = self.page.locator(self.SELECTORS["cart_items"]).all()

        for item_loc in item_locators:
            try:
                # 提取商品名称
                name_elem = item_loc.locator(self.SELECTORS["item_name"]).first
                name = name_elem.inner_text().strip() if name_elem.is_visible() else "Unknown"

                # 提取商品数量
                qty_elem = item_loc.locator(self.SELECTORS["item_quantity"]).first
                quantity = 1
                if qty_elem.is_visible():
                    qty_value = qty_elem.input_value()
                    quantity = int(qty_value) if qty_value else 1

                # 提取商品价格（解析文本中的数字）
                price_elem = item_loc.locator(self.SELECTORS["item_price"]).first
                price = 0.0
                if price_elem.is_visible():
                    price_text = price_elem.inner_text().strip()
                    # 简单解析价格（去除货币符号，提取数字）
                    import re
                    price_match = re.search(r"[\d,]+\.?\d*", price_text)
                    if price_match:
                        price = float(price_match.group().replace(",", ""))

                cart_item = CartItem(
                    name=name,
                    quantity=quantity,
                    price=price,
                    locator=item_loc,
                )
                items.append(cart_item)
                logger.debug(f"Found cart item: {cart_item}")

            except Exception as e:
                logger.warning(f"Failed to parse cart item: {e}")
                continue

        logger.info(f"Retrieved {len(items)} cart items")
        return items

    def get_item_count(self) -> int:
        """获取购物车商品总数

        Returns:
            int: 商品种类数量（不是总件数）
        """
        count = len(self.get_cart_items())
        logger.info(f"Cart item count: {count}")
        return count

    def update_quantity(self, item_index: int, new_quantity: int) -> None:
        """更新指定商品的数量

        Args:
            item_index: 商品索引（从 0 开始）
            new_quantity: 新的数量

        Raises:
            IndexError: 商品索引超出范围
        """
        items = self.get_cart_items()
        if item_index >= len(items):
            raise IndexError(f"Item index {item_index} out of range (total {len(items)} items)")

        target_item = items[item_index]
        qty_input = target_item.locator.locator(self.SELECTORS["item_quantity"]).first

        if qty_input.is_visible():
            logger.info(f"Updating quantity for '{target_item.name}' from {target_item.quantity} to {new_quantity}")
            qty_input.fill(str(new_quantity))
            # 触发 change 事件（某些网站需要）
            qty_input.press("Enter")
            self.page.wait_for_timeout(1000)  # 等待页面更新
        else:
            logger.warning(f"Quantity input not found for item {item_index}")

    def remove_item(self, item_index: int) -> None:
        """删除指定商品

        Args:
            item_index: 商品索引（从 0 开始）

        Raises:
            IndexError: 商品索引超出范围
        """
        items = self.get_cart_items()
        if item_index >= len(items):
            raise IndexError(f"Item index {item_index} out of range (total {len(items)} items)")

        target_item = items[item_index]
        remove_btn = target_item.locator.locator(self.SELECTORS["remove_button"]).first

        if remove_btn.is_visible():
            logger.info(f"Removing item '{target_item.name}' from cart")
            remove_btn.click()
            self.page.wait_for_timeout(1000)  # 等待页面更新
        else:
            logger.warning(f"Remove button not found for item {item_index}")

    def clear_cart(self) -> None:
        """清空购物车（删除所有商品）"""
        logger.info("Clearing cart...")
        while not self.is_empty():
            items = self.get_cart_items()
            if items:
                self.remove_item(0)  # 总是删除第一个商品
            else:
                break
        logger.info("Cart cleared")

    def get_subtotal(self) -> Optional[float]:
        """获取购物车小计（商品总价，不含运费等）

        Returns:
            Optional[float]: 小计金额，如果无法获取则返回 None
        """
        subtotal_elem = self.page.locator(self.SELECTORS["subtotal"]).first
        if subtotal_elem.is_visible():
            subtotal_text = subtotal_elem.inner_text().strip()
            import re
            match = re.search(r"[\d,]+\.?\d*", subtotal_text)
            if match:
                subtotal = float(match.group().replace(",", ""))
                logger.info(f"Cart subtotal: {subtotal}")
                return subtotal
        logger.warning("Subtotal not found")
        return None

    def get_total(self) -> Optional[float]:
        """获取购物车总计（包含运费、税等）

        Returns:
            Optional[float]: 总计金额，如果无法获取则返回 None
        """
        total_elem = self.page.locator(self.SELECTORS["total"]).first
        if total_elem.is_visible():
            total_text = total_elem.inner_text().strip()
            import re
            match = re.search(r"[\d,]+\.?\d*", total_text)
            if match:
                total = float(match.group().replace(",", ""))
                logger.info(f"Cart total: {total}")
                return total
        logger.warning("Total not found")
        return None

    def proceed_to_checkout(self) -> None:
        """点击结账按钮，进入结账流程

        Raises:
            Exception: 结账按钮不可见或点击失败
        """
        checkout_btn = self.page.locator(self.SELECTORS["checkout_button"]).first

        if not checkout_btn.is_visible():
            raise Exception("Checkout button not visible")

        logger.info("Clicking checkout button...")
        checkout_btn.click()
        # 等待页面跳转
        self.page.wait_for_load_state("domcontentloaded", timeout=30000)
        logger.info("Proceeded to checkout")

    def get_cart_summary(self) -> Dict:
        """获取购物车摘要信息

        Returns:
            Dict: 包含商品数量、小计、总计等信息的字典
        """
        items = self.get_cart_items()
        summary = {
            "item_count": len(items),
            "items": [
                {"name": item.name, "quantity": item.quantity, "price": item.price}
                for item in items
            ],
            "subtotal": self.get_subtotal(),
            "total": self.get_total(),
            "is_empty": self.is_empty(),
        }
        logger.info(f"Cart summary: {summary}")
        return summary
