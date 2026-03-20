# -*- coding: utf-8 -*-
"""
系统监控模块
负责 CPU、内存、网络、磁盘等系统资源的监控
"""

import time
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    import psutil
except ImportError:
    psutil = None


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        if not psutil:
            raise ImportError("psutil 库未安装，请运行：pip3 install psutil")
    
    def get_cpu_usage(self, interval: float = 1.0) -> Dict[str, Any]:
        """
        获取 CPU 使用率
        
        Args:
            interval: 采样间隔 (秒)
        
        Returns:
            包含 current, per_core, cores 的字典
        """
        # 总体使用率
        current = psutil.cpu_percent(interval=interval)
        
        # 每核心使用率
        per_core = psutil.cpu_percent(interval=0, percpu=True)
        
        # 核心数
        cores = psutil.cpu_count()
        logical_cores = psutil.cpu_count(logical=True)
        
        # 频率
        freq = psutil.cpu_freq()
        
        return {
            'current': current,
            'per_core': per_core,
            'cores': cores,
            'logical_cores': logical_cores,
            'frequency': {
                'current': freq.current if freq else 0,
                'min': freq.min if freq else 0,
                'max': freq.max if freq else 0
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """
        获取内存使用情况
        
        Returns:
            包含 total, used, available, percent 的字典
        """
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'total': mem.total / (1024 ** 3),  # GB
            'used': mem.used / (1024 ** 3),
            'available': mem.available / (1024 ** 3),
            'percent': mem.percent,
            'swap': {
                'total': swap.total / (1024 ** 3),
                'used': swap.used / (1024 ** 3),
                'percent': swap.percent
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_disk_usage(self, path: str = '/') -> Dict[str, Any]:
        """
        获取磁盘使用情况
        
        Args:
            path: 要检查的路径
        
        Returns:
            包含 total, used, free, percent 的字典
        """
        disk = psutil.disk_usage(path)
        
        # 所有分区
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total / (1024 ** 3),
                    'used': usage.used / (1024 ** 3),
                    'free': usage.free / (1024 ** 3),
                    'percent': usage.percent
                })
            except (PermissionError, OSError):
                continue
        
        return {
            'total': disk.total / (1024 ** 3),
            'used': disk.used / (1024 ** 3),
            'free': disk.free / (1024 ** 3),
            'percent': disk.percent,
            'partitions': partitions,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_network_stats(self) -> Dict[str, Any]:
        """
        获取网络统计信息
        
        Returns:
            包含发送/接收字节数、包数的字典
        """
        net = psutil.net_io_counters()
        
        # 每个网络接口的统计
        interfaces = {}
        for iface, stats in psutil.net_io_counters(pernic=True).items():
            interfaces[iface] = {
                'bytes_sent': stats.bytes_sent,
                'bytes_recv': stats.bytes_recv,
                'packets_sent': stats.packets_sent,
                'packets_recv': stats.packets_recv,
                'errin': stats.errin,
                'errout': stats.errout,
                'dropin': stats.dropin,
                'dropout': stats.dropout
            }
        
        return {
            'bytes_sent': net.bytes_sent,
            'bytes_recv': net.bytes_recv,
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv,
            'interfaces': interfaces,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_network_connections(self) -> List[Dict[str, Any]]:
        """获取网络连接信息"""
        connections = []
        for conn in psutil.net_connections(kind='inet'):
            connections.append({
                'fd': conn.fd,
                'family': str(conn.family),
                'type': str(conn.type),
                'local_addr': f'{conn.laddr.ip}:{conn.laddr.port}' if conn.laddr else None,
                'remote_addr': f'{conn.raddr.ip}:{conn.raddr.port}' if conn.raddr else None,
                'status': conn.status,
                'pid': conn.pid
            })
        return connections
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """获取进程列表"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'] or 0,
                    'memory': proc.info['memory_percent'] or 0
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 按 CPU 使用率排序
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:50]  # 返回前 50 个
    
    def get_top_processes(self, n: int = 10, by: str = 'cpu') -> List[Dict[str, Any]]:
        """
        获取资源占用最高的进程
        
        Args:
            n: 返回数量
            by: 排序依据 ('cpu' 或 'memory')
        
        Returns:
            进程列表
        """
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'cpu': pinfo['cpu_percent'] or 0,
                    'memory': pinfo['memory_percent'] or 0,
                    'status': pinfo['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # 排序
        if by == 'memory':
            processes.sort(key=lambda x: x['memory'], reverse=True)
        else:
            processes.sort(key=lambda x: x['cpu'], reverse=True)
        
        return processes[:n]
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform
        boot_time = psutil.boot_time()
        
        return {
            'platform': {
                'system': platform.system(),
                'node': platform.node(),
                'release': platform.release(),
                'version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor()
            },
            'boot_time': datetime.fromtimestamp(boot_time).isoformat(),
            'uptime': time.time() - boot_time,
            'users': [u.name for u in psutil.users()],
            'timestamp': datetime.now().isoformat()
        }
    
    def get_sensors(self) -> Dict[str, Any]:
        """获取传感器信息 (温度、风扇等)"""
        sensors = {}
        
        # 温度
        temps = psutil.sensors_temperatures()
        if temps:
            sensors['temperatures'] = {}
            for name, entries in temps.items():
                sensors['temperatures'][name] = [
                    {
                        'label': entry.label or 'N/A',
                        'current': entry.current,
                        'high': entry.high,
                        'critical': entry.critical
                    }
                    for entry in entries
                ]
        
        # 风扇
        fans = psutil.sensors_fans()
        if fans:
            sensors['fans'] = {}
            for name, entries in fans.items():
                sensors['fans'][name] = [
                    {
                        'label': entry.label or 'N/A',
                        'current': entry.current
                    }
                    for entry in entries
                ]
        
        # 电池
        battery = psutil.sensors_battery()
        if battery:
            sensors['battery'] = {
                'percent': battery.percent,
                'secsleft': battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else 'unlimited',
                'power_plugged': battery.power_plugged
            }
        
        return sensors
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有监控数据"""
        return {
            'cpu': self.get_cpu_usage(interval=0),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_stats(),
            'system': self.get_system_info(),
            'timestamp': datetime.now().isoformat()
        }
    
    def check_alerts(self, thresholds: Dict[str, float] = None) -> List[Dict[str, Any]]:
        """
        检查告警
        
        Args:
            thresholds: 告警阈值配置
        
        Returns:
            告警列表
        """
        if thresholds is None:
            thresholds = {
                'cpu': 80,
                'memory': 90,
                'disk': 85
            }
        
        alerts = []
        
        # CPU 检查
        cpu = self.get_cpu_usage(interval=0)
        if cpu['current'] > thresholds.get('cpu', 80):
            alerts.append({
                'level': 'WARNING',
                'type': 'cpu',
                'message': f'CPU 使用率过高：{cpu["current"]:.1f}%',
                'value': cpu['current'],
                'threshold': thresholds.get('cpu', 80)
            })
        
        # 内存检查
        mem = self.get_memory_usage()
        if mem['percent'] > thresholds.get('memory', 90):
            alerts.append({
                'level': 'WARNING',
                'type': 'memory',
                'message': f'内存使用率过高：{mem["percent"]:.1f}%',
                'value': mem['percent'],
                'threshold': thresholds.get('memory', 90)
            })
        
        # 磁盘检查
        disk = self.get_disk_usage()
        if disk['percent'] > thresholds.get('disk', 85):
            alerts.append({
                'level': 'WARNING',
                'type': 'disk',
                'message': f'磁盘使用率过高：{disk["percent"]:.1f}%',
                'value': disk['percent'],
                'threshold': thresholds.get('disk', 85)
            })
        
        return alerts
