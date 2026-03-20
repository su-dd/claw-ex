#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claw-ex Cron 定时任务模块
支持定时执行任务、备份、清理等
Cron 表达式解析
"""

import sys
import os
import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum

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

# 路径配置
OPENCLAW_HOME = Path(os.environ.get('OPENCLAW_HOME', Path.home() / '.openclaw'))
CRON_CONFIG_FILE = OPENCLAW_HOME / 'cron-config.json'
CRON_LOG_DIR = OPENCLAW_HOME / 'cron-logs'

class TaskStatus(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'
    SKIPPED = 'skipped'

@dataclass
class CronJob:
    id: str
    name: str
    schedule: str  # Cron 表达式
    command: str
    enabled: bool = True
    last_run: str = None
    next_run: str = None
    last_status: str = 'pending'
    last_duration: float = None
    run_count: int = 0
    created_at: str = ''
    description: str = ''
    
    def to_dict(self):
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class CronParser:
    """简单的 Cron 表达式解析器"""
    
    @staticmethod
    def parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """解析单个 cron 字段"""
        if field == '*':
            return list(range(min_val, max_val + 1))
        
        values = []
        for part in field.split(','):
            if '-' in part:
                # 范围：1-5
                start, end = map(int, part.split('-'))
                values.extend(range(start, end + 1))
            elif '/' in part:
                # 步长：*/5 或 1-10/2
                base, step = part.split('/')
                step = int(step)
                if base == '*':
                    values.extend(range(min_val, max_val + 1, step))
                else:
                    start = int(base)
                    values.extend(range(start, max_val + 1, step))
            else:
                values.append(int(part))
        
        return sorted(set(v for v in values if min_val <= v <= max_val))
    
    @staticmethod
    def parse(expression: str) -> Dict[str, List[int]]:
        """解析 cron 表达式 (5 字段：分 时 日 月 周)"""
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"无效的 cron 表达式：需要 5 个字段，得到 {len(parts)} 个")
        
        return {
            'minute': CronParser.parse_field(parts[0], 0, 59),
            'hour': CronParser.parse_field(parts[1], 0, 23),
            'day': CronParser.parse_field(parts[2], 1, 31),
            'month': CronParser.parse_field(parts[3], 1, 12),
            'weekday': CronParser.parse_field(parts[4], 0, 6)  # 0=Sunday
        }
    
    @staticmethod
    def get_next_run(expression: str, from_time: datetime = None) -> datetime:
        """计算下次运行时间"""
        from datetime import timedelta
        
        if from_time is None:
            from_time = datetime.now()
        
        parsed = CronParser.parse(expression)
        current = from_time.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # 最多查找一年
        for _ in range(525600):  # 一年的分钟数
            # 检查是否匹配
            if (current.month in parsed['month'] and
                current.day in parsed['day'] and
                current.weekday() in parsed['weekday'] and
                current.hour in parsed['hour'] and
                current.minute in parsed['minute']):
                return current
            
            current = current + timedelta(minutes=1)
        
        raise ValueError("无法计算下次运行时间")
    
    @staticmethod
    def is_due(expression: str, check_time: datetime = None) -> bool:
        """检查是否应该运行"""
        if check_time is None:
            check_time = datetime.now()
        
        parsed = CronParser.parse(expression)
        
        return (check_time.month in parsed['month'] and
                check_time.day in parsed['day'] and
                check_time.weekday() in parsed['weekday'] and
                check_time.hour in parsed['hour'] and
                check_time.minute in parsed['minute'])

def generate_job_id(name: str) -> str:
    """生成唯一的任务 ID"""
    import hashlib
    timestamp = datetime.now().isoformat()
    return hashlib.md5(f"{name}-{timestamp}".encode()).hexdigest()[:12]

def load_jobs() -> List[CronJob]:
    """加载定时任务配置"""
    if not CRON_CONFIG_FILE.exists():
        return []
    
    try:
        with open(CRON_CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [CronJob.from_dict(r) for r in data.get('jobs', [])]
    except Exception as e:
        print(c_yellow(f'⚠️  加载定时任务配置失败：{e}'))
        return []

def save_jobs(jobs: List[CronJob]):
    """保存定时任务配置"""
    CRON_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        'version': '1.0',
        'updated_at': datetime.now().isoformat(),
        'jobs': [j.to_dict() for j in jobs]
    }
    with open(CRON_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_job_execution(job_id: str, job_name: str, status: str, output: str = '', duration: float = 0):
    """记录任务执行日志"""
    CRON_LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    log_file = CRON_LOG_DIR / f"{job_id}.log"
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        'timestamp': timestamp,
        'job_id': job_id,
        'job_name': job_name,
        'status': status,
        'duration': duration,
        'output': output[:10000] if output else ''  # 限制日志大小
    }
    
    # 追加到日志文件
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

def run_job(job: CronJob) -> bool:
    """执行定时任务"""
    print(c_cyan(f'\n▶️  执行任务：{job.name}\n'))
    
    start_time = time.time()
    
    try:
        # 执行命令
        result = subprocess.run(
            job.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=3600  # 1 小时超时
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            status = 'completed'
            print(c_green(f'✅ 任务完成 (耗时：{duration:.2f}s)\n'))
        else:
            status = 'failed'
            print(c_red(f'❌ 任务失败 (退出码：{result.returncode})\n'))
        
        # 记录日志
        output = result.stdout + result.stderr
        log_job_execution(job.id, job.name, status, output, duration)
        
        # 更新任务状态
        jobs = load_jobs()
        for j in jobs:
            if j.id == job.id:
                j.last_run = datetime.now().isoformat()
                j.last_status = status
                j.last_duration = duration
                j.run_count += 1
                j.next_run = CronParser.get_next_run(job.schedule).isoformat()
                break
        save_jobs(jobs)
        
        return status == 'completed'
    
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        log_job_execution(job.id, job.name, 'failed', '任务超时', duration)
        print(c_red(f'❌ 任务超时\n'))
        return False
    
    except Exception as e:
        duration = time.time() - start_time
        log_job_execution(job.id, job.name, 'failed', str(e), duration)
        print(c_red(f'❌ 任务执行异常：{e}\n'))
        return False

class CronScheduler:
    """Cron 调度器"""
    
    def __init__(self):
        self.running = False
        self.thread = None
    
    def start(self):
        """启动调度器"""
        if self.running:
            print(c_yellow('⚠️  调度器已在运行\n'))
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print(c_green('✅ 调度器已启动\n'))
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print(c_green('✅ 调度器已停止\n'))
    
    def _run(self):
        """调度器主循环"""
        print(c_gray('调度器运行中... (每分钟检查)\n'))
        
        while self.running:
            try:
                jobs = load_jobs()
                now = datetime.now()
                
                for job in jobs:
                    if not job.enabled:
                        continue
                    
                    # 检查是否到运行时间
                    if CronParser.is_due(job.schedule, now):
                        # 避免重复执行（1 分钟内）
                        if job.last_run:
                            last_run = datetime.fromisoformat(job.last_run)
                            if (now - last_run).total_seconds() < 60:
                                continue
                        
                        run_job(job)
                
                # 每分钟检查一次
                time.sleep(60)
            
            except Exception as e:
                print(c_red(f'调度器错误：{e}\n'))
                time.sleep(60)

# 全局调度器实例
_scheduler = None

def cmd_cron_list(args: List[str]):
    """列出所有定时任务"""
    jobs = load_jobs()
    
    print(c_cyan('\n⏰ 定时任务:\n'))
    
    if not jobs:
        print(c_gray('  （无定时任务）\n'))
        return
    
    headers = ['ID', '名称', 'Schedule', '状态', '上次运行', '下次运行', '执行次数']
    rows = []
    
    for job in jobs:
        status_icon = '🟢' if job.enabled else '🔴'
        last_run = datetime.fromisoformat(job.last_run).strftime('%m-%d %H:%M') if job.last_run else '从未'
        next_run = datetime.fromisoformat(job.next_run).strftime('%m-%d %H:%M') if job.next_run else '计算中'
        
        rows.append([
            job.id[:8],
            job.name[:15],
            job.schedule,
            status_icon,
            last_run,
            next_run,
            job.run_count
        ])
    
    # 表格输出
    col_widths = [max(len(h), max(len(str(row[i])) for row in rows)) + 2 for i, h in enumerate(headers)]
    
    line = '┌' + '┬'.join('─' * w for w in col_widths) + '┐'
    sep = '├' + '┼'.join('─' * w for w in col_widths) + '┤'
    end = '└' + '┴'.join('─' * w for w in col_widths) + '┘'
    
    header_row = '│' + '│'.join(h.ljust(w) for h, w in zip(headers, col_widths)) + '│'
    
    output = [line, header_row, sep]
    for row in rows:
        padded_row = list(row) + [''] * (len(headers) - len(row))
        row_str = '│' + '│'.join(str(cell).ljust(w) for cell, w in zip(padded_row, col_widths)) + '│'
        output.append(row_str)
    output.append(end)
    
    print('\n'.join(output))
    print(f"\n共 {len(jobs)} 个任务\n")

def cmd_cron_create(args: List[str]):
    """创建定时任务"""
    if len(args) < 5:
        print(c_red('❌ 参数不足'))
        print('用法：claw-ex cron create <name> <schedule> <command> [选项]')
        print('示例:')
        print('  claw-ex cron create "每日备份" "0 2 * * *" "claw-ex backup"')
        print('  claw-ex cron create "清理日志" "0 3 * * 0" "find /var/log -name \\"*.log\\" -mtime +30 -delete"')
        print('  claw-ex cron create "健康检查" "*/5 * * * *" "claw-ex health"')
        print('\nSchedule 格式：分 时 日 月 周')
        print('  * * * * *')
        print('  │ │ │ │ │')
        print('  │ │ │ │ └─ 星期 (0-6, 0=周日)')
        print('  │ │ │ └─── 月份 (1-12)')
        print('  │ │ └───── 日期 (1-31)')
        print('  │ └─────── 小时 (0-23)')
        print('  └───────── 分钟 (0-59)')
        print('\n选项：--enabled --description <text>')
        sys.exit(1)
    
    name = args[2]
    schedule = args[3]
    command = args[4]
    
    # 验证 cron 表达式
    try:
        CronParser.parse(schedule)
    except ValueError as e:
        print(c_red(f'❌ 无效的 cron 表达式：{e}'))
        sys.exit(1)
    
    # 计算下次运行时间
    try:
        next_run = CronParser.get_next_run(schedule)
    except Exception as e:
        print(c_red(f'❌ 无法计算下次运行时间：{e}'))
        sys.exit(1)
    
    # 解析选项
    enabled = True
    description = ''
    
    if '--no-enabled' in args:
        enabled = False
    
    if '--description' in args:
        idx = args.index('--description')
        if idx + 1 < len(args):
            description = args[idx + 1]
    
    # 创建任务
    job = CronJob(
        id=generate_job_id(name),
        name=name,
        schedule=schedule,
        command=command,
        enabled=enabled,
        description=description,
        created_at=datetime.now().isoformat(),
        next_run=next_run.isoformat()
    )
    
    # 保存
    jobs = load_jobs()
    jobs.append(job)
    save_jobs(jobs)
    
    print(c_green(f'\n✅ 定时任务已创建:\n'))
    print(f"  ID:          {c_bold(job.id)}")
    print(f"  名称：       {job.name}")
    print(f"  Schedule:    {job.schedule}")
    print(f"  命令：       {job.command}")
    print(f"  下次运行：   {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  状态：       {'🟢 已启用' if enabled else '🔴 已禁用'}")
    if description:
        print(f"  描述：       {description}")
    print()

def cmd_cron_delete(args: List[str]):
    """删除定时任务"""
    if len(args) < 3:
        print(c_red('❌ 缺少任务 ID 或名称'))
        print('用法：claw-ex cron delete <id|name> [--confirm]')
        sys.exit(1)
    
    identifier = args[2]
    confirm = '--confirm' in args
    
    jobs = load_jobs()
    
    # 查找任务
    found = None
    for job in jobs:
        if job.id == identifier or job.name == identifier:
            found = job
            break
    
    if not found:
        print(c_red(f'❌ 未找到定时任务：{identifier}'))
        sys.exit(1)
    
    if not confirm:
        print(c_yellow(f'⚠️  确定要删除定时任务 "{found.name}" 吗？'))
        print('使用 --confirm 确认删除')
        sys.exit(1)
    
    jobs = [j for j in jobs if j.id != found.id]
    save_jobs(jobs)
    
    # 删除日志文件
    log_file = CRON_LOG_DIR / f"{found.id}.log"
    if log_file.exists():
        log_file.unlink()
    
    print(c_green(f'✅ 定时任务已删除：{found.name}\n'))

def cmd_cron_run(args: List[str]):
    """手动执行定时任务"""
    if len(args) < 3:
        print(c_red('❌ 缺少任务 ID 或名称'))
        print('用法：claw-ex cron run <id|name>')
        sys.exit(1)
    
    identifier = args[2]
    
    jobs = load_jobs()
    
    # 查找任务
    found = None
    for job in jobs:
        if job.id == identifier or job.name == identifier:
            found = job
            break
    
    if not found:
        print(c_red(f'❌ 未找到定时任务：{identifier}'))
        sys.exit(1)
    
    run_job(found)

def cmd_cron_enable(args: List[str]):
    """启用/禁用定时任务"""
    if len(args) < 4:
        print(c_red('❌ 参数不足'))
        print('用法：claw-ex cron enable <id|name> <true|false>')
        sys.exit(1)
    
    identifier = args[2]
    enable = args[3].lower() in ['true', '1', 'yes']
    
    jobs = load_jobs()
    
    # 查找任务
    found = None
    for job in jobs:
        if job.id == identifier or job.name == identifier:
            found = job
            break
    
    if not found:
        print(c_red(f'❌ 未找到定时任务：{identifier}'))
        sys.exit(1)
    
    found.enabled = enable
    
    save_jobs(jobs)
    
    status = '🟢 已启用' if enable else '🔴 已禁用'
    print(c_green(f'✅ 定时任务 {status}: {found.name}\n'))

def cmd_cron_logs(args: List[str]):
    """查看任务执行日志"""
    if len(args) < 3:
        print(c_red('❌ 缺少任务 ID 或名称'))
        print('用法：claw-ex cron logs <id|name> [--lines <n>]')
        sys.exit(1)
    
    identifier = args[2]
    lines = 10
    
    if '--lines' in args:
        idx = args.index('--lines')
        if idx + 1 < len(args):
            try:
                lines = int(args[idx + 1])
            except ValueError:
                pass
    
    jobs = load_jobs()
    
    # 查找任务
    found = None
    for job in jobs:
        if job.id == identifier or job.name == identifier:
            found = job
            break
    
    if not found:
        print(c_red(f'❌ 未找到定时任务：{identifier}'))
        sys.exit(1)
    
    log_file = CRON_LOG_DIR / f"{found.id}.log"
    
    if not log_file.exists():
        print(c_gray(f'\n📄 暂无执行日志\n'))
        return
    
    print(c_cyan(f'\n📜 任务日志：{found.name} (最近 {lines} 条)\n'))
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_logs = [json.loads(line) for line in f if line.strip()]
        
        recent = all_logs[-lines:][::-1]
        
        for entry in recent:
            timestamp = datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            status_icon = '✅' if entry['status'] == 'completed' else '❌'
            duration = f"{entry['duration']:.2f}s" if entry.get('duration') else 'N/A'
            
            print(f"{c_gray(timestamp)} {status_icon} {entry['status']} (耗时：{duration})")
            if entry.get('output'):
                output_lines = entry['output'].split('\n')[:5]
                for line in output_lines:
                    print(c_gray(f"  {line}"))
                if len(entry['output'].split('\n')) > 5:
                    print(c_gray(f"  ... (还有更多)"))
            print()
    
    except Exception as e:
        print(c_red(f'读取日志失败：{e}\n'))

def cmd_cron_start(args: List[str]):
    """启动调度器"""
    global _scheduler
    
    if _scheduler and _scheduler.running:
        print(c_yellow('⚠️  调度器已在运行\n'))
        return
    
    _scheduler = CronScheduler()
    _scheduler.start()

def cmd_cron_stop(args: List[str]):
    """停止调度器"""
    global _scheduler
    
    if not _scheduler or not _scheduler.running:
        print(c_yellow('⚠️  调度器未运行\n'))
        return
    
    _scheduler.stop()
    _scheduler = None

def cmd_cron_status(args: List[str]):
    """查看调度器状态"""
    global _scheduler
    
    print(c_cyan('\n⏰ 调度器状态:\n'))
    
    if _scheduler and _scheduler.running:
        print(f"  状态：{c_green('运行中')}")
        print(f"  线程：{_scheduler.thread.name if _scheduler.thread else 'N/A'}")
    else:
        print(f"  状态：{c_gray('已停止')}")
    
    jobs = load_jobs()
    enabled_count = sum(1 for j in jobs if j.enabled)
    
    print(f"  任务总数：{len(jobs)}")
    print(f"  已启用：{enabled_count}")
    print(f"  已禁用：{len(jobs) - enabled_count}")
    print()
