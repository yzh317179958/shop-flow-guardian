#!/usr/bin/env python3
"""
告警发送脚本

根据测试结果自动判断是否发送告警，
支持多种通知渠道：Slack、邮件、企业微信。
"""

import os
import sys
import json
import requests
import smtplib
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import argparse


class AlertEngine:
    """告警引擎"""

    def __init__(self, config_path: str = 'config/alert_config.json'):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.history_file = Path(self.config.get('history', {}).get('storage_file', 'data/alert_history.json'))

    def _load_config(self) -> Dict:
        """加载告警配置"""
        if not self.config_path.exists():
            print(f"⚠️ 配置文件不存在: {self.config_path}")
            return self._get_default_config()

        with open(self.config_path) as f:
            return json.load(f)

    def _get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "enabled": True,
            "thresholds": {
                "pass_rate": 0.90,
                "consecutive_failures": 3,
                "failure_spike_multiplier": 2.0
            },
            "channels": {
                "slack": {"enabled": True},
                "email": {"enabled": True}
            }
        }

    def should_alert(self, test_results: Dict) -> Tuple[bool, str, str]:
        """
        判断是否触发告警

        Args:
            test_results: 测试结果字典

        Returns:
            (是否告警, 告警原因, 告警级别)
        """
        if not self.config.get('enabled', True):
            return False, "", ""

        reasons = []
        severity = "low"

        # 规则1: P0 商品失败（严重）
        p0_failures = test_results.get('summary', {}).get('p0_failures', 0)
        if p0_failures > 0:
            reasons.append(f"{p0_failures} 个 P0 核心商品测试失败")
            severity = "critical"

        # 规则2: 通过率低于阈值（高优先级）
        pass_rate = test_results.get('pass_rate', 1.0)
        threshold = self.config['thresholds']['pass_rate']
        if pass_rate < threshold:
            reasons.append(f"通过率 {pass_rate:.1%} 低于阈值 {threshold:.1%}")
            if severity == "low":
                severity = "high"

        # 规则3: 连续失败次数（高优先级）
        consecutive = test_results.get('consecutive_failures', 0)
        if consecutive >= self.config['thresholds']['consecutive_failures']:
            reasons.append(f"连续失败 {consecutive} 次")
            if severity == "low":
                severity = "high"

        # 规则4: 失败数量突增（中等优先级）
        current_failures = test_results.get('failed', 0)
        avg_failures = test_results.get('avg_failures_last_7_days', 0)
        multiplier = self.config['thresholds']['failure_spike_multiplier']
        if avg_failures > 0 and current_failures > avg_failures * multiplier:
            reasons.append(f"失败数量突增：{current_failures} (平均: {avg_failures:.0f})")
            if severity == "low":
                severity = "medium"

        # 检查静默时间
        if self._is_quiet_hours() and severity != "critical":
            print("⏰ 当前处于静默时间，非严重告警将被抑制")
            return False, "", ""

        return len(reasons) > 0, '\n'.join(reasons), severity

    def _is_quiet_hours(self) -> bool:
        """检查是否在静默时间内"""
        quiet_config = self.config.get('quiet_hours', {})
        if not quiet_config.get('enabled', False):
            return False

        # TODO: 实现时区转换和时间检查
        return False

    def send_alert(
        self,
        channel: str,
        message: str,
        results: Dict,
        severity: str = "medium"
    ) -> bool:
        """
        发送告警

        Args:
            channel: 通知渠道 (slack/email/wechat)
            message: 告警消息
            results: 测试结果
            severity: 严重程度

        Returns:
            是否发送成功
        """
        channel_config = self.config.get('channels', {}).get(channel, {})
        if not channel_config.get('enabled', False):
            print(f"⏭️  {channel} 通道未启用")
            return False

        if channel == 'slack':
            return self._send_slack(message, results, severity)
        elif channel == 'email':
            return self._send_email(message, results, severity)
        elif channel == 'wechat':
            return self._send_wechat(message, results, severity)
        else:
            print(f"❌ 未知的通知渠道: {channel}")
            return False

    def _send_slack(self, message: str, results: Dict, severity: str) -> bool:
        """发送 Slack 通知"""
        webhook_url = os.getenv(
            self.config['channels']['slack'].get('webhook_env', 'SLACK_WEBHOOK_URL')
        )

        if not webhook_url:
            print("⚠️ SLACK_WEBHOOK_URL 未配置")
            return False

        # 严重程度对应的颜色和图标
        severity_config = {
            "critical": {"color": "#FF0000", "icon": "🚨"},
            "high": {"color": "#FFA500", "icon": "⚠️"},
            "medium": {"color": "#FFFF00", "icon": "ℹ️"},
            "low": {"color": "#00FF00", "icon": "📢"}
        }

        config = severity_config.get(severity, severity_config["medium"])

        # 构建富文本消息
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{config['icon']} Fiido E2E 测试告警"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*通过率:*\n{results.get('pass_rate', 0):.1%}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*失败数:*\n{results.get('failed', 0)}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*测试时间:*\n{results.get('timestamp', 'N/A')}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*严重程度:*\n{severity.upper()}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*告警原因:*\n```{message}```"
                }
            }
        ]

        # 添加失败商品列表
        failures = results.get('failures', [])
        if failures:
            max_show = self.config['channels']['slack'].get('max_failures_to_show', 5)
            failure_list = '\n'.join([
                f"• {f.get('product_name', 'Unknown')} ({f.get('priority', 'P2')})"
                for f in failures[:max_show]
            ])

            if len(failures) > max_show:
                failure_list += f"\n... 还有 {len(failures) - max_show} 个失败"

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*失败商品:*\n{failure_list}"
                }
            })

        # 添加报告链接（如果有）
        if results.get('report_url'):
            blocks.append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "查看完整报告"
                        },
                        "url": results['report_url'],
                        "style": "danger" if severity == "critical" else "primary"
                    }
                ]
            })

        # Mention 用户（如果是 P0 失败）
        mention_on_p0 = self.config['channels']['slack'].get('mention_on_p0_failure', False)
        if mention_on_p0 and results.get('summary', {}).get('p0_failures', 0) > 0:
            mention_users = self.config['channels']['slack'].get('mention_users', [])
            if mention_users:
                mention_text = ' '.join(mention_users)
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📢 {mention_text} 请立即查看！"
                    }
                })

        payload = {
            "blocks": blocks,
            "attachments": [{
                "color": config['color']
            }]
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ Slack 告警已发送")
                return True
            else:
                print(f"❌ Slack 告警发送失败: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Slack 告警发送异常: {e}")
            return False

    def _send_email(self, message: str, results: Dict, severity: str) -> bool:
        """发送邮件通知"""
        channel_config = self.config['channels']['email']

        sender = os.getenv(channel_config.get('sender_env', 'ALERT_EMAIL_SENDER'))
        recipients = os.getenv(channel_config.get('recipients_env', 'ALERT_EMAIL_RECIPIENTS'), '').split(',')
        smtp_server = os.getenv(channel_config.get('smtp_server_env', 'SMTP_SERVER'), 'smtp.gmail.com')
        smtp_port = int(os.getenv(channel_config.get('smtp_port_env', 'SMTP_PORT'), '587'))
        smtp_user = os.getenv(channel_config.get('smtp_user_env', 'SMTP_USER'))
        smtp_password = os.getenv(channel_config.get('smtp_password_env', 'SMTP_PASSWORD'))

        if not all([sender, recipients, smtp_user, smtp_password]):
            print("⚠️ 邮件配置不完整，跳过邮件告警")
            return False

        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 Fiido E2E 测试告警 [{severity.upper()}] - 通过率 {results.get('pass_rate', 0):.1%}"
        msg['From'] = sender
        msg['To'] = ', '.join(recipients)

        # HTML 邮件内容
        failures = results.get('failures', [])
        failure_rows = '\n'.join([
            f"<tr><td>{f.get('product_name', 'Unknown')}</td><td>{f.get('priority', 'P2')}</td><td>{f.get('error_message', '')[:100]}...</td></tr>"
            for f in failures[:10]
        ])

        html = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; }}
              table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
              th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
              th {{ background-color: #f2f2f2; }}
              .critical {{ color: #d32f2f; font-weight: bold; }}
              .high {{ color: #ff6f00; font-weight: bold; }}
              .medium {{ color: #fbc02d; }}
            </style>
          </head>
          <body>
            <h2>🚨 Fiido E2E 测试告警</h2>

            <p><strong>严重程度:</strong> <span class="{severity}">{severity.upper()}</span></p>

            <table>
              <tr><th>指标</th><th>值</th></tr>
              <tr><td>通过率</td><td>{results.get('pass_rate', 0):.1%}</td></tr>
              <tr><td>总测试数</td><td>{results.get('total', 0)}</td></tr>
              <tr><td>通过</td><td>{results.get('passed', 0)}</td></tr>
              <tr><td>失败</td><td>{results.get('failed', 0)}</td></tr>
              <tr><td>跳过</td><td>{results.get('skipped', 0)}</td></tr>
              <tr><td>P0 失败</td><td>{results.get('summary', {}).get('p0_failures', 0)}</td></tr>
              <tr><td>测试时间</td><td>{results.get('timestamp', 'N/A')}</td></tr>
            </table>

            <h3>告警原因:</h3>
            <pre>{message}</pre>

            <h3>失败商品:</h3>
            <table>
              <tr><th>商品名称</th><th>优先级</th><th>错误信息</th></tr>
              {failure_rows}
            </table>

            {'<p>... 还有 ' + str(len(failures) - 10) + ' 个失败</p>' if len(failures) > 10 else ''}

            <p><a href="{results.get('report_url', '#')}">查看完整报告</a></p>

            <hr>
            <p style="color: #666; font-size: 12px;">
              此邮件由 Fiido E2E 测试系统自动发送<br>
              生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </p>
          </body>
        </html>
        """

        msg.attach(MIMEText(html, 'html'))

        # 发送邮件
        try:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
            print("✅ 邮件告警已发送")
            return True
        except Exception as e:
            print(f"❌ 邮件发送失败: {e}")
            return False

    def _send_wechat(self, message: str, results: Dict, severity: str) -> bool:
        """发送企业微信通知"""
        webhook_url = os.getenv(
            self.config['channels']['wechat'].get('webhook_env', 'WECHAT_WEBHOOK_URL')
        )

        if not webhook_url:
            print("⚠️ WECHAT_WEBHOOK_URL 未配置")
            return False

        # 企业微信 Markdown 格式
        content = f"""**🚨 Fiido E2E 测试告警 [{severity.upper()}]**

> 告警原因:
> {message}

**测试统计:**
- 通过率: {results.get('pass_rate', 0):.1%}
- 失败数: {results.get('failed', 0)}
- P0 失败: {results.get('summary', {}).get('p0_failures', 0)}

[查看详细报告]({results.get('report_url', '#')})
"""

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": content
            }
        }

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ 企业微信告警已发送")
                return True
            else:
                print(f"❌ 企业微信告警发送失败: {response.text}")
                return False
        except Exception as e:
            print(f"❌ 企业微信告警发送异常: {e}")
            return False

    def save_alert_history(self, results: Dict, alerted: bool, channels: List[str]):
        """保存告警历史"""
        if not self.config.get('history', {}).get('enabled', True):
            return

        self.history_file.parent.mkdir(parents=True, exist_ok=True)

        # 加载历史记录
        history = []
        if self.history_file.exists():
            with open(self.history_file) as f:
                history = json.load(f)

        # 添加新记录
        record = {
            "timestamp": datetime.now().isoformat(),
            "pass_rate": results.get('pass_rate', 0),
            "total_tests": results.get('total', 0),
            "failed_tests": results.get('failed', 0),
            "p0_failures": results.get('summary', {}).get('p0_failures', 0),
            "alert_triggered": alerted,
            "alert_channels": channels if alerted else []
        }

        history.append(record)

        # 保留最近的记录
        max_records = self.config.get('history', {}).get('max_records', 1000)
        history = history[-max_records:]

        # 保存
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='发送测试告警')
    parser.add_argument(
        '--channel',
        choices=['slack', 'email', 'wechat', 'all'],
        default='all',
        help='通知渠道'
    )
    parser.add_argument(
        '--results-file',
        default='reports/test-results.json',
        help='测试结果文件路径'
    )
    parser.add_argument(
        '--priority',
        choices=['normal', 'urgent'],
        default='normal',
        help='告警优先级'
    )
    parser.add_argument(
        '--config',
        default='config/alert_config.json',
        help='告警配置文件路径'
    )

    args = parser.parse_args()

    # 检查结果文件
    results_file = Path(args.results_file)
    if not results_file.exists():
        print(f"❌ 测试结果文件不存在: {results_file}")
        sys.exit(1)

    # 加载测试结果
    with open(results_file) as f:
        results = json.load(f)

    # 创建告警引擎
    engine = AlertEngine(config_path=args.config)

    # 检查是否需要告警
    should_alert, reason, severity = engine.should_alert(results)

    if not should_alert:
        print("✅ 测试通过，无需告警")
        engine.save_alert_history(results, False, [])
        sys.exit(0)

    # 发送告警
    print(f"\n🚨 触发告警 [{severity.upper()}]:")
    print(f"   {reason}\n")

    channels_to_use = []
    if args.channel == 'all':
        channels_to_use = ['slack', 'email', 'wechat']
    else:
        channels_to_use = [args.channel]

    success_channels = []
    for channel in channels_to_use:
        if engine.send_alert(channel, reason, results, severity):
            success_channels.append(channel)

    # 保存历史
    engine.save_alert_history(results, True, success_channels)

    if success_channels:
        print(f"\n✅ 告警已通过以下渠道发送: {', '.join(success_channels)}")
    else:
        print("\n⚠️ 所有渠道发送失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
