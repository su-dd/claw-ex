#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
claw-ex - OpenClaw CLI 终端程序
尚书省任务管理工具 - 工部开发
"""

import sys
import os
import json
from datetime import datetime

# 自动添加 src 目录到 Python 路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# 颜色支持
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GRAY = '\033[90m'
    
    @classmethod
    def disable(cls):
        cls.RESET = ''
        cls.BOLD = ''
        cls.RED = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.GRAY = ''

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

# 命令实现
def cmd_env_list():
    print(c_cyan('\n📦 OpenClaw 环境变量:\n'))
    headers = ['变量', '值']
    rows = [
        ['PYTHON_VERSION', sys.version.split()[0]],
        ['PLATFORM', sys.platform],
        ['PWD', os.getcwd()],
        ['OPENCLAW_HOME', os.environ.get('OPENCLAW_HOME', '~/.openclaw')],
        ['WORKSPACE', os.environ.get('OPENCLAW_WORKSPACE', '未设置')],
        ['CHANNEL', os.environ.get('OPENCLAW_CHANNEL', '未设置')]
    ]
    print(create_table(headers, rows))
    print()

def cmd_env_info():
    import platform
    
    print(c_cyan('\n💻 系统信息:\n'))
    headers = ['属性', '值']
    
    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_total = f"{mem.total // (1024**3)} GB"
        mem_avail = f"{mem.available // (1024**3)} GB"
    except ImportError:
        mem_total = 'N/A'
        mem_avail = 'N/A'
    
    rows = [
        ['平台', f"{sys.platform} {platform.machine()}"],
        ['Python 版本', sys.version.split()[0]],
        ['主机名', platform.node()],
        ['内存总量', mem_total],
        ['可用内存', mem_avail]
    ]
    print(create_table(headers, rows))
    print()

def cmd_env_check():
    print(c_cyan('\n🔍 环境检查:\n'))
    checks = [
        ('Python 版本', sys.version_info >= (3, 8)),
        ('工作目录', bool(os.environ.get('OPENCLAW_WORKSPACE'))),
    ]
    all_pass = True
    for name, passed in checks:
        icon = c_green('✓') if passed else c_red('✗')
        status = c_green('通过') if passed else c_red('失败')
        print(f"  {icon} {name}: {status}")
        if not passed:
            all_pass = False
    print()
    if all_pass:
        print(c_green('✅ 所有检查通过!\n'))
    else:
        print(c_red('❌ 存在关键问题\n'))

def cmd_env_create(env_name, description=''):
    """创建新环境"""
    from env_config import create_environment
    
    print(c_cyan(f'\n📦 创建环境：{c_yellow(env_name)}\n'))
    
    success, message = create_environment(env_name, description)
    
    if success:
        print(c_green(f'✅ {message}\n'))
        print(c_gray('提示：使用 claw-ex env switch <name> 切换到新环境\n'))
    else:
        print(c_red(f'❌ {message}\n'))
        sys.exit(1)

def cmd_env_switch(env_name):
    """切换到指定环境"""
    from env_config import switch_environment, get_environment
    
    print(c_cyan(f'\n🔄 切换环境：{c_yellow(env_name)}\n'))
    
    success, message = switch_environment(env_name)
    
    if success:
        print(c_green(f'✅ {message}\n'))
        
        # 显示新环境信息
        env = get_environment(env_name)
        if env:
            headers = ['属性', '值']
            rows = [
                ['环境名称', env['name']],
                ['描述', env.get('description', '无')],
                ['创建时间', env.get('created_at', '未知')[:19].replace('T', ' ')]
            ]
            print(create_table(headers, rows))
            print()
    else:
        print(c_red(f'❌ {message}\n'))
        sys.exit(1)

def cmd_env_list_detailed():
    """列出所有环境（增强版）"""
    from env_config import list_environments
    
    envs = list_environments()
    
    print(c_cyan('\n📦 环境列表:\n'))
    
    if not envs:
        print(c_yellow('  暂无环境，使用 claw-ex env create <name> 创建第一个环境\n'))
        return
    
    headers = ['名称', '描述', '状态', '创建时间']
    rows = []
    for env in envs:
        status_parts = []
        if env['is_active']:
            status_parts.append(c_green('● 当前'))
        if env['is_default']:
            status_parts.append(c_cyan('★ 默认'))
        status = ' '.join(status_parts) if status_parts else ''
        
        created = env.get('created_at', '')[:19].replace('T', ' ') if env.get('created_at') else ''
        
        rows.append([
            c_yellow(env['name']) if env['is_active'] else env['name'],
            env.get('description', '')[:20] + ('...' if len(env.get('description', '')) > 20 else ''),
            status,
            created
        ])
    
    print(create_table(headers, rows))
    print(c_gray(f'\n共 {len(envs)} 个环境\n'))

def cmd_agent_list():
    print(c_cyan('\n🤖 Agent 列表:\n'))
    headers = ['ID', '名称', '状态', '部门']
    rows = [
        ['agent:shangshu:main', '尚书省', c_green('active'), '尚书省'],
        ['agent:gongbu:main', '工部', c_green('active'), '工部'],
        ['agent:libu:hr', '吏部', c_green('active'), '吏部']
    ]
    print(create_table(headers, rows))
    print(c_gray('\n共 3 个 Agent\n'))

def cmd_agent_status(agent_id):
    print(c_cyan(f'\n📊 Agent 状态：{c_yellow(agent_id)}\n'))
    headers = ['属性', '值']
    rows = [
        ['ID', agent_id],
        ['状态', c_green('active')],
        ['运行时间', '2h 15m'],
        ['任务数', '5']
    ]
    print(create_table(headers, rows))
    print()

def cmd_task_list():
    print(c_cyan('\n📋 任务列表:\n'))
    headers = ['任务 ID', '标题', '状态', '部门', '优先级']
    rows = [
        ['JJC-20260320-001', '系统架构设计', c_green('Done'), '工部', c_red('high')],
        ['JJC-20260320-002', 'claw-ex 终端程序开发', c_yellow('Doing'), '工部', c_red('high')],
        ['JJC-20260320-003', '文档编写', c_gray('Todo'), '工部', c_yellow('medium')]
    ]
    print(create_table(headers, rows))
    print(c_gray('\n共 3 个任务\n'))

def cmd_task_show(task_id):
    print(c_cyan(f'\n📄 任务详情：{c_yellow(task_id)}\n'))
    headers = ['属性', '值']
    rows = [
        ['标题', 'claw-ex 终端程序开发'],
        ['状态', c_yellow('Doing')],
        ['部门', '工部'],
        ['优先级', c_red('high')],
        ['创建时间', '2026-03-20 10:00'],
        ['更新时间', '2026-03-20 10:21']
    ]
    print(create_table(headers, rows))
    print()

def cmd_session_list():
    print(c_cyan('\n💬 会话列表:\n'))
    headers = ['会话 ID', 'Agent', '渠道', '状态']
    rows = [
        ['sess-001', 'agent:shangshu:main', 'feishu', c_green('active')],
        ['sess-002', 'agent:gongbu:main', 'feishu', c_green('active')],
        ['sess-003', 'agent:gongbu:subagent', 'feishu', c_green('active')]
    ]
    print(create_table(headers, rows))
    print(c_gray('\n共 3 个会话\n'))

def cmd_config_list():
    print(c_cyan('\n⚙️  当前配置:\n'))
    headers = ['分类', '键', '值']
    rows = [
        ['api', 'baseUrl', 'http://localhost:3000'],
        ['api', 'timeout', '5000'],
        ['display', 'theme', 'dark'],
        ['display', 'colors', 'true'],
        ['behavior', 'debug', 'false']
    ]
    print(create_table(headers, rows))
    print()

def cmd_config_validate(path=None, validate_all=False, strict=False, json_output=False):
    """验证配置文件"""
    # 添加兵部 workspace 到路径
    BINGBU_PATH = os.path.join(os.path.expanduser('~'), '.openclaw', 'workspace-bingbu')
    if BINGBU_PATH not in sys.path:
        sys.path.insert(0, BINGBU_PATH)
    
    try:
        from agent_config_validator import ConfigValidator
        
        validator = ConfigValidator()
        
        if validate_all:
            # 验证所有 Agent 配置
            result = validator.validate_all_agents()
            
            if json_output:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(c_cyan('\n🔍 Agent 配置验证报告\n'))
                print(c_bold('=' * 60))
                summary = result["summary"]
                print(f"总数：{summary['total']}")
                print(f"有效：{c_green(summary['valid'])}")
                print(f"无效：{c_red(summary['invalid'])}")
                print(f"通过率：{summary['pass_rate']}")
                print(c_bold('=' * 60) + '\n')
                
                for agent_id, details in result["details"].items():
                    status = c_green('✅') if details["valid"] else c_red('❌')
                    print(f"{status} {c_yellow(agent_id)}")
                    if details["errors"]:
                        for error in details["errors"]:
                            print(f"   {c_red('错误')}: {error}")
                    if details["warnings"]:
                        for warning in details["warnings"]:
                            print(f"   {c_yellow('警告')}: {warning}")
                print()
            
            sys.exit(0 if result["summary"]["invalid"] == 0 else 1)
        
        elif path:
            from pathlib import Path as FilePath
            p = FilePath(path)
            
            if p.is_file():
                result = validator.validate_file(str(p))
            elif p.is_dir():
                results = validator.validate_directory(str(p))
                result = {
                    "directory": str(p),
                    "files": results,
                    "summary": {
                        "total": len(results),
                        "valid": sum(1 for r in results if r["valid"]),
                        "invalid": sum(1 for r in results if not r["valid"]),
                    }
                }
            else:
                print(c_red(f'错误：路径不存在：{p}'))
                sys.exit(1)
            
            if json_output:
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(c_cyan(f'\n🔍 配置验证：{c_yellow(str(p))}\n'))
                print(c_bold('=' * 60))
                
                if "files" in result:
                    for file_result in result["files"]:
                        status = c_green('✅') if file_result["valid"] else c_red('❌')
                        print(f"{status} {file_result['file']}")
                        if file_result["errors"]:
                            for error in file_result["errors"]:
                                print(f"   {c_red('错误')}: {error}")
                        if file_result["warnings"]:
                            for warning in file_result["warnings"]:
                                print(f"   {c_yellow('警告')}: {warning}")
                    print(f"\n汇总：{c_green(result['summary']['valid'])}/{result['summary']['total']} 通过")
                else:
                    status = c_green('✅ 通过') if result["valid"] else c_red('❌ 失败')
                    print(f"验证结果：{status}")
                    print(f"文件：{result['file']}")
                    print(f"Agent: {result.get('agent_id', 'unknown')} - {result.get('agent_name', 'unknown')}")
                    
                    if result["errors"]:
                        print(f"\n{c_red(f'错误 ({len(result['errors'])})')}:")
                        for error in result["errors"]:
                            print(f"  - {error}")
                    
                    if result["warnings"]:
                        print(f"\n{c_yellow(f'警告 ({len(result['warnings'])})')}:")
                        for warning in result["warnings"]:
                            print(f"  - {warning}")
            
            has_errors = False
            if "files" in result:
                has_errors = result["summary"]["invalid"] > 0
            else:
                has_errors = not result["valid"]
            
            if strict:
                has_warnings = False
                if "files" in result:
                    has_warnings = any(len(r.get("warnings", [])) > 0 for r in result["files"])
                else:
                    has_warnings = len(result.get("warnings", [])) > 0
                has_errors = has_errors or has_warnings
            
            sys.exit(0 if not has_errors else 1)
        
        else:
            print(c_red('错误：请指定配置文件路径或使用 --all 参数'))
            print('使用 claw-ex config validate --help 查看帮助')
            sys.exit(1)
    
    except ImportError as e:
        print(c_red(f'错误：配置验证器导入失败：{e}'))
        print(f'请确保兵部 workspace 中有 agent_config_validator.py')
        sys.exit(1)
    except Exception as e:
        print(c_red(f'错误：{e}'))
        sys.exit(1)

# ==================== 日志管理命令 ====================

def cmd_logs_tail(follow=False, lines=100, level=None):
    """查看日志末尾"""
    import requests
    import time
    
    base_url = os.environ.get('CLAW_EX_API_URL', 'http://localhost:8000')
    
    if follow:
        print(c_cyan(f'\n📜 实时日志跟随 (按 Ctrl+C 退出):\n'))
        try:
            last_count = 0
            while True:
                resp = requests.get(f'{base_url}/api/logs/tail', params={'lines': 20, 'level': level})
                if resp.status_code == 200:
                    data = resp.json()
                    logs = data.get('logs', [])
                    if len(logs) > last_count:
                        for log in logs[last_count:]:
                            level_color = {
                                'DEBUG': c_gray,
                                'INFO': c_cyan,
                                'WARNING': c_yellow,
                                'ERROR': c_red
                            }.get(log.get('level', 'INFO'), lambda x: x)
                            print(f"{c_gray(log.get('timestamp', '')[:19])} {level_color(f'[{log.get(\"level\", \"INFO\")}]')} {log.get('message', '')}")
                        last_count = len(logs)
                time.sleep(1)
        except KeyboardInterrupt:
            print('\n退出日志跟随')
    else:
        resp = requests.get(f'{base_url}/api/logs/tail', params={'lines': lines, 'level': level})
        if resp.status_code == 200:
            data = resp.json()
            print(c_cyan(f'\n📜 最近 {len(data.get(\"logs\", []))} 条日志:\n'))
            for log in data.get('logs', []):
                level_color = {
                    'DEBUG': c_gray,
                    'INFO': c_cyan,
                    'WARNING': c_yellow,
                    'ERROR': c_red
                }.get(log.get('level', 'INFO'), lambda x: x)
                print(f"{c_gray(log.get('timestamp', '')[:19])} {level_color(f'[{log.get(\"level\", \"INFO\")}]')} {log.get('message', '')}")
        else:
            print(c_red(f'错误：{resp.status_code} - {resp.text}'))

def cmd_logs_export(output='logs_export.log', level=None, start_time=None, end_time=None):
    """导出日志"""
    import requests
    
    base_url = os.environ.get('CLAW_EX_API_URL', 'http://localhost:8000')
    
    payload = {
        'output_path': output,
        'level': level,
        'start_time': start_time,
        'end_time': end_time
    }
    
    resp = requests.post(f'{base_url}/api/logs/export', json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(c_green(f'\n✅ 日志导出成功!\n'))
        print(f"  文件：{c_cyan(data.get('path', output))}")
        print(f"  数量：{c_cyan(data.get('count', 0))} 条\n")
    else:
        print(c_red(f'错误：{resp.status_code} - {resp.text}'))

def cmd_logs_search(keyword, level=None, source=None, limit=100):
    """搜索日志"""
    import requests
    
    base_url = os.environ.get('CLAW_EX_API_URL', 'http://localhost:8000')
    
    params = {'keyword': keyword, 'limit': limit}
    if level:
        params['level'] = level
    if source:
        params['source'] = source
    
    resp = requests.get(f'{base_url}/api/logs/search', params=params)
    if resp.status_code == 200:
        data = resp.json()
        logs = data.get('logs', [])
        print(c_cyan(f'\n🔍 搜索结果：找到 {len(logs)} 条匹配日志\n'))
        for log in logs:
            level_color = {
                'DEBUG': c_gray,
                'INFO': c_cyan,
                'WARNING': c_yellow,
                'ERROR': c_red
            }.get(log.get('level', 'INFO'), lambda x: x)
            print(f"{c_gray(log.get('timestamp', '')[:19])} {level_color(f'[{log.get(\"level\", \"INFO\")}]')} {log.get('message', '')}")
    else:
        print(c_red(f'错误：{resp.status_code} - {resp.text}'))

def cmd_logs_stats():
    """日志统计"""
    import requests
    
    base_url = os.environ.get('CLAW_EX_API_URL', 'http://localhost:8000')
    
    resp = requests.get(f'{base_url}/api/logs/stats')
    if resp.status_code == 200:
        data = resp.json()
        print(c_cyan('\n📊 日志统计:\n'))
        headers = ['统计项', '数值']
        rows = [
            ['总行数', str(data.get('total_lines', 0))],
            ['文件大小', f"{data.get('file_size', 0) / 1024:.1f} KB"],
            ['轮转文件', str(data.get('rotated_files', 0))],
        ]
        
        by_level = data.get('by_level', {})
        for level, count in sorted(by_level.items()):
            rows.append([f'级别：{level}', str(count)])
        
        by_source = data.get('by_source', {})
        for source, count in sorted(by_source.items()):
            rows.append([f'来源：{source}', str(count)])
        
        print(create_table(headers, rows))
        print()
    else:
        print(c_red(f'错误：{resp.status_code} - {resp.text}'))

# ==================== 批量操作命令 ====================

def cmd_batch_start(pattern, filter_expr=None):
    """批量启动 Agent"""
    import requests
    
    base_url = os.environ.get('CLAW_EX_API_URL', 'http://localhost:8000')
    
    payload = {'pattern': pattern}
    if filter_expr:
        payload['filter'] = filter_expr
    
    resp = requests.post(f'{base_url}/api/batch/start', json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(c_green(f'\n✅ 批量启动完成!\n'))
        print(f"  任务 ID: {c_cyan(data.get('job_id', 'N/A'))}")
        print(f"  影响数量：{c_cyan(data.get('affected', 0))}")
        print(f"  消息：{c_cyan(data.get('message', ''))}\n")
    else:
        print(c_red(f'错误：{resp.status_code} - {resp.text}'))

def cmd_batch_stop(pattern, ids=None):
    """批量停止任务"""
    import requests
    
    base_url = os.environ.get('CLAW_EX_API_URL', 'http://localhost:8000')
    
    payload = {'pattern': pattern}
    if ids:
        payload['ids'] = ids.split(',') if isinstance(ids, str) else ids
    
    resp = requests.post(f'{base_url}/api/batch/stop', json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(c_green(f'\n✅ 批量停止完成!\n'))
        print(f"  任务 ID: {c_cyan(data.get('job_id', 'N/A'))}")
        print(f"  影响数量：{c_cyan(data.get('affected', 0))}\n")
    else:
        print(c_red(f'错误：{resp.status_code} - {resp.text}'))

def cmd_batch_run(workflow, parallel=False, targets=None):
    """批量执行工作流"""
    import requests
    
    base_url = os.environ.get('CLAW_EX_API_URL', 'http://localhost:8000')
    
    payload = {
        'workflow': workflow,
        'parallel': parallel,
        'targets': targets.split(',') if targets else []
    }
    
    resp = requests.post(f'{base_url}/api/batch/run', json=payload)
    if resp.status_code == 200:
        data = resp.json()
        print(c_green(f'\n✅ 批量执行启动!\n'))
        print(f"  任务 ID: {c_cyan(data.get('job_id', 'N/A'))}")
        print(f"  工作流：{c_cyan(workflow)}")
        print(f"  并行模式：{c_cyan('是' if parallel else '否')}\n")
    else:
        print(c_red(f'错误：{resp.status_code} - {resp.text}'))

def cmd_batch_status(job_id):
    """查看批量任务状态"""
    import requests
    
    base_url = os.environ.get('CLAW_EX_API_URL', 'http://localhost:8000')
    
    resp = requests.get(f'{base_url}/api/batch/status/{job_id}')
    if resp.status_code == 200:
        data = resp.json()
        job = data.get('job', {})
        print(c_cyan(f'\n📋 批量任务状态:\n'))
        headers = ['属性', '值']
        rows = [
            ['任务 ID', job.get('job_id', 'N/A')],
            ['状态', c_green(job.get('status', 'unknown')) if job.get('status') == 'completed' else c_yellow(job.get('status', 'unknown'))],
            ['创建时间', job.get('created_at', 'N/A')],
            ['总数', str(job.get('total', 0))],
            ['已完成', str(job.get('completed', 0))],
            ['失败', str(job.get('failed', 0))]
        ]
        print(create_table(headers, rows))
        print()
    else:
        print(c_red(f'错误：{resp.status_code} - {resp.text}'))

# 命令映射
COMMANDS = {
    'env': {
        'description': '环境管理',
        'subcommands': {
            'list': cmd_env_list_detailed,
            'info': cmd_env_info,
            'check': cmd_env_check,
            'create': lambda: cmd_env_create(sys.argv[2] if len(sys.argv) > 2 else '', sys.argv[3] if len(sys.argv) > 3 else ''),
            'switch': lambda: cmd_env_switch(sys.argv[2] if len(sys.argv) > 2 else '')
        }
    },
    'agent': {
        'description': 'Agent 管理',
        'subcommands': {
            'list': cmd_agent_list,
            'status': lambda: cmd_agent_status('agent:unknown')
        }
    },
    'task': {
        'description': '任务管理',
        'subcommands': {
            'list': cmd_task_list,
            'show': lambda: cmd_task_show('JJC-unknown')
        }
    },
    'session': {
        'description': '会话管理',
        'subcommands': {
            'list': cmd_session_list
        }
    },
    'config': {
        'description': '配置管理',
        'subcommands': {
            'list': cmd_config_list,
            'validate': lambda: cmd_config_validate(
                path=sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith('-') else None,
                validate_all='--all' in sys.argv or '-a' in sys.argv,
                strict='--strict' in sys.argv or '-s' in sys.argv,
                json_output='--json' in sys.argv or '-j' in sys.argv
            )
        }
    },
    'logs': {
        'description': '日志管理',
        'subcommands': {
            'tail': lambda: cmd_logs_tail(
                follow='-f' in sys.argv or '--follow' in sys.argv,
                lines=int(sys.argv[sys.argv.index('--lines') + 1]) if '--lines' in sys.argv and len(sys.argv) > sys.argv.index('--lines') + 1 else 100,
                level=sys.argv[sys.argv.index('--level') + 1] if '--level' in sys.argv and len(sys.argv) > sys.argv.index('--level') + 1 else None
            ),
            'export': lambda: cmd_logs_export(
                output=sys.argv[sys.argv.index('--output') + 1] if '--output' in sys.argv and len(sys.argv) > sys.argv.index('--output') + 1 else 'logs_export.log',
                level=sys.argv[sys.argv.index('--level') + 1] if '--level' in sys.argv and len(sys.argv) > sys.argv.index('--level') + 1 else None
            ),
            'search': lambda: cmd_logs_search(
                keyword=sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else '',
                level=sys.argv[sys.argv.index('--level') + 1] if '--level' in sys.argv and len(sys.argv) > sys.argv.index('--level') + 1 else None
            ),
            'stats': cmd_logs_stats
        }
    },
    'batch': {
        'description': '批量操作',
        'subcommands': {
            'start': lambda: cmd_batch_start(
                pattern=sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else 'agent:*',
                filter_expr=sys.argv[sys.argv.index('--filter') + 1] if '--filter' in sys.argv and len(sys.argv) > sys.argv.index('--filter') + 1 else None
            ),
            'stop': lambda: cmd_batch_stop(
                pattern=sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else 'task:*',
                ids=sys.argv[sys.argv.index('--ids') + 1] if '--ids' in sys.argv and len(sys.argv) > sys.argv.index('--ids') + 1 else None
            ),
            'run': lambda: cmd_batch_run(
                workflow=sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else 'default',
                parallel='--parallel' in sys.argv,
                targets=sys.argv[sys.argv.index('--targets') + 1] if '--targets' in sys.argv and len(sys.argv) > sys.argv.index('--targets') + 1 else None
            ),
            'status': lambda: cmd_batch_status(sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else 'job-unknown')
        }
    }
}

def show_help():
    print(f"""
{c_cyan('claw-ex')} - {c_cyan('OpenClaw CLI 终端程序')}

{c_bold('用法:')}
  claw-ex <command> [subcommand] [options]

{c_bold('命令:')}
  {c_yellow('env')}       {COMMANDS['env']['description']}
  {c_yellow('agent')}     {COMMANDS['agent']['description']}
  {c_yellow('task')}      {COMMANDS['task']['description']}
  {c_yellow('session')}   {COMMANDS['session']['description']}
  {c_yellow('config')}    {COMMANDS['config']['description']}
  {c_yellow('logs')}      {COMMANDS['logs']['description']}
  {c_yellow('batch')}     {COMMANDS['batch']['description']}

{c_bold('子命令详情:')}
  {c_yellow('config validate')} <path|--all> [选项]  验证配置文件
    {c_gray('-a, --all')}      验证所有 Agent 配置
    {c_gray('-s, --strict')}   严格模式（警告视为错误）
    {c_gray('-j, --json')}     JSON 格式输出

{c_bold('全局选项:')}
  {c_cyan('-h, --help')}      显示帮助信息
  {c_cyan('-v, --version')}   显示版本号
  {c_cyan('--no-color')}      禁用颜色输出

{c_bold('示例:')}
  python3 claw-ex.py env list                    # 列出环境变量
  python3 claw-ex.py task list                   # 列出所有任务
  python3 claw-ex.py config validate --all       # 验证所有 Agent 配置
  python3 claw-ex.py logs tail -f --lines 100    # 实时日志跟随
  python3 claw-ex.py logs search "error" --level ERROR  # 搜索错误日志
  python3 claw-ex.py logs stats                  # 日志统计
  python3 claw-ex.py batch start "agent:*" --filter "dept=gongbu"  # 批量启动
  python3 claw-ex.py batch status job-123        # 查看批量任务状态
  python3 claw-ex.py --help                      # 显示此帮助

{c_gray('工部开发 · 尚书省任务管理工具')}
""")

def show_version():
    print('claw-ex v0.1.0')

def main():
    args = sys.argv[1:]
    
    # 处理全局选项
    if '--no-color' in args:
        Colors.disable()
        args.remove('--no-color')
    
    if not args or args[0] in ['-h', '--help']:
        show_help()
        return
    
    if args[0] in ['-v', '--version']:
        show_version()
        return
    
    cmd = args[0]
    
    if cmd not in COMMANDS:
        print(c_red(f'未知命令：{cmd}'))
        print('使用 claw-ex --help 查看可用命令')
        sys.exit(1)
    
    if len(args) == 1:
        print(f"{c_cyan(cmd)} - {COMMANDS[cmd]['description']}")
        print('\n子命令:')
        for sub in COMMANDS[cmd]['subcommands']:
            print(f"  {c_yellow(sub)}")
        print(f"\n使用 claw-ex {cmd} <subcommand> 执行子命令")
        return
    
    subcmd = args[1]
    
    if subcmd not in COMMANDS[cmd]['subcommands']:
        print(c_red(f'未知子命令：{subcmd}'))
        sys.exit(1)
    
    # 处理带参数的子命令
    if subcmd == 'status' and len(args) > 2:
        cmd_agent_status(args[2])
    elif subcmd == 'show' and len(args) > 2:
        cmd_task_show(args[2])
    elif subcmd == 'create' and len(args) > 2:
        # env create 命令需要特殊处理，因为参数已经在 lambda 中获取
        cmd_env_create(args[2], args[3] if len(args) > 3 else '')
    elif subcmd == 'switch' and len(args) > 2:
        # env switch 命令需要特殊处理
        cmd_env_switch(args[2])
    else:
        COMMANDS[cmd]['subcommands'][subcmd]()

if __name__ == '__main__':
    main()
