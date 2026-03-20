# -*- coding: utf-8 -*-
"""
环境检测与配置模块
负责 OpenClaw 环境检测、依赖检查、配置生成、环境管理
"""

import os
import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path
from datetime import datetime


# ============== 环境管理模块 ==============

class EnvironmentManager:
    """OpenClaw 环境管理器 - 支持多环境创建/切换"""
    
    def __init__(self):
        self.openclaw_dir = Path.home() / '.openclaw'
        self.environments_dir = self.openclaw_dir / 'environments'
        self.state_file = self.openclaw_dir / 'env_state.json'
        self.environments_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_env_dir(self, name: str) -> Path:
        """获取环境目录"""
        return self.environments_dir / name
    
    def _get_env_config(self, name: str) -> Path:
        """获取环境配置文件路径"""
        return self._get_env_dir(name) / 'config.json'
    
    def _load_state(self) -> dict:
        """加载环境状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'active': 'default', 'environments': {}}
    
    def _save_state(self, state: dict):
        """保存环境状态"""
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def create(self, name: str, template: str = 'default') -> dict:
        """创建新环境"""
        # 验证环境名
        if not name or not name.replace('_', '').replace('-', '').isalnum():
            return {
                'success': False,
                'error': '环境名只能包含字母、数字、下划线和连字符'
            }
        
        env_dir = self._get_env_dir(name)
        
        # 检查是否已存在
        if env_dir.exists():
            return {
                'success': False,
                'error': f'环境已存在：{name}'
            }
        
        try:
            # 创建环境目录
            env_dir.mkdir(parents=True, exist_ok=True)
            (env_dir / 'workspace').mkdir(exist_ok=True)
            (env_dir / 'logs').mkdir(exist_ok=True)
            (env_dir / 'sessions').mkdir(exist_ok=True)
            (env_dir / 'agents').mkdir(exist_ok=True)
            
            # 生成配置文件
            config = self._generate_env_config(name, template)
            with open(self._get_env_config(name), 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 复制 Agent 配置模板
            self._copy_agent_template(name)
            
            # 更新状态
            state = self._load_state()
            state['environments'][name] = {
                'created': datetime.now().isoformat(),
                'template': template,
                'workspace': str(env_dir / 'workspace')
            }
            self._save_state(state)
            
            return {
                'success': True,
                'path': str(env_dir),
                'config': str(self._get_env_config(name))
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'创建失败：{str(e)}'
            }
    
    def switch(self, name: str) -> dict:
        """切换环境"""
        env_dir = self._get_env_dir(name)
        
        # 验证环境存在
        if not env_dir.exists():
            return {
                'success': False,
                'error': f'环境不存在：{name}'
            }
        
        # 验证配置文件
        if not self._get_env_config(name).exists():
            return {
                'success': False,
                'error': f'环境配置损坏：{name}'
            }
        
        try:
            # 更新状态
            state = self._load_state()
            old_active = state['active']
            state['active'] = name
            state['last_switch'] = datetime.now().isoformat()
            self._save_state(state)
            
            return {
                'success': True,
                'from': old_active,
                'to': name,
                'path': str(env_dir)
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'切换失败：{str(e)}'
            }
    
    def list_all(self) -> list:
        """列出所有环境"""
        state = self._load_state()
        environments = []
        
        for name, info in state['environments'].items():
            env_dir = self._get_env_dir(name)
            environments.append({
                'name': name,
                'active': name == state['active'],
                'created': info.get('created', 'N/A'),
                'template': info.get('template', 'default'),
                'path': str(env_dir),
                'valid': env_dir.exists() and self._get_env_config(name).exists()
            })
        
        # 添加 default 环境
        if 'default' not in state['environments']:
            environments.insert(0, {
                'name': 'default',
                'active': state['active'] == 'default',
                'created': 'N/A',
                'template': 'default',
                'path': str(self.openclaw_dir),
                'valid': True
            })
        
        return environments
    
    def get_active(self) -> str:
        """获取当前活跃环境"""
        state = self._load_state()
        return state.get('active', 'default')
    
    def _generate_env_config(self, name: str, template: str) -> dict:
        """生成环境配置"""
        env_dir = self._get_env_dir(name)
        
        return {
            'version': '0.1.0',
            'name': name,
            'template': template,
            'created_at': datetime.now().isoformat(),
            'paths': {
                'workspace': str(env_dir / 'workspace'),
                'logs': str(env_dir / 'logs'),
                'sessions': str(env_dir / 'sessions'),
                'agents': str(env_dir / 'agents')
            },
            'process': {
                'auto_restart': True,
                'health_check_interval': 30,
                'max_restarts': 3
            },
            'monitor': {
                'cpu_threshold': 80,
                'memory_threshold': 90,
                'disk_threshold': 85,
                'check_interval': 60
            },
            'logs': {
                'level': 'INFO',
                'max_size_mb': 100,
                'retention_days': 30
            },
            'sessions': {
                'default': 'default'
            }
        }
    
    def _copy_agent_template(self, name: str):
        """复制 Agent 配置模板"""
        agent_dir = self._get_env_dir(name) / 'agents'
        
        # 默认 Agent 配置
        default_agents = {
            'shangshu': {
                'name': '尚书省',
                'role': 'coordinator',
                'enabled': True
            },
            'gongbu': {
                'name': '工部',
                'role': 'developer',
                'enabled': True
            },
            'libu': {
                'name': '吏部',
                'role': 'hr',
                'enabled': True
            }
        }
        
        config_file = agent_dir / 'agents.json'
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_agents, f, indent=2, ensure_ascii=False)


# ============== 环境检测模块 ==============

class EnvironmentChecker:
    """OpenClaw 环境检测器"""
    
    def __init__(self):
        self.openclaw_dir = Path.home() / '.openclaw'
        self.workspace_dir = Path.home() / '.openclaw' / 'workspace-bingbu'
        self.results = {}
    
    def check_python(self):
        """检查 Python 环境"""
        checks = []
        
        # Python 版本
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        checks.append({
            'name': 'Python 版本',
            'passed': sys.version_info.major >= 3 and sys.version_info.minor >= 8,
            'message': f'{version}',
            'detail': f'要求：Python 3.8+'
        })
        
        # psutil 依赖
        try:
            import psutil
            checks.append({
                'name': 'psutil 库',
                'passed': True,
                'message': f'已安装 (v{psutil.__version__})',
                'detail': '系统监控依赖'
            })
        except ImportError:
            checks.append({
                'name': 'psutil 库',
                'passed': False,
                'message': '未安装',
                'detail': '运行：pip3 install psutil'
            })
        
        return checks
    
    def check_openclaw(self):
        """检查 OpenClaw 环境"""
        checks = []
        
        # OpenClaw 目录
        checks.append({
            'name': 'OpenClaw 目录',
            'passed': self.openclaw_dir.exists(),
            'message': str(self.openclaw_dir),
            'detail': 'OpenClaw 主目录'
        })
        
        # 工作空间
        checks.append({
            'name': '工作空间',
            'passed': self.workspace_dir.exists(),
            'message': str(self.workspace_dir),
            'detail': '兵部工作空间'
        })
        
        # Gateway 状态
        gateway_check = self._check_gateway()
        checks.append(gateway_check)
        
        return checks
    
    def _check_gateway(self):
        """检查 Gateway 状态"""
        try:
            # 尝试检查 Gateway 进程
            import psutil
            gateway_running = False
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info['cmdline'] or [])
                    if 'openclaw' in cmdline.lower() and 'gateway' in cmdline.lower():
                        gateway_running = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if gateway_running:
                return {
                    'name': 'Gateway 服务',
                    'passed': True,
                    'message': '运行中',
                    'detail': 'Gateway 守护进程正常'
                }
            else:
                return {
                    'name': 'Gateway 服务',
                    'passed': False,
                    'message': '未运行',
                    'detail': '运行：openclaw gateway start'
                }
        except Exception as e:
            return {
                'name': 'Gateway 服务',
                'passed': False,
                'message': f'检测失败：{str(e)}',
                'detail': '无法检查 Gateway 状态'
            }
    
    def check_system(self):
        """检查系统环境"""
        checks = []
        
        # 操作系统
        system = platform.system()
        release = platform.release()
        checks.append({
            'name': '操作系统',
            'passed': True,
            'message': f'{system} {release}',
            'detail': platform.platform()
        })
        
        # 架构
        arch = platform.machine()
        checks.append({
            'name': '系统架构',
            'passed': True,
            'message': arch,
            'detail': 'CPU 架构'
        })
        
        # 内存
        try:
            import psutil
            mem = psutil.virtual_memory()
            mem_gb = mem.total / (1024 ** 3)
            checks.append({
                'name': '系统内存',
                'passed': mem_gb >= 2,
                'message': f'{mem_gb:.2f} GB',
                'detail': f'可用：{mem.available / (1024 ** 3):.2f} GB'
            })
        except Exception as e:
            checks.append({
                'name': '系统内存',
                'passed': False,
                'message': f'检测失败：{str(e)}',
                'detail': ''
            })
        
        # 磁盘空间
        try:
            import psutil
            disk = psutil.disk_usage('/')
            free_gb = disk.free / (1024 ** 3)
            checks.append({
                'name': '磁盘空间',
                'passed': free_gb >= 5,
                'message': f'可用 {free_gb:.2f} GB',
                'detail': f'总计：{disk.total / (1024 ** 3):.2f} GB, 使用：{disk.percent}%'
            })
        except Exception as e:
            checks.append({
                'name': '磁盘空间',
                'passed': False,
                'message': f'检测失败：{str(e)}',
                'detail': ''
            })
        
        return checks
    
    def check_all(self):
        """执行全部检查"""
        self.results = {
            'Python 环境': self.check_python(),
            'OpenClaw 环境': self.check_openclaw(),
            '系统环境': self.check_system()
        }
        return self.results
    
    def generate_config(self):
        """生成配置文件"""
        config = {
            'version': '0.1.0',
            'created_at': datetime.now().isoformat(),
            'openclaw_dir': str(self.openclaw_dir),
            'workspace_dir': str(self.workspace_dir),
            'process': {
                'auto_restart': True,
                'health_check_interval': 30,
                'max_restarts': 3
            },
            'monitor': {
                'cpu_threshold': 80,
                'memory_threshold': 90,
                'disk_threshold': 85,
                'check_interval': 60
            },
            'logs': {
                'level': 'INFO',
                'max_size_mb': 100,
                'retention_days': 30,
                'path': str(self.workspace_dir / 'logs')
            },
            'sessions': {
                'default': 'default',
                'path': str(self.workspace_dir / 'sessions')
            }
        }
        
        # 执行环境检查并保存结果
        config['env_check'] = self.check_all()
        config['last_check'] = datetime.now().isoformat()
        
        return config
    
    def get_summary(self):
        """获取检查摘要"""
        if not self.results:
            self.check_all()
        
        total = 0
        passed = 0
        for category, checks in self.results.items():
            for check in checks:
                total += 1
                if check['passed']:
                    passed += 1
        
        return {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'health_rate': f'{(passed / total * 100):.1f}%' if total > 0 else 'N/A'
        }
