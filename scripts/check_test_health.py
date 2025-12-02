#!/usr/bin/env python3
"""
测试健康检查脚本

分析测试历史记录，检测测试系统的健康状况，
识别趋势和潜在问题。
"""

import json
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta
from collections import defaultdict
import argparse


class TestHealthChecker:
    """测试健康检查器"""

    def __init__(self, history_file: str = "data/alert_history.json"):
        self.history_file = Path(history_file)
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """加载历史记录"""
        if not self.history_file.exists():
            print(f"⚠️ 历史记录文件不存在: {self.history_file}")
            return []

        with open(self.history_file) as f:
            return json.load(f)

    def check_health(self) -> Dict:
        """
        检查测试健康状况

        Returns:
            健康检查报告
        """
        if not self.history:
            return {
                "status": "unknown",
                "message": "无历史数据"
            }

        # 分析最近的数据
        recent_days = 7
        recent_records = self._get_recent_records(days=recent_days)

        if not recent_records:
            return {
                "status": "unknown",
                "message": f"最近 {recent_days} 天无测试数据"
            }

        report = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "period": f"最近 {recent_days} 天",
            "total_runs": len(recent_records),
            "metrics": self._calculate_metrics(recent_records),
            "trends": self._analyze_trends(recent_records),
            "issues": [],
            "recommendations": []
        }

        # 检测问题
        report["issues"] = self._detect_issues(report["metrics"], report["trends"])

        # 生成建议
        report["recommendations"] = self._generate_recommendations(report["issues"])

        # 确定整体健康状态
        report["status"] = self._determine_status(report["issues"])

        return report

    def _get_recent_records(self, days: int = 7) -> List[Dict]:
        """获取最近N天的记录"""
        cutoff = datetime.now() - timedelta(days=days)
        recent = []

        for record in self.history:
            timestamp = datetime.fromisoformat(record['timestamp'])
            if timestamp >= cutoff:
                recent.append(record)

        return recent

    def _calculate_metrics(self, records: List[Dict]) -> Dict:
        """计算关键指标"""
        if not records:
            return {}

        pass_rates = [r['pass_rate'] for r in records]
        failed_tests = [r['failed_tests'] for r in records]
        p0_failures = [r['p0_failures'] for r in records]
        alerts = [1 for r in records if r['alert_triggered']]

        return {
            "avg_pass_rate": sum(pass_rates) / len(pass_rates),
            "min_pass_rate": min(pass_rates),
            "max_pass_rate": max(pass_rates),
            "avg_failures": sum(failed_tests) / len(failed_tests),
            "max_failures": max(failed_tests),
            "total_p0_failures": sum(p0_failures),
            "alert_count": len(alerts),
            "alert_rate": len(alerts) / len(records) if records else 0,
            "runs_with_p0_failures": sum(1 for r in records if r['p0_failures'] > 0)
        }

    def _analyze_trends(self, records: List[Dict]) -> Dict:
        """分析趋势"""
        if len(records) < 2:
            return {"trend": "insufficient_data"}

        # 分前后两半进行对比
        mid = len(records) // 2
        first_half = records[:mid]
        second_half = records[mid:]

        first_avg = sum(r['pass_rate'] for r in first_half) / len(first_half)
        second_avg = sum(r['pass_rate'] for r in second_half) / len(second_half)

        change = second_avg - first_avg

        if abs(change) < 0.01:
            trend = "stable"
        elif change > 0:
            trend = "improving"
        else:
            trend = "degrading"

        return {
            "trend": trend,
            "change": change,
            "first_half_avg": first_avg,
            "second_half_avg": second_avg
        }

    def _detect_issues(self, metrics: Dict, trends: Dict) -> List[Dict]:
        """检测问题"""
        issues = []

        # 问题1: 平均通过率低
        if metrics.get('avg_pass_rate', 1) < 0.85:
            issues.append({
                "type": "low_pass_rate",
                "severity": "high",
                "description": f"平均通过率仅 {metrics['avg_pass_rate']:.1%}",
                "metric": metrics['avg_pass_rate']
            })

        # 问题2: 频繁告警
        if metrics.get('alert_rate', 0) > 0.3:
            issues.append({
                "type": "frequent_alerts",
                "severity": "medium",
                "description": f"告警率高达 {metrics['alert_rate']:.1%}",
                "metric": metrics['alert_rate']
            })

        # 问题3: P0 失败
        if metrics.get('total_p0_failures', 0) > 0:
            issues.append({
                "type": "p0_failures",
                "severity": "critical",
                "description": f"发生 {metrics['total_p0_failures']} 次 P0 核心失败",
                "metric": metrics['total_p0_failures']
            })

        # 问题4: 趋势恶化
        if trends.get('trend') == 'degrading':
            issues.append({
                "type": "degrading_trend",
                "severity": "medium",
                "description": f"测试质量趋势下降 {trends['change']:.1%}",
                "metric": trends['change']
            })

        # 问题5: 失败数量持续增加
        if metrics.get('avg_failures', 0) > 10:
            issues.append({
                "type": "high_failures",
                "severity": "high",
                "description": f"平均失败数量达到 {metrics['avg_failures']:.1f}",
                "metric": metrics['avg_failures']
            })

        return issues

    def _generate_recommendations(self, issues: List[Dict]) -> List[str]:
        """生成改进建议"""
        recommendations = []

        issue_types = {issue['type'] for issue in issues}

        if 'low_pass_rate' in issue_types:
            recommendations.append("🔧 建议优化测试用例，或修复失败的功能")

        if 'frequent_alerts' in issue_types:
            recommendations.append("📊 检查告警阈值设置是否过于敏感")

        if 'p0_failures' in issue_types:
            recommendations.append("🚨 立即修复 P0 核心功能，这影响关键业务流程")

        if 'degrading_trend' in issue_types:
            recommendations.append("📉 分析测试质量下降原因，可能是代码质量下降或测试环境不稳定")

        if 'high_failures' in issue_types:
            recommendations.append("🔍 审查失败最多的测试用例，考虑重构或删除不稳定的测试")

        if not recommendations:
            recommendations.append("✅ 测试系统运行健康，保持当前状态")

        return recommendations

    def _determine_status(self, issues: List[Dict]) -> str:
        """确定整体健康状态"""
        if not issues:
            return "healthy"

        severities = [issue['severity'] for issue in issues]

        if 'critical' in severities:
            return "critical"
        elif 'high' in severities:
            return "unhealthy"
        elif 'medium' in severities:
            return "warning"
        else:
            return "healthy"

    def print_report(self, report: Dict):
        """打印健康报告"""
        status_icons = {
            "healthy": "✅",
            "warning": "⚠️",
            "unhealthy": "❌",
            "critical": "🚨",
            "unknown": "❓"
        }

        icon = status_icons.get(report['status'], "❓")

        print(f"\n{icon} 测试系统健康报告")
        print(f"=" * 60)
        print(f"状态: {report['status'].upper()}")
        print(f"分析周期: {report.get('period', 'N/A')}")
        print(f"测试运行次数: {report.get('total_runs', 0)}")
        print(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 打印关键指标
        if report.get('metrics'):
            metrics = report['metrics']
            print("📊 关键指标:")
            print(f"  平均通过率: {metrics.get('avg_pass_rate', 0):.1%}")
            print(f"  通过率范围: {metrics.get('min_pass_rate', 0):.1%} - {metrics.get('max_pass_rate', 0):.1%}")
            print(f"  平均失败数: {metrics.get('avg_failures', 0):.1f}")
            print(f"  P0 失败次数: {metrics.get('total_p0_failures', 0)}")
            print(f"  告警率: {metrics.get('alert_rate', 0):.1%}")
            print()

        # 打印趋势
        if report.get('trends'):
            trends = report['trends']
            trend_icons = {
                "improving": "📈",
                "stable": "➡️",
                "degrading": "📉",
                "insufficient_data": "❓"
            }
            trend_icon = trend_icons.get(trends.get('trend'), "❓")

            print(f"📈 趋势分析: {trend_icon} {trends.get('trend', 'unknown').upper()}")
            if 'change' in trends:
                print(f"  变化: {trends['change']:+.1%}")
            print()

        # 打印问题
        if report.get('issues'):
            print("⚠️  发现的问题:")
            for i, issue in enumerate(report['issues'], 1):
                severity_icons = {
                    "critical": "🚨",
                    "high": "❌",
                    "medium": "⚠️",
                    "low": "ℹ️"
                }
                severity_icon = severity_icons.get(issue['severity'], "ℹ️")
                print(f"  {i}. {severity_icon} [{issue['severity'].upper()}] {issue['description']}")
            print()

        # 打印建议
        if report.get('recommendations'):
            print("💡 改进建议:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"  {i}. {rec}")
            print()

        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试系统健康检查')
    parser.add_argument(
        '--history-file',
        default='data/alert_history.json',
        help='历史记录文件路径'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='分析最近N天的数据'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='输出 JSON 格式'
    )

    args = parser.parse_args()

    checker = TestHealthChecker(history_file=args.history_file)
    report = checker.check_health()

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        checker.print_report(report)

    # 根据状态返回退出码
    status_codes = {
        "healthy": 0,
        "warning": 1,
        "unhealthy": 2,
        "critical": 3,
        "unknown": 0
    }

    sys.exit(status_codes.get(report['status'], 0))


if __name__ == '__main__':
    main()
