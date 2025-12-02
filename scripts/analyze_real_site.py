#!/usr/bin/env python3
"""
分析 fiido.com 真实网站结构
"""

from playwright.sync_api import sync_playwright
import json

def analyze_product_page(page, url):
    """分析商品详情页"""
    print(f'\n{"="*60}')
    print(f'分析商品页面: {url}')
    print("="*60)

    page.goto(url, wait_until='domcontentloaded', timeout=60000)
    page.wait_for_timeout(5000)

    print(f'页面标题: {page.title()}')
    print(f'当前URL: {page.url}')

    # 分析关键元素
    analysis = {
        'url': url,
        'title': page.title(),
        'elements': {}
    }

    # 1. 商品标题
    print('\n1. 查找商品标题...')
    title_selectors = [
        'h1.product__title',
        'h1[class*="title"]',
        '.product-title',
        'h1',
    ]
    for sel in title_selectors:
        if page.locator(sel).count() > 0:
            title = page.locator(sel).first.text_content()
            print(f'   ✅ {sel}: {title[:50]}')
            analysis['elements']['title'] = {'selector': sel, 'text': title}
            break

    # 2. 价格
    print('\n2. 查找价格...')
    price_selectors = [
        '.price',
        '[class*="price"]',
        '.product__price',
        'span[data-price]',
    ]
    for sel in price_selectors:
        if page.locator(sel).count() > 0:
            price = page.locator(sel).first.text_content()
            print(f'   ✅ {sel}: {price[:50]}')
            analysis['elements']['price'] = {'selector': sel, 'text': price}
            break

    # 3. Add to Cart 按钮
    print('\n3. 查找 Add to Cart 按钮...')
    add_to_cart_selectors = [
        'button[name="add"]',
        'button:has-text("Add to cart")',
        'button:has-text("ADD TO CART")',
        'button.product-form__submit',
        'form[action*="cart"] button[type="submit"]',
        '#AddToCart',
        '[data-action="add-to-cart"]',
    ]

    for sel in add_to_cart_selectors:
        count = page.locator(sel).count()
        if count > 0:
            btn = page.locator(sel).first
            is_visible = btn.is_visible()
            is_enabled = btn.is_enabled()
            try:
                text = btn.text_content().strip()
            except:
                text = ''

            print(f'   {"✅" if is_visible else "⚠️"} {sel}:')
            print(f'      数量: {count}')
            print(f'      可见: {is_visible}')
            print(f'      启用: {is_enabled}')
            print(f'      文本: {text[:30]}')

            if is_visible:
                analysis['elements']['add_to_cart'] = {
                    'selector': sel,
                    'visible': is_visible,
                    'enabled': is_enabled,
                    'text': text
                }
                break

    # 4. 购物车图标/计数
    print('\n4. 查找购物车...')
    cart_selectors = [
        '.cart-icon',
        '[href="/cart"]',
        '[data-cart-count]',
        'a[href*="cart"]',
    ]
    for sel in cart_selectors:
        if page.locator(sel).count() > 0:
            print(f'   ✅ {sel}')
            analysis['elements']['cart_link'] = {'selector': sel}
            break

    # 5. 查找配置选项（如果有）
    print('\n5. 查找配置选项...')
    variant_selectors = [
        'select[name="id"]',
        'input[type="radio"][name*="option"]',
        '.product-form__input',
        'fieldset',
    ]
    for sel in variant_selectors:
        if page.locator(sel).count() > 0:
            print(f'   ✅ {sel}')
            analysis['elements']['variants'] = {'selector': sel}
            break

    # 截图
    screenshot_path = f'screenshots/analysis-{url.split("/")[-1]}.png'
    page.screenshot(path=screenshot_path, full_page=True)
    print(f'\n截图已保存: {screenshot_path}')

    return analysis


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 测试多个商品页面
        test_urls = [
            'https://fiido.com/products/fiido-c11',
            'https://fiido.com/products/fiido-d11',
            'https://fiido.com/products/fiido-m1-pro-fat-tire-electric-bike',
        ]

        results = []

        for url in test_urls:
            try:
                result = analyze_product_page(page, url)
                results.append(result)
            except Exception as e:
                print(f'\n❌ 分析 {url} 失败: {e}')

        # 保存分析结果
        with open('data/site-analysis.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print('\n' + '='*60)
        print('分析完成！结果已保存到: data/site-analysis.json')
        print('='*60)

        browser.close()


if __name__ == '__main__':
    main()
