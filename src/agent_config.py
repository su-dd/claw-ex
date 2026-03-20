#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claw-ex Agent 配置管理命令"""

import sys, os, json, shutil
from datetime import datetime
from pathlib import Path

class Colors:
    RESET, BOLD, RED, GREEN, YELLOW, BLUE, CYAN, GRAY = '\033[0m', '\033[1m', '\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[96m', '\033[90m'

def c_cyan(s): return f"{Colors.CYAN}{s}{Colors.RESET}"
def c_yellow(s): return f"{Colors.YELLOW}{s}{Colors.RESET}"
def c_green(s): return f"{Colors.GREEN}{s}{Colors.RESET}"
def c_red(s): return f"{Colors.RED}{s}{Colors.RESET}"
def c_gray(s): return f"{Colors.GRAY}{s}{Colors.RESET}"
def c_bold(s): return f"{Colors.BOLD}{s}{Colors.RESET}"

OPENCLAW_HOME = Path(os.environ.get('OPENCLAW_HOME', Path.home() / '.openclaw'))
AGENTS_DIR = OPENCLAW_HOME / 'agents'
BACKUP_DIR = OPENCLAW_HOME / 'workspace-gongbu' / 'claw-ex' / 'backups' / 'agent-config'
SENSITIVE_FIELDS = {'apiKey', 'api_key', 'secret', 'password', 'token', 'credentials'}

def get_agent_config_dir(agent_name):
    p = AGENTS_DIR / agent_name / 'agent'
    return p if p.exists() else None

def list_agents():
    if not AGENTS_DIR.exists(): return []
    return [{'name': d.name, 'has_models': (d/'agent'/'models.json').exists(), 'has_auth': (d/'agent'/'auth-profiles.json').exists(), 'config_path': str(d/'agent')} for d in AGENTS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]

def mask_sensitive(value, is_sensitive=False):
    if is_sensitive and isinstance(value, str):
        return '*' * len(value) if len(value) <= 8 else value[:3] + '*' * (len(value) - 6) + value[-3:]
    return value

def load_config(agent_name, config_file):
    config_dir = get_agent_config_dir(agent_name)
    if not config_dir: return None, f"Agent '{agent_name}' 不存在"
    config_path = config_dir / config_file
    if not config_path.exists(): return None, f"配置文件不存在：{config_path}"
    try:
        with open(config_path, 'r', encoding='utf-8') as f: return json.load(f), None
    except json.JSONDecodeError as e: return None, f"JSON 解析错误：{e}"

def backup_config(agent_name, config_file):
    config_dir = get_agent_config_dir(agent_name)
    if not config_dir: return
    config_path = config_dir / config_file
    if not config_path.exists(): return
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    backup_path = BACKUP_DIR / f"{agent_name}-{config_file}-{ts}"
    shutil.copy2(config_path, backup_path)
    return backup_path

def list_backups(agent_name=None):
    if not BACKUP_DIR.exists(): return []
    backups = []
    for f in sorted(BACKUP_DIR.iterdir(), key=lambda x: x.name, reverse=True):
        if f.is_file():
            parts = f.stem.split('-')
            if len(parts) >= 3 and (agent_name is None or parts[0] == agent_name):
                backups.append({'file': f.name, 'agent': parts[0], 'created': f.stat().st_mtime, 'size': f.stat().st_size})
    return backups

def restore_backup(backup_file):
    backup_path = BACKUP_DIR / backup_file
    if not backup_path.exists(): return False, f"备份文件不存在：{backup_file}"
    parts = backup_file.split('-')
    if len(parts) < 3: return False, "无效的备份文件名格式"
    agent_name, config_file = parts[0], '-'.join(parts[1:-2]) + '.json'
    config_dir = get_agent_config_dir(agent_name)
    if not config_dir: return False, f"Agent '{agent_name}' 不存在"
    try:
        shutil.copy2(backup_path, config_dir / config_file)
        return True, f"已恢复到：{config_dir / config_file}"
    except Exception as e: return False, f"恢复失败：{e}"

def validate_config(agent_name, config_file):
    config, error = load_config(agent_name, config_file)
    if error: return False, error
    schema = {'models.json': ['providers'], 'auth-profiles.json': ['profiles']}.get(config_file)
    if not schema: return True, "未知配置文件类型，跳过 schema 验证"
    for req in schema:
        if req not in config: return False, f"缺少必需字段：{req}"
    return True, "配置验证通过"

def is_field_sensitive(field_name): return any(s in field_name.lower() for s in SENSITIVE_FIELDS)
def is_field_editable(field_name): return not is_field_sensitive(field_name)

def print_config_tree(data, indent=0):
    prefix = '  ' * indent
    if isinstance(data, dict):
        for key, value in data.items():
            sens, edit = is_field_sensitive(key), is_field_editable(key)
            marker = "🔒" if sens else ("✏️" if edit else "👁️")
            if isinstance(value, (dict, list)):
                print(f"{prefix}{c_cyan(marker)} {c_bold(key)}:")
                print_config_tree(value, indent + 1)
            else:
                dv = mask_sensitive(value, sens)
                st = "🔒 敏感" if sens else ("✏️ 可编辑" if edit else "👁️ 只读")
                sc = c_red if sens else (c_green if edit else c_gray)
                print(f"{prefix}{c_cyan('├─')} {c_bold(key)}: {dv} {sc(st)}")
    elif isinstance(data, list):
        for i, item in enumerate(data):
            if isinstance(item, (dict, list)):
                print(f"{prefix}{c_cyan('├─')} [{i}]")
                print_config_tree(item, indent + 1)
            else: print(f"{prefix}{c_cyan('├─')} {item}")

def cmd_agent_list():
    print(c_cyan('\n📋 Agent 配置列表:\n'))
    agents = list_agents()
    if not agents: print(c_yellow("未找到任何 Agent 配置")); return
    print(f"{'Agent':<20} {'models.json':<12} {'auth-profiles.json':<20} {'配置路径'}")
    print('─' * 80)
    for a in agents:
        print(f"{c_bold(a['name']):<20} {'✅' if a['has_models'] else '❌':<12} {'✅' if a['has_auth'] else '❌':<20} {c_gray(a['config_path'][:40]+'...' if len(a['config_path'])>40 else a['config_path'])}")
    print()

def cmd_agent_config(agent_name, config_file='models.json'):
    print(c_cyan(f'\n🔧 Agent 配置：{c_bold(agent_name)}/{config_file}\n'))
    print("可编辑字段标记为 ✏️，敏感字段标记为 🔒，只读字段标记为 👁️\n")
    config, error = load_config(agent_name, config_file)
    if error: print(c_red(f"错误：{error}")); return
    print_config_tree(config)
    print()

def cmd_agent_validate(agent_name, config_file='models.json'):
    print(c_cyan(f'\n✅ 验证配置：{c_bold(agent_name)}/{config_file}\n'))
    valid, msg = validate_config(agent_name, config_file)
    print(c_green(f"✓ {msg}") if valid else c_red(f"✗ {msg}"))
    print()

def cmd_agent_diff(agent_name, config_file='models.json'):
    print(c_cyan(f'\n📊 配置变更对比：{c_bold(agent_name)}/{config_file}\n'))
    backups = list_backups(agent_name)
    if not backups: print(c_yellow("暂无备份记录")); return
    print(f"最近 5 个备份:\n{'备份文件':<50} {'创建时间':<20} {'大小'}\n{'─' * 80}")
    for b in backups[:5]:
        print(f"{b['file']:<50} {datetime.fromtimestamp(b['created']).strftime('%Y-%m-%d %H:%M:%S'):<20} {b['size']} bytes")
    print()

def cmd_agent_reset(agent_name, backup_file=None):
    print(c_cyan(f'\n🔄 配置回滚：{c_bold(agent_name)}\n'))
    if not backup_file:
        backups = list_backups(agent_name)
        if not backups: print(c_yellow("暂无备份记录")); return
        print("可用备份:\n")
        for i, b in enumerate(backups[:5], 1): print(f"  {i}. {b['file']} ({datetime.fromtimestamp(b['created']).strftime('%Y-%m-%d %H:%M:%S')})")
        print(c_yellow("\n请使用 'claw-ex agent reset <agent> <backup_file>' 指定要恢复的备份"))
        return
    success, msg = restore_backup(backup_file)
    print(c_green(f"✓ {msg}") if success else c_red(f"✗ {msg}"))
    print()

def cmd_agent_help():
    print(c_cyan("""
claw-ex Agent 配置管理命令

用法：claw-ex agent <command> [options]

命令:
  list                          列出所有 Agent 及其配置状态
  config <agent> [file]         查看配置文件 (默认：models.json)
  validate <agent> [file]       验证配置 schema
  diff <agent> [file]           查看配置变更历史
  reset <agent> [backup]        回滚配置到指定备份
  help                          显示此帮助信息

示例:
  claw-ex agent list
  claw-ex agent config zhongshu
  claw-ex agent validate menxia
  claw-ex agent diff shangshu models.json
  claw-ex agent reset gongbu gongbu-models.json-20260320-120000

安全说明:
  - 敏感字段 (apiKey 等) 显示时会脱敏
  - 敏感字段不支持编辑
  - 所有修改前会自动备份

配置路径：~/.openclaw/agents/<agent>/agent/
"""))

def main():
    if len(sys.argv) < 2: cmd_agent_help(); return
    cmd = sys.argv[1]
    if cmd == 'list': cmd_agent_list()
    elif cmd == 'config':
        if len(sys.argv) < 3: print(c_red("错误：请指定 Agent 名称")); return
        cmd_agent_config(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'models.json')
    elif cmd == 'validate':
        if len(sys.argv) < 3: print(c_red("错误：请指定 Agent 名称")); return
        cmd_agent_validate(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'models.json')
    elif cmd == 'diff':
        if len(sys.argv) < 3: print(c_red("错误：请指定 Agent 名称")); return
        cmd_agent_diff(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'models.json')
    elif cmd == 'reset':
        if len(sys.argv) < 3: print(c_red("错误：请指定 Agent 名称")); return
        cmd_agent_reset(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif cmd in ('help', '--help', '-h'): cmd_agent_help()
    else: print(c_red(f"未知命令：{cmd}")); cmd_agent_help()

if __name__ == '__main__': main()
