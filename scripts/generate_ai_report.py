#!/usr/bin/env python3
"""
AI 测试报告生成器

使用 Claude API 生成智能测试报告和失败分析。
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import anthropic

# 加载环境变量
load_dotenv()


class AIReportGenerator:
    """AI 报告生成器"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """初始化 AI 报告生成器

        Args:
            api_key: Claude API 密钥 (如果未提供,从环境变量读取)
            base_url: API 服务器地址 (如果未提供,从环境变量读取)
        """
        self.api_key = api_key or os.getenv('CLAUDE_API_KEY')
        self.base_url = base_url or os.getenv('CLAUDE_API_BASE_URL')

        if not self.api_key:
            raise ValueError(
                "Claude API key not found. "
                "Please set CLAUDE_API_KEY environment variable or pass api_key parameter."
            )

        # 创建客户端，如果有自定义 base_url 则使用
        if self.base_url:
            self.client = anthropic.Anthropic(
                api_key=self.api_key,
                base_url=self.base_url
            )
            print(f"✅ Claude API client initialized (base_url: {self.base_url})")
        else:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            print("✅ Claude API client initialized")

    def load_test_results(self, results_path: str = "reports/test-results.json") -> Dict:
        """加载测试结果

        Args:
            results_path: 测试结果 JSON 文件路径

        Returns:
            Dict: 测试结果数据
        """
        results_file = Path(results_path)

        if not results_file.exists():
            raise FileNotFoundError(f"Test results not found: {results_path}")

        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✅ Loaded test results from {results_path}")
        return data

    def generate_report(
        self,
        test_results: Dict,
        include_screenshots: bool = False,
    ) -> str:
        """生成 AI 测试报告

        Args:
            test_results: 测试结果数据
            include_screenshots: 是否包含截图分析

        Returns:
            str: Markdown 格式的测试报告
        """
        summary = test_results.get('summary', {})
        failures = test_results.get('failures', [])
        failures_by_product = test_results.get('failures_by_product', {})

        # 构建 Claude 提示词
        prompt = self._build_report_prompt(summary, failures, failures_by_product)

        print("🤖 Generating AI report with Claude...")

        # 调用 Claude API
        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        report = message.content[0].text

        print("✅ AI report generated successfully")

        return report

    def _build_report_prompt(
        self,
        summary: Dict,
        failures: List[Dict],
        failures_by_product: Dict,
    ) -> str:
        """构建 Claude 提示词

        Args:
            summary: 测试摘要
            failures: 失败测试列表
            failures_by_product: 按商品分组的失败测试

        Returns:
            str: Claude 提示词
        """
        # 限制失败测试数量 (避免超过 token 限制)
        max_failures = 15
        failures_sample = failures[:max_failures]

        prompt = f"""你是 Fiido 电商网站的 QA 专家。请分析以下 E2E 自动化测试结果并生成专业报告。

## 测试执行摘要

```json
{json.dumps(summary, indent=2, ensure_ascii=False)}
```

## 失败的测试 (显示前 {min(len(failures), max_failures)} 个)

```json
{json.dumps(failures_sample, indent=2, ensure_ascii=False)}
```

## 按商品分组的失败统计

```json
{json.dumps(failures_by_product, indent=2, ensure_ascii=False)}
```

---

请生成包含以下内容的专业测试报告：

### 1. 执行摘要 (Executive Summary)
- 用 3-5 句话总结本次测试执行情况
- 突出显示通过率、关键问题数量
- 说明测试覆盖范围

### 2. 关键指标 (Key Metrics)
- 总测试数
- 通过/失败/跳过数量
- 通过率
- 执行时间

### 3. 失败分析 (Failure Analysis)

按优先级分类失败:
- **P0 严重问题** (阻塞核心流程)
- **P1 高优先级问题** (影响重要功能)
- **P2 一般问题** (次要功能问题)

对每个失败提供:
- 测试名称
- 失败原因 (从 error_message 分析)
- 影响范围 (影响哪些商品/功能)
- 可能的根本原因
- 建议修复方案

### 4. 趋势洞察 (Trend Insights)
- 哪些商品分类失败率高?
- 是否有共同的失败模式?
- 是否有特定的功能区域问题?

### 5. 行动建议 (Action Items)
- 按优先级列出需要修复的问题
- 建议的调查方向
- 需要关注的区域

### 6. 结论 (Conclusion)
- 总体评价
- 下一步建议

---

**要求**:
- 使用 Markdown 格式
- 清晰简洁,技术准确
- 使用表格展示数据 (如果合适)
- 使用 emoji 增强可读性 (如: ✅ ❌ ⚠️ 📊 🔍)
- 专业的 QA 语气
- 中文输出
"""

        return prompt

    def save_report(
        self,
        report: str,
        output_path: str = "reports/latest-ai-report.md",
    ):
        """保存报告到文件

        Args:
            report: 报告内容
            output_path: 输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 添加报告头部
        header = f"""# Fiido E2E 测试 AI 分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析引擎**: Claude Sonnet 4.5
**项目**: Fiido Shop Flow Guardian

---

"""

        full_report = header + report

        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_report)

        print(f"✅ Report saved to {output_file}")

        return output_file

    def generate_failure_summary(self, test_results: Dict) -> str:
        """生成失败摘要 (简短版本)

        Args:
            test_results: 测试结果数据

        Returns:
            str: 失败摘要文本
        """
        summary = test_results.get('summary', {})
        failures = test_results.get('failures', [])

        if not failures:
            return "✅ 所有测试通过！"

        # 构建简短提示词
        failure_summary_text = []
        for f in failures[:5]:
            failure_summary_text.append(f"- {f.get('test_name')}: {f.get('error_message', 'Unknown')}")

        prompt = f"""作为测试工程师，请分析以下自动化测试结果:

测试统计:
- 通过率: {summary.get('pass_rate', 0)}%
- 失败数量: {summary.get('failed', 0)}
- 总测试数: {summary.get('total', 0)}

失败的测试:
{chr(10).join(failure_summary_text)}

请用3-5句话总结:
1. 主要问题原因
2. 影响的功能
3. 修复建议

用中文回答。"""

        message = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return message.content[0].text


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='生成 AI 驱动的测试报告'
    )
    parser.add_argument(
        '--results',
        default='reports/test-results.json',
        help='测试结果 JSON 文件路径'
    )
    parser.add_argument(
        '--output',
        default='reports/latest-ai-report.md',
        help='输出报告路径'
    )
    parser.add_argument(
        '--summary-only',
        action='store_true',
        help='仅生成简短摘要'
    )
    parser.add_argument(
        '--api-key',
        help='Claude API 密钥 (可选,默认从环境变量读取)'
    )
    parser.add_argument(
        '--base-url',
        help='Claude API 服务器地址 (可选,默认从环境变量读取)'
    )

    args = parser.parse_args()

    try:
        # 创建 AI 报告生成器
        generator = AIReportGenerator(api_key=args.api_key, base_url=args.base_url)

        # 加载测试结果
        test_results = generator.load_test_results(args.results)

        # 生成报告
        if args.summary_only:
            print("\n📝 Generating failure summary...")
            report = generator.generate_failure_summary(test_results)
            print("\n" + "="*60)
            print(report)
            print("="*60 + "\n")
        else:
            print("\n📝 Generating full AI report...")
            report = generator.generate_report(test_results)

            # 保存报告
            output_path = generator.save_report(report, args.output)

            print("\n" + "="*60)
            print("Report Preview:")
            print("="*60)
            print(report[:500] + "...\n")
            print(f"📄 Full report: {output_path}")

        print("\n✅ AI report generation completed!")

    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
