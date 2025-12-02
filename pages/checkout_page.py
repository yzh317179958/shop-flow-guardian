"""
结账页面对象模块

提供结账页面的 Page Object Model，封装结账流程的所有交互操作。
"""

import logging
from typing import Optional, Dict
from playwright.sync_api import Page, Locator

logger = logging.getLogger(__name__)


class CheckoutPage:
    """结账页面对象

    封装结账页面的所有交互操作，包括：
    - 页面导航
    - 填写配送信息
    - 选择配送方式
    - 填写支付信息
    - 应用折扣码
    - 提交订单
    - 获取订单确认信息
    """

    # 结账页面的常见 URL 路径
    CHECKOUT_URL_PATHS = [
        "/checkout",
        "/checkout/shipping",
        "/checkout/information",
    ]

    # 结账页面选择器（通用选择器，适配 Shopify 等常见电商平台）
    SELECTORS = {
        # 配送信息表单
        "email": "input[name='email'], input[type='email'], #email",
        "first_name": "input[name='firstName'], input[name='first_name'], #firstName",
        "last_name": "input[name='lastName'], input[name='last_name'], #lastName",
        "address1": "input[name='address1'], input[name='address'], #address1",
        "address2": "input[name='address2'], #address2",
        "city": "input[name='city'], #city",
        "country": "select[name='country'], #country",
        "province": "select[name='province'], select[name='state'], #province",
        "zip": "input[name='zip'], input[name='postalCode'], #zip",
        "phone": "input[name='phone'], input[type='tel'], #phone",

        # 配送方式
        "shipping_methods": "[data-shipping-method], .shipping-method, input[type='radio'][name*='shipping']",

        # 支付信息
        "card_number": "input[name='number'], iframe[name*='card'], #cardNumber",
        "card_name": "input[name='name'], #cardName",
        "card_expiry": "input[name='expiry'], #cardExpiry",
        "card_cvv": "input[name='cvv'], input[name='cvc'], #cvv",

        # 折扣码
        "discount_code": "input[name='discount'], input[name='code'], #discount",
        "apply_discount": "button[name='apply'], button:has-text('Apply')",

        # 按钮
        "continue_to_shipping": "button[type='submit']:has-text('Continue'), button:has-text('Continue to shipping')",
        "continue_to_payment": "button[type='submit']:has-text('Continue'), button:has-text('Continue to payment')",
        "submit_order": "button[type='submit']:has-text('Complete'), button[name='checkout'], button:has-text('Place order')",

        # 订单摘要
        "order_total": ".total-price, [data-total], .order-total",
        "shipping_cost": ".shipping-cost, [data-shipping]",
        "tax": ".tax, [data-tax]",
        "discount": ".discount, [data-discount]",

        # 订单确认
        "order_number": ".order-number, [data-order-number], .order-id",
        "confirmation_message": ".order-confirmation, .thank-you-message",
    }

    def __init__(self, page: Page, base_url: str = "https://fiido.com"):
        """初始化结账页面对象

        Args:
            page: Playwright Page 对象
            base_url: 网站基础 URL
        """
        self.page = page
        self.base_url = base_url.rstrip("/")
        logger.info("CheckoutPage initialized")

    def navigate(self, wait_until: str = "domcontentloaded", timeout: int = 60000) -> None:
        """导航到结账页面

        Args:
            wait_until: 等待状态 ('load', 'domcontentloaded', 'networkidle')
            timeout: 超时时间（毫秒）

        Raises:
            Exception: 页面导航失败
        """
        for path in self.CHECKOUT_URL_PATHS:
            checkout_url = f"{self.base_url}{path}"
            try:
                logger.info(f"Navigating to checkout page: {checkout_url}")
                self.page.goto(checkout_url, wait_until=wait_until, timeout=timeout)
                logger.debug("Checkout page navigation completed")
                return
            except Exception as e:
                logger.warning(f"Failed to navigate to {checkout_url}: {e}")
                continue

        raise Exception("Failed to navigate to checkout page with any known URL pattern")

    def fill_shipping_info(
        self,
        email: str,
        first_name: str,
        last_name: str,
        address1: str,
        city: str,
        zip_code: str,
        country: str = "United States",
        province: Optional[str] = None,
        phone: Optional[str] = None,
        address2: Optional[str] = None,
    ) -> None:
        """填写配送信息

        Args:
            email: 邮箱地址
            first_name: 名
            last_name: 姓
            address1: 地址行1
            city: 城市
            zip_code: 邮编
            country: 国家（默认美国）
            province: 省/州（可选）
            phone: 电话号码（可选）
            address2: 地址行2（可选）
        """
        logger.info("Filling shipping information...")

        # 邮箱
        self._fill_field("email", email, "Email")

        # 姓名
        self._fill_field("first_name", first_name, "First Name")
        self._fill_field("last_name", last_name, "Last Name")

        # 地址
        self._fill_field("address1", address1, "Address Line 1")
        if address2:
            self._fill_field("address2", address2, "Address Line 2")

        # 城市
        self._fill_field("city", city, "City")

        # 邮编
        self._fill_field("zip", zip_code, "Zip Code")

        # 国家（下拉选择）
        self._select_field("country", country, "Country")

        # 省/州（下拉选择，可选）
        if province:
            self._select_field("province", province, "Province/State")

        # 电话（可选）
        if phone:
            self._fill_field("phone", phone, "Phone")

        logger.info("Shipping information filled")

    def select_shipping_method(self, method_index: int = 0) -> None:
        """选择配送方式

        Args:
            method_index: 配送方式索引（默认选择第一个）
        """
        logger.info(f"Selecting shipping method {method_index}...")

        shipping_methods = self.page.locator(self.SELECTORS["shipping_methods"]).all()

        if not shipping_methods or method_index >= len(shipping_methods):
            logger.warning(f"Shipping method {method_index} not found, total: {len(shipping_methods)}")
            return

        method = shipping_methods[method_index]
        if method.is_visible():
            method.click()
            self.page.wait_for_timeout(1000)
            logger.info(f"Shipping method {method_index} selected")
        else:
            logger.warning(f"Shipping method {method_index} not visible")

    def continue_to_shipping(self) -> None:
        """点击"继续到配送"按钮"""
        self._click_button("continue_to_shipping", "Continue to Shipping")

    def continue_to_payment(self) -> None:
        """点击"继续到支付"按钮"""
        self._click_button("continue_to_payment", "Continue to Payment")

    def fill_payment_info(
        self,
        card_number: str,
        card_name: str,
        expiry: str,
        cvv: str,
    ) -> None:
        """填写支付信息

        注意：实际生产环境中不应使用真实信用卡信息
        此方法主要用于测试环境

        Args:
            card_number: 卡号
            card_name: 持卡人姓名
            expiry: 过期日期（格式：MM/YY）
            cvv: CVV安全码
        """
        logger.info("Filling payment information...")

        # 注意：某些支付字段可能在 iframe 中
        # 这里提供基础实现，实际使用时可能需要特殊处理

        self._fill_field("card_number", card_number, "Card Number")
        self._fill_field("card_name", card_name, "Cardholder Name")
        self._fill_field("card_expiry", expiry, "Expiry Date")
        self._fill_field("card_cvv", cvv, "CVV")

        logger.info("Payment information filled")

    def apply_discount_code(self, code: str) -> bool:
        """应用折扣码

        Args:
            code: 折扣码

        Returns:
            bool: True 如果成功应用，False 如果失败
        """
        logger.info(f"Applying discount code: {code}")

        try:
            # 填写折扣码
            discount_input = self.page.locator(self.SELECTORS["discount_code"]).first
            if discount_input.is_visible():
                discount_input.fill(code)

                # 点击应用按钮
                apply_btn = self.page.locator(self.SELECTORS["apply_discount"]).first
                if apply_btn.is_visible():
                    apply_btn.click()
                    self.page.wait_for_timeout(2000)  # 等待验证
                    logger.info("Discount code applied")
                    return True

            logger.warning("Discount code field not found")
            return False
        except Exception as e:
            logger.error(f"Failed to apply discount code: {e}")
            return False

    def submit_order(self) -> None:
        """提交订单

        注意：此操作会创建真实订单！
        仅在测试环境使用，或使用测试支付网关
        """
        logger.warning("Submitting order (this creates a real order!)")
        self._click_button("submit_order", "Submit Order")

    def get_order_total(self) -> Optional[float]:
        """获取订单总计

        Returns:
            Optional[float]: 订单总计，如果无法获取则返回 None
        """
        return self._get_price("order_total", "Order Total")

    def get_shipping_cost(self) -> Optional[float]:
        """获取运费

        Returns:
            Optional[float]: 运费，如果无法获取则返回 None
        """
        return self._get_price("shipping_cost", "Shipping Cost")

    def get_tax(self) -> Optional[float]:
        """获取税费

        Returns:
            Optional[float]: 税费，如果无法获取则返回 None
        """
        return self._get_price("tax", "Tax")

    def get_discount(self) -> Optional[float]:
        """获取折扣金额

        Returns:
            Optional[float]: 折扣金额，如果无法获取则返回 None
        """
        return self._get_price("discount", "Discount")

    def get_order_number(self) -> Optional[str]:
        """获取订单号（订单确认页面）

        Returns:
            Optional[str]: 订单号，如果无法获取则返回 None
        """
        try:
            order_num_elem = self.page.locator(self.SELECTORS["order_number"]).first
            if order_num_elem.is_visible(timeout=5000):
                order_number = order_num_elem.inner_text().strip()
                logger.info(f"Order number: {order_number}")
                return order_number
        except Exception as e:
            logger.warning(f"Failed to get order number: {e}")

        return None

    def is_order_confirmed(self) -> bool:
        """检查订单是否已确认

        Returns:
            bool: True 如果在订单确认页面，False 否则
        """
        try:
            confirmation_msg = self.page.locator(self.SELECTORS["confirmation_message"]).first
            is_confirmed = confirmation_msg.is_visible(timeout=5000)
            logger.info(f"Order confirmed: {is_confirmed}")
            return is_confirmed
        except Exception:
            return False

    def get_checkout_summary(self) -> Dict:
        """获取结账摘要信息

        Returns:
            Dict: 包含订单总计、运费、税费等信息的字典
        """
        summary = {
            "order_total": self.get_order_total(),
            "shipping_cost": self.get_shipping_cost(),
            "tax": self.get_tax(),
            "discount": self.get_discount(),
        }
        logger.info(f"Checkout summary: {summary}")
        return summary

    # ========== 私有辅助方法 ==========

    def _fill_field(self, selector_key: str, value: str, field_name: str) -> None:
        """填写表单字段的辅助方法"""
        try:
            field = self.page.locator(self.SELECTORS[selector_key]).first
            if field.is_visible(timeout=5000):
                field.fill(value)
                logger.debug(f"{field_name} filled with value: {value}")
            else:
                logger.warning(f"{field_name} field not visible")
        except Exception as e:
            logger.warning(f"Failed to fill {field_name}: {e}")

    def _select_field(self, selector_key: str, value: str, field_name: str) -> None:
        """选择下拉字段的辅助方法"""
        try:
            field = self.page.locator(self.SELECTORS[selector_key]).first
            if field.is_visible(timeout=5000):
                field.select_option(value)
                logger.debug(f"{field_name} selected: {value}")
            else:
                logger.warning(f"{field_name} field not visible")
        except Exception as e:
            logger.warning(f"Failed to select {field_name}: {e}")

    def _click_button(self, selector_key: str, button_name: str) -> None:
        """点击按钮的辅助方法"""
        try:
            button = self.page.locator(self.SELECTORS[selector_key]).first
            if button.is_visible(timeout=5000):
                logger.info(f"Clicking {button_name} button...")
                button.click()
                self.page.wait_for_load_state("domcontentloaded", timeout=30000)
                logger.info(f"{button_name} button clicked")
            else:
                logger.warning(f"{button_name} button not visible")
        except Exception as e:
            logger.error(f"Failed to click {button_name}: {e}")
            raise

    def _get_price(self, selector_key: str, price_name: str) -> Optional[float]:
        """获取价格的辅助方法"""
        try:
            elem = self.page.locator(self.SELECTORS[selector_key]).first
            if elem.is_visible(timeout=5000):
                price_text = elem.inner_text().strip()
                # 解析价格（去除货币符号，提取数字）
                import re
                match = re.search(r"[\d,]+\.?\d*", price_text)
                if match:
                    price = float(match.group().replace(",", ""))
                    logger.debug(f"{price_name}: {price}")
                    return price
        except Exception as e:
            logger.warning(f"Failed to get {price_name}: {e}")

        return None
