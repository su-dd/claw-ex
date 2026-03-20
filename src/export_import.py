#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claw-ex 导入导出模块
支持 Agent 配置、模板、环境数据的导入导出
"""

import sys
import os
import json
import yaml
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

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
AGENTS_DIR = OPENCLAW_HOME / 'agents'
TEMPLATES_DIR = OPENCLAW_HOME / 'templates'
ENV_CONFIG_FILE = OPENCLAW_HOME / 'env-config.json'
EXPORT_BACKUP_DIR = OPENCLAW_HOME / 'workspace-gongbu' / 'claw-ex' / 'backups' / 'exports'

# 支持导出的类型
EXPORT_TYPES = ['agent', 'template', 'env', 'all']

def detect_format(filepath: Path) -> str:
    """根据文件扩展名检测格式"""
    suffix = filepath.suffix.lower()
    if suffix in ['.json']:
        return 'json'
    elif suffix in ['.yaml', '.yml']:
        return 'yaml'
    return 'json'  # 默认

def load_file(filepath: Path) -> Any:
    """加载文件（支持 JSON/YAML）"""
    fmt = detect_format(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        if fmt == 'json':
            return json.load(f)
        else:
            return yaml.safe_load(f)

def save_file(filepath: Path, data: Any, fmt: str = 'json'):
    """保存文件（支持 JSON/YAML）"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        if fmt == 'yaml':
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)
        else:
            json.dump(data, f, ensure_ascii=False, indent=2)

def export_agent(agent_name: str, output_path: Path, fmt: str = 'json') -> bool:
    """导出 Agent 配置"""
    config_dir = AGENTS_DIR / agent_name / 'agent'
    if not config_dir.exists():
        print(c_red(f'❌ Agent "{agent_name}" 不存在'))
        return False
    
    export_data = {
        'metadata': {
            'type': 'agent',
            'name': agent_name,
            'exported_at': datetime.now().isoformat(),
            'version': '1.0'
        },
        'configs': {}
    }
    
    # 导出配置文件
    for config_file in ['models.json', 'auth-profiles.json', 'config.json']:
        config_path = config_dir / config_file
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    export_data['configs'][config_file] = json.load(f)
            except Exception as e:
                print(c_yellow(f'⚠️  跳过 {config_file}: {e}'))
    
    # 保存导出文件
    save_file(output_path, export_data, fmt)
    print(c_green(f'✅ Agent "{agent_name}" 已导出到：{output_path}'))
    return True

def export_template(template_name: str, output_path: Path, fmt: str = 'json') -> bool:
    """导出模板"""
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        print(c_red(f'❌ 模板 "{template_name}" 不存在'))
        return False
    
    export_data = {
        'metadata': {
            'type': 'template',
            'name': template_name,
            'exported_at': datetime.now().isoformat(),
            'version': '1.0'
        }
    }
    
    if template_path.is_file():
        with open(template_path, 'r', encoding='utf-8') as f:
            export_data['content'] = f.read()
    else:
        # 目录模板
        export_data['files'] = {}
        for f in template_path.rglob('*'):
            if f.is_file():
                rel_path = str(f.relative_to(template_path))
                with open(f, 'r', encoding='utf-8') as fp:
                    export_data['files'][rel_path] = fp.read()
    
    save_file(output_path, export_data, fmt)
    print(c_green(f'✅ 模板 "{template_name}" 已导出到：{output_path}'))
    return True

def export_env(output_path: Path, fmt: str = 'json') -> bool:
    """导出环境配置"""
    if not ENV_CONFIG_FILE.exists():
        print(c_red(f'❌ 环境配置文件不存在：{ENV_CONFIG_FILE}'))
        return False
    
    export_data = {
        'metadata': {
            'type': 'env',
            'exported_at': datetime.now().isoformat(),
            'version': '1.0'
        },
        'config': load_file(ENV_CONFIG_FILE)
    }
    
    save_file(output_path, export_data, fmt)
    print(c_green(f'✅ 环境配置已导出到：{output_path}'))
    return True

def export_all(output_path: Path, fmt: str = 'json') -> bool:
    """导出所有数据"""
    EXPORT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    base_path = output_path.parent / f"claw-ex-all-{ts}"
    
    exported = []
    
    # 导出所有 Agent
    if AGENTS_DIR.exists():
        for agent_dir in AGENTS_DIR.iterdir():
            if agent_dir.is_dir() and not agent_dir.name.startswith('.'):
                agent_file = base_path.with_name(f"{base_path.name}-agent-{agent_dir.name}.{fmt}")
                if export_agent(agent_dir.name, agent_file, fmt):
                    exported.append(str(agent_file))
    
    # 导出所有模板
    if TEMPLATES_DIR.exists():
        for template_path in TEMPLATES_DIR.iterdir():
            template_file = base_path.with_name(f"{base_path.name}-template-{template_path.name}.{fmt}")
            if export_template(template_path.name, template_file, fmt):
                exported.append(str(template_file))
    
    # 导出环境配置
    env_file = base_path.with_name(f"{base_path.name}-env.{fmt}")
    if export_env(env_file, fmt):
        exported.append(str(env_file))
    
    print(c_green(f'\n✅ 共导出 {len(exported)} 个文件'))
    for f in exported:
        print(c_gray(f'  - {f}'))
    return True

def import_file(input_path: Path, overwrite: bool = False) -> bool:
    """导入文件"""
    if not input_path.exists():
        print(c_red(f'❌ 文件不存在：{input_path}'))
        return False
    
    try:
        data = load_file(input_path)
    except Exception as e:
        print(c_red(f'❌ 文件加载失败：{e}'))
        return False
    
    if not isinstance(data, dict) or 'metadata' not in data:
        print(c_red('❌ 无效的导出文件格式（缺少 metadata）'))
        return False
    
    metadata = data['metadata']
    export_type = metadata.get('type')
    
    if export_type == 'agent':
        return import_agent(data, overwrite)
    elif export_type == 'template':
        return import_template(data, overwrite)
    elif export_type == 'env':
        return import_env(data, overwrite)
    else:
        print(c_red(f'❌ 未知的导出类型：{export_type}'))
        return False

def import_agent(data: Dict, overwrite: bool = False) -> bool:
    """导入 Agent 配置"""
    agent_name = data['metadata'].get('name')
    if not agent_name:
        print(c_red('❌ 缺少 Agent 名称'))
        return False
    
    target_dir = AGENTS_DIR / agent_name / 'agent'
    
    if target_dir.exists() and not overwrite:
        print(c_yellow(f'⚠️  Agent "{agent_name}" 已存在，使用 --overwrite 强制覆盖'))
        return False
    
    target_dir.mkdir(parents=True, exist_ok=True)
    
    configs = data.get('configs', {})
    for config_file, content in configs.items():
        config_path = target_dir / config_file
        if config_path.exists() and not overwrite:
            backup_path = config_path.with_suffix(f'.json.bak.{datetime.now().strftime("%Y%m%d-%H%M%S")}')
            shutil.copy2(config_path, backup_path)
            print(c_gray(f'  备份：{config_path.name} → {backup_path.name}'))
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        print(c_green(f'  ✓ 写入：{config_file}'))
    
    print(c_green(f'\n✅ Agent "{agent_name}" 导入完成'))
    return True

def import_template(data: Dict, overwrite: bool = False) -> bool:
    """导入模板"""
    template_name = data['metadata'].get('name')
    if not template_name:
        print(c_red('❌ 缺少模板名称'))
        return False
    
    target_path = TEMPLATES_DIR / template_name
    
    if target_path.exists() and not overwrite:
        print(c_yellow(f'⚠️  模板 "{template_name}" 已存在，使用 --overwrite 强制覆盖'))
        return False
    
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    
    if 'content' in data:
        # 单文件模板
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(data['content'])
        print(c_green(f'  ✓ 写入：{template_name}'))
    elif 'files' in data:
        # 多文件模板
        target_path.mkdir(parents=True, exist_ok=True)
        for rel_path, content in data['files'].items():
            file_path = target_path / rel_path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(c_green(f'  ✓ 写入：{rel_path}'))
    
    print(c_green(f'\n✅ 模板 "{template_name}" 导入完成'))
    return True

def import_env(data: Dict, overwrite: bool = False) -> bool:
    """导入环境配置"""
    if ENV_CONFIG_FILE.exists() and not overwrite:
        backup_path = ENV_CONFIG_FILE.with_suffix(f'.json.bak.{datetime.now().strftime("%Y%m%d-%H%M%S")}')
        shutil.copy2(ENV_CONFIG_FILE, backup_path)
        print(c_gray(f'备份：{ENV_CONFIG_FILE.name} → {backup_path.name}'))
    
    ENV_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    save_file(ENV_CONFIG_FILE, data.get('config', {}), 'json')
    print(c_green(f'\n✅ 环境配置导入完成：{ENV_CONFIG_FILE}'))
    return True

def cmd_export(args: List[str]):
    """export 命令实现"""
    if len(args) < 3:
        print(c_red('❌ 参数不足'))
        print('用法：claw-ex export <type> <output> [--format json|yaml]')
        print('类型：agent, template, env, all')
        print('示例:')
        print('  claw-ex export agent my-agent ./backup.json')
        print('  claw-ex export template my-template ./template.yaml --format yaml')
        print('  claw-ex export env ./env-config.json')
        print('  claw-ex export all ./full-backup')
        sys.exit(1)
    
    export_type = args[2]
    output_path = Path(args[3]) if len(args) > 3 else None
    
    # 解析格式参数
    fmt = 'json'
    if '--format' in args:
        fmt_idx = args.index('--format')
        if fmt_idx + 1 < len(args):
            fmt = args[fmt_idx + 1].lower()
    
    if export_type not in EXPORT_TYPES:
        print(c_red(f'❌ 不支持的导出类型：{export_type}'))
        print(f'支持的类型：{", ".join(EXPORT_TYPES)}')
        sys.exit(1)
    
    if export_type == 'all':
        if not output_path:
            output_path = EXPORT_BACKUP_DIR / f"claw-ex-all-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        export_all(output_path, fmt)
    elif export_type == 'agent':
        if len(args) < 4:
            print(c_red('❌ 缺少 agent 名称'))
            sys.exit(1)
        agent_name = args[2]
        output_path = Path(args[3]) if len(args) > 3 else None
        if not output_path:
            output_path = EXPORT_BACKUP_DIR / f"agent-{agent_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.{fmt}"
        export_agent(agent_name, output_path, fmt)
    elif export_type == 'template':
        if len(args) < 4:
            print(c_red('❌ 缺少模板名称'))
            sys.exit(1)
        template_name = args[2]
        output_path = Path(args[3]) if len(args) > 3 else None
        if not output_path:
            output_path = EXPORT_BACKUP_DIR / f"template-{template_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.{fmt}"
        export_template(template_name, output_path, fmt)
    elif export_type == 'env':
        output_path = Path(args[2]) if len(args) > 2 else None
        if not output_path:
            output_path = EXPORT_BACKUP_DIR / f"env-{datetime.now().strftime('%Y%m%d-%H%M%S')}.{fmt}"
        export_env(output_path, fmt)

def cmd_import(args: List[str]):
    """import 命令实现"""
    if len(args) < 3:
        print(c_red('❌ 参数不足'))
        print('用法：claw-ex import <file> [--overwrite]')
        print('示例:')
        print('  claw-ex import ./backup.json')
        print('  claw-ex import ./template.yaml --overwrite')
        sys.exit(1)
    
    input_path = Path(args[2])
    overwrite = '--overwrite' in args
    
    import_file(input_path, overwrite)

def cmd_export_list(args: List[str]):
    """列出可导出的项目"""
    print(c_cyan('\n📦 可导出的 Agent:\n'))
    if AGENTS_DIR.exists():
        agents = [d.name for d in AGENTS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
        if agents:
            for agent in agents:
                print(f"  - {c_green(agent)}")
        else:
            print(c_gray('  （无）'))
    else:
        print(c_gray('  （Agents 目录不存在）'))
    
    print(c_cyan('\n📄 可导出的模板:\n'))
    if TEMPLATES_DIR.exists():
        templates = [f.name for f in TEMPLATES_DIR.iterdir()]
        if templates:
            for t in templates:
                print(f"  - {c_green(t)}")
        else:
            print(c_gray('  （无）'))
    else:
        print(c_gray('  （模板目录不存在）'))
    
    print(c_cyan('\n⚙️  环境配置:\n'))
    if ENV_CONFIG_FILE.exists():
        print(f"  - {c_green(str(ENV_CONFIG_FILE))}")
    else:
        print(c_gray('  （未配置）'))
    print()
