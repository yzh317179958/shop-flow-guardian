#!/usr/bin/env python3
"""
历史趋势分析工具

分析过去 30 天的测试数据，生成趋势报告：
- 测试通过率趋势
- 高频失败用例排行
- 不同地区的测试成功率对比
- 性能指标趋势
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import argparse


class TrendAnalyzer:
    """历史趋势分析器"""

    def __init__(
        self,
        reports_dir: str = "reports",
        days: int = 30,
        output_file: str = "reports/trend_analysis.json"
    ):
        """
        初始化趋势分析器

        Args:
            reports_dir: 测试报告目录
            days: 分析的天数
            output_file: 输出文件路径
        """
        self.reports_dir = Path(reports_dir)
        self.days = days
        self.output_file = Path(output_file)

    def _load_test_reports(self) -> List[Dict]:
        """
        加载测试报告

        Returns:
            测试报告列表，按时间排序
        """
        reports = []

        # 加载最近 N 天的报告
        cutoff_date = datetime.now() - timedelta(days=self.days)

        # 查找所有测试结果文件
        result_files = list(self.reports_dir.glob("**/test_results.json"))

        for result_file in result_files:
            try:
                with open(result_file) as f:
                    data = json.load(f)

                # 解析时间戳
                timestamp_str = data.get('timestamp', '')
                if timestamp_str:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

                    # 只保留最近 N 天的数据
                    if timestamp >= cutoff_date:
                        reports.append({
                            'timestamp': timestamp,
                            'data': data
                        })
            except (json.JSONDecodeError, ValueError) as e:
                print(f"⚠️ 跳过无效报告: {result_file} ({e})")
                continue

        # 按时间排序
        reports.sort(key=lambda x: x['timestamp'])

        return reports

    def _calculate_pass_rate_trend(self, reports: List[Dict]) -> Dict:
        """
        计算测试通过率趋势

        Args:
            reports: 测试报告列表

        Returns:
            通过率趋势数据
        """
        daily_stats = defaultdict(lambda: {'passed': 0, 'failed': 0, 'total': 0})

        for report in reports:
            date = report['timestamp'].date()
            data = report['data']

            summary = data.get('summary', {})
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)

            daily_stats[date]['passed'] += passed
            daily_stats[date]['failed'] += failed
            daily_stats[date]['total'] += passed + failed

        # 计算每日通过率
        trend_data = []
        for date in sorted(daily_stats.keys()):
            stats = daily_stats[date]
            pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0

            trend_data.append({
                'date': date.isoformat(),
                'passed': stats['passed'],
                'failed': stats['failed'],
                'total': stats['total'],
                'pass_rate': round(pass_rate, 2)
            })

        # 计算统计信息
        pass_rates = [d['pass_rate'] for d in trend_data]

        return {
            'data': trend_data,
            'statistics': {
                'average_pass_rate': round(statistics.mean(pass_rates), 2) if pass_rates else 0,
                'min_pass_rate': min(pass_rates) if pass_rates else 0,
                'max_pass_rate': max(pass_rates) if pass_rates else 0,
                'std_deviation': round(statistics.stdev(pass_rates), 2) if len(pass_rates) > 1 else 0,
                'trend': self._calculate_trend(pass_rates)
            }
        }

    def _calculate_trend(self, values: List[float]) -> str:
        """
        计算趋势方向

        Args:
            values: 数值列表

        Returns:
            趋势描述: 'improving', 'stable', 'declining'
        """
        if not values or len(values) < 2:
            return 'stable'

        # 计算前半和后半的平均值
        mid = len(values) // 2
        first_half_avg = statistics.mean(values[:mid])
        second_half_avg = statistics.mean(values[mid:])

        diff = second_half_avg - first_half_avg

        if diff > 2:  # 提升超过 2%
            return 'improving'
        elif diff < -2:  # 下降超过 2%
            return 'declining'
        else:
            return 'stable'

    def _analyze_frequent_failures(self, reports: List[Dict]) -> Dict:
        """
        分析高频失败用例

        Args:
            reports: 测试报告列表

        Returns:
            高频失败分析数据
        """
        failure_counter = Counter()
        failure_details = defaultdict(lambda: {
            'count': 0,
            'product_name': '',
            'error_types': Counter(),
            'first_seen': None,
            'last_seen': None
        })

        for report in reports:
            data = report['data']
            timestamp = report['timestamp']

            # 统计失败的测试
            for test in data.get('tests', []):
                if test.get('status') == 'failed':
                    product_id = test.get('product_id', 'unknown')
                    error_type = test.get('error_type', 'unknown')

                    failure_counter[product_id] += 1

                    # 记录详细信息
                    details = failure_details[product_id]
                    details['count'] += 1
                    details['product_name'] = test.get('product_name', product_id)
                    details['error_types'][error_type] += 1

                    if details['first_seen'] is None:
                        details['first_seen'] = timestamp
                    details['last_seen'] = timestamp

        # 生成排行榜
        top_failures = []
        for product_id, count in failure_counter.most_common(20):
            details = failure_details[product_id]

            # 计算失败天数
            if details['first_seen'] and details['last_seen']:
                failure_days = (details['last_seen'] - details['first_seen']).days + 1
            else:
                failure_days = 1

            # 主要错误类型
            main_error_type = details['error_types'].most_common(1)[0][0] if details['error_types'] else 'unknown'

            top_failures.append({
                'product_id': product_id,
                'product_name': details['product_name'],
                'failure_count': count,
                'failure_days': failure_days,
                'main_error_type': main_error_type,
                'error_types': dict(details['error_types']),
                'first_seen': details['first_seen'].isoformat() if details['first_seen'] else None,
                'last_seen': details['last_seen'].isoformat() if details['last_seen'] else None
            })

        return {
            'total_unique_failures': len(failure_counter),
            'top_failures': top_failures
        }

    def _analyze_regional_performance(self, reports: List[Dict]) -> Dict:
        """
        分析不同地区的测试成功率

        Args:
            reports: 测试报告列表

        Returns:
            地区性能分析数据
        """
        regional_stats = defaultdict(lambda: {'passed': 0, 'failed': 0, 'total': 0})

        for report in reports:
            data = report['data']

            # 统计每个地区的测试结果
            for test in data.get('tests', []):
                region = test.get('region', 'unknown')
                status = test.get('status', 'unknown')

                regional_stats[region]['total'] += 1

                if status == 'passed':
                    regional_stats[region]['passed'] += 1
                elif status == 'failed':
                    regional_stats[region]['failed'] += 1

        # 计算每个地区的成功率
        regional_performance = []
        for region, stats in regional_stats.items():
            pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0

            regional_performance.append({
                'region': region,
                'total_tests': stats['total'],
                'passed': stats['passed'],
                'failed': stats['failed'],
                'pass_rate': round(pass_rate, 2)
            })

        # 按通过率排序
        regional_performance.sort(key=lambda x: x['pass_rate'], reverse=True)

        return {
            'total_regions': len(regional_performance),
            'regions': regional_performance
        }

    def _analyze_performance_trends(self, reports: List[Dict]) -> Dict:
        """
        分析性能指标趋势

        Args:
            reports: 测试报告列表

        Returns:
            性能趋势数据
        """
        daily_performance = defaultdict(lambda: {
            'page_load_times': [],
            'api_response_times': []
        })

        for report in reports:
            date = report['timestamp'].date()
            data = report['data']

            # 收集性能数据
            for test in data.get('tests', []):
                metrics = test.get('metrics', {})

                page_load_time = metrics.get('page_load_time')
                if page_load_time:
                    daily_performance[date]['page_load_times'].append(page_load_time)

                api_response_time = metrics.get('api_response_time')
                if api_response_time:
                    daily_performance[date]['api_response_times'].append(api_response_time)

        # 计算每日平均性能
        performance_data = []
        for date in sorted(daily_performance.keys()):
            perf = daily_performance[date]

            avg_page_load = statistics.mean(perf['page_load_times']) if perf['page_load_times'] else 0
            avg_api_response = statistics.mean(perf['api_response_times']) if perf['api_response_times'] else 0

            performance_data.append({
                'date': date.isoformat(),
                'avg_page_load_time': round(avg_page_load, 2),
                'avg_api_response_time': round(avg_api_response, 2),
                'test_count': len(perf['page_load_times'])
            })

        # 计算趋势
        page_load_times = [d['avg_page_load_time'] for d in performance_data if d['avg_page_load_time'] > 0]
        api_response_times = [d['avg_api_response_time'] for d in performance_data if d['avg_api_response_time'] > 0]

        return {
            'data': performance_data,
            'statistics': {
                'avg_page_load_time': round(statistics.mean(page_load_times), 2) if page_load_times else 0,
                'avg_api_response_time': round(statistics.mean(api_response_times), 2) if api_response_times else 0,
                'page_load_trend': self._calculate_trend(page_load_times) if page_load_times else 'stable',
                'api_response_trend': self._calculate_trend(api_response_times) if api_response_times else 'stable'
            }
        }

    def _identify_periodic_issues(self, reports: List[Dict]) -> Dict:
        """
        识别周期性问题

        Args:
            reports: 测试报告列表

        Returns:
            周期性问题分析
        """
        # 按星期几统计失败率
        weekday_stats = defaultdict(lambda: {'passed': 0, 'failed': 0, 'total': 0})

        for report in reports:
            weekday = report['timestamp'].strftime('%A')  # Monday, Tuesday, etc.
            data = report['data']

            summary = data.get('summary', {})
            passed = summary.get('passed', 0)
            failed = summary.get('failed', 0)

            weekday_stats[weekday]['passed'] += passed
            weekday_stats[weekday]['failed'] += failed
            weekday_stats[weekday]['total'] += passed + failed

        # 计算每个星期的失败率
        weekday_performance = []
        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        for weekday in weekday_order:
            if weekday in weekday_stats:
                stats = weekday_stats[weekday]
                failure_rate = (stats['failed'] / stats['total'] * 100) if stats['total'] > 0 else 0

                weekday_performance.append({
                    'weekday': weekday,
                    'total_tests': stats['total'],
                    'failed': stats['failed'],
                    'failure_rate': round(failure_rate, 2)
                })

        # 找出失败率最高的日子
        highest_failure_day = max(weekday_performance, key=lambda x: x['failure_rate']) if weekday_performance else None

        return {
            'weekday_performance': weekday_performance,
            'highest_failure_day': highest_failure_day
        }

    def analyze(self) -> Dict:
        """
        执行完整的趋势分析

        Returns:
            趋势分析报告
        """
        print(f"📊 正在分析过去 {self.days} 天的测试数据...")

        # 加载测试报告
        reports = self._load_test_reports()

        if not reports:
            print("⚠️ 未找到测试报告数据")
            return {
                'error': 'No test reports found',
                'reports_dir': str(self.reports_dir),
                'days': self.days
            }

        print(f"✅ 已加载 {len(reports)} 个测试报告")

        # 执行各项分析
        print("🔍 分析测试通过率趋势...")
        pass_rate_trend = self._calculate_pass_rate_trend(reports)

        print("🔍 分析高频失败用例...")
        frequent_failures = self._analyze_frequent_failures(reports)

        print("🔍 分析地区性能...")
        regional_performance = self._analyze_regional_performance(reports)

        print("🔍 分析性能趋势...")
        performance_trends = self._analyze_performance_trends(reports)

        print("🔍 识别周期性问题...")
        periodic_issues = self._identify_periodic_issues(reports)

        # 生成综合报告
        report = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period': {
                'days': self.days,
                'start_date': reports[0]['timestamp'].isoformat() if reports else None,
                'end_date': reports[-1]['timestamp'].isoformat() if reports else None,
                'total_reports': len(reports)
            },
            'pass_rate_trend': pass_rate_trend,
            'frequent_failures': frequent_failures,
            'regional_performance': regional_performance,
            'performance_trends': performance_trends,
            'periodic_issues': periodic_issues,
            'insights': self._generate_insights(
                pass_rate_trend,
                frequent_failures,
                regional_performance,
                performance_trends,
                periodic_issues
            )
        }

        return report

    def _generate_insights(
        self,
        pass_rate_trend: Dict,
        frequent_failures: Dict,
        regional_performance: Dict,
        performance_trends: Dict,
        periodic_issues: Dict
    ) -> List[Dict]:
        """
        生成洞察建议

        Args:
            pass_rate_trend: 通过率趋势
            frequent_failures: 高频失败
            regional_performance: 地区性能
            performance_trends: 性能趋势
            periodic_issues: 周期性问题

        Returns:
            洞察列表
        """
        insights = []

        # 1. 通过率趋势洞察
        trend = pass_rate_trend['statistics']['trend']
        avg_pass_rate = pass_rate_trend['statistics']['average_pass_rate']

        if trend == 'improving':
            insights.append({
                'type': 'positive',
                'category': 'pass_rate',
                'message': f'测试通过率呈上升趋势，平均通过率 {avg_pass_rate}%',
                'priority': 'info'
            })
        elif trend == 'declining':
            insights.append({
                'type': 'warning',
                'category': 'pass_rate',
                'message': f'测试通过率呈下降趋势，平均通过率 {avg_pass_rate}%，需要关注',
                'priority': 'high'
            })

        if avg_pass_rate < 90:
            insights.append({
                'type': 'warning',
                'category': 'pass_rate',
                'message': f'平均通过率 {avg_pass_rate}% 低于目标值 90%',
                'priority': 'high'
            })

        # 2. 高频失败洞察
        top_failures = frequent_failures.get('top_failures', [])
        if top_failures:
            top_failure = top_failures[0]
            insights.append({
                'type': 'action_required',
                'category': 'frequent_failures',
                'message': f'最高频失败商品: {top_failure["product_name"]} ({top_failure["failure_count"]} 次失败)',
                'data': top_failure,
                'priority': 'high'
            })

            # 检查是否有长期存在的问题
            chronic_failures = [f for f in top_failures if f['failure_days'] > 7]
            if chronic_failures:
                insights.append({
                    'type': 'warning',
                    'category': 'frequent_failures',
                    'message': f'{len(chronic_failures)} 个商品存在持续 7 天以上的失败问题',
                    'priority': 'high'
                })

        # 3. 地区性能洞察
        regions = regional_performance.get('regions', [])
        if regions:
            # 找出低通过率地区
            low_pass_regions = [r for r in regions if r['pass_rate'] < 90]
            if low_pass_regions:
                insights.append({
                    'type': 'action_required',
                    'category': 'regional',
                    'message': f'{len(low_pass_regions)} 个地区通过率低于 90%: {", ".join([r["region"] for r in low_pass_regions[:3]])}',
                    'priority': 'medium'
                })

        # 4. 性能趋势洞察
        perf_stats = performance_trends.get('statistics', {})
        page_load_trend = perf_stats.get('page_load_trend', 'stable')
        avg_page_load = perf_stats.get('avg_page_load_time', 0)

        if page_load_trend == 'declining':  # 性能下降（加载时间增加）
            insights.append({
                'type': 'warning',
                'category': 'performance',
                'message': f'页面加载时间呈上升趋势，平均 {avg_page_load}s，需要优化',
                'priority': 'medium'
            })

        if avg_page_load > 3:
            insights.append({
                'type': 'action_required',
                'category': 'performance',
                'message': f'平均页面加载时间 {avg_page_load}s 超过 3 秒阈值',
                'priority': 'medium'
            })

        # 5. 周期性问题洞察
        highest_failure_day = periodic_issues.get('highest_failure_day')
        if highest_failure_day and highest_failure_day['failure_rate'] > 10:
            insights.append({
                'type': 'warning',
                'category': 'periodic',
                'message': f'每周 {highest_failure_day["weekday"]} 失败率最高 ({highest_failure_day["failure_rate"]}%)，建议避免在该时间部署',
                'priority': 'medium'
            })

        return insights

    def save_report(self, report: Dict):
        """
        保存趋势分析报告

        Args:
            report: 趋势分析报告
        """
        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"💾 趋势分析报告已保存: {self.output_file}")

    def print_report(self, report: Dict):
        """
        打印趋势分析报告摘要

        Args:
            report: 趋势分析报告
        """
        print("\n" + "=" * 70)
        print("📈 历史趋势分析报告")
        print("=" * 70)

        # 分析周期
        period = report['analysis_period']
        print(f"\n📅 分析周期: {period['days']} 天 ({period['total_reports']} 个报告)")

        # 通过率趋势
        pass_rate = report['pass_rate_trend']['statistics']
        trend_emoji = {
            'improving': '📈',
            'stable': '➡️',
            'declining': '📉'
        }
        print(f"\n✅ 测试通过率:")
        print(f"  平均通过率: {pass_rate['average_pass_rate']}%")
        print(f"  趋势: {trend_emoji.get(pass_rate['trend'], '➡️')} {pass_rate['trend']}")

        # 高频失败
        failures = report['frequent_failures']
        print(f"\n❌ 高频失败商品 (Top 5):")
        for failure in failures['top_failures'][:5]:
            print(f"  - {failure['product_name']}: {failure['failure_count']} 次失败 ({failure['failure_days']} 天)")

        # 地区性能
        regions = report['regional_performance']['regions']
        print(f"\n🌍 地区性能 (Top 5):")
        for region in regions[:5]:
            print(f"  - {region['region']}: {region['pass_rate']}% ({region['total_tests']} 个测试)")

        # 洞察建议
        insights = report.get('insights', [])
        if insights:
            print(f"\n💡 关键洞察:")
            for insight in insights[:5]:
                emoji = {
                    'positive': '✅',
                    'warning': '⚠️',
                    'action_required': '🚨'
                }
                print(f"  {emoji.get(insight['type'], '•')} {insight['message']}")

        print("\n" + "=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='历史趋势分析')
    parser.add_argument(
        '--reports-dir',
        default='reports',
        help='测试报告目录'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='分析的天数（默认 30 天）'
    )
    parser.add_argument(
        '--output',
        default='reports/trend_analysis.json',
        help='输出文件路径'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='输出 JSON 格式'
    )

    args = parser.parse_args()

    analyzer = TrendAnalyzer(
        reports_dir=args.reports_dir,
        days=args.days,
        output_file=args.output
    )

    # 执行分析
    report = analyzer.analyze()

    # 保存报告
    analyzer.save_report(report)

    # 打印报告
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        analyzer.print_report(report)


if __name__ == '__main__':
    main()
