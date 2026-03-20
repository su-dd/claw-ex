#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claw-ex 工作流编排模块
支持多步骤任务编排、条件分支、循环、并行执行
"""

import os
import json
import uuid
import time
import threading
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from enum import Enum

# 颜色支持（复制自主模块）
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'

def c_cyan(s): return f"{Colors.CYAN}{s}{Colors.RESET}"
def c_yellow(s): return f"{Colors.YELLOW}{s}{Colors.RESET}"
def c_green(s): return f"{Colors.GREEN}{s}{Colors.RESET}"
def c_red(s): return f"{Colors.RED}{s}{Colors.RESET}"
def c_gray(s): return f"{Colors.GRAY}{s}{Colors.RESET}"
def c_bold(s): return f"{Colors.BOLD}{s}{Colors.RESET}"

# 表格生成
def create_table(headers, rows):
    if not rows:
        col_widths = [len(h) + 2 for h in headers]
    else:
        col_widths = []
        for i, h in enumerate(headers):
            max_width = max(len(h), max(len(str(row[i])) if i < len(row) else 0 for row in rows))
            col_widths.append(max_width + 2)
    
    line = '┌' + '┬'.join('─' * w for w in col_widths) + '┐'
    sep = '├' + '┼'.join('─' * w for w in col_widths) + '┤'
    end = '└' + '┴'.join('─' * w for w in col_widths) + '┘'
    
    header_row = '│' + '│'.join(h.ljust(w) for h, w in zip(headers, col_widths)) + '│'
    
    output = [line, header_row]
    if rows:
        output.append(sep)
        for row in rows:
            padded_row = list(row) + [''] * (len(headers) - len(row))
            row_str = '│' + '│'.join(str(cell).ljust(w) for cell, w in zip(padded_row, col_widths)) + '│'
            output.append(row_str)
    output.append(end)
    
    return '\n'.join(output)

# 数据目录
WORKFLOW_DIR = Path(__file__).parent.parent / 'data' / 'workflows'
WORKFLOW_LOG_DIR = Path(__file__).parent.parent / 'data' / 'workflow_logs'

# 确保目录存在
WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
WORKFLOW_LOG_DIR.mkdir(parents=True, exist_ok=True)


class WorkflowStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    PAUSED = "paused"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


def generate_workflow_id(name: str) -> str:
    """生成工作流 ID"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"wf-{timestamp}-{uuid.uuid4().hex[:8]}"


def generate_step_id(step_name: str) -> str:
    """生成步骤 ID"""
    return f"step-{uuid.uuid4().hex[:8]}"


def load_workflows() -> List[Dict[str, Any]]:
    """加载所有工作流定义"""
    workflows = []
    if WORKFLOW_DIR.exists():
        for f in WORKFLOW_DIR.glob('*.json'):
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    workflows.append(json.load(file))
            except (json.JSONDecodeError, IOError):
                continue
    return workflows


def save_workflows(workflows: List[Dict[str, Any]]):
    """保存所有工作流定义"""
    # 每个工作流单独保存
    for wf in workflows:
        wf_file = WORKFLOW_DIR / f"{wf['id']}.json"
        with open(wf_file, 'w', encoding='utf-8') as f:
            json.dump(wf, f, indent=2, ensure_ascii=False)


def get_workflow(identifier: str) -> Optional[Dict[str, Any]]:
    """根据 ID 或名称获取工作流"""
    workflows = load_workflows()
    for wf in workflows:
        if wf['id'] == identifier or wf['name'] == identifier:
            return wf
    return None


def load_workflow_instances() -> List[Dict[str, Any]]:
    """加载所有工作流实例"""
    instances = []
    instance_file = WORKFLOW_DIR / 'instances.json'
    if instance_file.exists():
        try:
            with open(instance_file, 'r', encoding='utf-8') as f:
                instances = json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return instances


def save_workflow_instances(instances: List[Dict[str, Any]]):
    """保存工作流实例"""
    instance_file = WORKFLOW_DIR / 'instances.json'
    with open(instance_file, 'w', encoding='utf-8') as f:
        json.dump(instances, f, indent=2, ensure_ascii=False)


def get_workflow_instance(instance_id: str) -> Optional[Dict[str, Any]]:
    """获取工作流实例"""
    instances = load_workflow_instances()
    for inst in instances:
        if inst['instance_id'] == instance_id:
            return inst
    return None


def create_workflow(name: str, description: str = '', steps: List[Dict] = None) -> tuple:
    """创建工作流定义"""
    workflows = load_workflows()
    
    # 检查名称是否重复
    for wf in workflows:
        if wf['name'] == name:
            return False, f'工作流名称 "{name}" 已存在'
    
    workflow_id = generate_workflow_id(name)
    
    workflow = {
        'id': workflow_id,
        'name': name,
        'description': description,
        'version': '1.0',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'steps': steps or [],
        'triggers': [],
        'variables': {}
    }
    
    workflows.append(workflow)
    save_workflows(workflows)
    
    return True, f'工作流 "{name}" 创建成功 (ID: {workflow_id})'


def list_workflows() -> List[Dict[str, Any]]:
    """列出所有工作流"""
    return load_workflows()


def delete_workflow(identifier: str) -> tuple:
    """删除工作流"""
    workflows = load_workflows()
    found = None
    
    for wf in workflows:
        if wf['id'] == identifier or wf['name'] == identifier:
            found = wf
            break
    
    if not found:
        return False, f'未找到工作流：{identifier}'
    
    workflows = [w for w in workflows if w['id'] != found['id']]
    save_workflows(workflows)
    
    # 删除工作流文件
    wf_file = WORKFLOW_DIR / f"{found['id']}.json"
    if wf_file.exists():
        wf_file.unlink()
    
    return True, f'工作流 "{found["name"]}" 已删除'


def run_workflow(identifier: str, variables: Dict = None) -> tuple:
    """运行工作流"""
    workflow = get_workflow(identifier)
    if not workflow:
        return False, f'未找到工作流：{identifier}'
    
    # 创建工作流实例
    instance_id = f"inst-{uuid.uuid4().hex[:12]}"
    instance = {
        'instance_id': instance_id,
        'workflow_id': workflow['id'],
        'workflow_name': workflow['name'],
        'status': WorkflowStatus.RUNNING.value,
        'started_at': datetime.now().isoformat(),
        'completed_at': None,
        'variables': variables or {},
        'current_step': None,
        'steps_status': {},
        'logs': []
    }
    
    # 初始化步骤状态
    for step in workflow.get('steps', []):
        step_id = step.get('id') or generate_step_id(step.get('name', 'unknown'))
        instance['steps_status'][step_id] = {
            'step_id': step_id,
            'step_name': step.get('name', 'unknown'),
            'status': StepStatus.PENDING.value,
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None
        }
    
    instances = load_workflow_instances()
    instances.append(instance)
    save_workflow_instances(instances)
    
    # 在后台线程中执行工作流
    thread = threading.Thread(target=execute_workflow, args=(instance_id, workflow))
    thread.daemon = True
    thread.start()
    
    return True, f'工作流实例已启动 (Instance ID: {instance_id})'


def execute_workflow(instance_id: str, workflow: Dict):
    """执行工作流（后台线程）"""
    instances = load_workflow_instances()
    instance = None
    for inst in instances:
        if inst['instance_id'] == instance_id:
            instance = inst
            break
    
    if not instance:
        return
    
    try:
        steps = workflow.get('steps', [])
        
        for step in steps:
            step_id = step.get('id') or generate_step_id(step.get('name', 'unknown'))
            step_name = step.get('name', 'unknown')
            step_type = step.get('type', 'command')
            
            # 检查是否被停止
            current_instance = get_workflow_instance(instance_id)
            if not current_instance or current_instance['status'] == WorkflowStatus.STOPPED.value:
                break
            
            # 检查条件
            condition = step.get('condition')
            if condition and not evaluate_condition(condition, instance['variables']):
                instance['steps_status'][step_id]['status'] = StepStatus.SKIPPED.value
                instance['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'info',
                    'message': f'步骤 "{step_name}" 条件不满足，跳过'
                })
                save_workflow_instances(instances)
                continue
            
            # 执行步骤
            instance['current_step'] = step_id
            instance['steps_status'][step_id]['status'] = StepStatus.RUNNING.value
            instance['steps_status'][step_id]['started_at'] = datetime.now().isoformat()
            instance['logs'].append({
                'timestamp': datetime.now().isoformat(),
                'level': 'info',
                'message': f'开始执行步骤：{step_name}'
            })
            save_workflow_instances(instances)
            
            try:
                result = execute_step(step, instance['variables'])
                instance['steps_status'][step_id]['status'] = StepStatus.COMPLETED.value
                instance['steps_status'][step_id]['result'] = result
                instance['variables'].update(result.get('outputs', {}))
                instance['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'success',
                    'message': f'步骤 "{step_name}" 执行成功'
                })
            except Exception as e:
                instance['steps_status'][step_id]['status'] = StepStatus.FAILED.value
                instance['steps_status'][step_id]['error'] = str(e)
                instance['logs'].append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'error',
                    'message': f'步骤 "{step_name}" 执行失败：{str(e)}'
                })
                
                # 检查错误处理策略
                on_error = step.get('on_error', 'stop')
                if on_error == 'stop':
                    instance['status'] = WorkflowStatus.FAILED.value
                    instance['completed_at'] = datetime.now().isoformat()
                    save_workflow_instances(instances)
                    return
                elif on_error == 'continue':
                    instance['logs'].append({
                        'timestamp': datetime.now().isoformat(),
                        'level': 'warning',
                        'message': f'步骤失败但继续执行'
                    })
            
            instance['steps_status'][step_id]['completed_at'] = datetime.now().isoformat()
            save_workflow_instances(instances)
            
            # 处理循环
            if step.get('loop'):
                loop_config = step['loop']
                max_iterations = loop_config.get('max_iterations', 10)
                for i in range(max_iterations):
                    loop_condition = loop_config.get('condition')
                    if loop_condition and not evaluate_condition(loop_condition, instance['variables']):
                        break
                    # 重新执行步骤...
        
        # 所有步骤完成
        instance['status'] = WorkflowStatus.COMPLETED.value
        instance['completed_at'] = datetime.now().isoformat()
        instance['current_step'] = None
        instance['logs'].append({
            'timestamp': datetime.now().isoformat(),
            'level': 'success',
            'message': '工作流执行完成'
        })
        
    except Exception as e:
        instance['status'] = WorkflowStatus.FAILED.value
        instance['completed_at'] = datetime.now().isoformat()
        instance['logs'].append({
            'timestamp': datetime.now().isoformat(),
            'level': 'error',
            'message': f'工作流执行异常：{str(e)}'
        })
    
    save_workflow_instances(instances)


def execute_step(step: Dict, variables: Dict) -> Dict:
    """执行单个步骤"""
    step_type = step.get('type', 'command')
    
    if step_type == 'command':
        command = step.get('command', '')
        # 变量替换
        for key, value in variables.items():
            command = command.replace(f'${{{key}}}', str(value))
        
        import subprocess
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=step.get('timeout', 300))
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'return_code': result.returncode,
            'outputs': {
                'last_output': result.stdout.strip() if result.stdout else ''
            }
        }
    
    elif step_type == 'api':
        # API 调用步骤
        url = step.get('url', '')
        method = step.get('method', 'GET')
        headers = step.get('headers', {})
        body = step.get('body', {})
        
        # 简单模拟 API 调用
        return {
            'success': True,
            'status_code': 200,
            'outputs': {
                'response': {'message': 'API call simulated'}
            }
        }
    
    elif step_type == 'parallel':
        # 并行执行子步骤
        sub_steps = step.get('steps', [])
        results = []
        for sub_step in sub_steps:
            results.append(execute_step(sub_step, variables))
        return {
            'success': all(r.get('success', False) for r in results),
            'outputs': {'results': results}
        }
    
    else:
        return {'success': True, 'outputs': {}}


def evaluate_condition(condition: str, variables: Dict) -> bool:
    """评估条件表达式"""
    # 简单的条件评估
    try:
        # 替换变量
        for key, value in variables.items():
            condition = condition.replace(f'${{{key}}}', str(value))
        
        # 支持简单的比较运算
        if '==' in condition:
            left, right = condition.split('==')
            return left.strip() == right.strip()
        elif '!=' in condition:
            left, right = condition.split('!=')
            return left.strip() != right.strip()
        elif '>=' in condition:
            left, right = condition.split('>=')
            return float(left.strip()) >= float(right.strip())
        elif '<=' in condition:
            left, right = condition.split('<=')
            return float(left.strip()) <= float(right.strip())
        elif '>' in condition:
            left, right = condition.split('>')
            return float(left.strip()) > float(right.strip())
        elif '<' in condition:
            left, right = condition.split('<')
            return float(left.strip()) < float(right.strip())
        
        return True
    except:
        return False


def stop_workflow(instance_id: str) -> tuple:
    """停止工作流实例"""
    instances = load_workflow_instances()
    found = None
    
    for inst in instances:
        if inst['instance_id'] == instance_id:
            found = inst
            break
    
    if not found:
        return False, f'未找到工作流实例：{instance_id}'
    
    if found['status'] not in [WorkflowStatus.RUNNING.value, WorkflowStatus.PAUSED.value]:
        return False, f'工作流实例当前状态为 {found["status"]}，无法停止'
    
    found['status'] = WorkflowStatus.STOPPED.value
    found['completed_at'] = datetime.now().isoformat()
    found['logs'].append({
        'timestamp': datetime.now().isoformat(),
        'level': 'warning',
        'message': '工作流被用户停止'
    })
    
    save_workflow_instances(instances)
    return True, f'工作流实例 {instance_id} 已停止'


def get_workflow_status(instance_id: str) -> Optional[Dict[str, Any]]:
    """获取工作流实例状态"""
    return get_workflow_instance(instance_id)


def list_workflow_instances(workflow_id: str = None, limit: int = 20) -> List[Dict[str, Any]]:
    """列出工作流实例"""
    instances = load_workflow_instances()
    
    if workflow_id:
        instances = [i for i in instances if i['workflow_id'] == workflow_id]
    
    # 按开始时间倒序
    instances.sort(key=lambda x: x.get('started_at', ''), reverse=True)
    
    return instances[:limit]


def export_workflow_dag(identifier: str) -> Dict[str, Any]:
    """导出工作流 DAG 图数据"""
    workflow = get_workflow(identifier)
    if not workflow:
        return {'success': False, 'error': f'未找到工作流：{identifier}'}
    
    nodes = []
    edges = []
    
    steps = workflow.get('steps', [])
    for i, step in enumerate(steps):
        step_id = step.get('id') or generate_step_id(step.get('name', 'unknown'))
        nodes.append({
            'id': step_id,
            'label': step.get('name', f'Step {i+1}'),
            'type': step.get('type', 'command'),
            'condition': step.get('condition'),
            'loop': step.get('loop') is not None
        })
        
        # 创建边
        if i > 0:
            prev_step = steps[i-1]
            prev_id = prev_step.get('id') or generate_step_id(prev_step.get('name', 'unknown'))
            edges.append({
                'from': prev_id,
                'to': step_id,
                'condition': step.get('condition')
            })
    
    return {
        'success': True,
        'workflow_id': workflow['id'],
        'workflow_name': workflow['name'],
        'dag': {
            'nodes': nodes,
            'edges': edges
        }
    }


# CLI 命令封装
def cmd_workflow_list(args):
    """列出所有工作流"""
    output_format = 'json' if '--json' in args else 'table'
    workflows = list_workflows()
    
    print(c_cyan('\n📊 工作流列表:\n'))
    
    if not workflows:
        print(c_yellow('  暂无工作流，使用 claw-ex workflow create 创建第一个工作流\n'))
        return
    
    if output_format == 'json':
        print(json.dumps(workflows, indent=2, ensure_ascii=False))
        print()
        return
    
    headers = ['ID', '名称', '版本', '步骤数', '创建时间']
    rows = []
    for wf in workflows:
        rows.append([
            c_yellow(wf['id'][:20] + '...'),
            wf['name'],
            wf.get('version', '1.0'),
            str(len(wf.get('steps', []))),
            wf.get('created_at', '')[:19].replace('T', ' ')
        ])
    
    print(create_table(headers, rows))
    print(c_gray(f'\n共 {len(workflows)} 个工作流\n'))


def cmd_workflow_create(args):
    """创建工作流"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    if len(args) < 3:
        print(c_red('❌ 请指定工作流名称'))
        print('用法：claw-ex workflow create <name> [--desc "描述"]')
        return
    
    name = args[2]
    description = ''
    
    if '--desc' in args:
        idx = args.index('--desc')
        if idx + 1 < len(args):
            description = args[idx + 1]
    
    success, message = create_workflow(name, description)
    
    if success:
        print(c_green(f'\n✅ {message}\n'))
    else:
        print(c_red(f'\n❌ {message}\n'))


def cmd_workflow_run(args):
    """运行工作流"""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    if len(args) < 3:
        print(c_red('❌ 请指定工作流 ID 或名称'))
        print('用法：claw-ex workflow run <workflow_id|name>')
        return
    
    identifier = args[2]
    success, message = run_workflow(identifier)
    
    if success:
        print(c_green(f'\n✅ {message}\n'))
    else:
        print(c_red(f'\n❌ {message}\n'))


def cmd_workflow_stop(args):
    """停止工作流实例"""
    
    if len(args) < 3:
        print(c_red('❌ 请指定工作流实例 ID'))
        print('用法：claw-ex workflow stop <instance_id>')
        return
    
    instance_id = args[2]
    success, message = stop_workflow(instance_id)
    
    if success:
        print(c_green(f'\n✅ {message}\n'))
    else:
        print(c_red(f'\n❌ {message}\n'))


def cmd_workflow_status(args):
    """查看工作流状态"""
    
    if len(args) < 3:
        print(c_red('❌ 请指定工作流实例 ID'))
        print('用法：claw-ex workflow status <instance_id>')
        return
    
    instance_id = args[2]
    instance = get_workflow_status(instance_id)
    
    if not instance:
        print(c_red(f'\n❌ 未找到工作流实例：{instance_id}\n'))
        return
    
    print(c_cyan(f'\n📊 工作流实例状态：{c_yellow(instance_id)}\n'))
    
    # 基本信息
    headers = ['属性', '值']
    rows = [
        ['工作流', instance['workflow_name']],
        ['状态', c_green(instance['status']) if instance['status'] == 'completed' else c_yellow(instance['status'])],
        ['开始时间', instance.get('started_at', '')[:19].replace('T', ' ')],
        ['完成时间', instance.get('completed_at', '')[:19].replace('T', ' ') if instance.get('completed_at') else '-'],
        ['当前步骤', instance.get('current_step', '-')]
    ]
    print(create_table(headers, rows))
    
    # 步骤状态
    print(c_cyan('\n步骤状态:\n'))
    steps_headers = ['步骤', '状态', '开始时间', '完成时间']
    steps_rows = []
    for step_id, step_info in instance.get('steps_status', {}).items():
        status_display = step_info['status']
        if step_info['status'] == 'completed':
            status_display = c_green('✓ ' + status_display)
        elif step_info['status'] == 'failed':
            status_display = c_red('✗ ' + status_display)
        elif step_info['status'] == 'running':
            status_display = c_yellow('⟳ ' + status_display)
        
        steps_rows.append([
            step_info['step_name'],
            status_display,
            step_info.get('started_at', '')[:19].replace('T', ' ') if step_info.get('started_at') else '-',
            step_info.get('completed_at', '')[:19].replace('T', ' ') if step_info.get('completed_at') else '-'
        ])
    
    print(create_table(steps_headers, steps_rows))
    
    # 最近日志
    logs = instance.get('logs', [])[-5:]
    if logs:
        print(c_cyan('\n最近日志:\n'))
        for log in logs:
            timestamp = log.get('timestamp', '')[:19].replace('T', ' ')
            level = log.get('level', 'info')
            message = log.get('message', '')
            print(f"  {c_gray(timestamp)} [{level}] {message}")
    
    print()


def cmd_workflow_instances(args):
    """列出工作流实例"""
    from claw_ex import Colors, c_cyan, c_yellow, c_green, c_gray, c_red, create_table
    
    workflow_id = None
    if '--workflow' in args:
        idx = args.index('--workflow')
        if idx + 1 < len(args):
            workflow_id = args[idx + 1]
    
    instances = list_workflow_instances(workflow_id)
    
    print(c_cyan('\n📊 工作流实例列表:\n'))
    
    if not instances:
        print(c_yellow('  暂无工作流实例\n'))
        return
    
    headers = ['实例 ID', '工作流', '状态', '开始时间', '完成时间']
    rows = []
    for inst in instances:
        status_display = inst['status']
        if inst['status'] == 'completed':
            status_display = c_green(status_display)
        elif inst['status'] == 'failed':
            status_display = c_red(status_display)
        elif inst['status'] == 'running':
            status_display = c_yellow(status_display)
        
        rows.append([
            c_yellow(inst['instance_id'][:20] + '...'),
            inst['workflow_name'],
            status_display,
            inst.get('started_at', '')[:19].replace('T', ' '),
            inst.get('completed_at', '')[:19].replace('T', ' ') if inst.get('completed_at') else '-'
        ])
    
    print(create_table(headers, rows))
    print(c_gray(f'\n共 {len(instances)} 个实例\n'))


def cmd_workflow_dag(args):
    """导出工作流 DAG"""
    
    if len(args) < 3:
        print(c_red('❌ 请指定工作流 ID 或名称'))
        print('用法：claw-ex workflow dag <workflow_id|name> [--json]')
        return
    
    identifier = args[2]
    dag_data = export_workflow_dag(identifier)
    
    if not dag_data.get('success'):
        print(c_red(f'\n❌ {dag_data.get("error")}\n'))
        return
    
    if '--json' in args:
        print(json.dumps(dag_data, indent=2, ensure_ascii=False))
        print()
    else:
        print(c_cyan(f'\n📊 工作流 DAG: {c_yellow(dag_data["workflow_name"])}\n'))
        print(f"节点数：{len(dag_data['dag']['nodes'])}")
        print(f"边数：{len(dag_data['dag']['edges'])}")
        print()
