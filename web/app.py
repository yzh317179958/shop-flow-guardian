#!/usr/bin/env python3
"""
Fiido 测试工作台 Web 应用

提供简单易用的 UI 界面，非技术人员可以通过浏览器使用测试系统。
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
import threading

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)
CORS(app)  # 允许跨域访问

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
REPORTS_DIR = PROJECT_ROOT / "reports"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

# 当前运行的任务
running_tasks = {}


def run_command(command, task_id=None):
    """
    执行命令并返回结果

    Args:
        command: 要执行的命令列表
        task_id: 任务 ID（用于后台任务）

    Returns:
        命令执行结果
    """
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )

        output = {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }

        if task_id:
            running_tasks[task_id] = {
                'status': 'completed' if result.returncode == 0 else 'failed',
                'result': output,
                'completed_at': datetime.now().isoformat()
            }

        return output
    except subprocess.TimeoutExpired:
        error = {'success': False, 'error': '命令执行超时'}
        if task_id:
            running_tasks[task_id] = {
                'status': 'timeout',
                'result': error,
                'completed_at': datetime.now().isoformat()
            }
        return error
    except Exception as e:
        error = {'success': False, 'error': str(e)}
        if task_id:
            running_tasks[task_id] = {
                'status': 'error',
                'result': error,
                'completed_at': datetime.now().isoformat()
            }
        return error


@app.route('/')
def index():
    """首页 - 工作台"""
    return render_template('index.html')


@app.route('/api/health')
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})


@app.route('/api/products/discover', methods=['POST'])
def discover_products():
    """发现商品"""
    task_id = f"discover_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.now().isoformat()
    }

    # 后台执行
    def run_discovery():
        command = ['./run.sh', 'python3', 'scripts/discover_products.py']
        run_command(command, task_id)

    thread = threading.Thread(target=run_discovery)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started'})


@app.route('/api/products/list')
def list_products():
    """获取商品列表"""
    products_file = DATA_DIR / 'products.json'

    if not products_file.exists():
        return jsonify({'products': [], 'total': 0})

    try:
        with open(products_file) as f:
            products = json.load(f)

        return jsonify({
            'products': products,
            'total': len(products)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/tests/run', methods=['POST'])
def run_tests():
    """运行测试"""
    data = request.json or {}

    # 构建测试命令
    command = ['./run_tests.sh']

    # 添加过滤参数
    if data.get('priority'):
        command.append(f"--priority={data['priority']}")

    if data.get('category'):
        command.append(f"--category={data['category']}")

    if data.get('product_id'):
        command.append(f"--product-id={data['product_id']}")

    task_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.now().isoformat(),
        'params': data
    }

    # 后台执行
    def run_test():
        run_command(command, task_id)

    thread = threading.Thread(target=run_test)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started'})


@app.route('/api/tests/status/<task_id>')
def test_status(task_id):
    """查询测试状态"""
    if task_id not in running_tasks:
        return jsonify({'error': 'Task not found'}), 404

    return jsonify(running_tasks[task_id])


@app.route('/api/reports/list')
def list_reports():
    """获取报告列表"""
    reports = []

    # 查找所有测试报告
    for report_dir in REPORTS_DIR.glob('test_*'):
        if report_dir.is_dir():
            result_file = report_dir / 'test_results.json'
            if result_file.exists():
                try:
                    with open(result_file) as f:
                        data = json.load(f)

                    reports.append({
                        'id': report_dir.name,
                        'timestamp': data.get('timestamp', ''),
                        'summary': data.get('summary', {}),
                        'path': str(report_dir.relative_to(PROJECT_ROOT))
                    })
                except:
                    pass

    # 按时间倒序排序
    reports.sort(key=lambda x: x['timestamp'], reverse=True)

    return jsonify({'reports': reports, 'total': len(reports)})


@app.route('/api/reports/latest')
def latest_report():
    """获取最新报告"""
    result_file = REPORTS_DIR / 'test_results.json'

    if not result_file.exists():
        return jsonify({'error': 'No reports found'}), 404

    try:
        with open(result_file) as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/reports/ai/generate', methods=['POST'])
def generate_ai_report():
    """生成 AI 报告"""
    data = request.json or {}
    provider = data.get('provider', 'deepseek')

    command = [
        './run.sh',
        'python3',
        'scripts/generate_universal_ai_report.py',
        '--provider', provider
    ]

    if data.get('summary_only'):
        command.append('--summary-only')

    task_id = f"ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.now().isoformat()
    }

    # 后台执行
    def run_ai():
        run_command(command, task_id)

    thread = threading.Thread(target=run_ai)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started'})


@app.route('/api/changes/detect', methods=['POST'])
def detect_changes():
    """检测商品变更"""
    command = [
        './run.sh',
        'python3',
        'scripts/detect_product_changes.py',
        '--save-history'
    ]

    task_id = f"changes_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.now().isoformat()
    }

    # 后台执行
    def run_detect():
        run_command(command, task_id)

    thread = threading.Thread(target=run_detect)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started'})


@app.route('/api/changes/latest')
def latest_changes():
    """获取最新变更"""
    changes_file = DATA_DIR / 'product_changes.json'

    if not changes_file.exists():
        return jsonify({'error': 'No changes detected yet'}), 404

    try:
        with open(changes_file) as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trends/analyze', methods=['POST'])
def analyze_trends():
    """分析历史趋势"""
    data = request.json or {}
    days = data.get('days', 30)

    command = [
        './run.sh',
        'python3',
        'scripts/analyze_trends.py',
        '--days', str(days)
    ]

    task_id = f"trends_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.now().isoformat()
    }

    # 后台执行
    def run_trends():
        run_command(command, task_id)

    thread = threading.Thread(target=run_trends)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started'})


@app.route('/api/trends/latest')
def latest_trends():
    """获取最新趋势分析"""
    trends_file = REPORTS_DIR / 'trend_analysis.json'

    if not trends_file.exists():
        return jsonify({'error': 'No trend analysis found'}), 404

    try:
        with open(trends_file) as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/dashboard/generate', methods=['POST'])
def generate_dashboard():
    """生成质量看板"""
    command = [
        './run.sh',
        'python3',
        'scripts/generate_dashboard.py'
    ]

    result = run_command(command)

    if result['success']:
        return jsonify({'status': 'success', 'url': '/dashboard'})
    else:
        return jsonify({'error': result.get('stderr', 'Unknown error')}), 500


@app.route('/dashboard')
def view_dashboard():
    """查看质量看板"""
    dashboard_file = REPORTS_DIR / 'dashboard.html'

    if not dashboard_file.exists():
        return "Dashboard not generated yet. Please generate it first.", 404

    return send_file(dashboard_file)


@app.route('/api/health/check')
def health_check():
    """系统健康检查"""
    health_file = REPORTS_DIR / 'test_health.json'

    if not health_file.exists():
        # 运行健康检查
        command = ['./run.sh', 'python3', 'scripts/check_test_health.py']
        run_command(command)

    if health_file.exists():
        try:
            with open(health_file) as f:
                data = json.load(f)
            return jsonify(data)
        except:
            pass

    return jsonify({'status': 'UNKNOWN'})


@app.route('/api/config')
def get_config():
    """获取系统配置"""
    return jsonify({
        'project_name': 'Fiido Shop Flow Guardian',
        'version': 'v1.4.0',
        'data_dir': str(DATA_DIR.relative_to(PROJECT_ROOT)),
        'reports_dir': str(REPORTS_DIR.relative_to(PROJECT_ROOT))
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Fiido 测试工作台启动中...")
    print("=" * 60)
    print(f"📁 项目目录: {PROJECT_ROOT}")
    print(f"📊 数据目录: {DATA_DIR}")
    print(f"📈 报告目录: {REPORTS_DIR}")
    print("=" * 60)
    print("✅ 服务已启动！")
    print("🌐 访问地址: http://localhost:5000")
    print("=" * 60)

    # 开发模式启动
    app.run(host='0.0.0.0', port=5000, debug=True)
