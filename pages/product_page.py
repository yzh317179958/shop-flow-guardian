"""
商品页面对象模块

提供商品详情页的 Page Object Model，封装商品页面的所有交互操作。
"""

import logging
from typing import Optional, List
from playwright.async_api import Page

from core.models import Product, ProductVariant
from core.selector_manager import SelectorManager

logger = logging.getLogger(__name__)


class ProductPage:
    """通用商品页面对象

    封装商品详情页的所有交互操作，包括：
    - 页面导航
    - 获取商品信息（标题、价格）
    - 选择商品变体
    - 加入购物车
    - 检查库存状态
    """

    def __init__(self, page: Page, product: Product):
        """初始化商品页面对象

        Args:
            page: Playwright Page 对象
            product: 商品模型对象
        """
        self.page = page
        self.product = product
        self.selector_mgr = SelectorManager()
        logger.info(f"ProductPage initialized for: {product.name}")

    async def navigate(self, wait_until: str = 'networkidle'):
        """导航到商品页

        Args:
            wait_until: 等待状态 ('load', 'domcontentloaded', 'networkidle')

        Raises:
            Exception: 页面导航失败或服务器错误
        """
        try:
            logger.info(f"Navigating to {self.product.url}")
            response = await self.page.goto(str(self.product.url), wait_until=wait_until)

            # 🔧 新增: 检查HTTP响应状态码
            if response:
                status = response.status
                if status >= 500:
                    raise Exception(f"服务器错误: HTTP {status} - 服务器可能宕机或不可用")
                elif status >= 400:
                    raise Exception(f"请求错误: HTTP {status} - 页面可能不存在或无法访问")

            # 🔧 新增: 检查页面是否是错误页面
            page_content = await self.page.content()
            error_indicators = [
                "502 Bad Gateway",
                "503 Service Unavailable",
                "504 Gateway Timeout",
                "500 Internal Server Error",
                "Site Maintenance",
                "Server Error",
                "is currently unable to handle this request",
                "Connection refused",
                "This site can't be reached"
            ]
            for indicator in error_indicators:
                if indicator.lower() in page_content.lower():
                    raise Exception(f"服务器错误页面: 检测到 '{indicator}'")

            logger.debug("Page navigation completed")
        except Exception as e:
            logger.error(f"Failed to navigate to product page: {e}")
            raise

    async def get_title(self) -> Optional[str]:
        """获取商品标题

        Returns:
            商品标题文本，如果未找到返回 None
        """
        try:
            element = await self.selector_mgr.find_element(
                self.page,
                'product_title'
            )
            if element:
                title = await element.text_content()
                logger.debug(f"Found product title: {title}")
                return title.strip() if title else None
            logger.warning("Product title element not found")
            return None
        except Exception as e:
            logger.error(f"Error getting product title: {e}")
            return None

    async def get_price(self) -> Optional[str]:
        """获取商品价格

        Returns:
            价格文本，如果未找到返回 None
        """
        try:
            element = await self.selector_mgr.find_element(
                self.page,
                'product_price'
            )
            if element:
                price_text = await element.text_content()
                logger.debug(f"Found product price: {price_text}")
                return price_text.strip() if price_text else None
            logger.warning("Product price element not found")
            return None
        except Exception as e:
            logger.error(f"Error getting product price: {e}")
            return None

    async def select_variant(self, variant: ProductVariant, wait_time: int = 500) -> bool:
        """选择商品变体

        Args:
            variant: 变体对象
            wait_time: 选择后等待时间（毫秒），用于等待价格更新

        Returns:
            是否成功选择变体
        """
        try:
            logger.info(f"Selecting variant: {variant.name} ({variant.type})")
            await self.page.click(variant.selector, timeout=3000)
            await self.page.wait_for_timeout(wait_time)
            logger.debug(f"Variant {variant.name} selected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to select variant {variant.name}: {e}")
            return False

    async def add_to_cart(self) -> bool:
        """加入购物车

        Returns:
            是否成功加入购物车
        """
        try:
            logger.info("Attempting to add product to cart")

            # 监听 Console 错误
            errors = []

            def console_handler(msg):
                if msg.type == 'error':
                    errors.append(msg.text)

            self.page.on('console', console_handler)

            # 点击加购按钮
            add_button = await self.selector_mgr.find_element(
                self.page,
                'add_to_cart_button'
            )

            if not add_button:
                logger.warning("Add to cart button not found")
                return False

            await add_button.click()
            logger.debug("Add to cart button clicked")

            # 等待购物车更新（尝试找到购物车计数器）
            try:
                cart_count = await self.selector_mgr.find_element(
                    self.page,
                    'cart_count'
                )

                if cart_count:
                    # 等待元素可见
                    await self.page.wait_for_timeout(1000)  # 简单等待
                    logger.debug("Cart count element updated")
            except Exception as e:
                logger.debug(f"Cart count check skipped: {e}")

            # 检查是否有错误
            if errors:
                logger.warning(f"Console errors detected during add to cart: {errors}")
                return False

            logger.info("Product added to cart successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to add product to cart: {e}")
            return False

    async def is_in_stock(self) -> bool:
        """检查商品是否有货

        Returns:
            True 表示有货，False 表示缺货
        """
        # 检查"售罄"相关的选择器
        sold_out_selectors = [
            'button:has-text("Sold Out")',
            'button:has-text("Out of Stock")',
            'button:has-text("售罄")',
            'button[disabled]:has-text("Add")',
            '.sold-out',
            '.out-of-stock'
        ]

        for selector in sold_out_selectors:
            try:
                count = await self.page.locator(selector).count()
                if count > 0:
                    logger.info(f"Product out of stock (found selector: {selector})")
                    return False
            except Exception:
                continue

        logger.debug("Product is in stock")
        return True

    async def get_available_variants(self) -> List[str]:
        """获取可用的变体选项

        Returns:
            可用变体名称列表
        """
        variants = []
        try:
            # 尝试查找颜色选项
            color_selector = self.selector_mgr.get_selector('color', selector_type='variant_selectors')
            if color_selector:
                color_elements = await self.page.locator(color_selector).all()
                for element in color_elements:
                    text = await element.text_content()
                    if text:
                        variants.append(text.strip())

            # 尝试查找尺寸选项
            size_selector = self.selector_mgr.get_selector('size', selector_type='variant_selectors')
            if size_selector:
                size_elements = await self.page.locator(size_selector).all()
                for element in size_elements:
                    text = await element.text_content()
                    if text:
                        variants.append(text.strip())

            logger.debug(f"Found {len(variants)} available variants")
        except Exception as e:
            logger.error(f"Error getting available variants: {e}")

        return variants

    async def take_screenshot(self, path: str):
        """截取页面截图

        Args:
            path: 截图保存路径
        """
        try:
            await self.page.screenshot(path=path, full_page=True)
            logger.info(f"Screenshot saved to {path}")
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            raise

    async def get_product_info(self) -> dict:
        """获取完整商品信息

        Returns:
            包含标题、价格、库存状态的字典
        """
        return {
            'title': await self.get_title(),
            'price': await self.get_price(),
            'in_stock': await self.is_in_stock(),
            'variants': await self.get_available_variants()
        }
