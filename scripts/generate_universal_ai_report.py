#!/usr/bin/env python3
"""
通用 AI 测试报告生成器

支持多个 AI 提供商:
- DeepSeek (推荐，免费)
- 豆包/字节跳动
- Claude (需要付费 API)

版本: v2.0.0 - 使用 Lyra 优化的专家级提示词
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

# 系统提示词文件路径
SYSTEM_PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "fiido_test_analyst_system_prompt.md"


def load_system_prompt() -> str:
    """加载系统提示词文件

    Returns:
        系统提示词内容
    """
    if SYSTEM_PROMPT_FILE.exists():
        with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            # 移除文件开头的元信息注释（版本、日期等）
            # 找到第一个 "# 角色定义" 开始的位置
            role_start = content.find("# 角色定义")
            if role_start > 0:
                content = content[role_start:]
            return content
    else:
        # 降级到简单提示词
        print(f"⚠️ 系统提示词文件不存在: {SYSTEM_PROMPT_FILE}")
        print("  使用简化版提示词")
        return """你是一个专业的Fiido电商测试分析专家，擅长分析测试结果并提供深入的业务洞察。
请用中文输出，使用Markdown格式，包含表格、emoji和清晰的结构。
重点关注：1) 区分真正的Bug和功能缺失 2) 从用户和业务角度分析影响 3) 给出可执行的修复建议。"""


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
        self.system_prompt = load_system_prompt()
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com"
            )
            print("✅ DeepSeek API 初始化成功")
            print(f"✅ 系统提示词已加载 ({len(self.system_prompt)} 字符)")
        except ImportError:
            print("❌ 需要安装 openai 库: pip install openai")
            raise

    def generate_report(self, prompt: str, max_tokens: int = 8000) -> str:
        """使用 DeepSeek 生成报告

        Args:
            prompt: 用户消息（测试数据）
            max_tokens: 最大输出token数（增加到8000以支持详细报告）

        Returns:
            AI生成的分析报告
        """
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
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
        """生成 AI 测试报告

        Args:
            test_results: 完整的测试结果数据

        Returns:
            AI生成的分析报告
        """
        summary = test_results.get('summary', {})
        failures = test_results.get('failures', [])
        failures_by_product = test_results.get('failures_by_product', {})

        # 构建提示词 - 传递完整测试数据
        prompt = self._build_report_prompt(
            summary, failures, failures_by_product,
            test_results=test_results  # 传递完整数据
        )

        print("🤖 正在生成 AI 报告...")
        print(f"   提示词长度: {len(prompt)} 字符")

        # 调用 AI 生成报告
        report = self.provider.generate_report(prompt)

        print("✅ AI 报告生成成功")

        return report

    def _build_report_prompt(
        self,
        summary: Dict,
        failures: List[Dict],
        failures_by_product: Dict,
        test_results: Optional[Dict] = None,
    ) -> str:
        """构建报告提示词 - 传递完整测试数据供AI分析

        Args:
            summary: 测试摘要统计
            failures: 失败列表（兼容旧格式）
            failures_by_product: 按商品分组的失败（兼容旧格式）
            test_results: 完整的测试结果数据（新格式优先）

        Returns:
            用户消息提示词
        """
        # 如果有完整的测试结果数据，优先使用
        if test_results:
            # 构建符合新提示词期望的JSON数据
            test_data = {
                "test_id": test_results.get("id", test_results.get("test_id", "unknown")),
                "timestamp": test_results.get("timestamp", datetime.now().isoformat()),
                "test_mode": test_results.get("test_mode", "unknown"),
                "test_scope": test_results.get("test_scope", ""),
                "summary": {
                    "total": summary.get("total", 0),
                    "passed": summary.get("passed", 0),
                    "failed": summary.get("failed", 0),
                    "skipped": summary.get("skipped", 0),
                    "pass_rate": summary.get("pass_rate", 0),
                    "duration": summary.get("duration", 0)
                },
                "products": []
            }

            # 添加商品详情
            products = test_results.get("products", test_results.get("tests", []))
            for product in products:
                product_data = {
                    "product_id": product.get("product_id", "unknown"),
                    "product_name": product.get("product_name", product.get("name", "unknown")),
                    "status": product.get("status", "unknown"),
                    "steps": []
                }

                # 添加测试步骤
                steps = product.get("steps", [])
                for step in steps:
                    step_data = {
                        "number": step.get("number", 0),
                        "name": step.get("name", ""),
                        "status": step.get("status", ""),
                        "message": step.get("result", step.get("message", "")),
                    }
                    # 添加问题详情（如果有）
                    if step.get("issue_details"):
                        step_data["issue_details"] = step["issue_details"]
                    if step.get("error"):
                        step_data["error"] = step["error"]

                    product_data["steps"].append(step_data)

                test_data["products"].append(product_data)

            # 提取JS错误
            js_errors = test_results.get("js_errors_captured", [])
            if js_errors:
                test_data["js_errors_captured"] = js_errors

            prompt = f"""请分析以下Fiido电商网站的自动化测试结果，并生成专业的分析报告。

## 测试数据

```json
{json.dumps(test_data, ensure_ascii=False, indent=2)}
```

请严格按照系统提示词中定义的报告格式输出分析报告。重点关注：
1. 区分真正的Bug（failed）和功能缺失（skipped）
2. 从用户和业务角度分析问题影响
3. 给出具体可执行的修复建议
4. 识别问题之间的关联和系统性模式
"""
            return prompt

        # 兼容旧格式：从failures构建提示词
        max_failures = 10
        failures_sample = failures[:max_failures]

        failure_texts = []
        for f in failures_sample:
            failure_texts.append(
                f"- 测试: {f.get('test_name')}\n"
                f"  商品: {f.get('product_id', 'N/A')}\n"
                f"  错误: {f.get('error_message', 'Unknown')}"
            )

        prompt = f"""请分析以下Fiido电商网站的自动化测试结果，并生成专业的分析报告。

## 测试执行摘要

- 总测试数: {summary.get('total', 0)}
- 通过: {summary.get('passed', 0)}
- 失败: {summary.get('failed', 0)}
- 跳过: {summary.get('skipped', 0)}
- 通过率: {summary.get('pass_rate', 0)}%
- 执行时间: {summary.get('duration', 0):.2f} 秒

## 失败的测试 (前 {min(len(failures), max_failures)} 个)

{chr(10).join(failure_texts) if failure_texts else "无失败测试"}

## 按商品分组的失败数量

{json.dumps(dict(list(failures_by_product.items())[:5]), indent=2, ensure_ascii=False) if failures_by_product else "{}"}

请严格按照系统提示词中定义的报告格式输出分析报告。
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
