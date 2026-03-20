# -*- coding: utf-8 -*-
"""
日志管理模块
负责日志收集、查看、搜索和归档
"""

import os
import json
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import deque


class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = None):
        if log_dir:
            self.log_dir = Path(log_dir)
        else:
            self.log_dir = Path.home() / '.openclaw' / 'claw-ex' / 'logs'
        
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / 'claw-ex.log'
        self.index_file = self.log_dir / 'index.json'
        self.max_size = 100 * 1024 * 1024  # 100 MB
        self.max_lines = 10000  # 内存中保留的最大行数
        
        # 内存中的日志缓存
        self._cache: deque = deque(maxlen=self.max_lines)
        self._load_index()
    
    def _load_index(self):
        """加载日志索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
            except Exception:
                self._index = {'entries': [], 'total_lines': 0}
        else:
            self._index = {'entries': [], 'total_lines': 0}
    
    def _save_index(self):
        """保存日志索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self._index, f, indent=2, ensure_ascii=False)
    
    def log(self, message: str, level: str = 'INFO', source: str = 'claw-ex', 
            metadata: Dict[str, Any] = None):
        """
        记录日志
        
        Args:
            message: 日志消息
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
            source: 日志来源
            metadata: 额外元数据
        """
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'source': source,
            'message': message,
            'metadata': metadata or {}
        }
        
        # 添加到缓存
        self._cache.append(entry)
        
        # 写入文件
        self._write_to_file(entry)
        
        # 更新索引
        self._index['entries'].append({
            'timestamp': entry['timestamp'],
            'level': level,
            'source': source,
            'offset': self._index.get('total_lines', 0)
        })
        self._index['total_lines'] = self._index.get('total_lines', 0) + 1
        
        # 检查是否需要轮转
        self._check_rotation()
    
    def _write_to_file(self, entry: Dict):
        """写入日志到文件"""
        line = json.dumps(entry, ensure_ascii=False) + '\n'
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(line)
    
    def _check_rotation(self):
        """检查是否需要日志轮转"""
        if self.log_file.exists():
            size = self.log_file.stat().st_size
            if size > self.max_size:
                self._rotate()
    
    def _rotate(self):
        """日志轮转"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rotated_file = self.log_dir / f'claw-ex.{timestamp}.log.gz'
        
        # 压缩旧日志
        with open(self.log_file, 'rb') as f_in:
            with gzip.open(rotated_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 清空当前日志文件
        with open(self.log_file, 'w', encoding='utf-8') as f:
            pass
        
        # 更新索引
        self._index['rotated_files'] = self._index.get('rotated_files', [])
        self._index['rotated_files'].append({
            'file': str(rotated_file),
            'timestamp': timestamp,
            'size': rotated_file.stat().st_size
        })
        
        self._save_index()
    
    def tail(self, lines: int = 20, level: str = None) -> List[Dict]:
        """
        获取日志末尾
        
        Args:
            lines: 行数
            level: 日志级别过滤
        
        Returns:
            日志条目列表
        """
        result = []
        
        # 优先从缓存读取
        if self._cache:
            for entry in reversed(self._cache):
                if level and entry['level'] != level:
                    continue
                result.append(entry)
                if len(result) >= lines:
                    break
            result.reverse()
            return result
        
        # 从文件读取
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
            
            for line in reversed(all_lines[-lines:]):
                try:
                    entry = json.loads(line.strip())
                    if level and entry['level'] != level:
                        continue
                    result.append(entry)
                except json.JSONDecodeError:
                    continue
            
            result.reverse()
        except Exception:
            pass
        
        return result
    
    def search(self, keyword: str, level: str = None, 
               source: str = None, start_time: str = None,
               end_time: str = None) -> List[Dict]:
        """
        搜索日志
        
        Args:
            keyword: 搜索关键词
            level: 日志级别过滤
            source: 来源过滤
            start_time: 开始时间 (ISO 格式)
            end_time: 结束时间 (ISO 格式)
        
        Returns:
            匹配的日志条目列表
        """
        result = []
        
        # 搜索缓存
        for entry in self._cache:
            if self._matches(entry, keyword, level, source, start_time, end_time):
                result.append(entry)
        
        # 搜索文件
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            if self._matches(entry, keyword, level, source, start_time, end_time):
                                result.append(entry)
                        except json.JSONDecodeError:
                            continue
            except Exception:
                pass
        
        # 按时间排序
        result.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return result
    
    def _matches(self, entry: Dict, keyword: str, level: str, 
                 source: str, start_time: str, end_time: str) -> bool:
        """检查日志条目是否匹配搜索条件"""
        # 关键词匹配
        if keyword and keyword.lower() not in entry.get('message', '').lower():
            return False
        
        # 级别匹配
        if level and entry.get('level') != level:
            return False
        
        # 来源匹配
        if source and entry.get('source') != source:
            return False
        
        # 时间范围匹配
        timestamp = entry.get('timestamp', '')
        if start_time and timestamp < start_time:
            return False
        if end_time and timestamp > end_time:
            return False
        
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """获取日志统计信息"""
        stats = {
            'total_lines': self._index.get('total_lines', 0),
            'by_level': {},
            'by_source': {},
            'file_size': 0,
            'rotated_files': len(self._index.get('rotated_files', []))
        }
        
        if self.log_file.exists():
            stats['file_size'] = self.log_file.stat().st_size
        
        # 统计各级别数量
        for entry in self._cache:
            level = entry.get('level', 'INFO')
            source = entry.get('source', 'unknown')
            
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
            stats['by_source'][source] = stats['by_source'].get(source, 0) + 1
        
        return stats
    
    def clear(self) -> Dict[str, Any]:
        """清空日志"""
        count = 0
        
        # 计算要删除的行数
        if self.log_file.exists():
            with open(self.log_file, 'r', encoding='utf-8') as f:
                count = sum(1 for _ in f)
            
            # 清空文件
            with open(self.log_file, 'w', encoding='utf-8') as f:
                pass
        
        # 清空缓存
        self._cache.clear()
        
        # 重置索引
        self._index = {'entries': [], 'total_lines': 0}
        self._save_index()
        
        return {
            'success': True,
            'count': count,
            'message': f'已清空 {count} 条日志'
        }
    
    def export(self, output_path: str, level: str = None, 
               start_time: str = None, end_time: str = None) -> Dict[str, Any]:
        """
        导出日志
        
        Args:
            output_path: 输出文件路径
            level: 日志级别过滤
            start_time: 开始时间
            end_time: 结束时间
        
        Returns:
            导出结果
        """
        logs = self.search('', level, start_time=start_time, end_time=end_time)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for entry in logs:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        return {
            'success': True,
            'count': len(logs),
            'path': str(output_file)
        }
    
    def cleanup(self, retention_days: int = 30) -> Dict[str, Any]:
        """
        清理旧日志
        
        Args:
            retention_days: 保留天数
        
        Returns:
            清理结果
        """
        cutoff = datetime.now() - timedelta(days=retention_days)
        deleted = 0
        
        rotated_files = self._index.get('rotated_files', [])
        remaining = []
        
        for file_info in rotated_files:
            try:
                file_path = Path(file_info['file'])
                if not file_path.exists():
                    continue
                
                # 检查文件时间
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time < cutoff:
                    file_path.unlink()
                    deleted += 1
                else:
                    remaining.append(file_info)
            except Exception:
                remaining.append(file_info)
        
        self._index['rotated_files'] = remaining
        self._save_index()
        
        return {
            'success': True,
            'deleted': deleted,
            'remaining': len(remaining)
        }
    
    def get_recent_errors(self, hours: int = 24) -> List[Dict]:
        """获取最近的错误日志"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        return self.search('', level='ERROR', start_time=start_time)
    
    def get_recent_warnings(self, hours: int = 24) -> List[Dict]:
        """获取最近的警告日志"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        return self.search('', level='WARNING', start_time=start_time)
