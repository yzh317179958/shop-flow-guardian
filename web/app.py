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

# 当前活跃的测试任务ID（每次只能运行一个测试）
active_test_task_id = None

# 线程锁 - 保护任务状态的并发访问
task_lock = threading.Lock()

# 任务保留时间（秒）- 已完成的任务保留1小时后自动清理
TASK_RETENTION_SECONDS = 3600


def cleanup_old_tasks():
    """清理已完成的旧任务，释放内存

    保留最近1小时内完成的任务，清理更旧的任务。
    """
    now = datetime.now()
    tasks_to_remove = []

    for task_id, task in running_tasks.items():
        # 只清理已完成/失败/超时/停止的任务
        if task.get('status') in ['completed', 'failed', 'timeout', 'error', 'stopped']:
            completed_at = task.get('completed_at') or task.get('stopped_at')
            if completed_at:
                try:
                    completed_time = datetime.fromisoformat(completed_at)
                    age_seconds = (now - completed_time).total_seconds()
                    if age_seconds > TASK_RETENTION_SECONDS:
                        tasks_to_remove.append(task_id)
                except (ValueError, TypeError):
                    # 解析失败的任务也清理
                    tasks_to_remove.append(task_id)

    # 删除旧任务
    for task_id in tasks_to_remove:
        del running_tasks[task_id]

    if tasks_to_remove:
        print(f"[任务清理] 已清理 {len(tasks_to_remove)} 个旧任务，当前任务数: {len(running_tasks)}")

    return len(tasks_to_remove)


def _save_test_report(task_id):
    """保存测试报告到文件

    将内存中的测试结果持久化到reports目录，以便报告中心能够显示

    Args:
        task_id: 任务ID
    """
    if task_id not in running_tasks:
        return

    task = running_tasks[task_id]

    # 只保存测试任务的结果（task_id以test_开头）
    if not task_id.startswith('test_'):
        return

    # 构建报告数据
    test_steps = task.get('test_steps', [])
    product_results = task.get('product_results', {})
    params = task.get('params', {})
    test_mode = task.get('test_mode', 'quick')

    # 计算统计信息
    total_steps = 0
    passed_steps = 0
    failed_steps = 0
    skipped_steps = 0

    # 如果有多商品结果，从product_results统计
    if product_results:
        for product_id, product_data in product_results.items():
            steps = product_data.get('steps', [])
            total_steps += len(steps)
            passed_steps += len([s for s in steps if s.get('status') == 'passed'])
            failed_steps += len([s for s in steps if s.get('status') == 'failed'])
            skipped_steps += len([s for s in steps if s.get('status') == 'skipped'])
    else:
        # 单商品测试，从test_steps统计
        total_steps = len(test_steps)
        passed_steps = len([s for s in test_steps if s.get('status') == 'passed'])
        failed_steps = len([s for s in test_steps if s.get('status') == 'failed'])
        skipped_steps = len([s for s in test_steps if s.get('status') == 'skipped'])

    # 计算耗时
    started_at = task.get('started_at')
    completed_at = task.get('completed_at')
    duration = 0
    if started_at and completed_at:
        try:
            start_time = datetime.fromisoformat(started_at)
            end_time = datetime.fromisoformat(completed_at)
            duration = (end_time - start_time).total_seconds()
        except (ValueError, TypeError):
            pass

    # 生成测试范围描述
    test_scope = "测试"
    if params.get('product_id'):
        test_scope = f"单个商品测试"
    elif params.get('product_ids'):
        count = len(params['product_ids'])
        test_scope = f"自定义选择 {count} 个商品"
    elif params.get('category'):
        test_scope = f"分类: {params['category']}"
    else:
        if product_results:
            test_scope = f"批量测试 {len(product_results)} 个商品"
        else:
            test_scope = "单个商品测试"

    # 构建报告数据
    report_data = {
        'id': task_id,
        'timestamp': task.get('started_at'),
        'test_mode': test_mode,
        'test_scope': test_scope,
        'test_config': params,
        'summary': {
            'total': total_steps,
            'passed': passed_steps,
            'failed': failed_steps,
            'skipped': skipped_steps,
            'duration': duration,
            'pass_rate': round((passed_steps / total_steps * 100), 1) if total_steps > 0 else 0
        },
        'products': [],
        'status': task.get('status', 'completed')
    }

    # 添加商品详情
    if product_results:
        for product_id, product_data in product_results.items():
            product_entry = {
                'product_id': product_id,
                'product_name': product_data.get('name', product_id),
                'status': product_data.get('status', 'unknown'),
                'steps': product_data.get('steps', [])
            }
            report_data['products'].append(product_entry)
    elif test_steps:
        # 单商品测试
        product_id = params.get('product_id', 'unknown')
        all_passed = all(s.get('status') == 'passed' for s in test_steps)
        report_data['products'].append({
            'product_id': product_id,
            'product_name': product_id,
            'status': 'passed' if all_passed else 'failed',
            'steps': test_steps
        })

    # 保存到文件
    report_file = REPORTS_DIR / f"{task_id}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"[报告保存] 测试报告已保存: {report_file}")
    except Exception as e:
        print(f"[报告保存] 保存失败: {e}")


def stop_task(task_id):
    """停止指定任务

    Args:
        task_id: 任务ID

    Returns:
        是否成功停止
    """
    global active_test_task_id

    if task_id not in running_tasks:
        return False

    task = running_tasks[task_id]

    # 标记任务为停止状态
    task['status'] = 'stopped'
    task['stopped_at'] = datetime.now().isoformat()
    task['stopped_by_user'] = True

    # 如果有进程，尝试终止
    if 'process' in task and task['process'] is not None:
        try:
            task['process'].terminate()
            task['process'].wait(timeout=5)
        except Exception:
            try:
                task['process'].kill()
            except Exception:
                pass

    # 清除活跃任务标记
    if active_test_task_id == task_id:
        active_test_task_id = None

    return True


def run_command(command, task_id=None):
    """
    执行命令并返回结果（支持实时输出捕获）

    Args:
        command: 要执行的命令列表
        task_id: 任务 ID（用于后台任务）

    Returns:
        命令执行结果
    """
    try:
        # 启动进程，实时捕获输出
        process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        stdout_lines = []
        stderr_lines = []

        # 如果有task_id，初始化日志存储并保存进程引用
        if task_id:
            running_tasks[task_id]['logs'] = []
            running_tasks[task_id]['progress'] = {
                'current': 0,
                'total': 0,
                'message': '正在初始化...'
            }
            running_tasks[task_id]['process'] = process  # 保存进程引用

        # 实时读取输出
        import select
        import time

        timeout = 600  # 10分钟超时
        start_time = time.time()

        while True:
            # 检查任务是否被用户停止
            if task_id and running_tasks.get(task_id, {}).get('status') == 'stopped':
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                return {'success': False, 'stopped': True, 'error': '测试被用户停止'}

            # 检查超时
            if time.time() - start_time > timeout:
                process.kill()
                raise subprocess.TimeoutExpired(command, timeout)

            # 检查进程是否结束
            if process.poll() is not None:
                # 读取剩余输出
                remaining_stdout = process.stdout.read()
                remaining_stderr = process.stderr.read()
                if remaining_stdout:
                    stdout_lines.append(remaining_stdout)
                    if task_id:
                        # 🔧 修复: 解析剩余日志中的每一行
                        for remaining_line in remaining_stdout.splitlines():
                            running_tasks[task_id]['logs'].append(remaining_line)
                            parse_progress_line(remaining_line, task_id)
                if remaining_stderr:
                    stderr_lines.append(remaining_stderr)
                break

            # 读取stdout
            line = process.stdout.readline()
            if line:
                stdout_lines.append(line)
                if task_id:
                    running_tasks[task_id]['logs'].append(line.rstrip())
                    # 解析进度信息
                    parse_progress_line(line, task_id)

            time.sleep(0.1)

        returncode = process.returncode
        stdout = ''.join(stdout_lines)
        stderr = ''.join(stderr_lines)

        output = {
            'success': returncode == 0,
            'stdout': stdout,
            'stderr': stderr,
            'returncode': returncode
        }

        if task_id:
            running_tasks[task_id].update({
                'status': 'completed' if returncode == 0 else 'failed',
                'result': output,
                'completed_at': datetime.now().isoformat()
            })
            # 保存测试报告到文件
            _save_test_report(task_id)

        return output

    except subprocess.TimeoutExpired:
        error = {'success': False, 'error': '命令执行超时'}
        if task_id:
            running_tasks[task_id].update({
                'status': 'timeout',
                'result': error,
                'completed_at': datetime.now().isoformat()
            })
        return error
    except Exception as e:
        error = {'success': False, 'error': str(e)}
        if task_id:
            running_tasks[task_id].update({
                'status': 'error',
                'result': error,
                'completed_at': datetime.now().isoformat()
            })
        return error


def parse_progress_line(line, task_id):
    """解析日志行，提取进度信息

    Args:
        line: 日志行
        task_id: 任务ID
    """
    import re

    # 解析多商品测试开始: [1/10] 测试商品: xxx
    match = re.search(r'\[(\d+)/(\d+)\]\s+测试商品:\s+(.+)', line)
    if match:
        current = int(match.group(1))
        total = int(match.group(2))
        product_name = match.group(3).strip()

        # 更新进度
        running_tasks[task_id]['progress'] = {
            'current': current,
            'total': total,
            'message': f'正在测试第 {current}/{total} 个商品: {product_name}'
        }

        # 初始化商品结果分组
        if 'product_results' not in running_tasks[task_id]:
            running_tasks[task_id]['product_results'] = {}

        # 设置当前正在测试的商品
        running_tasks[task_id]['current_product'] = {
            'index': current,
            'name': product_name,
            'steps': []
        }
        return

    # 解析商品ID: 商品ID: xxx
    match = re.search(r'商品ID:\s*(\S+)', line)
    if match:
        product_id = match.group(1).strip()
        if 'current_product' in running_tasks[task_id]:
            running_tasks[task_id]['current_product']['id'] = product_id
        return

    # 解析测试步骤: [步骤 1] 页面访问
    match = re.search(r'\[步骤\s+(\d+)\]\s+(.+)', line)
    if match:
        step_number = int(match.group(1))
        step_name = match.group(2).strip()

        # 创建步骤对象
        step = {
            'number': step_number,
            'name': step_name,
            'status': 'running'
        }

        # 如果在多商品测试中，添加到当前商品的步骤
        if 'current_product' in running_tasks[task_id]:
            running_tasks[task_id]['current_product']['steps'].append(step)
        else:
            # 单商品测试，添加到全局步骤
            if 'test_steps' not in running_tasks[task_id]:
                running_tasks[task_id]['test_steps'] = []
            running_tasks[task_id]['test_steps'].append(step)
        return

    # 解析步骤说明
    match = re.search(r'说明:\s*(.+)', line)
    if match:
        description = match.group(1).strip()
        steps = _get_current_steps(task_id)
        if steps:
            steps[-1]['description'] = description
        return

    # 解析步骤结果: ✓ 结果: xxx
    match = re.search(r'[✓✗⊘]\s*结果:\s*(.+?)(?:\s*\(耗时:\s*([\d.]+)s\))?$', line)
    if match:
        result = match.group(1).strip()
        duration = match.group(2)

        steps = _get_current_steps(task_id)
        if steps:
            step = steps[-1]
            step['result'] = result
            if duration:
                step['duration'] = float(duration)

            # 根据符号判断状态
            if '✓' in line:
                step['status'] = 'passed'
            elif '✗' in line:
                step['status'] = 'failed'
            elif '⊘' in line:
                step['status'] = 'skipped'
        return

    # 解析错误信息
    match = re.search(r'错误:\s*(.+)', line)
    if match:
        error = match.group(1).strip()
        steps = _get_current_steps(task_id)
        if steps:
            steps[-1]['error'] = error
        return

    # 解析测试完成标记（用于保存商品测试结果）
    # 注意：run_product_test.py 输出 "测试完成" 和 "总耗时" 是分开的两行
    # 所以只检测 "测试完成" 即可
    if '测试完成' in line and '步骤统计' not in line:
        _save_product_result(task_id)
        return

    # 🔧 新增: 解析问题详情 (📋 问题详情 后面的各行)
    # 解析场景
    match = re.search(r'场景:\s*(.+)', line)
    if match:
        scenario = match.group(1).strip()
        steps = _get_current_steps(task_id)
        if steps:
            if 'issue_details' not in steps[-1]:
                steps[-1]['issue_details'] = {}
            steps[-1]['issue_details']['scenario'] = scenario
        return

    # 解析操作
    match = re.search(r'操作:\s*(.+)', line)
    if match:
        operation = match.group(1).strip()
        steps = _get_current_steps(task_id)
        if steps:
            if 'issue_details' not in steps[-1]:
                steps[-1]['issue_details'] = {}
            steps[-1]['issue_details']['operation'] = operation
        return

    # 解析问题
    match = re.search(r'问题:\s*(.+)', line)
    if match:
        problem = match.group(1).strip()
        steps = _get_current_steps(task_id)
        if steps:
            if 'issue_details' not in steps[-1]:
                steps[-1]['issue_details'] = {}
            steps[-1]['issue_details']['problem'] = problem
        return

    # 解析根因
    match = re.search(r'根因:\s*(.+)', line)
    if match:
        root_cause = match.group(1).strip()
        steps = _get_current_steps(task_id)
        if steps:
            if 'issue_details' not in steps[-1]:
                steps[-1]['issue_details'] = {}
            steps[-1]['issue_details']['root_cause'] = root_cause
        return

    # 解析JS错误
    match = re.search(r'JS错误:\s*(.+)', line)
    if match:
        js_error = match.group(1).strip()
        steps = _get_current_steps(task_id)
        if steps:
            if 'issue_details' not in steps[-1]:
                steps[-1]['issue_details'] = {}
            if 'js_errors' not in steps[-1]['issue_details']:
                steps[-1]['issue_details']['js_errors'] = []
            steps[-1]['issue_details']['js_errors'].append(js_error)
        return

    # 解析 "[1/10] Processing collection: xxx" (商品发现)
    match = re.search(r'\[(\d+)/(\d+)\]\s+Processing collection:\s+(.+)', line)
    if match:
        current = int(match.group(1))
        total = int(match.group(2))
        collection = match.group(3).strip()
        running_tasks[task_id]['progress'] = {
            'current': current,
            'total': total,
            'message': f'正在处理分类 {current}/{total}: {collection}'
        }
        return

    # 解析 "Found X products in xxx"
    match = re.search(r'Found (\d+) products in (.+)', line)
    if match:
        count = match.group(1)
        collection = match.group(2).strip()
        current_progress = running_tasks[task_id].get('progress', {})
        current_progress['message'] = f'在 {collection} 中发现 {count} 个商品'
        return

    # 解析 "Discovering all collections..."
    if 'Discovering all collections' in line:
        running_tasks[task_id]['progress']['message'] = '正在发现所有商品分类...'
        return

    # 解析 "Found X collections"
    match = re.search(r'Found (\d+) collections', line)
    if match:
        count = match.group(1)
        running_tasks[task_id]['progress']['message'] = f'发现了 {count} 个商品分类'
        running_tasks[task_id]['progress']['total'] = int(count)
        return

    # 解析统计信息
    if '扫描分类数:' in line:
        match = re.search(r'扫描分类数:\s*(\d+)', line)
        if match and task_id in running_tasks:
            running_tasks[task_id]['stats'] = {'collections': int(match.group(1))}

    if '商品总数:' in line:
        match = re.search(r'商品总数:\s*(\d+)', line)
        if match and task_id in running_tasks:
            if 'stats' not in running_tasks[task_id]:
                running_tasks[task_id]['stats'] = {}
            running_tasks[task_id]['stats']['total_products'] = int(match.group(1))

    if '新增商品:' in line:
        match = re.search(r'新增商品:\s*(\d+)', line)
        if match and task_id in running_tasks:
            if 'stats' not in running_tasks[task_id]:
                running_tasks[task_id]['stats'] = {}
            running_tasks[task_id]['stats']['new_products'] = int(match.group(1))

    if '执行耗时:' in line:
        match = re.search(r'执行耗时:\s*([\d.]+)\s*秒', line)
        if match and task_id in running_tasks:
            if 'stats' not in running_tasks[task_id]:
                running_tasks[task_id]['stats'] = {}
            running_tasks[task_id]['stats']['duration'] = float(match.group(1))


def _get_current_steps(task_id):
    """获取当前活跃的步骤列表（多商品时为当前商品的步骤，单商品时为全局步骤）"""
    if 'current_product' in running_tasks[task_id]:
        return running_tasks[task_id]['current_product'].get('steps', [])
    return running_tasks[task_id].get('test_steps', [])


def _save_product_result(task_id):
    """保存当前商品的测试结果到product_results"""
    if task_id not in running_tasks:
        return

    if 'current_product' not in running_tasks[task_id]:
        return

    current = running_tasks[task_id]['current_product']

    # 检查是否有有效的步骤数据
    if not current.get('steps'):
        return

    product_id = current.get('id', f"product_{current.get('index', 0)}")

    # 保存到product_results
    if 'product_results' not in running_tasks[task_id]:
        running_tasks[task_id]['product_results'] = {}

    running_tasks[task_id]['product_results'][product_id] = {
        'name': current.get('name', ''),
        'index': current.get('index', 0),
        'steps': current.get('steps', []).copy(),  # 复制步骤列表
        'status': 'passed' if all(s.get('status') == 'passed' for s in current.get('steps', [])) else 'failed'
    }

    # 同时更新test_steps（保持兼容性）
    if 'test_steps' not in running_tasks[task_id]:
        running_tasks[task_id]['test_steps'] = []
    running_tasks[task_id]['test_steps'].extend(current.get('steps', []))

    # 清除current_product，准备下一个商品测试
    del running_tasks[task_id]['current_product']


def _find_latest_report():
    """查找最新的测试报告文件

    Returns:
        最新报告的ID（不含扩展名），如 'batch_test_20251205_151606'
        如果没有找到报告，返回 None
    """
    latest_file = None
    latest_time = None

    # 查找所有 batch_test_*.json 文件
    for report_file in REPORTS_DIR.glob('batch_test_*.json'):
        try:
            mtime = report_file.stat().st_mtime
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_file = report_file
        except Exception:
            pass

    # 也查找 test_*.json 文件
    for report_file in REPORTS_DIR.glob('test_*.json'):
        try:
            mtime = report_file.stat().st_mtime
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_file = report_file
        except Exception:
            pass

    if latest_file:
        return latest_file.stem  # 返回文件名（不含扩展名）

    return None


@app.route('/')
def index():
    """首页 - 工作台"""
    return render_template('index.html')


@app.route('/products')
def products():
    """商品管理页面"""
    return render_template('products.html')


@app.route('/tests')
def tests():
    """测试执行页面"""
    return render_template('tests.html')


@app.route('/reports')
def reports():
    """报告中心页面"""
    return render_template('reports.html')


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
        return jsonify({'products': [], 'total': 0, 'metadata': {}})

    try:
        with open(products_file) as f:
            data = json.load(f)

        # 处理新格式：{metadata: {...}, products: [...]}
        if isinstance(data, dict) and 'products' in data:
            products = data['products']
            metadata = data.get('metadata', {})
        else:
            # 兼容旧格式：直接是数组
            products = data if isinstance(data, list) else []
            metadata = {}

        return jsonify({
            'products': products,
            'total': len(products),
            'metadata': metadata
        })
    except Exception as e:
        print(f"[ERROR] Failed to load products: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tests/run', methods=['POST'])
def run_tests():
    """运行测试

    支持多种测试范围：
    - 单个商品: product_id 参数
    - 自定义多选: product_ids 参数（数组）
    - 按分类: category 参数
    - 所有商品: 无特定参数（或明确的all范围）
    """
    global active_test_task_id

    data = request.json or {}
    test_mode = data.get('test_mode', 'quick')  # quick 或 full

    # 使用锁保护检查和设置active_test_task_id
    with task_lock:
        # 检查是否有正在运行的测试
        if active_test_task_id and active_test_task_id in running_tasks:
            active_task = running_tasks[active_test_task_id]
            if active_task.get('status') == 'running':
                # 返回冲突信息，让前端处理
                return jsonify({
                    'conflict': True,
                    'active_task_id': active_test_task_id,
                    'active_task_started': active_task.get('started_at'),
                    'active_task_params': active_task.get('params', {}),
                    'message': '已有测试正在运行'
                }), 409

        # 构建测试命令
        # 优先级: product_id > product_ids > category > all

        if data.get('product_id'):
            # 单个商品测试
            command = [
                './run.sh',
                'python3',
                'scripts/run_product_test.py',
                '--product-id', data['product_id'],
                '--mode', test_mode
            ]
        elif data.get('product_ids') and len(data.get('product_ids', [])) > 0:
            # 自定义多选商品测试
            product_ids = data['product_ids']

            if len(product_ids) == 1:
                # 只选了一个商品，使用单商品测试脚本
                command = [
                    './run.sh',
                    'python3',
                    'scripts/run_product_test.py',
                    '--product-id', product_ids[0],
                    '--mode', test_mode
                ]
            else:
                # 多个商品，使用批量测试脚本并传递商品ID列表
                command = [
                    './run.sh',
                    'python3',
                    'scripts/batch_test_products.py',
                    '--mode', test_mode,
                    '--product-ids', ','.join(product_ids)  # 逗号分隔的商品ID列表
                ]
        else:
            # 使用批量测试脚本（按分类或所有商品）
            command = [
                './run.sh',
                'python3',
                'scripts/batch_test_products.py',
                '--mode', test_mode
            ]

            # 添加过滤参数
            if data.get('priority'):
                command.extend(['--priority', data['priority']])

            if data.get('category'):
                command.extend(['--category', data['category']])

        task_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        running_tasks[task_id] = {
            'status': 'running',
            'started_at': datetime.now().isoformat(),
            'params': data,
            'test_steps': [],  # 存储测试步骤
            'test_mode': test_mode,  # 记录测试模式
            'product_results': {}  # 存储多商品测试结果（按商品分组）
        }

        # 设置为当前活跃测试
        active_test_task_id = task_id

    # 后台执行（在锁外启动线程）
    def run_test():
        global active_test_task_id
        run_command(command, task_id)
        # 测试完成后清除活跃标记
        with task_lock:
            if active_test_task_id == task_id:
                active_test_task_id = None

    thread = threading.Thread(target=run_test)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started'})


@app.route('/api/tests/status/<task_id>')
def test_status(task_id):
    """查询测试状态"""
    if task_id not in running_tasks:
        return jsonify({'error': 'Task not found'}), 404

    # 排除不可序列化的字段（如process对象）
    task_data = {k: v for k, v in running_tasks[task_id].items() if k != 'process'}
    return jsonify(task_data)


@app.route('/api/tests/stop/<task_id>', methods=['POST'])
def stop_test(task_id):
    """停止测试任务

    Args:
        task_id: 要停止的任务ID

    Returns:
        停止结果
    """
    if task_id not in running_tasks:
        return jsonify({'error': 'Task not found'}), 404

    success = stop_task(task_id)

    if success:
        return jsonify({
            'success': True,
            'message': '测试已停止',
            'task_id': task_id
        })
    else:
        return jsonify({
            'success': False,
            'message': '停止测试失败'
        }), 500


@app.route('/api/tests/active')
def get_active_test():
    """获取当前活跃的测试任务"""
    global active_test_task_id

    if active_test_task_id and active_test_task_id in running_tasks:
        task = running_tasks[active_test_task_id]
        if task.get('status') == 'running':
            return jsonify({
                'has_active': True,
                'task_id': active_test_task_id,
                'started_at': task.get('started_at'),
                'params': task.get('params', {}),
                'test_mode': task.get('test_mode')
            })

    return jsonify({'has_active': False})


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
                        'test_mode': data.get('test_mode', ''),
                        'test_scope': data.get('test_scope', ''),
                        'test_config': data.get('test_config', {}),
                        'path': str(report_dir.relative_to(PROJECT_ROOT))
                    })
                except:
                    pass

    # 也查找批量测试报告
    for report_file in REPORTS_DIR.glob('batch_test_*.json'):
        try:
            with open(report_file) as f:
                data = json.load(f)

            # 从文件名提取时间戳
            filename = report_file.stem
            reports.append({
                'id': filename,
                'timestamp': data.get('timestamp', ''),
                'summary': data.get('summary', {}),
                'test_mode': data.get('test_mode', ''),
                'test_scope': data.get('test_scope', ''),
                'test_config': data.get('test_config', {}),
                'path': str(report_file.relative_to(PROJECT_ROOT))
            })
        except:
            pass

    # 查找单商品测试报告文件 (test_*.json，排除目录形式的)
    for report_file in REPORTS_DIR.glob('test_*.json'):
        try:
            with open(report_file) as f:
                data = json.load(f)

            filename = report_file.stem
            # 避免重复添加（如果同名目录已处理过）
            if any(r['id'] == filename for r in reports):
                continue

            reports.append({
                'id': filename,
                'timestamp': data.get('timestamp', ''),
                'summary': data.get('summary', {}),
                'test_mode': data.get('test_mode', ''),
                'test_scope': data.get('test_scope', ''),
                'test_config': data.get('test_config', {}),
                'path': str(report_file.relative_to(PROJECT_ROOT))
            })
        except:
            pass

    # 按时间倒序排序
    reports.sort(key=lambda x: x['timestamp'], reverse=True)

    return jsonify({'reports': reports, 'total': len(reports)})


@app.route('/api/reports/detail/<report_id>')
def report_detail(report_id):
    """获取报告详情

    Args:
        report_id: 报告ID（目录名或文件名）

    Returns:
        报告详细内容
    """
    # 尝试查找目录形式的报告
    report_dir = REPORTS_DIR / report_id
    if report_dir.is_dir():
        result_file = report_dir / 'test_results.json'
        if result_file.exists():
            try:
                with open(result_file) as f:
                    data = json.load(f)
                data['id'] = report_id
                return jsonify(data)
            except Exception as e:
                return jsonify({'error': f'读取报告失败: {str(e)}'}), 500

    # 尝试查找文件形式的报告
    report_file = REPORTS_DIR / f'{report_id}.json'
    if report_file.exists():
        try:
            with open(report_file) as f:
                data = json.load(f)
            data['id'] = report_id
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': f'读取报告失败: {str(e)}'}), 500

    return jsonify({'error': '报告不存在'}), 404


@app.route('/api/reports/delete', methods=['POST'])
def delete_reports():
    """批量删除报告

    请求体:
        {
            "ids": ["report_id_1", "report_id_2", ...]
        }

    Returns:
        删除结果
    """
    import shutil

    data = request.json or {}
    ids_to_delete = data.get('ids', [])

    if not ids_to_delete:
        return jsonify({'error': '未指定要删除的报告'}), 400

    deleted = []
    failed = []

    for report_id in ids_to_delete:
        try:
            report_found = False

            # 尝试删除目录形式的报告
            report_dir = REPORTS_DIR / report_id
            if report_dir.is_dir():
                shutil.rmtree(report_dir)
                report_found = True

            # 尝试删除文件形式的报告
            report_file = REPORTS_DIR / f'{report_id}.json'
            if report_file.exists():
                report_file.unlink()
                report_found = True

            # 始终尝试删除对应的AI分析报告（无论主报告是否存在）
            ai_report_file = REPORTS_DIR / f'{report_id}_ai_analysis.json'
            if ai_report_file.exists():
                ai_report_file.unlink()

            # 检查是否有任何相关的截图或其他资源文件
            # 模式: {report_id}_*.png, {report_id}_*.jpg 等
            for related_file in REPORTS_DIR.glob(f'{report_id}_*'):
                if related_file.is_file():
                    related_file.unlink()

            if report_found:
                deleted.append(report_id)
            else:
                failed.append({'id': report_id, 'reason': '报告不存在'})

        except Exception as e:
            failed.append({'id': report_id, 'reason': str(e)})

    return jsonify({
        'success': len(failed) == 0,
        'deleted': deleted,
        'failed': failed,
        'message': f'成功删除 {len(deleted)} 份报告' + (f', {len(failed)} 份失败' if failed else '')
    })


@app.route('/api/reports/ai/<report_id>')
def get_ai_analysis(report_id):
    """获取报告的AI分析

    Args:
        report_id: 报告ID

    Returns:
        AI分析内容
    """
    # 查找AI分析文件
    ai_file = REPORTS_DIR / f'{report_id}_ai_analysis.json'

    if ai_file.exists():
        try:
            with open(ai_file) as f:
                data = json.load(f)
            return jsonify(data)
        except Exception as e:
            return jsonify({'error': f'读取AI分析失败: {str(e)}'}), 500

    # 也尝试在报告目录内查找
    report_dir = REPORTS_DIR / report_id
    if report_dir.is_dir():
        ai_file_in_dir = report_dir / 'ai_analysis.json'
        if ai_file_in_dir.exists():
            try:
                with open(ai_file_in_dir) as f:
                    data = json.load(f)
                return jsonify(data)
            except Exception as e:
                return jsonify({'error': f'读取AI分析失败: {str(e)}'}), 500

    return jsonify({'error': 'AI分析不存在，请先生成'}), 404


@app.route('/api/reports/ai/list')
def list_ai_reports():
    """获取所有AI分析报告列表

    Returns:
        AI分析报告列表
    """
    ai_reports = []

    # 查找所有AI分析文件 (格式: xxx_ai_analysis.json)
    for ai_file in REPORTS_DIR.glob('*_ai_analysis.json'):
        try:
            with open(ai_file) as f:
                data = json.load(f)

            # 从文件名提取报告ID
            report_id = ai_file.stem.replace('_ai_analysis', '')

            ai_reports.append({
                'id': ai_file.stem,
                'report_id': report_id,
                'created_at': data.get('created_at', data.get('timestamp', '')),
                'provider': data.get('provider', 'unknown'),
                'summary': data.get('summary', data.get('analysis', '')[:100] + '...' if data.get('analysis') else '')
            })
        except Exception:
            pass

    # 也查找报告目录内的AI分析文件
    for report_dir in REPORTS_DIR.glob('test_*'):
        if report_dir.is_dir():
            ai_file = report_dir / 'ai_analysis.json'
            if ai_file.exists():
                try:
                    with open(ai_file) as f:
                        data = json.load(f)

                    ai_reports.append({
                        'id': f"{report_dir.name}_ai",
                        'report_id': report_dir.name,
                        'created_at': data.get('created_at', data.get('timestamp', '')),
                        'provider': data.get('provider', 'unknown'),
                        'summary': data.get('summary', data.get('analysis', '')[:100] + '...' if data.get('analysis') else '')
                    })
                except Exception:
                    pass

    # 按创建时间倒序排序
    ai_reports.sort(key=lambda x: x['created_at'], reverse=True)

    return jsonify({
        'ai_reports': ai_reports,
        'total': len(ai_reports)
    })


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


@app.route('/api/reports/ai/config-status')
def ai_config_status():
    """检查AI配置状态

    Returns:
        AI提供商的配置状态
    """
    import os
    from dotenv import load_dotenv
    load_dotenv()

    providers = {
        'deepseek': {
            'name': 'DeepSeek',
            'configured': bool(os.getenv('DEEPSEEK_API_KEY')),
            'env_key': 'DEEPSEEK_API_KEY',
            'help_url': 'https://platform.deepseek.com/'
        },
        'claude': {
            'name': 'Claude',
            'configured': bool(os.getenv('CLAUDE_API_KEY')),
            'env_key': 'CLAUDE_API_KEY',
            'help_url': 'https://console.anthropic.com/'
        }
    }

    # 检查是否有任何可用的AI提供商
    any_configured = any(p['configured'] for p in providers.values())

    return jsonify({
        'any_configured': any_configured,
        'providers': providers,
        'config_help': '请在项目根目录创建 .env 文件并设置对应的 API Key'
    })


@app.route('/api/reports/ai/generate', methods=['POST'])
def generate_ai_report():
    """生成 AI 报告

    请求体:
        {
            "provider": "deepseek",  # AI提供商，默认deepseek
            "summary_only": false,   # 是否仅生成摘要
            "report_id": "xxx"       # 可选，指定要分析的报告ID
        }
    """
    data = request.json or {}
    provider = data.get('provider', 'deepseek')
    report_id = data.get('report_id')

    # 如果是 'latest' 或未指定，查找最新的报告文件
    if not report_id or report_id == 'latest':
        latest_report = _find_latest_report()
        if not latest_report:
            return jsonify({
                'error': '没有找到可分析的测试报告',
                'message': '请先运行测试生成报告'
            }), 404
        report_id = latest_report
        print(f"[AI分析] 使用最新报告: {report_id}")

    command = [
        './run.sh',
        'python3',
        'scripts/generate_universal_ai_report.py',
        '--provider', provider,
        '--report-id', report_id  # 总是传递report_id
    ]

    if data.get('summary_only'):
        command.append('--summary-only')

    task_id = f"ai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    running_tasks[task_id] = {
        'status': 'running',
        'started_at': datetime.now().isoformat(),
        'report_id': report_id
    }

    # 后台执行
    def run_ai():
        run_command(command, task_id)

    thread = threading.Thread(target=run_ai)
    thread.start()

    return jsonify({'task_id': task_id, 'status': 'started', 'report_id': report_id})


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

    # 启动定时清理任务（每10分钟执行一次）
    def periodic_cleanup():
        import time
        while True:
            time.sleep(600)  # 每10分钟
            try:
                cleanup_old_tasks()
            except Exception as e:
                print(f"[任务清理] 清理失败: {e}")

    cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
    cleanup_thread.start()
    print("🧹 定时清理任务已启动（每10分钟）")

    print("✅ 服务已启动！")
    print("🌐 访问地址: http://localhost:5000")
    print("=" * 60)

    # 生产模式启动 (debug=False)
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
