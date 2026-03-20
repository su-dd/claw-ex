# -*- coding: utf-8 -*-
"""
会话管理模块
负责创建、列出、切换和删除会话
"""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any


class SessionManager:
    """会话管理器"""
    
    def __init__(self):
        self.sessions_dir = Path.home() / '.openclaw' / 'claw-ex' / 'sessions'
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.sessions_dir / 'state.json'
        self.sessions: Dict[str, Dict] = {}
        self.current_session: Optional[str] = None
        self._load_state()
    
    def _load_state(self):
        """加载会话状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self.sessions = state.get('sessions', {})
                    self.current_session = state.get('current_session')
            except Exception:
                self.sessions = {}
                self.current_session = None
    
    def _save_state(self):
        """保存会话状态"""
        state = {
            'sessions': self.sessions,
            'current_session': self.current_session,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def create(self, name: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        创建新会话
        
        Args:
            name: 会话名称
            metadata: 额外元数据
        
        Returns:
            包含 success, session_id, error 的字典
        """
        # 检查名称是否已存在
        if name in self.sessions:
            return {
                'success': False,
                'error': f'会话 {name} 已存在'
            }
        
        session_id = str(uuid.uuid4())[:8]
        session_dir = self.sessions_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        session_data = {
            'id': session_id,
            'name': name,
            'created': datetime.now().isoformat(),
            'active': True,
            'metadata': metadata or {},
            'context': {},
            'variables': {}
        }
        
        self.sessions[name] = session_data
        self._save_state()
        
        # 保存会话详情
        self._save_session(session_id, session_data)
        
        return {
            'success': True,
            'session_id': session_id,
            'message': f'会话 {name} 已创建'
        }
    
    def delete(self, name: str) -> Dict[str, Any]:
        """
        删除会话
        
        Args:
            name: 会话名称
        
        Returns:
            包含 success, error 的字典
        """
        if name not in self.sessions:
            return {
                'success': False,
                'error': f'会话 {name} 不存在'
            }
        
        session_data = self.sessions[name]
        session_id = session_data['id']
        
        # 删除会话目录
        session_dir = self.sessions_dir / session_id
        if session_dir.exists():
            import shutil
            shutil.rmtree(session_dir)
        
        # 从状态中移除
        del self.sessions[name]
        
        # 如果删除的是当前会话，重置当前会话
        if self.current_session == name:
            self.current_session = None
        
        self._save_state()
        
        return {
            'success': True,
            'message': f'会话 {name} 已删除'
        }
    
    def switch(self, name: str) -> Dict[str, Any]:
        """
        切换会话
        
        Args:
            name: 会话名称
        
        Returns:
            包含 success, error 的字典
        """
        if name not in self.sessions:
            return {
                'success': False,
                'error': f'会话 {name} 不存在'
            }
        
        # 将之前的当前会话设为非活跃
        if self.current_session and self.current_session in self.sessions:
            self.sessions[self.current_session]['active'] = False
        
        # 设置新会话为当前和活跃
        self.current_session = name
        self.sessions[name]['active'] = True
        self.sessions[name]['last_accessed'] = datetime.now().isoformat()
        
        self._save_state()
        self._save_session(self.sessions[name]['id'], self.sessions[name])
        
        return {
            'success': True,
            'message': f'已切换到会话 {name}'
        }
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        result = []
        for name, session in self.sessions.items():
            result.append({
                'name': name,
                'id': session['id'],
                'created': session['created'],
                'active': session.get('active', False),
                'last_accessed': session.get('last_accessed')
            })
        
        # 按创建时间排序
        result.sort(key=lambda x: x['created'], reverse=True)
        return result
    
    def get_current(self) -> Optional[Dict[str, Any]]:
        """获取当前会话"""
        if self.current_session and self.current_session in self.sessions:
            return self.sessions[self.current_session]
        return None
    
    def set_context(self, name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """设置会话上下文"""
        if name not in self.sessions:
            return {
                'success': False,
                'error': f'会话 {name} 不存在'
            }
        
        self.sessions[name]['context'] = context
        self._save_session(self.sessions[name]['id'], self.sessions[name])
        self._save_state()
        
        return {
            'success': True,
            'message': '上下文已更新'
        }
    
    def get_context(self, name: str) -> Dict[str, Any]:
        """获取会话上下文"""
        if name not in self.sessions:
            return {}
        return self.sessions[name].get('context', {})
    
    def set_variable(self, name: str, key: str, value: Any) -> Dict[str, Any]:
        """设置会话变量"""
        if name not in self.sessions:
            return {
                'success': False,
                'error': f'会话 {name} 不存在'
            }
        
        if 'variables' not in self.sessions[name]:
            self.sessions[name]['variables'] = {}
        
        self.sessions[name]['variables'][key] = value
        self._save_session(self.sessions[name]['id'], self.sessions[name])
        self._save_state()
        
        return {
            'success': True,
            'message': f'变量 {key} 已设置'
        }
    
    def get_variable(self, name: str, key: str, default: Any = None) -> Any:
        """获取会话变量"""
        if name not in self.sessions:
            return default
        
        return self.sessions[name].get('variables', {}).get(key, default)
    
    def _save_session(self, session_id: str, data: Dict):
        """保存会话详情到文件"""
        session_file = self.sessions_dir / session_id / 'session.json'
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def export(self, name: str, output_path: str) -> Dict[str, Any]:
        """导出会话到文件"""
        if name not in self.sessions:
            return {
                'success': False,
                'error': f'会话 {name} 不存在'
            }
        
        session_data = self.sessions[name]
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        return {
            'success': True,
            'message': f'会话已导出到 {output_path}'
        }
    
    def import_session(self, name: str, input_path: str) -> Dict[str, Any]:
        """从文件导入会话"""
        if name in self.sessions:
            return {
                'success': False,
                'error': f'会话 {name} 已存在'
            }
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # 验证必要字段
            if 'id' not in session_data or 'name' not in session_data:
                return {
                    'success': False,
                    'error': '无效的会话文件格式'
                }
            
            session_data['name'] = name  # 使用新名称
            self.sessions[name] = session_data
            self._save_state()
            
            return {
                'success': True,
                'message': f'会话已从 {input_path} 导入'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'导入失败：{str(e)}'
            }
