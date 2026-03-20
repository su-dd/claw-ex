#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
monitor 命令 - Agent 任务监控可视化
实时展示各 Agent 的任务执行状态、进展日志、资源消耗等信息
"""

import sys
import os
import json
import time
import argparse
from datetime import datetime

# 颜色支持（内联定义，避免依赖问题）
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

def get_sessions_data():
    """获取 sessions 数据（模拟 OpenClaw API）"""
    # 实际应从 OpenClaw sessions API 获取
    return {
        'sessions': [
            {
                'id': 'agent:zhongshu:main',
                'status': 'active',
                'channel': 'feishu',
                'created': '2026-03-20T08:00:00Z',
                'lastActive': '2026-03-20T12:38:00Z',
                'task': 'JJC-20260320-004',
                'progress': '尚书省派发任务中',
                'tokens': 15000,
                'cost': 0.045
            },
            {
                'id': 'agent:gongbu:subagent:0bd294f7',
                'status': 'active',
                'channel': 'feishu',
                'created': '2026-03-20T12:37:00Z',
                'lastActive': '2026-03-20T12:38:30Z',
                'task': 'JJC-20260320-004',
                'parent': 'agent:zhongshu:main',
                'progress': '需求分析阶段',
                'tokens': 5000,
                'cost': 0.015
            },
            {
                'id': 'agent:shangshu:main',
                'status': 'active',
                'channel': 'feishu',
                'created': '2026-03-20T09:00:00Z',
                'lastActive': '2026-03-20T12:37:00Z',
                'task': 'JJC-20260320-003',
                'progress': '任务派发完成',
                'tokens': 8000,
                'cost': 0.024
            }
        ]
    }

def cmd_monitor_list(options):
    """列出所有活跃 Agent 会话"""
    data = get_sessions_data()
    sessions = data['sessions']
    
    if options.json:
        print(json.dumps(sessions, indent=2, ensure_ascii=False))
        return
    
    if not sessions:
        print(c_yellow('\n暂无活跃会话\n'))
        return
    
    headers = ['Agent ID', '状态', '任务', '进展', 'Tokens', '成本']
    rows = []
    
    for s in sessions:
        status = c_green('● 活跃') if s['status'] == 'active' else c_gray('○ 空闲')
        tokens = c_gray(f"{s.get('tokens', 0):,}")
        cost = c_gray(f"${s.get('cost', 0):.4f}")
        rows.append([
            s['id'][:40],
            status,
            s.get('task', '-'),
            s.get('progress', '-')[:20],
            tokens,
            cost
        ])
    
    print(c_cyan('\n📊 Agent 会话监控列表:\n'))
    print(create_table(headers, rows))
    print(c_gray(f'\n共 {len(sessions)} 个活跃会话\n'))

def cmd_monitor_detail(session_id, options):
    """查看指定会话详情"""
    data = get_sessions_data()
    session = next((s for s in data['sessions'] if session_id in s['id']), None)
    
    if not session:
        print(c_red(f'\n未找到会话：{session_id}\n'))
        return
    
    if options.json:
        print(json.dumps(session, indent=2, ensure_ascii=False))
        return
    
    print(c_cyan(f'\n📄 会话详情：{c_yellow(session["id"])}\n'))
    
    headers = ['属性', '值']
    rows = [
        ['状态', c_green('活跃') if session['status'] == 'active' else c_gray('空闲')],
        ['渠道', session.get('channel', '-')],
        ['任务', session.get('task', '-')],
        ['进展', session.get('progress', '-')],
        ['创建时间', session.get('created', '-')],
        ['最后活跃', session.get('lastActive', '-')],
        ['Token 消耗', c_gray(f"{session.get('tokens', 0):,}")],
        ['成本', c_gray(f"${session.get('cost', 0):.4f}")]
    ]
    
    if 'parent' in session:
        rows.append(['父会话', session['parent']])
    
    print(create_table(headers, rows))
    print()

def cmd_monitor_watch(options):
    """实时监控模式（轮询刷新）"""
    interval = options.interval
    print(c_cyan(f'\n👁️  实时监控模式启动 (刷新间隔：{interval}秒)\n'))
    print(c_yellow('按 Ctrl+C 退出\n'))
    
    try:
        iteration = 0
        while True:
            iteration += 1
            os.system('clear' if os.name != 'nt' else 'cls')
            print(c_bold(f'\n═ 实时监控 (第{iteration}次刷新) {datetime.now().strftime("%H:%M:%S")} ═\n'))
            
            data = get_sessions_data()
            sessions = data['sessions']
            
            headers = ['Agent ID', '状态', '任务', '进展', 'Tokens', '成本']
            rows = []
            
            for s in sessions:
                status = c_green('● 活跃') if s['status'] == 'active' else c_gray('○ 空闲')
                tokens = c_gray(f"{s.get('tokens', 0):,}")
                cost = c_gray(f"${s.get('cost', 0):.4f}")
                rows.append([
                    s['id'][:35],
                    status,
                    s.get('task', '-'),
                    s.get('progress', '-')[:15],
                    tokens,
                    cost
                ])
            
            print(create_table(headers, rows))
            print(c_gray(f'\n共 {len(sessions)} 个活跃会话 | 下次刷新：{interval}秒\n'))
            
            time.sleep(interval)
    except KeyboardInterrupt:
        print(c_yellow('\n\n监控已停止\n'))

def main():
    parser = argparse.ArgumentParser(
        description='Agent 任务监控可视化',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  %(prog)s list                    # 列出所有活跃会话
  %(prog)s list --json             # JSON 格式输出
  %(prog)s detail agent:xxx        # 查看指定会话详情
  %(prog)s watch                   # 实时监控模式（默认 3 秒刷新）
  %(prog)s watch --interval 2      # 2 秒刷新间隔
  %(prog)s watch --interval 5      # 5 秒刷新间隔
'''
    )
    
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有活跃会话')
    list_parser.add_argument('-j', '--json', action='store_true', help='JSON 格式输出')
    
    # detail 命令
    detail_parser = subparsers.add_parser('detail', help='查看会话详情')
    detail_parser.add_argument('session_id', help='会话 ID')
    detail_parser.add_argument('-j', '--json', action='store_true', help='JSON 格式输出')
    
    # watch 命令
    watch_parser = subparsers.add_parser('watch', help='实时监控模式')
    watch_parser.add_argument('--interval', type=int, default=3, 
                             help='刷新间隔（秒），默认 3 秒，范围 1-60')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        cmd_monitor_list(args)
    elif args.command == 'detail':
        cmd_monitor_detail(args.session_id, args)
    elif args.command == 'watch':
        if args.interval < 1 or args.interval > 60:
            print(c_red('错误：刷新间隔必须在 1-60 秒之间\n'))
            sys.exit(1)
        cmd_monitor_watch(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
