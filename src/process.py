# -*- coding: utf-8 -*-
"""
进程管理模块
负责 Agent 进程的启动、停止、监控和管理
"""

import os
import json
import signal
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import psutil
except ImportError:
    psutil = None


class ProcessManager:
    """进程管理器"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.openclaw' / 'claw-ex' / 'processes'
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.processes: Dict[str, Dict] = {}
        self._load_state()
    
    def _load_state(self):
        """加载进程状态"""
        state_file = self.config_dir / 'state.json'
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    self.processes = json.load(f)
            except Exception:
                self.processes = {}
    
    def _save_state(self):
        """保存进程状态"""
        state_file = self.config_dir / 'state.json'
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(self.processes, f, indent=2, ensure_ascii=False)
    
    def start(self, name: str, command: str, args: List[str] = None, 
              workdir: str = None, env: Dict[str, str] = None) -> Dict[str, Any]:
        """
        启动进程
        
        Args:
            name: 进程名称
            command: 启动命令
            args: 命令参数列表
            workdir: 工作目录
            env: 环境变量
        
        Returns:
            包含 success, pid, error 的字典
        """
        # 检查是否已存在
        if name in self.processes and self._is_running(name):
            return {
                'success': False,
                'error': f'进程 {name} 已在运行 (PID: {self.processes[name]["pid"]})'
            }
        
        try:
            # 构建命令
            cmd = [command] + (args or [])
            
            # 设置工作环境
            cwd = workdir or os.getcwd()
            environment = os.environ.copy()
            if env:
                environment.update(env)
            
            # 启动进程 (后台运行)
            process = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True  # 创建新会话，避免被终端信号影响
            )
            
            # 记录进程信息
            self.processes[name] = {
                'name': name,
                'pid': process.pid,
                'command': command,
                'args': args or [],
                'workdir': cwd,
                'started': datetime.now().isoformat(),
                'status': 'running',
                'restarts': 0
            }
            
            self._save_state()
            
            return {
                'success': True,
                'pid': process.pid,
                'message': f'进程 {name} 已启动'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop(self, name: str, timeout: int = 10) -> Dict[str, Any]:
        """
        停止进程
        
        Args:
            name: 进程名称
            timeout: 等待终止的超时时间 (秒)
        
        Returns:
            包含 success, error 的字典
        """
        if name not in self.processes:
            return {
                'success': False,
                'error': f'进程 {name} 不存在'
            }
        
        proc_info = self.processes[name]
        pid = proc_info['pid']
        
        try:
            if psutil:
                # 使用 psutil 优雅终止
                try:
                    p = psutil.Process(pid)
                    # 先发送 SIGTERM
                    p.terminate()
                    # 等待进程结束
                    gone, alive = psutil.wait_procs([p], timeout=timeout)
                    
                    if alive:
                        # 如果还没结束，强制杀死
                        for p in alive:
                            p.kill()
                except psutil.NoSuchProcess:
                    pass
            else:
                # 降级处理：直接发送信号
                os.kill(pid, signal.SIGTERM)
            
            # 更新状态
            proc_info['status'] = 'stopped'
            proc_info['stopped'] = datetime.now().isoformat()
            self._save_state()
            
            return {
                'success': True,
                'message': f'进程 {name} 已停止'
            }
            
        except ProcessLookupError:
            # 进程已不存在
            proc_info['status'] = 'stopped'
            self._save_state()
            return {
                'success': True,
                'message': f'进程 {name} 已停止 (进程已不存在)'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'停止失败：{str(e)}'
            }
    
    def restart(self, name: str) -> Dict[str, Any]:
        """重启进程"""
        if name not in self.processes:
            return {
                'success': False,
                'error': f'进程 {name} 不存在'
            }
        
        proc_info = self.processes[name]
        
        # 停止
        stop_result = self.stop(name)
        if not stop_result['success']:
            return stop_result
        
        # 等待一小段时间
        import time
        time.sleep(1)
        
        # 重新启动
        return self.start(
            name=name,
            command=proc_info['command'],
            args=proc_info.get('args', []),
            workdir=proc_info.get('workdir')
        )
    
    def status(self, name: str) -> Dict[str, Any]:
        """获取进程状态"""
        if name not in self.processes:
            return {'exists': False}
        
        proc_info = self.processes[name].copy()
        proc_info['exists'] = True
        
        # 获取实时状态
        if psutil:
            try:
                p = psutil.Process(proc_info['pid'])
                proc_info['status'] = 'running' if p.is_running() else 'stopped'
                proc_info['cpu'] = p.cpu_percent(interval=0.1)
                mem_info = p.memory_info()
                proc_info['memory'] = f'{mem_info.rss / 1024 / 1024:.1f} MB'
                proc_info['threads'] = p.num_threads()
            except psutil.NoSuchProcess:
                proc_info['status'] = 'stopped'
                proc_info['cpu'] = 0
                proc_info['memory'] = '0 MB'
        else:
            # 检查进程是否存在
            try:
                os.kill(proc_info['pid'], 0)
                proc_info['status'] = 'running'
            except ProcessLookupError:
                proc_info['status'] = 'stopped'
        
        return proc_info
    
    def list_all(self) -> List[Dict[str, Any]]:
        """列出所有进程"""
        result = []
        
        for name in list(self.processes.keys()):
            status = self.status(name)
            if status.get('exists'):
                result.append(status)
            else:
                # 清理不存在的进程记录
                del self.processes[name]
        
        self._save_state()
        return result
    
    def _is_running(self, name: str) -> bool:
        """检查进程是否运行中"""
        if name not in self.processes:
            return False
        
        pid = self.processes[name]['pid']
        
        if psutil:
            try:
                p = psutil.Process(pid)
                return p.is_running()
            except psutil.NoSuchProcess:
                return False
        else:
            try:
                os.kill(pid, 0)
                return True
            except ProcessLookupError:
                return False
    
    def get_logs(self, name: str, lines: int = 50) -> List[str]:
        """获取进程日志 (如果有的话)"""
        if name not in self.processes:
            return []
        
        # 这里可以扩展为读取实际的标准输出/错误日志
        # 目前返回空列表，实际使用时需要重定向 stdout/stderr 到文件
        return []
    
    def cleanup(self) -> Dict[str, Any]:
        """清理僵尸进程记录"""
        cleaned = 0
        for name in list(self.processes.keys()):
            if not self._is_running(name):
                del self.processes[name]
                cleaned += 1
        
        self._save_state()
        return {
            'success': True,
            'cleaned': cleaned
        }
