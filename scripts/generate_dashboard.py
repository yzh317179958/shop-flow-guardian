#!/usr/bin/env python3
"""
质量看板生成工具

生成可视化的质量看板 HTML 页面，包含：
- 实时测试状态
- 通过率趋势图
- 高频失败商品
- 地区性能对比
- 性能趋势
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List


class DashboardGenerator:
    """质量看板生成器"""

    def __init__(
        self,
        trend_report_file: str = "reports/trend_analysis.json",
        test_results_file: str = "reports/test_results.json",
        health_report_file: str = "reports/test_health.json",
        output_file: str = "reports/dashboard.html"
    ):
        """
        初始化看板生成器

        Args:
            trend_report_file: 趋势分析报告文件
            test_results_file: 最新测试结果文件
            health_report_file: 健康检查报告文件
            output_file: 输出 HTML 文件路径
        """
        self.trend_report_file = Path(trend_report_file)
        self.test_results_file = Path(test_results_file)
        self.health_report_file = Path(health_report_file)
        self.output_file = Path(output_file)

    def _load_json_file(self, file_path: Path) -> Dict:
        """
        加载 JSON 文件

        Args:
            file_path: 文件路径

        Returns:
            JSON 数据，如果文件不存在返回空字典
        """
        if not file_path.exists():
            print(f"⚠️ 文件不存在: {file_path}")
            return {}

        try:
            with open(file_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败: {file_path} ({e})")
            return {}

    def generate_dashboard(self) -> str:
        """
        生成看板 HTML

        Returns:
            HTML 内容
        """
        # 加载数据
        trend_report = self._load_json_file(self.trend_report_file)
        test_results = self._load_json_file(self.test_results_file)
        health_report = self._load_json_file(self.health_report_file)

        # 生成 HTML
        html = self._generate_html(trend_report, test_results, health_report)

        return html

    def _generate_html(
        self,
        trend_report: Dict,
        test_results: Dict,
        health_report: Dict
    ) -> str:
        """
        生成 HTML 内容

        Args:
            trend_report: 趋势分析报告
            test_results: 测试结果
            health_report: 健康报告

        Returns:
            HTML 字符串
        """
        # 提取关键数据
        health_status = health_report.get('status', 'UNKNOWN')
        avg_pass_rate = health_report.get('metrics', {}).get('average_pass_rate', 0)

        # 通过率趋势数据
        pass_rate_trend = trend_report.get('pass_rate_trend', {})
        trend_data = pass_rate_trend.get('data', [])
        trend_stats = pass_rate_trend.get('statistics', {})

        # 高频失败数据
        frequent_failures = trend_report.get('frequent_failures', {})
        top_failures = frequent_failures.get('top_failures', [])[:10]

        # 地区性能数据
        regional_performance = trend_report.get('regional_performance', {})
        regions = regional_performance.get('regions', [])[:10]

        # 性能趋势数据
        performance_trends = trend_report.get('performance_trends', {})
        perf_data = performance_trends.get('data', [])
        perf_stats = performance_trends.get('statistics', {})

        # 洞察建议
        insights = trend_report.get('insights', [])

        # 最新测试结果
        latest_summary = test_results.get('summary', {})

        # 生成图表数据（JSON 格式）
        chart_data = {
            'pass_rate_trend': self._prepare_pass_rate_chart(trend_data),
            'regional_performance': self._prepare_regional_chart(regions),
            'performance_trend': self._prepare_performance_chart(perf_data)
        }

        # 生成 HTML
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fiido 测试质量看板</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #f5f7fa;
            color: #333;
            line-height: 1.6;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}

        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}

        header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
        }}

        header .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .status-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .status-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s;
        }}

        .status-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
        }}

        .status-card h3 {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .status-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .status-card.healthy .value {{ color: #10b981; }}
        .status-card.warning .value {{ color: #f59e0b; }}
        .status-card.critical .value {{ color: #ef4444; }}
        .status-card.info .value {{ color: #3b82f6; }}

        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}

        .chart-container h2 {{
            margin-bottom: 20px;
            color: #333;
            font-size: 1.5em;
        }}

        .chart-wrapper {{
            position: relative;
            height: 300px;
        }}

        .two-column {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}

        .failure-list {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }}

        .failure-list h2 {{
            margin-bottom: 20px;
            color: #333;
            font-size: 1.5em;
        }}

        .failure-item {{
            padding: 15px;
            border-left: 4px solid #ef4444;
            background: #fef2f2;
            margin-bottom: 15px;
            border-radius: 5px;
        }}

        .failure-item h4 {{
            color: #991b1b;
            margin-bottom: 5px;
        }}

        .failure-item .details {{
            font-size: 0.9em;
            color: #666;
        }}

        .insights {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }}

        .insights h2 {{
            margin-bottom: 20px;
            color: #333;
            font-size: 1.5em;
        }}

        .insight-item {{
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 5px;
            border-left: 4px solid;
        }}

        .insight-item.positive {{
            background: #f0fdf4;
            border-color: #10b981;
        }}

        .insight-item.warning {{
            background: #fef3c7;
            border-color: #f59e0b;
        }}

        .insight-item.action_required {{
            background: #fef2f2;
            border-color: #ef4444;
        }}

        .insight-item .icon {{
            font-size: 1.2em;
            margin-right: 10px;
        }}

        footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}

        @media (max-width: 768px) {{
            .two-column {{
                grid-template-columns: 1fr;
            }}

            .status-cards {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎯 Fiido 测试质量看板</h1>
            <p class="subtitle">实时监控 · 趋势分析 · 质量保障</p>
            <p class="subtitle">更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>

        <!-- 状态卡片 -->
        <div class="status-cards">
            <div class="status-card {self._get_status_class(health_status)}">
                <h3>系统状态</h3>
                <div class="value">{health_status}</div>
            </div>

            <div class="status-card {self._get_pass_rate_class(avg_pass_rate)}">
                <h3>平均通过率</h3>
                <div class="value">{avg_pass_rate:.1f}%</div>
                <div>趋势: {self._get_trend_emoji(trend_stats.get('trend', 'stable'))} {trend_stats.get('trend', 'stable')}</div>
            </div>

            <div class="status-card info">
                <h3>最近测试</h3>
                <div class="value">{latest_summary.get('total', 0)}</div>
                <div>通过: {latest_summary.get('passed', 0)} / 失败: {latest_summary.get('failed', 0)}</div>
            </div>

            <div class="status-card {self._get_failure_class(len(top_failures))}">
                <h3>高频失败</h3>
                <div class="value">{len(top_failures)}</div>
                <div>需要关注的商品</div>
            </div>
        </div>

        <!-- 通过率趋势图 -->
        <div class="chart-container">
            <h2>📈 测试通过率趋势</h2>
            <div class="chart-wrapper">
                <canvas id="passRateChart"></canvas>
            </div>
        </div>

        <!-- 双列布局 -->
        <div class="two-column">
            <!-- 地区性能对比 -->
            <div class="chart-container">
                <h2>🌍 地区性能对比</h2>
                <div class="chart-wrapper">
                    <canvas id="regionalChart"></canvas>
                </div>
            </div>

            <!-- 性能趋势 -->
            <div class="chart-container">
                <h2>⚡ 性能趋势</h2>
                <div class="chart-wrapper">
                    <canvas id="performanceChart"></canvas>
                </div>
                <div style="margin-top: 15px; font-size: 0.9em; color: #666;">
                    平均页面加载时间: {perf_stats.get('avg_page_load_time', 0):.2f}s
                </div>
            </div>
        </div>

        <!-- 高频失败商品列表 -->
        <div class="failure-list">
            <h2>❌ 高频失败商品 (Top 10)</h2>
            {self._generate_failure_list_html(top_failures)}
        </div>

        <!-- 洞察建议 -->
        <div class="insights">
            <h2>💡 关键洞察与建议</h2>
            {self._generate_insights_html(insights)}
        </div>

        <footer>
            <p>Fiido Shop Flow Guardian v1.4.0</p>
            <p>自动化测试质量看板 · 基于 Playwright + AI 分析</p>
        </footer>
    </div>

    <script>
        // 图表数据
        const chartData = {json.dumps(chart_data)};

        // 通过率趋势图
        new Chart(document.getElementById('passRateChart'), {{
            type: 'line',
            data: chartData.pass_rate_trend,
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // 地区性能对比图
        new Chart(document.getElementById('regionalChart'), {{
            type: 'bar',
            data: chartData.regional_performance,
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }},
                scales: {{
                    x: {{
                        beginAtZero: true,
                        max: 100,
                        ticks: {{
                            callback: function(value) {{
                                return value + '%';
                            }}
                        }}
                    }}
                }}
            }}
        }});

        // 性能趋势图
        new Chart(document.getElementById('performanceChart'), {{
            type: 'line',
            data: chartData.performance_trend,
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        display: true
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            callback: function(value) {{
                                return value + 's';
                            }}
                        }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""

        return html

    def _get_status_class(self, status: str) -> str:
        """获取状态样式类"""
        status_map = {
            'HEALTHY': 'healthy',
            'WARNING': 'warning',
            'CRITICAL': 'critical'
        }
        return status_map.get(status, 'info')

    def _get_pass_rate_class(self, pass_rate: float) -> str:
        """获取通过率样式类"""
        if pass_rate >= 95:
            return 'healthy'
        elif pass_rate >= 90:
            return 'warning'
        else:
            return 'critical'

    def _get_failure_class(self, failure_count: int) -> str:
        """获取失败数量样式类"""
        if failure_count == 0:
            return 'healthy'
        elif failure_count < 5:
            return 'warning'
        else:
            return 'critical'

    def _get_trend_emoji(self, trend: str) -> str:
        """获取趋势表情符号"""
        emoji_map = {
            'improving': '📈',
            'stable': '➡️',
            'declining': '📉'
        }
        return emoji_map.get(trend, '➡️')

    def _prepare_pass_rate_chart(self, trend_data: List[Dict]) -> Dict:
        """准备通过率图表数据"""
        labels = [d['date'] for d in trend_data]
        data = [d['pass_rate'] for d in trend_data]

        return {
            'labels': labels,
            'datasets': [{
                'label': '通过率',
                'data': data,
                'borderColor': 'rgb(16, 185, 129)',
                'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                'tension': 0.4,
                'fill': True
            }]
        }

    def _prepare_regional_chart(self, regions: List[Dict]) -> Dict:
        """准备地区性能图表数据"""
        labels = [r['region'] for r in regions]
        data = [r['pass_rate'] for r in regions]

        return {
            'labels': labels,
            'datasets': [{
                'label': '通过率',
                'data': data,
                'backgroundColor': 'rgba(59, 130, 246, 0.8)',
                'borderColor': 'rgb(59, 130, 246)',
                'borderWidth': 1
            }]
        }

    def _prepare_performance_chart(self, perf_data: List[Dict]) -> Dict:
        """准备性能趋势图表数据"""
        labels = [d['date'] for d in perf_data]
        page_load_times = [d['avg_page_load_time'] for d in perf_data]

        return {
            'labels': labels,
            'datasets': [{
                'label': '页面加载时间 (s)',
                'data': page_load_times,
                'borderColor': 'rgb(245, 158, 11)',
                'backgroundColor': 'rgba(245, 158, 11, 0.1)',
                'tension': 0.4,
                'fill': True
            }]
        }

    def _generate_failure_list_html(self, failures: List[Dict]) -> str:
        """生成失败列表 HTML"""
        if not failures:
            return '<p style="color: #10b981;">✅ 无高频失败商品</p>'

        html = ''
        for failure in failures:
            html += f"""
            <div class="failure-item">
                <h4>{failure['product_name']}</h4>
                <div class="details">
                    失败次数: {failure['failure_count']} |
                    持续天数: {failure['failure_days']} |
                    主要错误: {failure['main_error_type']}
                </div>
            </div>
            """

        return html

    def _generate_insights_html(self, insights: List[Dict]) -> str:
        """生成洞察建议 HTML"""
        if not insights:
            return '<p style="color: #10b981;">✅ 系统运行良好，暂无需要关注的问题</p>'

        icon_map = {
            'positive': '✅',
            'warning': '⚠️',
            'action_required': '🚨'
        }

        html = ''
        for insight in insights:
            icon = icon_map.get(insight['type'], '•')
            html += f"""
            <div class="insight-item {insight['type']}">
                <span class="icon">{icon}</span>
                {insight['message']}
            </div>
            """

        return html

    def save_dashboard(self):
        """生成并保存看板"""
        print("📊 正在生成质量看板...")

        html = self.generate_dashboard()

        self.output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"✅ 质量看板已生成: {self.output_file}")
        print(f"🌐 在浏览器中打开: file://{self.output_file.absolute()}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='生成质量看板')
    parser.add_argument(
        '--trend-report',
        default='reports/trend_analysis.json',
        help='趋势分析报告文件'
    )
    parser.add_argument(
        '--test-results',
        default='reports/test_results.json',
        help='最新测试结果文件'
    )
    parser.add_argument(
        '--health-report',
        default='reports/test_health.json',
        help='健康检查报告文件'
    )
    parser.add_argument(
        '--output',
        default='reports/dashboard.html',
        help='输出 HTML 文件路径'
    )

    args = parser.parse_args()

    generator = DashboardGenerator(
        trend_report_file=args.trend_report,
        test_results_file=args.test_results,
        health_report_file=args.health_report,
        output_file=args.output
    )

    generator.save_dashboard()


if __name__ == '__main__':
    main()
