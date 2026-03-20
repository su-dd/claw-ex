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
            'list': cmd_config_list
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

{c_bold('全局选项:')}
  {c_cyan('-h, --help')}      显示帮助信息
  {c_cyan('-v, --version')}   显示版本号
  {c_cyan('--no-color')}      禁用颜色输出

{c_bold('示例:')}
  python3 claw-ex.py env list           # 列出环境变量
  python3 claw-ex.py task list          # 列出所有任务
  python3 claw-ex.py --help             # 显示此帮助

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
