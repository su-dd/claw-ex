#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claw-ex 数据统计模块
Agent 使用统计、任务统计、会话统计
"""

import os
import json
import csv
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

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
STATS_DIR = Path(__file__).parent.parent / 'data' / 'stats'
STATS_DIR.mkdir(parents=True, exist_ok=True)

# 统计数据文件
AGENT_STATS_FILE = STATS_DIR / 'agent_stats.json'
TASK_STATS_FILE = STATS_DIR / 'task_stats.json'
SESSION_STATS_FILE = STATS_DIR / 'session_stats.json'


def load_json_file(file_path: Path, default: Any = None) -> Any:
    """加载 JSON 文件"""
    if file_path.exists():
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return default if default is not None else {}


def save_json_file(file_path: Path, data: Any):
    """保存 JSON 文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ========== Agent 统计 ==========

def record_agent_call(agent_id: str, model_id: str, success: bool, 
                      tokens_used: int = 0, duration_ms: int = 0, 
                      task_id: str = None, session_id: str = None):
    """记录 Agent 调用"""
    stats = load_json_file(AGENT_STATS_FILE, {'agents': {}, 'calls': []})
    
    if 'agents' not in stats:
        stats['agents'] = {}
    if 'calls' not in stats:
        stats['calls'] = []
    
    # 更新 Agent 统计
    if agent_id not in stats['agents']:
        stats['agents'][agent_id] = {
            'agent_id': agent_id,
            'model_id': model_id,
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_tokens': 0,
            'total_duration_ms': 0,
            'first_call': None,
            'last_call': None
        }
    
    agent_stat = stats['agents'][agent_id]
    agent_stat['total_calls'] += 1
    if success:
        agent_stat['successful_calls'] += 1
    else:
        agent_stat['failed_calls'] += 1
    agent_stat['total_tokens'] += tokens_used
    agent_stat['total_duration_ms'] += duration_ms
    
    now = datetime.now().isoformat()
    if not agent_stat['first_call']:
        agent_stat['first_call'] = now
    agent_stat['last_call'] = now
    
    # 记录调用详情
    call_record = {
        'timestamp': now,
        'agent_id': agent_id,
        'model_id': model_id,
        'success': success,
        'tokens_used': tokens_used,
        'duration_ms': duration_ms,
        'task_id': task_id,
        'session_id': session_id
    }
    stats['calls'].append(call_record)
    
    # 保留最近 10000 条记录
    if len(stats['calls']) > 10000:
        stats['calls'] = stats['calls'][-10000:]
    
    save_json_file(AGENT_STATS_FILE, stats)


def get_agent_stats(agent_id: str = None, days: int = 30) -> Dict[str, Any]:
    """获取 Agent 统计数据"""
    stats = load_json_file(AGENT_STATS_FILE, {'agents': {}, 'calls': []})
    
    if not stats.get('agents'):
        return {'agents': [], 'summary': {}}
    
    # 时间过滤
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    recent_calls = [c for c in stats.get('calls', []) if c.get('timestamp', '') > cutoff]
    
    if agent_id:
        # 单个 Agent 统计
        if agent_id not in stats['agents']:
            return {'error': f'未找到 Agent: {agent_id}'}
        
        agent_stat = stats['agents'][agent_id].copy()
        agent_calls = [c for c in recent_calls if c['agent_id'] == agent_id]
        
        # 计算成功率
        if agent_stat['total_calls'] > 0:
            agent_stat['success_rate'] = round(
                agent_stat['successful_calls'] / agent_stat['total_calls'] * 100, 2
            )
        else:
            agent_stat['success_rate'] = 0
        
        # 计算平均耗时
        if agent_stat['total_calls'] > 0:
            agent_stat['avg_duration_ms'] = round(
                agent_stat['total_duration_ms'] / agent_stat['total_calls']
            )
        else:
            agent_stat['avg_duration_ms'] = 0
        
        # 计算平均 tokens
        if agent_stat['total_calls'] > 0:
            agent_stat['avg_tokens'] = round(
                agent_stat['total_tokens'] / agent_stat['total_calls']
            )
        else:
            agent_stat['avg_tokens'] = 0
        
        return {'agent': agent_stat, 'recent_calls': agent_calls[-100:]}
    
    else:
        # 所有 Agent 统计
        agents_list = []
        for aid, astat in stats['agents'].items():
            astat_copy = astat.copy()
            if astat_copy['total_calls'] > 0:
                astat_copy['success_rate'] = round(
                    astat_copy['successful_calls'] / astat_copy['total_calls'] * 100, 2
                )
                astat_copy['avg_duration_ms'] = round(
                    astat_copy['total_duration_ms'] / astat_copy['total_calls']
                )
                astat_copy['avg_tokens'] = round(
                    astat_copy['total_tokens'] / astat_copy['total_calls']
                )
            else:
                astat_copy['success_rate'] = 0
                astat_copy['avg_duration_ms'] = 0
                astat_copy['avg_tokens'] = 0
            agents_list.append(astat_copy)
        
        # 按调用次数排序
        agents_list.sort(key=lambda x: x['total_calls'], reverse=True)
        
        # 总体汇总
        total_calls = sum(a['total_calls'] for a in agents_list)
        total_success = sum(a['successful_calls'] for a in agents_list)
        total_tokens = sum(a['total_tokens'] for a in agents_list)
        total_duration = sum(a['total_duration_ms'] for a in agents_list)
        
        summary = {
            'total_agents': len(agents_list),
            'total_calls': total_calls,
            'overall_success_rate': round(total_success / total_calls * 100, 2) if total_calls > 0 else 0,
            'total_tokens_used': total_tokens,
            'total_duration_ms': total_duration,
            'avg_duration_ms': round(total_duration / total_calls, 2) if total_calls > 0 else 0
        }
        
        return {'agents': agents_list, 'summary': summary, 'recent_calls': recent_calls[-100:]}


# ========== 任务统计 ==========

def record_task_event(task_id: str, event_type: str, 
                      duration_ms: int = 0, success: bool = True,
                      agent_id: str = None, metadata: Dict = None):
    """记录任务事件"""
    stats = load_json_file(TASK_STATS_FILE, {'tasks': {}, 'events': []})
    
    if 'tasks' not in stats:
        stats['tasks'] = {}
    if 'events' not in stats:
        stats['events'] = []
    
    # 更新任务统计
    if task_id not in stats['tasks']:
        stats['tasks'][task_id] = {
            'task_id': task_id,
            'total_events': 0,
            'completed_count': 0,
            'failed_count': 0,
            'total_duration_ms': 0,
            'first_event': None,
            'last_event': None
        }
    
    task_stat = stats['tasks'][task_id]
    task_stat['total_events'] += 1
    if event_type == 'completed' and success:
        task_stat['completed_count'] += 1
    elif event_type == 'failed' or not success:
        task_stat['failed_count'] += 1
    task_stat['total_duration_ms'] += duration_ms
    
    now = datetime.now().isoformat()
    if not task_stat['first_event']:
        task_stat['first_event'] = now
    task_stat['last_event'] = now
    
    # 记录事件详情
    event_record = {
        'timestamp': now,
        'task_id': task_id,
        'event_type': event_type,
        'duration_ms': duration_ms,
        'success': success,
        'agent_id': agent_id,
        'metadata': metadata or {}
    }
    stats['events'].append(event_record)
    
    # 保留最近 10000 条记录
    if len(stats['events']) > 10000:
        stats['events'] = stats['events'][-10000:]
    
    save_json_file(TASK_STATS_FILE, stats)


def get_task_stats(task_id: str = None, days: int = 30) -> Dict[str, Any]:
    """获取任务统计数据"""
    stats = load_json_file(TASK_STATS_FILE, {'tasks': {}, 'events': []})
    
    if not stats.get('tasks'):
        return {'tasks': [], 'summary': {}}
    
    # 时间过滤
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    recent_events = [e for e in stats.get('events', []) if e.get('timestamp', '') > cutoff]
    
    if task_id:
        # 单个任务统计
        if task_id not in stats['tasks']:
            return {'error': f'未找到任务：{task_id}'}
        
        task_stat = stats['tasks'][task_id].copy()
        task_events = [e for e in recent_events if e['task_id'] == task_id]
        
        # 计算成功率
        if task_stat['total_events'] > 0:
            task_stat['success_rate'] = round(
                task_stat['completed_count'] / task_stat['total_events'] * 100, 2
            )
        else:
            task_stat['success_rate'] = 0
        
        # 计算平均耗时
        if task_stat['completed_count'] > 0:
            task_stat['avg_duration_ms'] = round(
                task_stat['total_duration_ms'] / task_stat['completed_count']
            )
        else:
            task_stat['avg_duration_ms'] = 0
        
        return {'task': task_stat, 'recent_events': task_events[-100:]}
    
    else:
        # 所有任务统计
        tasks_list = []
        for tid, tstat in stats['tasks'].items():
            tstat_copy = tstat.copy()
            if tstat_copy['total_events'] > 0:
                tstat_copy['success_rate'] = round(
                    tstat_copy['completed_count'] / tstat_copy['total_events'] * 100, 2
                )
            else:
                tstat_copy['success_rate'] = 0
            if tstat_copy['completed_count'] > 0:
                tstat_copy['avg_duration_ms'] = round(
                    tstat_copy['total_duration_ms'] / tstat_copy['completed_count']
                )
            else:
                tstat_copy['avg_duration_ms'] = 0
            tasks_list.append(tstat_copy)
        
        # 按事件数排序
        tasks_list.sort(key=lambda x: x['total_events'], reverse=True)
        
        # 总体汇总
        total_events = sum(t['total_events'] for t in tasks_list)
        total_completed = sum(t['completed_count'] for t in tasks_list)
        total_failed = sum(t['failed_count'] for t in tasks_list)
        total_duration = sum(t['total_duration_ms'] for t in tasks_list)
        
        summary = {
            'total_tasks': len(tasks_list),
            'total_events': total_events,
            'total_completed': total_completed,
            'total_failed': total_failed,
            'overall_success_rate': round(total_completed / total_events * 100, 2) if total_events > 0 else 0,
            'total_duration_ms': total_duration,
            'avg_duration_ms': round(total_duration / total_completed, 2) if total_completed > 0 else 0
        }
        
        return {'tasks': tasks_list, 'summary': summary, 'recent_events': recent_events[-100:]}


# ========== 会话统计 ==========

def record_session_event(session_id: str, agent_id: str, event_type: str,
                         channel: str = 'feishu', metadata: Dict = None):
    """记录会话事件"""
    stats = load_json_file(SESSION_STATS_FILE, {'sessions': {}, 'events': []})
    
    if 'sessions' not in stats:
        stats['sessions'] = {}
    if 'events' not in stats:
        stats['events'] = []
    
    now = datetime.now().isoformat()
    
    # 更新会话统计
    if session_id not in stats['sessions']:
        stats['sessions'][session_id] = {
            'session_id': session_id,
            'agent_id': agent_id,
            'channel': channel,
            'total_events': 0,
            'messages_count': 0,
            'first_event': now,
            'last_event': now,
            'status': 'active'
        }
    
    session_stat = stats['sessions'][session_id]
    session_stat['total_events'] += 1
    session_stat['last_event'] = now
    
    if event_type == 'message':
        session_stat['messages_count'] += 1
    
    # 记录事件详情
    event_record = {
        'timestamp': now,
        'session_id': session_id,
        'agent_id': agent_id,
        'channel': channel,
        'event_type': event_type,
        'metadata': metadata or {}
    }
    stats['events'].append(event_record)
    
    # 保留最近 10000 条记录
    if len(stats['events']) > 10000:
        stats['events'] = stats['events'][-10000:]
    
    save_json_file(SESSION_STATS_FILE, stats)


def get_session_stats(session_id: str = None, days: int = 30, active_only: bool = False) -> Dict[str, Any]:
    """获取会话统计数据"""
    stats = load_json_file(SESSION_STATS_FILE, {'sessions': {}, 'events': []})
    
    if not stats.get('sessions'):
        return {'sessions': [], 'summary': {}}
    
    # 时间过滤
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    recent_events = [e for e in stats.get('events', []) if e.get('timestamp', '') > cutoff]
    
    if session_id:
        # 单个会话统计
        if session_id not in stats['sessions']:
            return {'error': f'未找到会话：{session_id}'}
        
        session_stat = stats['sessions'][session_id].copy()
        session_events = [e for e in recent_events if e['session_id'] == session_id]
        
        return {'session': session_stat, 'recent_events': session_events[-100:]}
    
    else:
        # 所有会话统计
        sessions_list = []
        for sid, sstat in stats['sessions'].items():
            sstat_copy = sstat.copy()
            
            # 检查是否活跃（最近 24 小时有事件）
            active_cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            sstat_copy['is_active'] = sstat_copy.get('last_event', '') > active_cutoff
            
            if active_only and not sstat_copy['is_active']:
                continue
            
            sessions_list.append(sstat_copy)
        
        # 按最后事件时间排序
        sessions_list.sort(key=lambda x: x.get('last_event', ''), reverse=True)
        
        # 总体汇总
        total_sessions = len(sessions_list)
        active_sessions = sum(1 for s in sessions_list if s.get('is_active', False))
        total_messages = sum(s['messages_count'] for s in sessions_list)
        
        # 按渠道统计
        channel_stats = defaultdict(int)
        for s in sessions_list:
            channel_stats[s.get('channel', 'unknown')] += 1
        
        summary = {
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'inactive_sessions': total_sessions - active_sessions,
            'total_messages': total_messages,
            'channel_distribution': dict(channel_stats)
        }
        
        return {'sessions': sessions_list, 'summary': summary, 'recent_events': recent_events[-100:]}


# ========== 数据导出 ==========

def export_stats_to_csv(stat_type: str, output_path: str, days: int = 30) -> tuple:
    """导出统计数据到 CSV"""
    try:
        if stat_type == 'agent':
            stats = get_agent_stats(days=days)
            if 'error' in stats:
                return False, stats['error']
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Agent ID', 'Model', '总调用', '成功', '失败', '成功率', '平均耗时 (ms)', '总 Tokens'])
                
                for agent in stats.get('agents', []):
                    writer.writerow([
                        agent['agent_id'],
                        agent['model_id'],
                        agent['total_calls'],
                        agent['successful_calls'],
                        agent['failed_calls'],
                        f"{agent['success_rate']}%",
                        agent['avg_duration_ms'],
                        agent['total_tokens']
                    ])
        
        elif stat_type == 'task':
            stats = get_task_stats(days=days)
            if 'error' in stats:
                return False, stats['error']
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['任务 ID', '总事件', '完成数', '失败数', '成功率', '平均耗时 (ms)'])
                
                for task in stats.get('tasks', []):
                    writer.writerow([
                        task['task_id'],
                        task['total_events'],
                        task['completed_count'],
                        task['failed_count'],
                        f"{task['success_rate']}%",
                        task['avg_duration_ms']
                    ])
        
        elif stat_type == 'session':
            stats = get_session_stats(days=days)
            if 'error' in stats:
                return False, stats['error']
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['会话 ID', 'Agent', '渠道', '消息数', '状态', '最后活跃'])
                
                for session in stats.get('sessions', []):
                    writer.writerow([
                        session['session_id'],
                        session['agent_id'],
                        session.get('channel', 'unknown'),
                        session['messages_count'],
                        'active' if session.get('is_active', False) else 'inactive',
                        session.get('last_event', '')[:19].replace('T', ' ')
                    ])
        
        else:
            return False, f'不支持的统计类型：{stat_type}'
        
        return True, f'统计数据已导出到：{output_path}'
    
    except Exception as e:
        return False, f'导出失败：{str(e)}'


def export_stats_to_json(stat_type: str, output_path: str, days: int = 30) -> tuple:
    """导出统计数据到 JSON"""
    try:
        if stat_type == 'agent':
            data = get_agent_stats(days=days)
        elif stat_type == 'task':
            data = get_task_stats(days=days)
        elif stat_type == 'session':
            data = get_session_stats(days=days)
        else:
            return False, f'不支持的统计类型：{stat_type}'
        
        if 'error' in data:
            return False, data['error']
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return True, f'统计数据已导出到：{output_path}'
    
    except Exception as e:
        return False, f'导出失败：{str(e)}'


# ========== CLI 命令封装 ==========

def cmd_stats_agent(args):
    """Agent 使用统计"""
    
    output_format = 'json' if '--json' in args else 'table'
    days = 30
    
    if '--days' in args:
        idx = args.index('--days')
        if idx + 1 < len(args):
            try:
                days = int(args[idx + 1])
            except ValueError:
                pass
    
    agent_id = None
    for i, arg in enumerate(args):
        if arg not in ['stats', 'agent', '--json', '--days'] and i > 2:
            agent_id = arg
            break
    
    stats_data = get_agent_stats(agent_id, days)
    
    if 'error' in stats_data:
        print(c_red(f'\n❌ {stats_data["error"]}\n'))
        return
    
    if output_format == 'json':
        print(json.dumps(stats_data, indent=2, ensure_ascii=False))
        print()
        return
    
    print(c_cyan(f'\n📊 Agent 使用统计 (最近 {days} 天):\n'))
    
    if agent_id:
        # 单个 Agent
        agent = stats_data.get('agent', {})
        headers = ['属性', '值']
        rows = [
            ['Agent ID', c_yellow(agent['agent_id'])],
            ['模型', agent['model_id']],
            ['总调用', str(agent['total_calls'])],
            ['成功', c_green(str(agent['successful_calls']))],
            ['失败', c_red(str(agent['failed_calls']))],
            ['成功率', f"{agent['success_rate']}%"],
            ['平均耗时', f"{agent['avg_duration_ms']} ms"],
            ['总 Tokens', str(agent['total_tokens'])],
            ['平均 Tokens', str(agent['avg_tokens'])],
            ['首次调用', agent.get('first_call', '')[:19].replace('T', ' ') if agent.get('first_call') else '-'],
            ['最后调用', agent.get('last_call', '')[:19].replace('T', ' ') if agent.get('last_call') else '-']
        ]
        print(create_table(headers, rows))
    else:
        # 所有 Agent
        summary = stats_data.get('summary', {})
        print(c_cyan('总体汇总:\n'))
        headers = ['总 Agent 数', '总调用', '成功率', '总 Tokens', '平均耗时']
        rows = [[
            str(summary.get('total_agents', 0)),
            str(summary.get('total_calls', 0)),
            f"{summary.get('overall_success_rate', 0)}%",
            str(summary.get('total_tokens_used', 0)),
            f"{summary.get('avg_duration_ms', 0)} ms"
        ]]
        print(create_table(headers, rows))
        
        print(c_cyan('\nAgent 排行:\n'))
        agents = stats_data.get('agents', [])[:10]
        headers = ['Agent ID', '调用次数', '成功率', '平均耗时']
        rows = []
        for agent in agents:
            rows.append([
                c_yellow(agent['agent_id'][:25]),
                str(agent['total_calls']),
                f"{agent['success_rate']}%",
                f"{agent['avg_duration_ms']} ms"
            ])
        print(create_table(headers, rows))
    
    print()


def cmd_stats_task(args):
    """任务统计"""
    
    output_format = 'json' if '--json' in args else 'table'
    days = 30
    
    if '--days' in args:
        idx = args.index('--days')
        if idx + 1 < len(args):
            try:
                days = int(args[idx + 1])
            except ValueError:
                pass
    
    task_id = None
    for i, arg in enumerate(args):
        if arg not in ['stats', 'task', '--json', '--days'] and i > 2:
            task_id = arg
            break
    
    stats_data = get_task_stats(task_id, days)
    
    if 'error' in stats_data:
        print(c_red(f'\n❌ {stats_data["error"]}\n'))
        return
    
    if output_format == 'json':
        print(json.dumps(stats_data, indent=2, ensure_ascii=False))
        print()
        return
    
    print(c_cyan(f'\n📊 任务统计 (最近 {days} 天):\n'))
    
    if task_id:
        # 单个任务
        task = stats_data.get('task', {})
        headers = ['属性', '值']
        rows = [
            ['任务 ID', c_yellow(task['task_id'])],
            ['总事件', str(task['total_events'])],
            ['完成数', c_green(str(task['completed_count']))],
            ['失败数', c_red(str(task['failed_count']))],
            ['成功率', f"{task['success_rate']}%"],
            ['平均耗时', f"{task['avg_duration_ms']} ms"]
        ]
        print(create_table(headers, rows))
    else:
        # 所有任务
        summary = stats_data.get('summary', {})
        print(c_cyan('总体汇总:\n'))
        headers = ['总任务数', '总事件', '完成数', '失败数', '成功率', '平均耗时']
        rows = [[
            str(summary.get('total_tasks', 0)),
            str(summary.get('total_events', 0)),
            c_green(str(summary.get('total_completed', 0))),
            c_red(str(summary.get('total_failed', 0))),
            f"{summary.get('overall_success_rate', 0)}%",
            f"{summary.get('avg_duration_ms', 0)} ms"
        ]]
        print(create_table(headers, rows))
        
        print(c_cyan('\n任务排行:\n'))
        tasks = stats_data.get('tasks', [])[:10]
        headers = ['任务 ID', '事件数', '成功率', '平均耗时']
        rows = []
        for task in tasks:
            rows.append([
                c_yellow(task['task_id'][:25]),
                str(task['total_events']),
                f"{task['success_rate']}%",
                f"{task['avg_duration_ms']} ms"
            ])
        print(create_table(headers, rows))
    
    print()


def cmd_stats_session(args):
    """会话统计"""
    
    output_format = 'json' if '--json' in args else 'table'
    days = 30
    active_only = '--active' in args
    
    if '--days' in args:
        idx = args.index('--days')
        if idx + 1 < len(args):
            try:
                days = int(args[idx + 1])
            except ValueError:
                pass
    
    session_id = None
    for i, arg in enumerate(args):
        if arg not in ['stats', 'session', '--json', '--days', '--active'] and i > 2:
            session_id = arg
            break
    
    stats_data = get_session_stats(session_id, days, active_only)
    
    if 'error' in stats_data:
        print(c_red(f'\n❌ {stats_data["error"]}\n'))
        return
    
    if output_format == 'json':
        print(json.dumps(stats_data, indent=2, ensure_ascii=False))
        print()
        return
    
    print(c_cyan(f'\n📊 会话统计 (最近 {days} 天):\n'))
    
    if session_id:
        # 单个会话
        session = stats_data.get('session', {})
        headers = ['属性', '值']
        rows = [
            ['会话 ID', c_yellow(session['session_id'])],
            ['Agent', session['agent_id']],
            ['渠道', session.get('channel', 'unknown')],
            ['消息数', str(session['messages_count'])],
            ['状态', c_green('active') if session.get('is_active', False) else c_gray('inactive')],
            ['首次事件', session.get('first_event', '')[:19].replace('T', ' ')],
            ['最后事件', session.get('last_event', '')[:19].replace('T', ' ')]
        ]
        print(create_table(headers, rows))
    else:
        # 所有会话
        summary = stats_data.get('summary', {})
        print(c_cyan('总体汇总:\n'))
        headers = ['总会话', '活跃会话', '非活跃', '总消息数']
        rows = [[
            str(summary.get('total_sessions', 0)),
            c_green(str(summary.get('active_sessions', 0))),
            c_gray(str(summary.get('inactive_sessions', 0))),
            str(summary.get('total_messages', 0))
        ]]
        print(create_table(headers, rows))
        
        # 渠道分布
        channel_dist = summary.get('channel_distribution', {})
        if channel_dist:
            print(c_cyan('\n渠道分布:\n'))
            for channel, count in channel_dist.items():
                print(f"  {c_yellow(channel)}: {count}")
        
        print(c_cyan('\n会话列表:\n'))
        sessions = stats_data.get('sessions', [])[:10]
        headers = ['会话 ID', 'Agent', '渠道', '消息数', '状态']
        rows = []
        for session in sessions:
            rows.append([
                c_yellow(session['session_id'][:20] + '...'),
                session['agent_id'][:20],
                session.get('channel', 'unknown'),
                str(session['messages_count']),
                c_green('active') if session.get('is_active', False) else c_gray('inactive')
            ])
        print(create_table(headers, rows))
    
    print()


def cmd_stats_export(args):
    """导出统计数据"""
    
    if len(args) < 5:
        print(c_red('❌ 参数不足'))
        print('用法：claw-ex stats export <agent|task|session> <csv|json> <output_path> [--days 30]')
        return
    
    stat_type = args[2]
    format_type = args[3]
    output_path = args[4]
    
    days = 30
    if '--days' in args:
        idx = args.index('--days')
        if idx + 1 < len(args):
            try:
                days = int(args[idx + 1])
            except ValueError:
                pass
    
    if format_type == 'csv':
        success, message = export_stats_to_csv(stat_type, output_path, days)
    elif format_type == 'json':
        success, message = export_stats_to_json(stat_type, output_path, days)
    else:
        print(c_red(f'\n❌ 不支持的导出格式：{format_type}\n'))
        return
    
    if success:
        print(c_green(f'\n✅ {message}\n'))
    else:
        print(c_red(f'\n❌ {message}\n'))
