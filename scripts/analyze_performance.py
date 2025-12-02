#!/usr/bin/env python3
"""
测试性能分析工具

分析测试执行时间，识别性能瓶颈，生成优化建议。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import argparse


class PerformanceAnalyzer:
    """测试性能分析器"""

    def __init__(self, results_file: str = "reports/test-results.json"):
        self.results_file = Path(results_file)
        self.results = self._load_results()

    def _load_results(self) -> Dict:
        """加载测试结果"""
        if not self.results_file.exists():
            print(f"❌ 测试结果文件不存在: {self.results_file}")
            return {}

        with open(self.results_file) as f:
            return json.load(f)

    def analyze(self) -> Dict:
        """
        分析测试性能

        Returns:
            性能分析报告
        """
        if not self.results:
            return {
                "status": "no_data",
                "message": "无测试数据"
            }

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_duration": self.results.get('duration', 0),
            "total_tests": self.results.get('total', 0),
            "avg_test_duration": 0,
            "slowest_tests": [],
            "performance_score": 0,
            "bottlenecks": [],
            "recommendations": []
        }

        # 计算平均测试时间
        if report['total_tests'] > 0:
            report['avg_test_duration'] = report['total_duration'] / report['total_tests']

        # 识别最慢的测试（如果有详细数据）
        if 'tests' in self.results:
            tests = self.results['tests']
            sorted_tests = sorted(
                tests,
                key=lambda x: x.get('duration', 0),
                reverse=True
            )
            report['slowest_tests'] = [
                {
                    'name': t.get('name', 'unknown'),
                    'duration': t.get('duration', 0),
                    'type': t.get('type', 'unknown')
                }
                for t in sorted_tests[:10]
            ]

        # 识别性能瓶颈
        report['bottlenecks'] = self._identify_bottlenecks(report)

        # 生成优化建议
        report['recommendations'] = self._generate_recommendations(report)

        # 计算性能评分 (0-100)
        report['performance_score'] = self._calculate_performance_score(report)

        return report

    def _identify_bottlenecks(self, report: Dict) -> List[Dict]:
        """识别性能瓶颈"""
        bottlenecks = []

        # 瓶颈1: 总执行时间过长
        total_duration = report['total_duration']
        if total_duration > 1800:  # 30分钟
            bottlenecks.append({
                "type": "long_total_duration",
                "severity": "high",
                "description": f"总执行时间过长: {total_duration:.1f}秒 (>{1800}秒)",
                "metric": total_duration
            })

        # 瓶颈2: 平均测试时间过长
        avg_duration = report['avg_test_duration']
        if avg_duration > 30:  # 30秒
            bottlenecks.append({
                "type": "slow_average_test",
                "severity": "medium",
                "description": f"平均测试时间过长: {avg_duration:.1f}秒/测试",
                "metric": avg_duration
            })

        # 瓶颈3: 存在超慢测试
        if report['slowest_tests']:
            slowest = report['slowest_tests'][0]
            if slowest['duration'] > 60:  # 1分钟
                bottlenecks.append({
                    "type": "very_slow_test",
                    "severity": "high",
                    "description": f"存在超慢测试: {slowest['name']} ({slowest['duration']:.1f}秒)",
                    "metric": slowest['duration'],
                    "test_name": slowest['name']
                })

        # 瓶颈4: E2E测试占比过高
        if report['slowest_tests']:
            e2e_count = sum(
                1 for t in report['slowest_tests'][:10]
                if 'e2e' in t.get('type', '').lower()
            )
            if e2e_count > 7:  # 前10个慢测试中有7个以上是E2E
                bottlenecks.append({
                    "type": "too_many_e2e_tests",
                    "severity": "medium",
                    "description": f"E2E测试占比过高: {e2e_count}/10 最慢测试",
                    "metric": e2e_count
                })

        return bottlenecks

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """生成优化建议"""
        recommendations = []

        bottleneck_types = {b['type'] for b in report['bottlenecks']}

        if 'long_total_duration' in bottleneck_types:
            recommendations.append(
                "🚀 增加并行测试 worker 数量: pytest -n auto (自动检测CPU核心数)"
            )
            recommendations.append(
                "📦 将测试按类型分组运行: 先运行单元测试，再运行集成/E2E测试"
            )

        if 'slow_average_test' in bottleneck_types:
            recommendations.append(
                "⚡ 优化测试中的等待时间，使用智能等待而非固定 sleep"
            )
            recommendations.append(
                "🔧 检查是否有不必要的页面加载，考虑使用 API 测试代替部分 E2E 测试"
            )

        if 'very_slow_test' in bottleneck_types:
            for b in report['bottlenecks']:
                if b['type'] == 'very_slow_test':
                    recommendations.append(
                        f"🐌 重构超慢测试: {b.get('test_name', 'unknown')} "
                        f"({b['metric']:.1f}秒 → 目标 <30秒)"
                    )

        if 'too_many_e2e_tests' in bottleneck_types:
            recommendations.append(
                "🎯 减少E2E测试覆盖范围，仅测试关键路径（Happy Path）"
            )
            recommendations.append(
                "🔄 将部分E2E测试转换为集成测试或API测试"
            )

        # 通用建议
        if not recommendations:
            recommendations.append("✅ 测试性能良好，继续保持当前优化策略")
            recommendations.append("💡 考虑启用测试缓存: pytest --cache-show")

        # 总是提供的建议
        recommendations.append(
            "📊 定期运行性能分析: python scripts/analyze_performance.py"
        )

        return recommendations

    def _calculate_performance_score(self, report: Dict) -> int:
        """
        计算性能评分 (0-100)

        评分标准:
        - 总时间 < 10分钟: 40分
        - 平均时间 < 10秒: 30分
        - 无严重瓶颈: 30分
        """
        score = 100

        # 根据总时间扣分
        total_duration = report['total_duration']
        if total_duration > 600:  # 10分钟
            score -= min(40, (total_duration - 600) / 30)  # 每超过30秒扣1分

        # 根据平均时间扣分
        avg_duration = report['avg_test_duration']
        if avg_duration > 10:
            score -= min(30, (avg_duration - 10) * 2)  # 每超过1秒扣2分

        # 根据瓶颈数量和严重程度扣分
        for bottleneck in report['bottlenecks']:
            if bottleneck['severity'] == 'high':
                score -= 15
            elif bottleneck['severity'] == 'medium':
                score -= 10
            else:
                score -= 5

        return max(0, int(score))

    def print_report(self, report: Dict):
        """打印性能分析报告"""
        print("\n⚡ 测试性能分析报告")
        print("=" * 60)

        # 性能评分
        score = report['performance_score']
        if score >= 80:
            score_emoji = "🟢"
            score_text = "优秀"
        elif score >= 60:
            score_emoji = "🟡"
            score_text = "良好"
        elif score >= 40:
            score_emoji = "🟠"
            score_text = "一般"
        else:
            score_emoji = "🔴"
            score_text = "需优化"

        print(f"\n{score_emoji} 性能评分: {score}/100 ({score_text})")

        # 基本统计
        print(f"\n📊 基本统计:")
        print(f"  总测试数: {report['total_tests']}")
        print(f"  总执行时间: {report['total_duration']:.1f}秒 ({report['total_duration']/60:.1f}分钟)")
        print(f"  平均测试时间: {report['avg_test_duration']:.2f}秒/测试")

        # 最慢的测试
        if report['slowest_tests']:
            print(f"\n🐌 最慢的10个测试:")
            for i, test in enumerate(report['slowest_tests'][:10], 1):
                print(f"  {i}. {test['name']}: {test['duration']:.1f}秒")

        # 性能瓶颈
        if report['bottlenecks']:
            print(f"\n⚠️  性能瓶颈:")
            for i, bottleneck in enumerate(report['bottlenecks'], 1):
                severity_icons = {
                    "high": "🔴",
                    "medium": "🟡",
                    "low": "🟢"
                }
                icon = severity_icons.get(bottleneck['severity'], "⚪")
                print(f"  {i}. {icon} [{bottleneck['severity'].upper()}] {bottleneck['description']}")

        # 优化建议
        if report['recommendations']:
            print(f"\n💡 优化建议:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")

        print("\n" + "=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试性能分析')
    parser.add_argument(
        '--results-file',
        default='reports/test-results.json',
        help='测试结果文件路径'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='输出 JSON 格式'
    )

    args = parser.parse_args()

    analyzer = PerformanceAnalyzer(results_file=args.results_file)
    report = analyzer.analyze()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        analyzer.print_report(report)

    # 根据性能评分返回退出码
    score = report.get('performance_score', 0)
    if score < 40:
        sys.exit(2)  # 性能差
    elif score < 60:
        sys.exit(1)  # 性能一般
    else:
        sys.exit(0)  # 性能良好


if __name__ == '__main__':
    main()
