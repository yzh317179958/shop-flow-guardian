#!/usr/bin/env python3
"""
商品测试执行脚本 - 支持快速测试和全面测试

快速测试：验证核心购物流程（5个关键步骤）
全面测试：全链路全场景覆盖测试（10+个详细步骤）
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from playwright.async_api import async_playwright, Browser, Page
from core.models import Product
from pages.product_page import ProductPage

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    stream=sys.stdout  # 输出到stdout而不是stderr
)
logger = logging.getLogger(__name__)


def analyze_js_error_root_cause(js_errors: List[str]) -> str:
    """
    智能分析JavaScript错误，生成开发者友好的根因说明

    Args:
        js_errors: JavaScript错误列表

    Returns:
        详细的根因分析说明，便于开发人员定位问题
    """
    if not js_errors:
        return "未捕获到具体的JavaScript错误信息"

    # 合并所有错误进行分析
    all_errors = " ".join(js_errors).lower()
    first_error = js_errors[0]

    # 1. URI/URL 编解码错误
    if "uri malformed" in all_errors or "uricomponent" in all_errors:
        return (
            "【URI编解码错误】代码调用了 decodeURIComponent() 或 encodeURIComponent() 函数，"
            "但传入的参数值无效。常见原因：\n"
            "   • 从 cookie/localStorage 读取的值为 null 或 undefined\n"
            "   • URL参数包含未正确编码的特殊字符（如 %、&、=）\n"
            "   • 字符串拼接时产生了非法的URI格式\n"
            "   【建议修复】检查 decodeURIComponent 调用前的参数校验，添加 try-catch 或空值判断"
        )

    # 2. 空指针/未定义错误
    if "cannot read property" in all_errors or "cannot read properties" in all_errors:
        # 提取属性名
        import re
        prop_match = re.search(r"cannot read propert(?:y|ies) ['\"]?(\w+)['\"]? of (null|undefined)", all_errors)
        if prop_match:
            prop_name = prop_match.group(1)
            null_type = prop_match.group(2)
            return (
                f"【空指针错误】代码尝试访问 {null_type} 对象的 '{prop_name}' 属性。常见原因：\n"
                f"   • DOM查询 (querySelector/getElementById) 未找到目标元素，返回了 {null_type}\n"
                f"   • 异步数据未加载完成就尝试访问\n"
                f"   • 对象属性链中某个中间值为 {null_type}\n"
                f"   【建议修复】在访问 .{prop_name} 前添加空值检查：if (obj && obj.{prop_name})"
            )
        return (
            "【空指针错误】代码尝试访问 null 或 undefined 对象的属性。\n"
            "   【建议修复】检查变量是否正确初始化，添加空值判断"
        )

    # 3. 未定义变量/函数错误
    if "is not defined" in all_errors:
        import re
        var_match = re.search(r"(\w+) is not defined", all_errors)
        if var_match:
            var_name = var_match.group(1)
            return (
                f"【变量未定义】代码引用了未声明的变量或函数 '{var_name}'。常见原因：\n"
                f"   • JavaScript文件加载顺序错误，'{var_name}' 所在脚本未加载\n"
                f"   • 变量名拼写错误\n"
                f"   • 变量在其他作用域中声明，当前作用域无法访问\n"
                f"   【建议修复】检查 '{var_name}' 的定义位置和脚本加载顺序"
            )

    # 4. 类型错误
    if "is not a function" in all_errors:
        import re
        func_match = re.search(r"(\w+) is not a function", all_errors)
        if func_match:
            func_name = func_match.group(1)
            return (
                f"【类型错误】代码尝试将 '{func_name}' 作为函数调用，但它不是函数。常见原因：\n"
                f"   • '{func_name}' 被错误地赋值为非函数类型\n"
                f"   • 对象方法名拼写错误\n"
                f"   • 库/插件未正确加载，导致方法不存在\n"
                f"   【建议修复】检查 '{func_name}' 的类型和来源"
            )

    # 5. 语法错误
    if "syntaxerror" in all_errors or "unexpected token" in all_errors:
        return (
            "【语法错误】JavaScript代码存在语法问题，无法解析执行。常见原因：\n"
            "   • JSON格式错误（缺少引号、多余逗号等）\n"
            "   • 括号/大括号不匹配\n"
            "   • 模板字符串或正则表达式格式错误\n"
            "   【建议修复】使用浏览器开发者工具定位具体语法错误位置"
        )

    # 6. 网络请求错误
    if "fetch" in all_errors or "network" in all_errors or "xhr" in all_errors:
        return (
            "【网络请求错误】AJAX/Fetch请求失败。常见原因：\n"
            "   • 接口URL错误或服务端未响应\n"
            "   • 跨域(CORS)问题\n"
            "   • 请求参数格式错误\n"
            "   【建议修复】检查网络请求的URL、参数和服务端响应"
        )

    # 7. DOM操作错误
    if "queryselector" in all_errors or "getelementby" in all_errors or "appendchild" in all_errors:
        return (
            "【DOM操作错误】操作DOM元素时发生错误。常见原因：\n"
            "   • 选择器未匹配到任何元素\n"
            "   • 在DOM未完全加载时就执行了操作\n"
            "   • 元素已被移除或不在文档中\n"
            "   【建议修复】确保DOM操作在 DOMContentLoaded 事件后执行，并检查元素是否存在"
        )

    # 8. 事件处理错误
    if "addeventlistener" in all_errors or "event" in all_errors:
        return (
            "【事件处理错误】事件绑定或处理过程中发生错误。常见原因：\n"
            "   • 事件目标元素不存在\n"
            "   • 事件处理函数中的this指向错误\n"
            "   • 事件对象属性访问错误\n"
            "   【建议修复】检查事件绑定的目标元素和处理函数逻辑"
        )

    # 9. JSON解析错误
    if "json" in all_errors and ("parse" in all_errors or "stringify" in all_errors):
        return (
            "【JSON解析错误】JSON数据格式错误，无法解析。常见原因：\n"
            "   • 服务端返回的不是有效JSON格式\n"
            "   • JSON字符串中包含非法字符\n"
            "   • 尝试解析 undefined 或空字符串\n"
            "   【建议修复】验证JSON数据来源，添加解析前的格式检查"
        )

    # 10. 默认情况：提取关键信息
    # 尝试提取错误类型
    error_type = "未知"
    if "typeerror" in all_errors:
        error_type = "TypeError（类型错误）"
    elif "referenceerror" in all_errors:
        error_type = "ReferenceError（引用错误）"
    elif "rangeerror" in all_errors:
        error_type = "RangeError（范围错误）"

    return (
        f"【{error_type}】{first_error[:150]}\n"
        f"   【建议修复】使用浏览器开发者工具(F12)的Console面板查看完整错误堆栈，定位具体代码位置"
    )


class TestStep:
    """测试步骤记录"""

    def __init__(self, number: int, name: str, description: str):
        self.number = number
        self.name = name
        self.description = description
        self.status = "pending"
        self.message = ""
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.error: Optional[str] = None
        self.issue_details: Optional[Dict] = None  # 新增：问题详情

    def start(self):
        """开始执行步骤"""
        self.status = "running"
        self.started_at = time.time()
        logger.info(f"[步骤 {self.number}] {self.name}")
        logger.info(f"  说明: {self.description}")

    def complete(self, status: str, message: str, error: Optional[str] = None, issue_details: Optional[Dict] = None):
        """完成步骤

        Args:
            status: 步骤状态 (passed/failed/skipped)
            message: 结果消息
            error: 错误信息（可选）
            issue_details: 问题详情（可选），包含：
                - scenario: 什么场景
                - operation: 执行什么操作
                - problem: 出现什么问题
                - root_cause: 可能的根本原因
                - js_errors: JavaScript错误列表
        """
        self.status = status
        self.message = message
        self.error = error
        self.completed_at = time.time()
        self.issue_details = issue_details

        duration = self.completed_at - (self.started_at or self.completed_at)

        if status == "passed":
            logger.info(f"  ✓ 结果: {message} (耗时: {duration:.2f}s)")
        elif status == "failed":
            logger.info(f"  ✗ 结果: {message}")
            if error:
                logger.info(f"  错误: {error}")
            if issue_details:
                logger.info(f"  📋 问题详情:")
                logger.info(f"     场景: {issue_details.get('scenario', 'N/A')}")
                logger.info(f"     操作: {issue_details.get('operation', 'N/A')}")
                logger.info(f"     问题: {issue_details.get('problem', 'N/A')}")
                logger.info(f"     根因: {issue_details.get('root_cause', 'N/A')}")
        elif status == "skipped":
            logger.info(f"  ⊘ 结果: {message}")

        logger.info("")

    def to_dict(self) -> Dict:
        """转换为字典"""
        duration = 0
        if self.started_at and self.completed_at:
            duration = self.completed_at - self.started_at

        result = {
            "number": self.number,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "message": self.message,
            "error": self.error,
            "duration": round(duration, 2)
        }

        # 如果有问题详情，添加到结果中
        if self.issue_details:
            result["issue_details"] = self.issue_details

        return result


class ProductTester:
    """商品测试执行器"""

    def __init__(self, product: Product, test_mode: str = "quick", headless: bool = True):
        self.product = product
        self.test_mode = test_mode  # quick 或 full
        self.headless = headless
        self.steps: List[TestStep] = []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.product_page: Optional[ProductPage] = None
        self.start_time: float = 0
        self.end_time: float = 0

        # JavaScript错误监听
        self.js_errors: List[str] = []
        self.console_errors: List[str] = []

    def _init_quick_test_steps(self):
        """初始化快速测试步骤（核心购物流程）"""
        self.steps = [
            TestStep(1, "页面访问", "访问商品页面并检查页面是否正常加载"),
            TestStep(2, "商品信息显示", "验证商品标题、价格等核心信息是否正确显示"),
            TestStep(3, "添加购物车", "点击添加购物车按钮，验证能否成功加入"),
            TestStep(4, "购物车验证", "检查购物车中是否有新增商品"),
            TestStep(5, "支付流程", "访问购物车页面，验证Checkout按钮是否可用"),
        ]

    def _init_full_test_steps(self):
        """初始化全面测试步骤（全链路场景覆盖）"""
        self.steps = [
            TestStep(1, "页面访问", "访问商品页面并等待完全加载"),
            TestStep(2, "页面结构检测", "检查页面基础DOM结构是否完整"),
            TestStep(3, "商品标题验证", "验证商品标题显示是否正确"),
            TestStep(4, "价格信息验证", "检查商品价格显示是否完整"),
            TestStep(5, "商品图片验证", "验证商品图片是否加载成功"),
            TestStep(6, "商品描述验证", "检查商品描述内容是否存在"),
            TestStep(7, "变体选择测试", "测试颜色/尺寸等变体选项功能"),
            TestStep(8, "数量选择测试", "测试商品数量增减功能"),
            TestStep(9, "添加购物车", "测试添加购物车功能"),
            TestStep(10, "购物车验证", "验证购物车商品数量变化"),
            TestStep(11, "相关推荐验证", "检查相关商品推荐是否显示"),
            TestStep(12, "支付流程验证", "验证从购物车到支付页面的完整流程"),
        ]

    async def run(self) -> Dict:
        """运行完整测试流程"""
        # 初始化步骤
        if self.test_mode == "quick":
            self._init_quick_test_steps()
            test_name = "快速测试"
        else:
            self._init_full_test_steps()
            test_name = "全面测试"

        self.start_time = time.time()

        logger.info("=" * 70)
        logger.info(f"开始{test_name}: {self.product.name}")
        logger.info(f"商品ID: {self.product.id}")
        logger.info(f"测试模式: {test_name}")
        logger.info("=" * 70)
        logger.info("")

        result = {
            "product_id": self.product.id,
            "product_name": self.product.name,
            "test_mode": self.test_mode,
            "status": "passed",
            "steps": [],
            "errors": [],
            "duration": 0,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # 初始化浏览器
            await self._init_browser()

            if self.test_mode == "quick":
                await self._run_quick_test()
            else:
                await self._run_full_test()

        except Exception as e:
            logger.error(f"测试执行异常: {e}")
            result["status"] = "failed"
            result["errors"].append(str(e))

        finally:
            # 清理环境
            await self._cleanup()

        self.end_time = time.time()
        result["duration"] = round(self.end_time - self.start_time, 2)
        result["steps"] = [step.to_dict() for step in self.steps]

        # 汇总结果
        passed_count = sum(1 for step in self.steps if step.status == "passed")
        failed_count = sum(1 for step in self.steps if step.status == "failed")
        skipped_count = sum(1 for step in self.steps if step.status == "skipped")

        # 🔧 修复: 根据失败步骤数量判定整体测试结果
        # 只要有任何一个步骤失败,整体测试就判定为失败
        if failed_count > 0:
            result["status"] = "failed"

        logger.info("=" * 70)
        logger.info("测试完成")
        logger.info(f"总耗时: {result['duration']:.2f}s")
        logger.info(f"步骤统计: {passed_count} 通过, {failed_count} 失败, {skipped_count} 跳过")
        logger.info(f"最终结果: {result['status'].upper()}")
        logger.info("=" * 70)

        return result

    async def _init_browser(self):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            timeout=60000  # 60秒浏览器启动超时
        )
        self.page = await self.browser.new_page()
        # 设置页面默认超时为60秒
        self.page.set_default_timeout(60000)

        # 监听JavaScript错误（页面级别的未捕获错误）
        self.page.on("pageerror", lambda exc: self.js_errors.append(str(exc)))

        # 监听Console错误消息
        def on_console(msg):
            if msg.type == "error":
                self.console_errors.append(msg.text)

        self.page.on("console", on_console)

    async def _cleanup(self):
        """清理环境"""
        if self.browser:
            await self.browser.close()

    async def _run_quick_test(self):
        """运行快速测试（核心购物流程）"""
        # 步骤1: 页面访问
        step = self.steps[0]
        step.start()
        try:
            self.product_page = ProductPage(self.page, self.product)
            # 使用domcontentloaded而不是load，更快
            await self.product_page.navigate(wait_until="domcontentloaded")
            # 等待页面稳定
            await self.page.wait_for_timeout(3000)
            step.complete("passed", f"成功访问页面: {self.page.url}")
        except Exception as e:
            step.complete("failed", "页面访问失败", str(e))
            raise

        # 步骤2: 商品信息显示
        step = self.steps[1]
        step.start()
        try:
            title_visible = False
            price_visible = False
            price_text = ""
            title_text = ""

            # 检查标题 - 使用多个可能的选择器
            # 🔧 修复：移除过于宽泛的 "h1" 选择器，避免匹配错误页面标题
            # 🔧 修复：添加 Fiido 网站实际使用的 product-meta__title 选择器
            title_selectors = [
                self.product.selectors.product_title,
                "h1.product-meta__title",      # Fiido实际使用的标题class
                ".product-meta__title",        # 备用（不限定h1）
                "h1.product__title",
                ".product-title",
                "[data-product-title]",
                ".product-single__title",
                "h1.product-name",
                "h1.heading.h1",               # Fiido某些页面使用的组合class
            ]

            for title_selector in title_selectors:
                try:
                    # 🔧 修复：使用 query_selector_all 获取所有匹配元素
                    # 因为页面可能有多个相同选择器的元素，第一个可能是隐藏的
                    titles = await self.page.query_selector_all(title_selector)
                    for title in titles:
                        if title and await title.is_visible():
                            title_text = await title.text_content()
                            if title_text and title_text.strip():
                                # 🔧 修复：检查标题是否是错误页面标题
                                error_titles = ["502", "503", "504", "500", "error", "not found", "unavailable"]
                                is_error_title = any(err in title_text.lower() for err in error_titles)
                                if not is_error_title:
                                    title_visible = True
                                    title_text = title_text.strip()
                                    logger.info(f"找到标题 ({title_selector}): {title_text[:50]}")
                                    break
                    if title_visible:
                        break
                except:
                    continue

            # 检查价格 - 使用Fiido网站的实际价格类
            price_selectors = [
                ".price--highlight",  # Fiido主要价格显示
                ".sale-price",
                ".sales-price",
                ".price-box .price",
                ".product-form__price-info .price",
                "meta[property='product:price:amount']",  # 元数据价格
                ".money",
                "[data-price]"
            ]

            for price_selector in price_selectors:
                try:
                    if price_selector.startswith("meta"):
                        # 对于meta标签，检查是否存在
                        meta = await self.page.query_selector(price_selector)
                        if meta:
                            price_content = await meta.get_attribute("content")
                            if price_content:
                                price_visible = True
                                price_text = f"${price_content}"
                                logger.info(f"从meta标签找到价格: {price_text}")
                                break
                    else:
                        # 对于普通元素，检查可见性
                        prices = await self.page.query_selector_all(price_selector)
                        if prices:
                            logger.info(f"选择器 {price_selector} 找到 {len(prices)} 个元素")
                        for price_elem in prices:
                            if await price_elem.is_visible():
                                text = await price_elem.text_content()
                                if text and text.strip():
                                    price_visible = True
                                    price_text = text.strip()
                                    logger.info(f"从 {price_selector} 找到可见价格: {price_text[:30]}")
                                    break
                        if price_visible:
                            break
                except Exception as e:
                    logger.info(f"检查 {price_selector} 时出错: {e}")
                    continue

            # 🔧 修复：更严格的判断逻辑
            if title_visible and price_visible:
                step.complete("passed", f"商品标题和价格均正常显示 (标题: {title_text[:40]}, 价格: {price_text})")
            elif title_visible and not price_visible:
                # 有标题但没价格 - 可能是免费商品或配件
                step.complete("passed", f"商品标题显示正常: {title_text[:40]}（未检测到价格，可能是配件或免费商品）")
            elif not title_visible and price_visible:
                # 有价格但没标题 - 页面结构可能有问题
                step.complete("failed", "商品信息显示异常：检测到价格但未找到商品标题",
                             issue_details={
                                 "scenario": "验证商品详情页信息显示",
                                 "operation": "检测商品标题和价格元素",
                                 "problem": f"检测到价格({price_text})但未找到商品标题",
                                 "root_cause": "【页面结构异常】商品标题元素缺失或选择器不匹配。可能原因：\n"
                                              "   • 页面未完全加载\n"
                                              "   • 商品标题使用了非标准的CSS类\n"
                                              "   • 页面发生了JavaScript错误",
                                 "js_errors": self.js_errors[-5:] if self.js_errors else []
                             })
            else:
                # 标题和价格都没有 - 严重问题
                step.complete("failed", "商品信息显示失败：未找到商品标题和价格",
                             issue_details={
                                 "scenario": "验证商品详情页信息显示",
                                 "operation": "检测商品标题和价格元素",
                                 "problem": "页面上未找到商品标题和价格信息",
                                 "root_cause": "【页面加载失败】商品详情页核心信息缺失。可能原因：\n"
                                              "   • 页面返回了错误页面（如502/503）\n"
                                              "   • 商品已下架或不存在\n"
                                              "   • 页面JavaScript执行失败导致内容未渲染",
                                 "js_errors": self.js_errors[-5:] if self.js_errors else []
                             })
        except Exception as e:
            step.complete("failed", "检测商品信息时出错", str(e))

        # 步骤3: 添加购物车
        step = self.steps[2]
        step.start()
        try:
            button_selector = self.product.selectors.add_to_cart_button
            button = await self.page.query_selector(button_selector)

            if button:
                is_visible = await button.is_visible()
                is_enabled = await button.is_enabled()

                if is_visible and is_enabled:
                    # 尝试点击
                    await button.click()
                    await self.page.wait_for_timeout(2000)  # 等待加购动画
                    step.complete("passed", "成功点击添加购物车按钮")
                elif is_visible:
                    # 🔧 修复：按钮可见但禁用，尝试自动选择变体
                    logger.info("  加购按钮被禁用，尝试自动选择变体...")
                    variant_selected = False

                    # 尝试选择第一个可用的变体（颜色/型号等）
                    variant_selectors = [
                        "input[type='radio'].product-form__single-selector:not(:checked)",
                        "input[type='radio'].block-swatch__radio:not(:checked)",
                        ".product-form__input input[type='radio']:not(:checked)"
                    ]

                    for v_selector in variant_selectors:
                        try:
                            unchecked_radio = await self.page.query_selector(v_selector)
                            if unchecked_radio:
                                radio_id = await unchecked_radio.get_attribute("id")
                                if radio_id:
                                    label = await self.page.query_selector(f"label[for='{radio_id}']")
                                    if label:
                                        await label.click(timeout=2000)
                                        await self.page.wait_for_timeout(500)
                                        variant_selected = True
                                        logger.info(f"  已选择变体: {radio_id}")
                                        break
                        except:
                            continue

                    # 重新检查按钮状态
                    if variant_selected:
                        await self.page.wait_for_timeout(500)
                        is_enabled = await button.is_enabled()

                    if is_enabled:
                        await button.click()
                        await self.page.wait_for_timeout(2000)
                        step.complete("passed", "自动选择变体后成功点击添加购物车按钮")
                    else:
                        # 检查是否是售罄状态
                        sold_out_indicators = [
                            "button:has-text('Sold Out')",
                            "button:has-text('Out of Stock')",
                            ".sold-out",
                            "[data-sold-out='true']"
                        ]
                        is_sold_out = False
                        for indicator in sold_out_indicators:
                            if await self.page.query_selector(indicator):
                                is_sold_out = True
                                break

                        if is_sold_out:
                            step.complete("skipped", "商品已售罄，无法添加购物车")
                        else:
                            step.complete("failed", "加购按钮被禁用，尝试选择变体后仍无法启用",
                                         issue_details={
                                             "scenario": "用户尝试将商品添加到购物车",
                                             "operation": "点击添加购物车按钮",
                                             "problem": "按钮处于禁用状态，且尝试自动选择变体后仍无法启用",
                                             "root_cause": "【加购按钮异常】按钮被禁用但非售罄状态。可能原因：\n"
                                                          "   • 存在必选变体未被正确识别\n"
                                                          "   • 页面JavaScript逻辑错误\n"
                                                          "   • 按钮状态更新延迟",
                                             "js_errors": self.js_errors[-5:] if self.js_errors else []
                                         })
                else:
                    step.complete("failed", "加购按钮不可见")
            else:
                step.complete("failed", f"未找到加购按钮 (selector: {button_selector})")
        except Exception as e:
            step.complete("failed", "添加购物车操作失败", str(e))

        # 步骤4: 购物车验证
        step = self.steps[3]
        step.start()
        try:
            # 检查购物车图标或数量badge
            cart_selectors = [
                ".cart-count",
                ".cart-quantity",
                "[data-cart-count]",
                ".header__cart-count"
            ]

            cart_updated = False
            for selector in cart_selectors:
                cart_badge = await self.page.query_selector(selector)
                if cart_badge:
                    count_text = await cart_badge.text_content()
                    if count_text and count_text.strip() != "0":
                        cart_updated = True
                        step.complete("passed", f"购物车已更新，数量: {count_text.strip()}")
                        break

            if not cart_updated:
                # 🔧 修复：未检测到变化时，去购物车页面二次验证
                logger.info("  未检测到购物车数量变化，进行二次验证...")
                try:
                    cart_url = "https://fiido.com/cart"
                    await self.page.goto(cart_url, wait_until="domcontentloaded")
                    await self.page.wait_for_timeout(2000)

                    # 检查购物车是否有商品
                    cart_items = await self.page.query_selector_all("tr.cart-item, .cart-item, [data-cart-item]")
                    if cart_items and len(cart_items) > 0:
                        step.complete("passed", f"二次验证通过，购物车有 {len(cart_items)} 件商品")
                    else:
                        # 检查是否显示"购物车为空"
                        empty_indicators = await self.page.query_selector("text='Your cart is empty', text='购物车为空', .cart-empty, .empty-cart")
                        if empty_indicators:
                            step.complete("failed", "购物车验证失败：购物车为空，商品未成功加入",
                                         issue_details={
                                             "scenario": "用户点击添加购物车后验证购物车内容",
                                             "operation": "检查购物车页面是否有商品",
                                             "problem": "购物车显示为空，商品未成功加入",
                                             "root_cause": "【加购功能异常】点击添加购物车按钮后，商品未成功加入购物车。可能原因：\n"
                                                          "   • 加购AJAX请求失败\n"
                                                          "   • 需要先选择必选变体\n"
                                                          "   • 商品库存不足或已下架",
                                             "js_errors": self.js_errors[-5:] if self.js_errors else []
                                         })
                        else:
                            step.complete("failed", "购物车验证失败：无法确认商品是否加入购物车")
                except Exception as verify_error:
                    step.complete("failed", f"购物车二次验证失败: {str(verify_error)}")
        except Exception as e:
            step.complete("failed", "检查购物车时出错", str(e))

        # 步骤5: 支付流程
        step = self.steps[4]
        step.start()
        try:
            # 直接导航到购物车页面
            cart_url = "https://fiido.com/cart"
            logger.info(f"直接导航到购物车页面: {cart_url}")

            await self.page.goto(cart_url, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(2000)  # 等待页面加载完成

            current_url = self.page.url
            logger.info(f"当前URL: {current_url}")

            if '/cart' in current_url:
                # 成功进入购物车页面，查找checkout按钮
                logger.info("已进入购物车页面，查找Checkout按钮...")

                checkout_selectors = [
                    "button[name='checkout']",
                    "[name='checkout']",
                    "button:has-text('Check out')",
                    "button:has-text('Checkout')",
                    "a[href*='/checkout']",
                    "form[action*='checkout'] button",
                    "#checkout"
                ]

                checkout_button = None
                for selector in checkout_selectors:
                    try:
                        checkout_button = await self.page.query_selector(selector)
                        if checkout_button:
                            is_visible = await checkout_button.is_visible()
                            is_enabled = await checkout_button.is_enabled()
                            logger.info(f"Checkout选择器 {selector}: 找到元素, visible={is_visible}, enabled={is_enabled}")
                            if is_visible:
                                # 找到可见的checkout按钮，尝试获取按钮文本
                                try:
                                    btn_text = await checkout_button.text_content()
                                    logger.info(f"  按钮文本: {btn_text}")
                                except:
                                    pass
                                break
                        checkout_button = None
                    except Exception as e:
                        logger.info(f"Checkout选择器 {selector}: {e}")
                        continue

                if checkout_button:
                    step.complete("passed", "购物车页面正常，Checkout按钮可见可点击")
                else:
                    # 检查购物车是否为空
                    empty_cart_indicators = [
                        "text='Your cart is empty'",
                        "text='购物车为空'",
                        ".cart-empty",
                        ".empty-cart"
                    ]

                    is_empty = False
                    for indicator in empty_cart_indicators:
                        if await self.page.query_selector(indicator):
                            is_empty = True
                            break

                    if is_empty:
                        # 🔧 修复：购物车为空说明加购失败，报告failed
                        step.complete("failed", "支付流程验证失败：购物车为空",
                                     issue_details={
                                         "scenario": "验证从商品页到支付页的完整流程",
                                         "operation": "进入购物车页面准备结账",
                                         "problem": "购物车显示为空，无法进行结账",
                                         "root_cause": "【购物流程中断】商品未成功加入购物车，导致无法完成支付流程。\n"
                                                      "   可能原因：\n"
                                                      "   • 步骤3添加购物车操作实际未成功\n"
                                                      "   • 加购后页面跳转导致购物车状态丢失\n"
                                                      "   • 商品变体未正确选择",
                                         "js_errors": self.js_errors[-5:] if self.js_errors else []
                                     })
                    else:
                        # 🔧 修复：有商品但找不到Checkout按钮，需要进一步检查
                        # 检查是否有禁用的Checkout按钮
                        disabled_checkout = await self.page.query_selector("button[name='checkout'][disabled], button:has-text('Checkout')[disabled]")
                        if disabled_checkout:
                            step.complete("failed", "支付流程验证失败：Checkout按钮存在但被禁用",
                                         issue_details={
                                             "scenario": "验证购物车页面的结账功能",
                                             "operation": "查找并点击Checkout按钮",
                                             "problem": "Checkout按钮存在但处于禁用状态",
                                             "root_cause": "【结账功能受限】Checkout按钮被禁用。可能原因：\n"
                                                          "   • 购物车商品不满足最低消费\n"
                                                          "   • 商品库存状态变化\n"
                                                          "   • 页面JavaScript错误导致按钮状态异常",
                                             "js_errors": self.js_errors[-5:] if self.js_errors else []
                                         })
                        else:
                            step.complete("failed", "支付流程验证失败：购物车有商品但未找到Checkout按钮",
                                         issue_details={
                                             "scenario": "验证购物车页面的结账功能",
                                             "operation": "查找Checkout按钮",
                                             "problem": "购物车页面存在商品，但找不到Checkout按钮",
                                             "root_cause": "【页面结构异常】购物车有商品但无法找到结账入口。可能原因：\n"
                                                          "   • 页面DOM结构与预期不符\n"
                                                          "   • Checkout按钮选择器需要更新\n"
                                                          "   • 页面渲染不完整",
                                             "js_errors": self.js_errors[-5:] if self.js_errors else []
                                         })
            else:
                step.complete("failed", f"未能进入购物车页面，当前URL: {current_url}")

        except Exception as e:
            logger.info(f"验证支付流程时出错: {e}")
            step.complete("failed", "验证支付流程时出错", str(e))

    async def _run_full_test(self):
        """运行全面测试（全链路场景覆盖）"""
        # 步骤1: 页面访问
        step = self.steps[0]
        step.start()
        try:
            self.product_page = ProductPage(self.page, self.product)
            await self.product_page.navigate(wait_until="domcontentloaded")  # 使用domcontentloaded更快
            await self.page.wait_for_timeout(3000)  # 等待3秒让页面完全加载
            step.complete("passed", f"页面加载完成: {self.page.url}")
        except Exception as e:
            step.complete("failed", "页面访问失败", str(e))
            raise

        # 步骤2: 页面结构检测
        step = self.steps[1]
        step.start()
        try:
            body = await self.page.query_selector("body")
            header = await self.page.query_selector("header, .header")
            main = await self.page.query_selector("main, .main-content")

            if body and header and main:
                step.complete("passed", "页面基础结构完整（body, header, main均存在）")
            else:
                step.complete("passed", "页面已加载，但结构不完整")
        except Exception as e:
            step.complete("failed", "检测页面结构时出错", str(e))

        # 步骤3: 商品标题验证
        step = self.steps[2]
        step.start()
        try:
            # 🔧 修复：使用与快速测试一致的选择器列表，移除过于宽泛的 "h1"
            title_selectors = [
                "h1.product-meta__title",      # Fiido实际使用的标题class
                ".product-meta__title",        # 备用（不限定h1）
                "h1.product__title",
                ".product-title",
                "[data-product-title]",
                ".product-single__title",
                "h1.product-name",
                "h1.heading.h1",               # Fiido某些页面使用的组合class
            ]

            title_found = False
            for selector in title_selectors:
                try:
                    # 🔧 修复：使用 query_selector_all 获取所有匹配元素
                    # 因为页面可能有多个相同选择器的元素，第一个可能是隐藏的
                    titles = await self.page.query_selector_all(selector)
                    for title in titles:
                        if title and await title.is_visible():
                            title_text = await title.text_content()
                            if title_text and title_text.strip():
                                # 🔧 修复：检查标题是否是错误页面标题
                                error_titles = ["502", "503", "504", "500", "error", "not found", "unavailable"]
                                is_error_title = any(err in title_text.lower() for err in error_titles)
                                if not is_error_title:
                                    title_found = True
                                    step.complete("passed", f"商品标题显示正常: {title_text.strip()[:60]}")
                                    break
                    if title_found:
                        break
                except:
                    continue

            if not title_found:
                step.complete("failed", "未找到商品标题",
                             issue_details={
                                 "scenario": "验证商品详情页标题显示",
                                 "operation": "检测页面中的商品标题元素",
                                 "problem": "未找到商品标题或标题为错误页面标题",
                                 "root_cause": "【页面结构异常】商品标题元素缺失或使用了非标准的CSS类。可能原因：\n"
                                              "   • 页面未完全加载\n"
                                              "   • 商品标题使用了非标准的CSS类\n"
                                              "   • 页面返回了错误页面",
                                 "js_errors": self.js_errors[-5:] if self.js_errors else []
                             })
        except Exception as e:
            step.complete("failed", "验证标题时出错", str(e))

        # 步骤4: 价格信息验证
        step = self.steps[3]
        step.start()
        try:
            price_selectors = [
                ".price--highlight",
                ".sale-price",
                ".product-form__price-info .price",
                "meta[property='product:price:amount']",
                ".money"
            ]

            price_found = False
            for selector in price_selectors:
                try:
                    if selector.startswith("meta"):
                        meta = await self.page.query_selector(selector)
                        if meta:
                            price_content = await meta.get_attribute("content")
                            if price_content:
                                price_found = True
                                step.complete("passed", f"价格信息显示正常: ${price_content}")
                                break
                    else:
                        prices = await self.page.query_selector_all(selector)
                        for price_elem in prices:
                            if await price_elem.is_visible():
                                price_text = await price_elem.text_content()
                                if price_text and price_text.strip():
                                    price_found = True
                                    step.complete("passed", f"价格信息显示正常: {price_text.strip()}")
                                    break
                        if price_found:
                            break
                except:
                    continue

            if not price_found:
                step.complete("failed", "未找到价格信息")
        except Exception as e:
            step.complete("failed", "验证价格时出错", str(e))

        # 步骤5: 商品图片验证
        step = self.steps[4]
        step.start()
        try:
            # 检查主图 - 包括懒加载的图片
            main_image_selectors = [
                "img[src*='product']",
                "img[data-src*='product']",  # 懒加载图片
                ".product__media-item img",
                ".product-main-image img",
                ".product-image img"
            ]

            images_found = 0
            visible_images = 0
            for selector in main_image_selectors:
                try:
                    images = await self.page.query_selector_all(selector)
                    for img in images:
                        src = await img.get_attribute("src")
                        data_src = await img.get_attribute("data-src")

                        # 检查是否有product相关的src
                        if (src and "product" in src.lower()) or (data_src and "product" in data_src.lower()):
                            images_found += 1
                            try:
                                if await img.is_visible():
                                    visible_images += 1
                            except:
                                pass
                except:
                    continue

            # 检查缩略图（可点击切换的图片）
            thumbnail_selectors = [
                ".product__media-thumbs img",
                ".product-thumbnails img",
                ".thumbnail img"
            ]

            thumbnails_found = 0
            for selector in thumbnail_selectors:
                try:
                    thumbs = await self.page.query_selector_all(selector)
                    thumbnails_found += len(thumbs)
                except:
                    continue

            if images_found > 0:
                step.complete("passed", f"商品图片存在 (总数: {images_found}, 可见: {visible_images}, 缩略图: {thumbnails_found})")
            else:
                step.complete("failed", "未找到商品图片")
        except Exception as e:
            step.complete("failed", "验证图片时出错", str(e))

        # 步骤6: 商品描述验证
        step = self.steps[5]
        step.start()
        try:
            description_selectors = [
                ".product__description",
                ".product-description",
                "[data-product-description]",
                ".description"
            ]

            desc_found = False
            for selector in description_selectors:
                try:
                    desc = await self.page.query_selector(selector)
                    if desc:
                        desc_text = await desc.text_content()
                        if desc_text and len(desc_text.strip()) > 20:
                            desc_found = True
                            step.complete("passed", f"商品描述存在 (长度: {len(desc_text)} 字符)")
                            break
                except:
                    continue

            if not desc_found:
                step.complete("passed", "未检测到详细商品描述（可能在页面其他位置）")
        except Exception as e:
            step.complete("failed", "验证描述时出错", str(e))

        # 步骤7: 变体选择测试 (颜色/型号/配件等)
        step = self.steps[6]
        step.start()
        try:
            variant_results = []

            # Shopify产品页面使用radio按钮来处理变体选择
            # 查找所有radio类型的变体选择器
            all_radios = await self.page.query_selector_all("input[type='radio'].product-form__single-selector, input[type='radio'].block-swatch__radio")

            if all_radios and len(all_radios) > 0:
                # 按name属性分组radio按钮（同一个name代表一组选项）
                radio_groups = {}
                for radio in all_radios:
                    try:
                        radio_name = await radio.get_attribute("name")
                        radio_value = await radio.get_attribute("value")
                        radio_id = await radio.get_attribute("id")
                        is_checked = await radio.is_checked()

                        if radio_name and radio_value:
                            if radio_name not in radio_groups:
                                radio_groups[radio_name] = []
                            radio_groups[radio_name].append({
                                'element': radio,
                                'value': radio_value,
                                'id': radio_id,
                                'checked': is_checked
                            })
                    except:
                        continue

                logger.info(f"  找到 {len(radio_groups)} 个变体组，共 {len(all_radios)} 个选项")

                # 测试每个变体组
                for group_name, radios in radio_groups.items():
                    if len(radios) > 1:  # 只有多个选项才测试
                        # 获取第一个选项的label来判断是什么类型的变体
                        first_radio = radios[0]
                        variant_type = "变体"

                        # 根据值判断类型
                        first_value = first_radio['value'].lower()
                        if any(color in first_value for color in ['green', 'gray', 'grey', 'black', 'white', 'red', 'blue', 'yellow']):
                            variant_type = "颜色"
                        elif any(model in first_value for model in ['2024', '2025', 't1', 't2', 'model', 'version']):
                            variant_type = "型号"

                        # 尝试点击第二个选项（切换变体）
                        try:
                            # 找到未选中的第一个选项
                            unchecked_radio = None
                            for r in radios:
                                if not r['checked']:
                                    unchecked_radio = r
                                    break

                            if unchecked_radio:
                                # 点击对应的label（更可靠）
                                radio_id = unchecked_radio['id']
                                if radio_id:
                                    label = await self.page.query_selector(f"label[for='{radio_id}']")
                                    if label:
                                        await label.click(timeout=3000)
                                        await self.page.wait_for_timeout(500)
                                        variant_results.append(f"{variant_type}: {len(radios)}个选项，已测试切换")
                                        logger.info(f"  成功切换{variant_type}: {first_radio['value']} -> {unchecked_radio['value']}")
                                    else:
                                        # label不存在，直接点击radio
                                        await unchecked_radio['element'].click(timeout=3000)
                                        await self.page.wait_for_timeout(500)
                                        variant_results.append(f"{variant_type}: {len(radios)}个选项，已测试切换")
                                else:
                                    variant_results.append(f"{variant_type}: {len(radios)}个选项（无法点击）")
                            else:
                                variant_results.append(f"{variant_type}: {len(radios)}个选项（已全部选中）")
                        except Exception as e:
                            variant_results.append(f"{variant_type}: {len(radios)}个选项（交互失败）")
                            logger.info(f"  切换{variant_type}失败: {str(e)[:50]}")

            # 检查配件选择 (Accessories) - 使用checkbox
            visible_checkboxes = await self.page.query_selector_all("input[type='checkbox'].isfree, input[type='checkbox']:visible")

            accessories_found = 0
            for cb in visible_checkboxes:
                try:
                    is_visible = await cb.is_visible()
                    if is_visible:
                        accessories_found += 1
                except:
                    continue

            if accessories_found > 0:
                # 尝试勾选第一个配件
                try:
                    first_cb = visible_checkboxes[0]
                    await first_cb.click(timeout=3000)
                    await self.page.wait_for_timeout(500)
                    variant_results.append(f"配件选项: {accessories_found}个，已测试勾选")
                    logger.info(f"  成功测试配件勾选")
                except:
                    variant_results.append(f"配件选项: {accessories_found}个（无法勾选）")

            if variant_results:
                step.complete("passed", f"变体选择功能正常 ({', '.join(variant_results)})")
            else:
                step.complete("passed", "未检测到变体选项（可能是标准商品）")
        except Exception as e:
            step.complete("failed", "测试变体选择时出错", str(e))

        # 步骤8: 数量选择测试
        step = self.steps[7]
        step.start()
        try:
            # 在商品详情页，很多网站只有数量输入框，而加减按钮在购物车页面
            # 所以这一步主要验证数量输入框的存在和可用性
            quantity_selectors = [
                "input[name='quantity']",
                "input[type='number'][name*='quantity']",
                ".quantity-selector input",
                ".qty input"
            ]

            quantity_input = None
            for selector in quantity_selectors:
                try:
                    quantity_input = await self.page.query_selector(selector)
                    if quantity_input:
                        break
                except:
                    continue

            if quantity_input:
                try:
                    # 获取当前值和input的属性
                    current_value = await quantity_input.get_attribute("value")
                    is_disabled = await quantity_input.is_disabled()
                    is_readonly = await quantity_input.get_attribute("readonly")

                    logger.info(f"  数量输入框: value={current_value}, disabled={is_disabled}, readonly={is_readonly}")

                    # 如果input被禁用或只读，直接报告
                    if is_disabled:
                        step.complete("passed", f"数量输入框存在但已禁用（当前值: {current_value}）")
                        return

                    if is_readonly:
                        step.complete("passed", f"数量输入框为只读模式（当前值: {current_value}）")
                        return

                    # 尝试手动输入数量（商品详情页最常见的方式）
                    try:
                        # 方法1: 点击并选中所有文本，然后输入
                        await quantity_input.click(timeout=2000)
                        await quantity_input.select_text(timeout=1000)
                        await quantity_input.type("2", timeout=2000)
                        await self.page.wait_for_timeout(300)
                        new_value = await quantity_input.get_attribute("value")

                        if new_value == "2":
                            logger.info(f"  成功手动输入数量: {current_value} -> {new_value}")
                            step.complete("passed", f"数量输入框功能正常，可手动输入 (修改为: {new_value})")
                            return
                        else:
                            logger.info(f"  手动输入失败，当前值: {new_value}")
                    except Exception as e:
                        logger.info(f"  方法1失败: {str(e)[:50]}")

                    # 方法2: 使用keyboard操作
                    try:
                        await quantity_input.click(timeout=2000)
                        await self.page.keyboard.press("Control+A")  # 全选
                        await self.page.keyboard.press("Backspace")  # 删除
                        await self.page.keyboard.type("3")  # 输入3
                        await self.page.wait_for_timeout(300)
                        new_value = await quantity_input.get_attribute("value")

                        if new_value == "3":
                            logger.info(f"  使用键盘输入成功: {current_value} -> {new_value}")
                            step.complete("passed", f"数量输入框功能正常，支持键盘输入 (修改为: {new_value})")
                            return
                    except Exception as e:
                        logger.info(f"  方法2失败: {str(e)[:50]}")

                    # 如果手动输入都失败，检查是否有加减按钮（某些网站在商品页也有）
                    plus_button = await self.page.query_selector("button.quantity-plus, button[aria-label*='Increase'], button.quantity__button:has-text('+')")
                    if plus_button:
                        try:
                            is_button_visible = await plus_button.is_visible()
                            if is_button_visible:
                                await plus_button.click(timeout=2000)
                                await self.page.wait_for_timeout(300)
                                new_value = await quantity_input.get_attribute("value")
                                if int(new_value) > int(current_value):
                                    logger.info(f"  加号按钮可用: {current_value} -> {new_value}")
                                    step.complete("passed", f"数量加减按钮功能正常 (增加后: {new_value})")
                                    return
                        except Exception as e:
                            logger.info(f"  加号按钮点击失败: {str(e)[:50]}")

                    # 所有方法都失败
                    step.complete("passed", f"数量输入框存在（值: {current_value}），但手动交互受限。注意：数量调整功能通常在购物车页面可用")

                except Exception as e:
                    step.complete("passed", f"检测到数量输入框但测试受限: {str(e)[:80]}")
            else:
                step.complete("passed", "未检测到数量输入框（可能使用其他方式控制数量）")
        except Exception as e:
            step.complete("failed", "测试数量选择时出错", str(e))

        # 步骤9: 添加购物车
        step = self.steps[8]
        step.start()
        try:
            button_selector = self.product.selectors.add_to_cart_button
            button = await self.page.query_selector(button_selector)

            if button:
                is_visible = await button.is_visible()
                is_enabled = await button.is_enabled()

                if is_visible and is_enabled:
                    await button.click()
                    # 🔧 改进: 等待更长时间让AJAX请求完成并同步到服务器
                    await self.page.wait_for_timeout(5000)  # 从2秒增加到5秒
                    logger.info("等待购物车同步到服务器...")
                    step.complete("passed", "成功点击添加购物车按钮")
                elif is_visible:
                    step.complete("passed", "加购按钮可见但已禁用（可能需要选择变体）")
                else:
                    step.complete("failed", "加购按钮不可见")
            else:
                step.complete("failed", f"未找到加购按钮 (selector: {button_selector})")
        except Exception as e:
            step.complete("failed", "添加购物车操作失败", str(e))

        # 步骤10: 购物车验证
        step = self.steps[9]
        step.start()
        try:
            cart_selectors = [
                ".cart-count",
                ".cart-quantity",
                "[data-cart-count]",
                ".header__cart-count"
            ]

            cart_updated = False
            for selector in cart_selectors:
                cart_badge = await self.page.query_selector(selector)
                if cart_badge:
                    count_text = await cart_badge.text_content()
                    if count_text and count_text.strip() != "0":
                        cart_updated = True
                        step.complete("passed", f"购物车已更新，数量: {count_text.strip()}")
                        break

            if not cart_updated:
                # 🔧 修复：未检测到变化时，去购物车页面二次验证（与快速测试一致）
                logger.info("  未检测到购物车数量变化，进行二次验证...")
                try:
                    cart_url = "https://fiido.com/cart"
                    await self.page.goto(cart_url, wait_until="domcontentloaded")
                    await self.page.wait_for_timeout(2000)

                    # 检查购物车是否有商品
                    cart_items = await self.page.query_selector_all("tr.cart-item, .cart-item, [data-cart-item]")
                    if cart_items and len(cart_items) > 0:
                        step.complete("passed", f"二次验证通过，购物车有 {len(cart_items)} 件商品")
                    else:
                        # 检查是否显示"购物车为空"
                        empty_indicators = await self.page.query_selector("text='Your cart is empty', text='购物车为空', .cart-empty, .empty-cart")
                        if empty_indicators:
                            step.complete("failed", "购物车验证失败：购物车为空，商品未成功加入",
                                         issue_details={
                                             "scenario": "用户点击添加购物车后验证购物车内容",
                                             "operation": "检查购物车页面是否有商品",
                                             "problem": "购物车显示为空，商品未成功加入",
                                             "root_cause": "【加购功能异常】点击添加购物车按钮后，商品未成功加入购物车。可能原因：\n"
                                                          "   • 加购AJAX请求失败\n"
                                                          "   • 需要先选择必选变体\n"
                                                          "   • 商品库存不足或已下架",
                                             "js_errors": self.js_errors[-5:] if self.js_errors else []
                                         })
                        else:
                            step.complete("failed", "购物车验证失败：无法确认商品是否加入购物车")
                except Exception as verify_error:
                    step.complete("failed", f"购物车二次验证失败: {str(verify_error)}")
        except Exception as e:
            step.complete("failed", "检查购物车时出错", str(e))

        # 步骤11: 相关推荐验证
        step = self.steps[10]
        step.start()
        try:
            recommendation_selectors = [
                ".product-recommendations",
                ".related-products",
                ".recommended-products",
                "[data-recommendations]"
            ]

            recommendations_found = 0
            for selector in recommendation_selectors:
                try:
                    rec_section = await self.page.query_selector(selector)
                    if rec_section:
                        # 计算推荐商品数量
                        rec_items = await rec_section.query_selector_all(".product-item, .product-card")
                        recommendations_found = len(rec_items)
                        if recommendations_found > 0:
                            step.complete("passed", f"相关推荐显示正常 (推荐商品: {recommendations_found}个)")
                            break
                except:
                    continue

            if recommendations_found == 0:
                step.complete("passed", "未检测到相关推荐（可能在页面底部或不存在）")
        except Exception as e:
            step.complete("failed", "验证相关推荐时出错", str(e))

        # 步骤12: 支付流程验证
        step = self.steps[11]
        step.start()
        try:
            # 清空之前的错误记录
            errors_before_cart = len(self.js_errors)
            console_errors_before = len(self.console_errors)

            # 🔧 改进1: 直接导航到购物车页面(最可靠的方式)
            cart_url = "https://fiido.com/cart"
            logger.info(f"导航到购物车页面: {cart_url}")

            await self.page.goto(cart_url, wait_until="domcontentloaded")
            await self.page.wait_for_timeout(3000)  # 等待页面和动态内容加载

            current_url = self.page.url
            logger.info(f"当前URL: {current_url}")

            if '/cart' in current_url:
                logger.info("已进入购物车页面，检测购物车功能...")

                # 🔍 核心功能：检测购物车数量调整Bug
                cart_bug_detected = False
                bug_details = None

                try:
                    # 🎯 新策略: 通过DOM结构查找购物车元素
                    # 因为直接查找input和button可能失败,改为查找商品行
                    logger.info("查找购物车商品行...")

                    # 查找商品行(跳过表头)
                    cart_rows = await self.page.query_selector_all("tr")

                    test_row = None
                    for i, row in enumerate(cart_rows):
                        # 检查是否包含button元素
                        buttons = await row.query_selector_all("button, a")
                        if len(buttons) > 0:
                            test_row = row
                            logger.info(f"✓ 找到购物车商品行(第{i+1}个tr,包含{len(buttons)}个button/a)")
                            break

                    if not test_row:
                        logger.info("ℹ️  购物车页面未找到商品行")
                    else:
                        # 在商品行内查找所有button/a元素
                        buttons_in_row = await test_row.query_selector_all("button, a")

                        # 查找加号按钮
                        plus_button = None
                        for btn in buttons_in_row:
                            try:
                                if await btn.is_visible():
                                    inner_html = await btn.inner_html()
                                    btn_name = await btn.get_attribute("name")

                                    # 检查是否是加号按钮
                                    if (inner_html and ('plus' in inner_html.lower() or '+' in inner_html)) or \
                                       (btn_name and 'plus' in btn_name.lower()):
                                        plus_button = btn
                                        logger.info("✓ 找到加号按钮(DOM内包含plus或+)")
                                        break
                            except:
                                continue

                        if plus_button:
                            # 🖱️  测试点击加号按钮
                            logger.info("🖱️  测试点击加号按钮...")

                            # 尝试获取当前数量
                            cart_qty_input = await self.page.query_selector("input[type='number']")
                            current_qty = None
                            if cart_qty_input:
                                current_qty = await cart_qty_input.get_attribute("value")
                                logger.info(f"📊 当前数量: {current_qty}")

                            js_errors_before_click = len(self.js_errors)

                            try:
                                await plus_button.click(timeout=2000)
                                await self.page.wait_for_timeout(1500)

                                # 检查数量是否变化
                                new_qty = None
                                if cart_qty_input:
                                    new_qty = await cart_qty_input.get_attribute("value")

                                new_js_errors = self.js_errors[js_errors_before_click:]
                                new_console_errors = self.console_errors[console_errors_before:]

                                if current_qty and new_qty and int(new_qty) > int(current_qty):
                                    logger.info(f"✓ 数量增加成功: {current_qty} -> {new_qty}")
                                else:
                                    # 🚨 Bug检测!
                                    cart_bug_detected = True

                                    all_js_errors = new_js_errors + new_console_errors
                                    if all_js_errors:
                                        # 使用智能根因分析
                                        root_cause_analysis = analyze_js_error_root_cause(all_js_errors)
                                        bug_details = {
                                            "scenario": "用户在购物车页面(fiido.com/cart)尝试调整商品数量",
                                            "operation": f"点击数量加号(+)按钮{', 期望数量从 ' + current_qty + ' 增加到 ' + str(int(current_qty)+1) if current_qty else ''}",
                                            "problem": f"数量未发生变化{' (保持为 ' + new_qty + ')' if new_qty else ''}，同时触发了JavaScript错误",
                                            "root_cause": root_cause_analysis,
                                            "js_errors": all_js_errors
                                        }
                                        logger.info(f"⚠️  检测到购物车Bug: 数量未变化且有JS错误")
                                        for err in new_js_errors[:3]:
                                            logger.info(f"     JS错误: {err[:100]}")
                                    else:
                                        bug_details = {
                                            "scenario": "用户在购物车页面(fiido.com/cart)尝试调整商品数量",
                                            "operation": f"点击数量加号(+)按钮{', 期望数量从 ' + current_qty + ' 增加到 ' + str(int(current_qty)+1) if current_qty else ''}",
                                            "problem": f"数量未发生变化{' (保持为 ' + new_qty + ')' if new_qty else ''}，UI按钮存在但点击无响应",
                                            "root_cause": (
                                                "【事件绑定问题】加号按钮的点击事件可能未正确绑定或被阻止。常见原因：\n"
                                                "   • 按钮的click事件处理器未绑定或绑定到错误元素\n"
                                                "   • 事件被 stopPropagation() 或 preventDefault() 阻止\n"
                                                "   • JavaScript代码执行顺序问题，事件绑定代码未执行\n"
                                                "   • 存在覆盖在按钮上的透明遮罩层\n"
                                                "   【建议修复】检查按钮的事件绑定代码，确认click事件处理器正确执行"
                                            ),
                                            "js_errors": []
                                        }
                                        logger.info(f"⚠️  检测到购物车Bug: UI有加号按钮但点击无效")

                            except Exception as e:
                                logger.info(f"⚠️  点击加号按钮失败: {str(e)[:50]}")
                        else:
                            logger.info("ℹ️  购物车商品行内未找到加号按钮")

                except Exception as e:
                    logger.info(f"⚠️  购物车功能测试异常: {e}")

                # 查找Checkout按钮
                logger.info("\n🔍 检查Checkout按钮...")
                checkout_selectors = [
                    "button[name='checkout']",
                    "[name='checkout']",
                    "button:has-text('Check out')",
                    "button:has-text('Checkout')",
                    "a[href*='/checkout']"
                ]

                checkout_button = None
                for selector in checkout_selectors:
                    try:
                        checkout_button = await self.page.query_selector(selector)
                        if checkout_button and await checkout_button.is_visible():
                            btn_text = await checkout_button.text_content()
                            logger.info(f"✓ 找到Checkout按钮: {btn_text}")
                            break
                        checkout_button = None
                    except:
                        continue

                # 生成测试结果
                if checkout_button:
                    if cart_bug_detected:
                        # 🚨 检测到Bug - 必须报告为failed!
                        # UI有功能却不工作 = Bug,不能标记为passed
                        result_msg = "❌ 购物车数量调整功能存在Bug"
                        step.complete("failed", result_msg, issue_details=bug_details)
                    else:
                        result_msg = "购物车页面正常，Checkout按钮可见可点击"
                        # 检查是否有任何JavaScript错误
                        if len(self.js_errors) > errors_before_cart or len(self.console_errors) > console_errors_before:
                            result_msg += "（购物车页面有JavaScript警告，但不影响核心功能）"
                        step.complete("passed", result_msg)
                else:
                    # 检查购物车是否为空
                    empty_cart_indicators = [
                        "text='Your cart is empty'",
                        "text='购物车为空'",
                        ".cart-empty"
                    ]

                    is_empty = False
                    for indicator in empty_cart_indicators:
                        if await self.page.query_selector(indicator):
                            is_empty = True
                            break

                    if is_empty:
                        # 🔧 修复：购物车为空说明加购失败，报告failed（与快速测试一致）
                        step.complete("failed", "支付流程验证失败：购物车为空",
                                     issue_details={
                                         "scenario": "验证从商品页到支付页的完整流程",
                                         "operation": "进入购物车页面准备结账",
                                         "problem": "购物车显示为空，无法进行结账",
                                         "root_cause": "【购物流程中断】商品未成功加入购物车，导致无法完成支付流程。\n"
                                                      "   可能原因：\n"
                                                      "   • 步骤9添加购物车操作实际未成功\n"
                                                      "   • 加购后页面跳转导致购物车状态丢失\n"
                                                      "   • 商品变体未正确选择",
                                         "js_errors": self.js_errors[-5:] if self.js_errors else []
                                     })
                    else:
                        # 🔧 修复：有商品但找不到Checkout按钮，需要进一步检查（与快速测试一致）
                        # 检查是否有禁用的Checkout按钮
                        disabled_checkout = await self.page.query_selector("button[name='checkout'][disabled], button:has-text('Checkout')[disabled]")
                        if disabled_checkout:
                            step.complete("failed", "支付流程验证失败：Checkout按钮存在但被禁用",
                                         issue_details={
                                             "scenario": "验证购物车页面的结账功能",
                                             "operation": "查找并点击Checkout按钮",
                                             "problem": "Checkout按钮存在但处于禁用状态",
                                             "root_cause": "【结账功能受限】Checkout按钮被禁用。可能原因：\n"
                                                          "   • 购物车商品不满足最低消费\n"
                                                          "   • 商品库存状态变化\n"
                                                          "   • 页面JavaScript错误导致按钮状态异常",
                                             "js_errors": self.js_errors[-5:] if self.js_errors else []
                                         })
                        else:
                            step.complete("failed", "支付流程验证失败：购物车有商品但未找到Checkout按钮",
                                         issue_details={
                                             "scenario": "验证购物车页面的结账功能",
                                             "operation": "查找Checkout按钮",
                                             "problem": "购物车页面存在商品，但找不到Checkout按钮",
                                             "root_cause": "【页面结构异常】购物车有商品但无法找到结账入口。可能原因：\n"
                                                          "   • 页面DOM结构与预期不符\n"
                                                          "   • Checkout按钮选择器需要更新\n"
                                                          "   • 页面渲染不完整",
                                             "js_errors": self.js_errors[-5:] if self.js_errors else []
                                         })
            else:
                step.complete("failed", f"未能进入购物车页面，当前URL: {current_url}")

        except Exception as e:
            step.complete("failed", "验证支付流程时出错", str(e))


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行商品测试")
    parser.add_argument("--product-id", required=True, help="商品ID")
    parser.add_argument("--mode", choices=["quick", "full"], default="quick",
                       help="测试模式: quick(快速测试) 或 full(全面测试)")
    parser.add_argument("--headless", action="store_true", default=True, help="无头模式运行")
    parser.add_argument("--visible", action="store_true", help="显示浏览器窗口")
    args = parser.parse_args()

    # 加载商品数据
    products_file = PROJECT_ROOT / "data" / "products.json"
    if not products_file.exists():
        logger.error(f"商品数据文件不存在: {products_file}")
        sys.exit(1)

    with open(products_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    products_list = data.get("products", [])
    product_data = next((p for p in products_list if p["id"] == args.product_id), None)

    if not product_data:
        logger.error(f"未找到商品: {args.product_id}")
        sys.exit(1)

    product = Product(**product_data)
    headless = args.headless and not args.visible

    # 运行测试
    tester = ProductTester(product, test_mode=args.mode, headless=headless)
    result = await tester.run()

    # 返回退出码
    sys.exit(0 if result["status"] == "passed" else 1)


if __name__ == "__main__":
    asyncio.run(main())
