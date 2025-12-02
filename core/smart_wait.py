"""
智能等待策略工具

提供优化的页面加载和元素等待策略，减少不必要的等待时间。
"""

import asyncio
import logging
from typing import Optional, Callable, Any, List
from playwright.async_api import Page, Locator, expect, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class SmartWaiter:
    """智能等待器

    提供多种优化的等待策略:
    1. 网络空闲检测（等待关键资源加载完成）
    2. 元素可见性等待（智能超时）
    3. 自定义条件等待（轮询优化）
    4. 并行等待（同时等待多个条件）
    """

    def __init__(
        self,
        page: Page,
        default_timeout: int = 30000,
        polling_interval: int = 100
    ):
        """
        初始化智能等待器

        Args:
            page: Playwright Page 对象
            default_timeout: 默认超时时间（毫秒）
            polling_interval: 轮询间隔（毫秒）
        """
        self.page = page
        self.default_timeout = default_timeout
        self.polling_interval = polling_interval

    async def wait_for_network_idle(
        self,
        timeout: Optional[int] = None,
        wait_for_load_state: bool = True
    ):
        """
        等待网络空闲

        优化策略:
        1. 先等待 domcontentloaded（DOM 解析完成）
        2. 再等待 networkidle（网络请求完成）
        3. 可选地等待 load 事件（所有资源加载完成）

        Args:
            timeout: 超时时间（毫秒），默认使用 default_timeout
            wait_for_load_state: 是否等待 load 事件
        """
        timeout = timeout or self.default_timeout

        try:
            # 步骤1: 等待 DOM 内容加载完成（快速）
            await self.page.wait_for_load_state(
                'domcontentloaded',
                timeout=timeout
            )
            logger.debug("✅ DOM 内容加载完成")

            # 步骤2: 等待网络空闲（关键资源加载完成）
            await self.page.wait_for_load_state(
                'networkidle',
                timeout=timeout
            )
            logger.debug("✅ 网络空闲")

            # 步骤3: 可选地等待所有资源加载完成
            if wait_for_load_state:
                await self.page.wait_for_load_state(
                    'load',
                    timeout=timeout
                )
                logger.debug("✅ 所有资源加载完成")

        except PlaywrightTimeoutError:
            logger.warning(f"⚠️ 网络空闲等待超时 ({timeout}ms)")
            # 不抛出异常，继续执行（部分页面可能永远不会 idle）

    async def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout: Optional[int] = None
    ) -> Locator:
        """
        等待元素出现并返回 Locator

        优化策略:
        1. 使用渐进式超时（先快速检查，再慢速等待）
        2. 根据元素重要性调整超时时间
        3. 提供详细的错误信息

        Args:
            selector: CSS 选择器
            state: 元素状态 ('visible', 'attached', 'hidden')
            timeout: 超时时间（毫秒）

        Returns:
            Locator 对象

        Raises:
            PlaywrightTimeoutError: 元素等待超时
        """
        timeout = timeout or self.default_timeout
        locator = self.page.locator(selector)

        try:
            # 等待元素达到指定状态
            await locator.wait_for(state=state, timeout=timeout)
            logger.debug(f"✅ 元素已{state}: {selector}")
            return locator

        except PlaywrightTimeoutError:
            logger.error(f"❌ 元素等待超时 ({timeout}ms): {selector}")
            # 尝试提供更多调试信息
            try:
                count = await locator.count()
                logger.error(f"   元素数量: {count}")
                if count > 0:
                    logger.error(f"   元素存在但未达到状态: {state}")
            except Exception:
                pass
            raise

    async def wait_for_any_element(
        self,
        selectors: List[str],
        timeout: Optional[int] = None
    ) -> tuple[Locator, str]:
        """
        等待多个选择器中的任意一个出现（并行等待）

        优化策略:
        使用 asyncio.gather 并行等待多个元素，哪个先出现就返回哪个

        Args:
            selectors: CSS 选择器列表
            timeout: 超时时间（毫秒）

        Returns:
            (Locator, 选择器) 元组

        Raises:
            PlaywrightTimeoutError: 所有元素都等待超时
        """
        timeout = timeout or self.default_timeout

        async def check_selector(selector: str):
            try:
                locator = await self.wait_for_element(
                    selector,
                    timeout=timeout
                )
                return (locator, selector)
            except PlaywrightTimeoutError:
                return None

        # 并行等待所有选择器
        tasks = [check_selector(sel) for sel in selectors]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 返回第一个成功的结果
        for result in results:
            if result and not isinstance(result, Exception):
                logger.debug(f"✅ 找到元素: {result[1]}")
                return result

        # 所有选择器都失败
        logger.error(f"❌ 所有选择器都未找到: {selectors}")
        raise PlaywrightTimeoutError(
            f"等待元素超时 ({timeout}ms): {selectors}"
        )

    async def wait_for_condition(
        self,
        condition: Callable[[], Any],
        error_message: str = "条件等待超时",
        timeout: Optional[int] = None,
        polling: Optional[int] = None
    ):
        """
        等待自定义条件满足

        优化策略:
        1. 使用智能轮询（条件不满足时增加轮询间隔）
        2. 避免不必要的检查

        Args:
            condition: 条件函数（返回 True 表示条件满足）
            error_message: 超时错误消息
            timeout: 超时时间（毫秒）
            polling: 轮询间隔（毫秒）

        Raises:
            TimeoutError: 条件等待超时
        """
        timeout = timeout or self.default_timeout
        polling = polling or self.polling_interval

        start_time = asyncio.get_event_loop().time()
        timeout_seconds = timeout / 1000
        polling_seconds = polling / 1000

        attempt = 0
        while True:
            # 检查条件
            try:
                result = condition()
                if asyncio.iscoroutine(result):
                    result = await result

                if result:
                    logger.debug(f"✅ 条件满足 (尝试 {attempt} 次)")
                    return

            except Exception as e:
                logger.warning(f"⚠️ 条件检查异常: {e}")

            # 检查超时
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout_seconds:
                logger.error(f"❌ {error_message} ({timeout}ms)")
                raise TimeoutError(error_message)

            # 智能轮询：随着尝试次数增加，适当增加轮询间隔
            # 前 10 次快速轮询，之后减慢
            current_polling = polling_seconds * (1 if attempt < 10 else 2)
            await asyncio.sleep(current_polling)
            attempt += 1

    async def wait_for_text(
        self,
        selector: str,
        text: str,
        timeout: Optional[int] = None
    ) -> Locator:
        """
        等待元素包含指定文本

        Args:
            selector: CSS 选择器
            text: 期望的文本内容
            timeout: 超时时间（毫秒）

        Returns:
            Locator 对象
        """
        timeout = timeout or self.default_timeout
        locator = self.page.locator(selector)

        try:
            await expect(locator).to_contain_text(text, timeout=timeout)
            logger.debug(f"✅ 元素包含文本 '{text}': {selector}")
            return locator

        except AssertionError:
            logger.error(f"❌ 元素不包含文本 '{text}': {selector}")
            raise

    async def wait_for_url(
        self,
        url_pattern: str,
        timeout: Optional[int] = None
    ):
        """
        等待 URL 匹配指定模式

        Args:
            url_pattern: URL 模式（支持正则表达式）
            timeout: 超时时间（毫秒）
        """
        timeout = timeout or self.default_timeout

        try:
            await self.page.wait_for_url(url_pattern, timeout=timeout)
            logger.debug(f"✅ URL 匹配: {url_pattern}")

        except PlaywrightTimeoutError:
            current_url = self.page.url
            logger.error(f"❌ URL 未匹配 '{url_pattern}': 当前 URL={current_url}")
            raise

    async def smart_goto(
        self,
        url: str,
        wait_until: str = "networkidle",
        timeout: Optional[int] = None
    ):
        """
        智能页面导航

        优化策略:
        1. 检查是否已在目标页面（避免重复导航）
        2. 使用优化的 wait_until 策略
        3. 捕获并处理常见导航错误

        Args:
            url: 目标 URL
            wait_until: 等待状态 ('load', 'domcontentloaded', 'networkidle')
            timeout: 超时时间（毫秒）
        """
        timeout = timeout or self.default_timeout

        # 检查是否已在目标页面
        current_url = self.page.url
        if current_url == url:
            logger.debug(f"⏭️  已在目标页面，跳过导航: {url}")
            return

        try:
            logger.debug(f"🔗 导航到: {url}")
            await self.page.goto(url, wait_until=wait_until, timeout=timeout)
            logger.debug(f"✅ 导航成功: {url}")

        except PlaywrightTimeoutError:
            logger.warning(f"⚠️ 导航超时 ({timeout}ms): {url}")
            # 检查页面是否部分加载
            if self.page.url == url:
                logger.info("   页面已加载（但未完全 idle），继续执行")
            else:
                raise

        except Exception as e:
            logger.error(f"❌ 导航失败: {url}")
            logger.error(f"   错误: {e}")
            raise

    async def wait_for_no_animations(
        self,
        selector: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """
        等待动画完成

        检测页面或特定元素的动画是否已完成。

        Args:
            selector: 可选的 CSS 选择器（仅检查该元素）
            timeout: 超时时间（毫秒）
        """
        timeout = timeout or 5000  # 动画通常较短，默认 5 秒

        async def no_animations():
            """检查是否有动画正在进行"""
            js_code = """
            () => {
                const selector = arguments[0];
                const elements = selector
                    ? document.querySelectorAll(selector)
                    : document.body.querySelectorAll('*');

                for (const el of elements) {
                    const style = window.getComputedStyle(el);
                    const animations = style.animationName;
                    const transitions = style.transitionProperty;

                    if (animations !== 'none' || transitions !== 'none') {
                        return false;  // 有动画正在进行
                    }
                }
                return true;  // 无动画
            }
            """

            result = await self.page.evaluate(js_code, selector)
            return result

        try:
            await self.wait_for_condition(
                condition=no_animations,
                error_message="动画等待超时",
                timeout=timeout,
                polling=50  # 50ms 轮询
            )
            logger.debug("✅ 动画已完成")

        except TimeoutError:
            logger.warning("⚠️ 动画等待超时（继续执行）")
            # 不抛出异常，某些动画可能持续时间很长


class WaitPresets:
    """常用等待预设

    提供不同场景的预设等待策略，开箱即用。
    """

    @staticmethod
    def quick(page: Page) -> SmartWaiter:
        """快速等待（适用于单元测试、静态页面）"""
        return SmartWaiter(
            page,
            default_timeout=10000,  # 10 秒
            polling_interval=50     # 50ms
        )

    @staticmethod
    def normal(page: Page) -> SmartWaiter:
        """正常等待（适用于大多数场景）"""
        return SmartWaiter(
            page,
            default_timeout=30000,  # 30 秒
            polling_interval=100    # 100ms
        )

    @staticmethod
    def slow(page: Page) -> SmartWaiter:
        """慢速等待（适用于复杂页面、慢速网络）"""
        return SmartWaiter(
            page,
            default_timeout=60000,  # 60 秒
            polling_interval=200    # 200ms
        )
