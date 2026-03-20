#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claw-ex · OpenClaw 终端管理工具
兵部出品 - 系统集成与进程管理
"""

import sys
import os
import argparse
import json
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from env import EnvironmentChecker
from process import ProcessManager
from session import SessionManager
from monitor import SystemMonitor
from logs import LogManager

VERSION = "0.1.0"
CONFIG_DIR = Path.home() / '.openclaw' / 'claw-ex'
CONFIG_FILE = CONFIG_DIR / 'config.json'


def ensure_config_dir():
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config):
    """保存配置文件"""
    ensure_config_dir()
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ============== 环境检测命令 ==============

def cmd_env_check(args):
    """环境检测"""
    checker = EnvironmentChecker()
    results = checker.check_all()
    
    print("\n🔍 OpenClaw 环境检测报告")
    print("=" * 50)
    
    for category, checks in results.items():
        print(f"\n【{category}】")
        for check in checks:
            status = "✅" if check['passed'] else "❌"
            print(f"  {status} {check['name']}: {check['message']}")
    
    # 保存检测结果
    config = load_config()
    config['last_env_check'] = results
    save_config(config)
    
    print("\n" + "=" * 50)
    all_passed = all(
        check['passed'] 
        for checks in results.values() 
        for check in checks
    )
    if all_passed:
        print("✅ 环境检查通过")
        return 0
    else:
        print("⚠️  存在环境问题，请检查上述报告")
        return 1


def cmd_env_init(args):
    """初始化环境配置"""
    checker = EnvironmentChecker()
    config = checker.generate_config()
    save_config(config)
    print(f"✅ 配置文件已生成：{CONFIG_FILE}")
    return 0


# ============== 进程管理命令 ==============

def cmd_process_start(args):
    """启动进程"""
    pm = ProcessManager()
    result = pm.start(
        name=args.name,
        command=args.command,
        args=args.args,
        workdir=args.workdir
    )
    if result['success']:
        print(f"✅ 进程已启动: {args.name} (PID: {result['pid']})")
        return 0
    else:
        print(f"❌ 启动失败：{result['error']}")
        return 1


def cmd_process_stop(args):
    """停止进程"""
    pm = ProcessManager()
    result = pm.stop(args.name)
    if result['success']:
        print(f"✅ 进程已停止：{args.name}")
        return 0
    else:
        print(f"❌ 停止失败：{result['error']}")
        return 1


def cmd_process_list(args):
    """列出进程"""
    pm = ProcessManager()
    processes = pm.list_all()
    
    if not processes:
        print("📭 暂无运行中的进程")
        return 0
    
    print("\n📊 进程列表")
    print("=" * 70)
    print(f"{'名称':<20} {'PID':<10} {'状态':<12} {'CPU':<8} {'内存':<10} {'启动时间'}")
    print("-" * 70)
    
    for proc in processes:
        status_map = {'running': '🟢 运行中', 'stopped': '🔴 已停止', 'zombie': '⚠️ 僵尸'}
        status = status_map.get(proc['status'], proc['status'])
        print(f"{proc['name']:<20} {proc['pid']:<10} {status:<12} {proc['cpu']:<8.1f}% {proc['memory']:<10} {proc['started']}")
    
    print("=" * 70)
    print(f"总计：{len(processes)} 个进程")
    return 0


def cmd_process_status(args):
    """查看进程状态"""
    pm = ProcessManager()
    status = pm.status(args.name)
    
    if status['exists']:
        print(f"\n📊 进程状态：{args.name}")
        print("=" * 50)
        for key, value in status.items():
            if key != 'exists':
                print(f"  {key}: {value}")
        return 0
    else:
        print(f"❌ 进程不存在：{args.name}")
        return 1


# ============== 会话管理命令 ==============

def cmd_session_create(args):
    """创建会话"""
    sm = SessionManager()
    result = sm.create(args.name)
    if result['success']:
        print(f"✅ 会话已创建：{args.name} (ID: {result['session_id']})")
        return 0
    else:
        print(f"❌ 创建失败：{result['error']}")
        return 1


def cmd_session_list(args):
    """列出会话"""
    sm = SessionManager()
    sessions = sm.list_sessions()
    
    if not sessions:
        print("📭 暂无会话")
        return 0
    
    print("\n📊 会话列表")
    print("=" * 60)
    print(f"{'名称':<20} {'ID':<25} {'状态':<10} {'创建时间'}")
    print("-" * 60)
    
    for sess in sessions:
        status = "🟢 活跃" if sess['active'] else "⚪ 非活跃"
        print(f"{sess['name']:<20} {sess['id']:<25} {status:<10} {sess['created']}")
    
    print("=" * 60)
    return 0


def cmd_session_switch(args):
    """切换会话"""
    sm = SessionManager()
    result = sm.switch(args.name)
    if result['success']:
        print(f"✅ 已切换到会话：{args.name}")
        return 0
    else:
        print(f"❌ 切换失败：{result['error']}")
        return 1


def cmd_session_delete(args):
    """删除会话"""
    sm = SessionManager()
    result = sm.delete(args.name)
    if result['success']:
        print(f"✅ 会话已删除：{args.name}")
        return 0
    else:
        print(f"❌ 删除失败：{result['error']}")
        return 1


# ============== 系统监控命令 ==============

def cmd_monitor_system(args):
    """系统资源监控"""
    mon = SystemMonitor()
    
    print("\n📊 系统资源监控")
    print("=" * 50)
    
    # CPU
    cpu = mon.get_cpu_usage(interval=1)
    print(f"\n🔸 CPU 使用率")
    print(f"   当前：{cpu['current']:.1f}%")
    print(f"   核心数：{cpu['cores']}")
    print(f"   每核：{', '.join(f'{c:.1f}%' for c in cpu['per_core'])}")
    
    # 内存
    mem = mon.get_memory_usage()
    print(f"\n🔸 内存使用")
    print(f"   总计：{mem['total']:.2f} GB")
    print(f"   已用：{mem['used']:.2f} GB ({mem['percent']:.1f}%)")
    print(f"   可用：{mem['available']:.2f} GB")
    
    # 磁盘
    disk = mon.get_disk_usage()
    print(f"\n🔸 磁盘使用")
    print(f"   总计：{disk['total']:.2f} GB")
    print(f"   已用：{disk['used']:.2f} GB ({disk['percent']:.1f}%)")
    print(f"   可用：{disk['free']:.2f} GB")
    
    # 网络
    net = mon.get_network_stats()
    print(f"\n🔸 网络流量")
    print(f"   发送：{net['bytes_sent'] / 1024 / 1024:.2f} MB")
    print(f"   接收：{net['bytes_recv'] / 1024 / 1024:.2f} MB")
    
    print("\n" + "=" * 50)
    return 0


def cmd_monitor_watch(args):
    """实时监控"""
    mon = SystemMonitor()
    
    print("📊 实时监控 (Ctrl+C 退出)")
    print("=" * 50)
    
    try:
        while True:
            cpu = mon.get_cpu_usage(interval=0.5)
            mem = mon.get_memory_usage()
            
            # 清屏并显示
            os.system('clear' if os.name != 'nt' else 'cls')
            print("📊 实时监控 [Ctrl+C 退出]")
            print("=" * 50)
            print(f"CPU: {cpu['current']:.1f}% | 内存：{mem['percent']:.1f}%")
            print(f"已用：{mem['used']:.2f}/{mem['total']:.2f} GB")
            print("=" * 50)
            
            # 告警检查
            if cpu['current'] > 80:
                print("⚠️  警告：CPU 使用率过高!")
            if mem['percent'] > 90:
                print("⚠️  警告：内存使用率过高!")
            
            import time
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n✅ 监控已停止")
        return 0


# ============== 日志管理命令 ==============

def cmd_logs_tail(args):
    """查看日志末尾"""
    lm = LogManager()
    logs = lm.tail(args.lines, level=args.level)
    
    if not logs:
        print("📭 暂无日志")
        return 0
    
    for log in logs:
        timestamp = log.get('timestamp', 'N/A')
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        print(f"[{timestamp}] [{level}] {message}")
    
    return 0


def cmd_logs_search(args):
    """搜索日志"""
    lm = LogManager()
    logs = lm.search(args.keyword, level=args.level)
    
    if not logs:
        print(f"📭 未找到匹配的日志：{args.keyword}")
        return 0
    
    print(f"📊 找到 {len(logs)} 条匹配的日志\n")
    for log in logs:
        timestamp = log.get('timestamp', 'N/A')
        level = log.get('level', 'INFO')
        message = log.get('message', '')
        print(f"[{timestamp}] [{level}] {message}")
    
    return 0


def cmd_logs_clear(args):
    """清空日志"""
    lm = LogManager()
    result = lm.clear()
    if result['success']:
        print(f"✅ 已清空 {result['count']} 条日志")
        return 0
    else:
        print(f"❌ 清空失败：{result['error']}")
        return 1


# ============== 主程序 ==============

def main():
    parser = argparse.ArgumentParser(
        prog='claw-ex',
        description='OpenClaw 终端管理工具 - 兵部出品',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  claw-ex env check          # 环境检测
  claw-ex process start nginx   # 启动进程
  claw-ex process list          # 列出进程
  claw-ex session create dev    # 创建会话
  claw-ex monitor system        # 系统监控
  claw-ex logs tail -n 50       # 查看日志
        '''
    )
    
    parser.add_argument('-v', '--version', action='version', version=f'claw-ex {VERSION}')
    parser.add_argument('--config', help='配置文件路径')
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # 环境检测命令
    env_parser = subparsers.add_parser('env', help='环境检测与配置')
    env_subparsers = env_parser.add_subparsers(dest='subcommand')
    
    env_check = env_subparsers.add_parser('check', help='环境检测')
    env_check.set_defaults(func=cmd_env_check)
    
    env_init = env_subparsers.add_parser('init', help='初始化配置')
    env_init.set_defaults(func=cmd_env_init)
    
    # 进程管理命令
    proc_parser = subparsers.add_parser('process', help='进程管理')
    proc_subparsers = proc_parser.add_subparsers(dest='subcommand')
    
    proc_start = proc_subparsers.add_parser('start', help='启动进程')
    proc_start.add_argument('name', help='进程名称')
    proc_start.add_argument('command', help='命令')
    proc_start.add_argument('--args', nargs='*', help='命令参数')
    proc_start.add_argument('--workdir', help='工作目录')
    proc_start.set_defaults(func=cmd_process_start)
    
    proc_stop = proc_subparsers.add_parser('stop', help='停止进程')
    proc_stop.add_argument('name', help='进程名称')
    proc_stop.set_defaults(func=cmd_process_stop)
    
    proc_list = proc_subparsers.add_parser('list', help='列出进程')
    proc_list.set_defaults(func=cmd_process_list)
    
    proc_status = proc_subparsers.add_parser('status', help='查看进程状态')
    proc_status.add_argument('name', help='进程名称')
    proc_status.set_defaults(func=cmd_process_status)
    
    # 会话管理命令
    sess_parser = subparsers.add_parser('session', help='会话管理')
    sess_subparsers = sess_parser.add_subparsers(dest='subcommand')
    
    sess_create = sess_subparsers.add_parser('create', help='创建会话')
    sess_create.add_argument('name', help='会话名称')
    sess_create.set_defaults(func=cmd_session_create)
    
    sess_list = sess_subparsers.add_parser('list', help='列出会话')
    sess_list.set_defaults(func=cmd_session_list)
    
    sess_switch = sess_subparsers.add_parser('switch', help='切换会话')
    sess_switch.add_argument('name', help='会话名称')
    sess_switch.set_defaults(func=cmd_session_switch)
    
    sess_delete = sess_subparsers.add_parser('delete', help='删除会话')
    sess_delete.add_argument('name', help='会话名称')
    sess_delete.set_defaults(func=cmd_session_delete)
    
    # 系统监控命令
    mon_parser = subparsers.add_parser('monitor', help='系统监控')
    mon_subparsers = mon_parser.add_subparsers(dest='subcommand')
    
    mon_system = mon_subparsers.add_parser('system', help='系统资源')
    mon_system.set_defaults(func=cmd_monitor_system)
    
    mon_watch = mon_subparsers.add_parser('watch', help='实时监控')
    mon_watch.add_argument('-i', '--interval', type=float, default=2.0, help='刷新间隔')
    mon_watch.set_defaults(func=cmd_monitor_watch)
    
    # 日志管理命令
    logs_parser = subparsers.add_parser('logs', help='日志管理')
    logs_subparsers = logs_parser.add_subparsers(dest='subcommand')
    
    logs_tail = logs_subparsers.add_parser('tail', help='查看日志末尾')
    logs_tail.add_argument('-n', '--lines', type=int, default=20, help='行数')
    logs_tail.add_argument('--level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='日志级别')
    logs_tail.set_defaults(func=cmd_logs_tail)
    
    logs_search = logs_subparsers.add_parser('search', help='搜索日志')
    logs_search.add_argument('keyword', help='搜索关键词')
    logs_search.add_argument('--level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], help='日志级别')
    logs_search.set_defaults(func=cmd_logs_search)
    
    logs_clear = logs_subparsers.add_parser('clear', help='清空日志')
    logs_clear.set_defaults(func=cmd_logs_clear)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    if hasattr(args, 'func'):
        return args.func(args)
    else:
        # 显示子命令帮助
        if args.command == 'env':
            env_parser.print_help()
        elif args.command == 'process':
            proc_parser.print_help()
        elif args.command == 'session':
            sess_parser.print_help()
        elif args.command == 'monitor':
            mon_parser.print_help()
        elif args.command == 'logs':
            logs_parser.print_help()
        return 0


if __name__ == '__main__':
    sys.exit(main())
