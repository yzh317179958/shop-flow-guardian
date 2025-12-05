#!/usr/bin/env python3
"""
通用 AI 测试报告生成器

支持多个 AI 提供商:
- DeepSeek (推荐，免费)
- 豆包/字节跳动
- Claude (需要付费 API)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class AIProvider:
    """AI 提供商基类"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_report(self, prompt: str) -> str:
        """生成报告 (由子类实现)"""
        raise NotImplementedError


class DeepSeekProvider(AIProvider):
    """DeepSeek AI 提供商 (免费，推荐)"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            print("✅ DeepSeek API 初始化成功")
        except ImportError:
            print("❌ 需要安装 openai 库: pip install openai")
            raise

    def generate_report(self, prompt: str, max_tokens: int = 4000) -> str:
        """使用 DeepSeek 生成报告"""
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个专业的软件测试工程师，擅长分析测试结果并提供深入的洞察。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.7,
            )

            return response.choices[0].message.content
        except Exception as e:
            print(f"❌ DeepSeek API 调用失败: {e}")
            raise


class UniversalAIReportGenerator:
    """通用 AI 报告生成器"""

    def __init__(self, provider: str = "deepseek", api_key: Optional[str] = None):
        """初始化 AI 报告生成器

        Args:
            provider: AI 提供商 (deepseek/claude)
            api_key: API 密钥 (如果未提供,从环境变量读取)
        """
        self.provider_name = provider.lower()

        # 根据提供商选择 API key 环境变量
        env_key_map = {
            "deepseek": "DEEPSEEK_API_KEY",
            "claude": "CLAUDE_API_KEY",
        }

        env_key = env_key_map.get(self.provider_name)
        self.api_key = api_key or os.getenv(env_key)

        if not self.api_key:
            raise ValueError(
                f"API key not found for {provider}. "
                f"Please set {env_key} environment variable or pass api_key parameter."
            )

        # 初始化提供商
        if self.provider_name == "deepseek":
            self.provider = DeepSeekProvider(self.api_key)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        print(f"✅ 使用 AI 提供商: {self.provider_name}")

    def load_test_results(self, results_path: str = "reports/test-results.json") -> Dict:
        """加载测试结果"""
        results_file = Path(results_path)

        if not results_file.exists():
            raise FileNotFoundError(f"Test results not found: {results_path}")

        with open(results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"✅ 已加载测试结果: {results_path}")
        return data

    def generate_report(self, test_results: Dict) -> str:
        """生成 AI 测试报告"""
        summary = test_results.get('summary', {})
        failures = test_results.get('failures', [])
        failures_by_product = test_results.get('failures_by_product', {})

        # 构建提示词
        prompt = self._build_report_prompt(summary, failures, failures_by_product)

        print("🤖 正在生成 AI 报告...")

        # 调用 AI 生成报告
        report = self.provider.generate_report(prompt)

        print("✅ AI 报告生成成功")

        return report

    def _build_report_prompt(
        self,
        summary: Dict,
        failures: List[Dict],
        failures_by_product: Dict,
    ) -> str:
        """构建报告提示词"""
        # 限制失败测试数量
        max_failures = 10
        failures_sample = failures[:max_failures]

        # 构建失败测试摘要
        failure_texts = []
        for f in failures_sample:
            failure_texts.append(
                f"- 测试: {f.get('test_name')}\n"
                f"  商品: {f.get('product_id', 'N/A')}\n"
                f"  错误: {f.get('error_message', 'Unknown')}"
            )

        prompt = f"""请分析以下 E2E 自动化测试结果并生成专业报告。

## 测试执行摘要

- 总测试数: {summary.get('total', 0)}
- 通过: {summary.get('passed', 0)}
- 失败: {summary.get('failed', 0)}
- 跳过: {summary.get('skipped', 0)}
- 通过率: {summary.get('pass_rate', 0)}%
- 执行时间: {summary.get('duration', 0):.2f} 秒

## 失败的测试 (前 {min(len(failures), max_failures)} 个)

{chr(10).join(failure_texts)}

## 按商品分组的失败数量

{json.dumps(dict(list(failures_by_product.items())[:5]), indent=2, ensure_ascii=False)}

---

请生成包含以下内容的测试报告:

### 1. 执行摘要
用 3-5 句话总结测试情况，包括通过率和主要发现。

### 2. 关键指标
以表格形式展示测试统计数据。

### 3. 失败分析
分析失败的测试，按优先级分类:
- **P0 严重问题** (阻塞核心流程)
- **P1 高优先级** (影响重要功能)
- **P2 一般问题** (次要功能)

对每个失败提供:
- 失败原因分析
- 影响范围
- 建议的修复方案

### 4. 趋势洞察
- 哪些商品/功能失败率高？
- 是否有共同的失败模式？
- 可能的根本原因

### 5. 行动建议
按优先级列出需要修复的问题和建议。

---

**要求**:
- 使用 Markdown 格式
- 专业简洁，技术准确
- 使用表格展示数据
- 使用适当的 emoji (✅ ❌ ⚠️ 📊)
- 中文输出
"""

        return prompt

    def generate_failure_summary(self, test_results: Dict) -> str:
        """生成失败摘要 (简短版本)"""
        summary = test_results.get('summary', {})
        failures = test_results.get('failures', [])

        if not failures:
            return "✅ 所有测试通过！"

        # 构建简短摘要
        failure_list = []
        for f in failures[:5]:
            failure_list.append(f"- {f.get('test_name')}: {f.get('error_message', 'Unknown')[:50]}")

        prompt = f"""请用 3-5 句话总结以下测试失败情况:

测试统计:
- 通过率: {summary.get('pass_rate', 0)}%
- 失败数量: {summary.get('failed', 0)} / {summary.get('total', 0)}

失败测试:
{chr(10).join(failure_list)}

请简洁说明:
1. 主要问题原因
2. 影响的功能
3. 修复建议

中文输出。"""

        return self.provider.generate_report(prompt, max_tokens=500)

    def save_report(
        self,
        report: str,
        output_path: str = "reports/latest-ai-report.md",
        report_id: Optional[str] = None,
    ):
        """保存报告到文件

        Args:
            report: AI生成的报告内容
            output_path: 输出路径
            report_id: 原始报告ID（用于保存JSON格式）
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # 如果输出路径是JSON格式（Web API调用），保存为JSON
        if output_path.endswith('.json'):
            json_data = {
                'analysis': report,
                'provider': self.provider_name,
                'created_at': datetime.now().isoformat(),
                'report_id': report_id,
            }
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            print(f"✅ AI分析报告已保存: {output_file}")
            return output_file

        # 否则保存为Markdown格式
        header = f"""# Fiido E2E 测试 AI 分析报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析引擎**: {self.provider_name.upper()}
**项目**: Fiido Shop Flow Guardian

---

"""

        full_report = header + report

        # 保存报告
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_report)

        print(f"✅ 报告已保存: {output_file}")

        return output_file


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='生成 AI 驱动的测试报告 (支持多个 AI 提供商)'
    )
    parser.add_argument(
        '--provider',
        default='deepseek',
        choices=['deepseek', 'claude'],
        help='AI 提供商 (默认: deepseek)'
    )
    parser.add_argument(
        '--results',
        default='reports/test-results.json',
        help='测试结果 JSON 文件路径'
    )
    parser.add_argument(
        '--report-id',
        help='报告ID (用于自动查找报告文件路径)'
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
        help='API 密钥 (可选,默认从环境变量读取)'
    )

    args = parser.parse_args()

    try:
        # 🔧 新增: 根据report-id自动查找报告文件
        results_path = args.results
        if args.report_id:
            results_path = find_report_file(args.report_id)
            if not results_path:
                print(f"❌ 未找到报告ID对应的文件: {args.report_id}")
                sys.exit(1)
            print(f"✅ 找到报告文件: {results_path}")

        # 创建 AI 报告生成器
        generator = UniversalAIReportGenerator(
            provider=args.provider,
            api_key=args.api_key
        )

        # 加载测试结果
        test_results = generator.load_test_results(results_path)

        # 生成报告
        if args.summary_only:
            print("\n📝 正在生成失败摘要...")
            report = generator.generate_failure_summary(test_results)
            print("\n" + "="*60)
            print(report)
            print("="*60 + "\n")
        else:
            print("\n📝 正在生成完整 AI 报告...")
            report = generator.generate_report(test_results)

            # 确定输出路径 - 如果有report_id,保存到对应位置
            if args.report_id:
                output_path = f"reports/{args.report_id}_ai_analysis.json"
            else:
                output_path = args.output

            # 保存报告
            saved_path = generator.save_report(report, output_path, args.report_id)

            print("\n" + "="*60)
            print("报告预览:")
            print("="*60)
            print(report[:800] + "...\n")
            print(f"📄 完整报告: {saved_path}")

        print("\n✅ AI 报告生成完成！")

    except ValueError as e:
        # API key 未配置的错误
        print(f"\n⚠️ 配置错误: {e}", file=sys.stderr)
        print("\n请参考以下步骤配置 API Key:")
        print("1. 复制 .env.example 为 .env")
        print("2. 在 .env 中设置 DEEPSEEK_API_KEY=你的密钥")
        print("3. 获取密钥: https://platform.deepseek.com/")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def find_report_file(report_id: str) -> Optional[str]:
    """根据报告ID查找对应的报告文件

    Args:
        report_id: 报告ID (如 batch_test_20251205_091054 或 test_20251205_091054)

    Returns:
        报告文件路径，如果未找到返回None
    """
    reports_dir = Path(__file__).parent.parent / "reports"

    # 尝试方式1: 直接作为JSON文件名
    json_file = reports_dir / f"{report_id}.json"
    if json_file.exists():
        return str(json_file)

    # 尝试方式2: 作为目录名，查找其中的test_results.json
    report_dir = reports_dir / report_id
    if report_dir.is_dir():
        results_file = report_dir / "test_results.json"
        if results_file.exists():
            return str(results_file)

    # 尝试方式3: 模糊匹配
    for f in reports_dir.glob(f"*{report_id}*"):
        if f.is_file() and f.suffix == '.json':
            return str(f)
        if f.is_dir():
            results_file = f / "test_results.json"
            if results_file.exists():
                return str(results_file)

    return None


if __name__ == '__main__':
    main()
