#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
环境配置管理模块
负责环境配置的创建、切换、持久化管理
"""

import os
import json
from datetime import datetime
from pathlib import Path

# 环境配置存储路径
ENV_CONFIG_DIR = Path.home() / '.openclaw' / 'envs'
ENV_INDEX_FILE = ENV_CONFIG_DIR / 'environments.json'
ENV_ACTIVE_FILE = ENV_CONFIG_DIR / 'active_env.json'

def ensure_env_dir():
    """确保环境配置目录存在"""
    ENV_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_env_index():
    """加载环境索引文件"""
    if not ENV_INDEX_FILE.exists():
        return {'environments': [], 'default': None}
    
    try:
        with open(ENV_INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'environments': [], 'default': None}

def save_env_index(index):
    """保存环境索引文件"""
    ensure_env_dir()
    with open(ENV_INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)

def get_active_env():
    """获取当前激活的环境"""
    if not ENV_ACTIVE_FILE.exists():
        return None
    
    try:
        with open(ENV_ACTIVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('active')
    except (json.JSONDecodeError, IOError):
        return None

def set_active_env(env_name):
    """设置当前激活的环境"""
    ensure_env_dir()
    with open(ENV_ACTIVE_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'active': env_name,
            'switched_at': datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)

def env_exists(env_name):
    """检查环境是否存在"""
    index = load_env_index()
    return any(env['name'] == env_name for env in index['environments'])

def create_environment(env_name, description='', variables=None):
    """
    创建新环境
    
    Args:
        env_name: 环境名称
        description: 环境描述
        variables: 环境变量字典
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not env_name or not env_name.strip():
        return False, '环境名称不能为空'
    
    env_name = env_name.strip()
    
    # 检查命名合法性
    if not env_name.replace('_', '').replace('-', '').isalnum():
        return False, '环境名称只能包含字母、数字、下划线和连字符'
    
    # 检查是否已存在
    if env_exists(env_name):
        return False, f'环境 "{env_name}" 已存在'
    
    # 创建环境配置
    env_config = {
        'name': env_name,
        'description': description or f'{env_name} 环境',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'variables': variables or {}
    }
    
    # 保存到索引
    index = load_env_index()
    index['environments'].append(env_config)
    
    # 如果是第一个环境，设为默认
    if not index['default']:
        index['default'] = env_name
        # 同时设为当前激活
        if not get_active_env():
            set_active_env(env_name)
    
    save_env_index(index)
    
    # 创建环境配置文件
    env_file = ENV_CONFIG_DIR / f'{env_name}.json'
    with open(env_file, 'w', encoding='utf-8') as f:
        json.dump(env_config, f, indent=2, ensure_ascii=False)
    
    return True, f'环境 "{env_name}" 创建成功'

def switch_environment(env_name):
    """
    切换到指定环境
    
    Args:
        env_name: 环境名称
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not env_name or not env_name.strip():
        return False, '环境名称不能为空'
    
    env_name = env_name.strip()
    
    # 检查环境是否存在
    if not env_exists(env_name):
        return False, f'环境 "{env_name}" 不存在，使用 claw-ex env list 查看可用环境'
    
    # 获取当前环境
    current_env = get_active_env()
    if current_env == env_name:
        return True, f'已在环境 "{env_name}" 中'
    
    # 切换环境
    set_active_env(env_name)
    
    prev_env = current_env or '无'
    return True, f'已从环境 "{prev_env}" 切换到 "{env_name}"'

def list_environments():
    """获取所有环境列表"""
    index = load_env_index()
    active_env = get_active_env()
    
    envs = []
    for env in index['environments']:
        envs.append({
            'name': env['name'],
            'description': env.get('description', ''),
            'created_at': env.get('created_at', ''),
            'is_active': env['name'] == active_env,
            'is_default': env['name'] == index.get('default')
        })
    
    return envs

def get_environment(env_name):
    """获取环境详细信息"""
    index = load_env_index()
    
    for env in index['environments']:
        if env['name'] == env_name:
            env_file = ENV_CONFIG_DIR / f'{env_name}.json'
            if env_file.exists():
                try:
                    with open(env_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except (json.JSONDecodeError, IOError):
                    pass
            return env
    
    return None

def delete_environment(env_name):
    """
    删除环境
    
    Args:
        env_name: 环境名称
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if not env_exists(env_name):
        return False, f'环境 "{env_name}" 不存在'
    
    index = load_env_index()
    
    # 不能删除当前激活的环境
    if get_active_env() == env_name:
        return False, f'不能删除当前激活的环境 "{env_name}"，请先切换到其他环境'
    
    # 从索引中移除
    index['environments'] = [e for e in index['environments'] if e['name'] != env_name]
    
    # 如果删除的是默认环境，清除默认设置
    if index.get('default') == env_name:
        index['default'] = index['environments'][0]['name'] if index['environments'] else None
    
    save_env_index(index)
    
    # 删除环境配置文件
    env_file = ENV_CONFIG_DIR / f'{env_name}.json'
    if env_file.exists():
        env_file.unlink()
    
    return True, f'环境 "{env_name}" 已删除'
