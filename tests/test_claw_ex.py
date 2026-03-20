#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
claw-ex 单元测试
"""

import sys
import os
import unittest
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))


class TestEnvironmentChecker(unittest.TestCase):
    """环境检测测试"""
    
    def setUp(self):
        from env import EnvironmentChecker
        self.checker = EnvironmentChecker()
    
    def test_check_python(self):
        """测试 Python 环境检查"""
        checks = self.checker.check_python()
        self.assertIsInstance(checks, list)
        self.assertTrue(len(checks) > 0)
    
    def test_check_system(self):
        """测试系统环境检查"""
        checks = self.checker.check_system()
        self.assertIsInstance(checks, list)
        # 至少应该有操作系统检查
        self.assertTrue(any(c['name'] == '操作系统' for c in checks))
    
    def test_check_all(self):
        """测试全部检查"""
        results = self.checker.check_all()
        self.assertIsInstance(results, dict)
        self.assertIn('Python 环境', results)
        self.assertIn('系统环境', results)
    
    def test_get_summary(self):
        """测试获取摘要"""
        self.checker.check_all()
        summary = self.checker.get_summary()
        self.assertIn('total', summary)
        self.assertIn('passed', summary)
        self.assertIn('health_rate', summary)


class TestProcessManager(unittest.TestCase):
    """进程管理测试"""
    
    def setUp(self):
        from process import ProcessManager
        self.pm = ProcessManager()
    
    def test_list_all_empty(self):
        """测试列出空进程列表"""
        processes = self.pm.list_all()
        self.assertIsInstance(processes, list)
    
    def test_status_nonexistent(self):
        """测试获取不存在进程的状态"""
        status = self.pm.status('nonexistent-process')
        self.assertFalse(status['exists'])
    
    def test_stop_nonexistent(self):
        """测试停止不存在的进程"""
        result = self.pm.stop('nonexistent-process')
        self.assertFalse(result['success'])
        self.assertIn('error', result)


class TestSessionManager(unittest.TestCase):
    """会话管理测试"""
    
    def setUp(self):
        from session import SessionManager
        self.sm = SessionManager()
        self.test_session = 'test-session-' + str(os.getpid())
    
    def tearDown(self):
        # 清理测试会话
        if self.test_session in self.sm.sessions:
            self.sm.delete(self.test_session)
    
    def test_create_session(self):
        """测试创建会话"""
        result = self.sm.create(self.test_session)
        self.assertTrue(result['success'])
        self.assertIn('session_id', result)
    
    def test_create_duplicate(self):
        """测试创建重复会话"""
        self.sm.create(self.test_session)
        result = self.sm.create(self.test_session)
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_list_sessions(self):
        """测试列出会话"""
        self.sm.create(self.test_session)
        sessions = self.sm.list_sessions()
        self.assertIsInstance(sessions, list)
        self.assertTrue(len(sessions) > 0)
    
    def test_switch_session(self):
        """测试切换会话"""
        self.sm.create(self.test_session)
        result = self.sm.switch(self.test_session)
        self.assertTrue(result['success'])
        current = self.sm.get_current()
        self.assertEqual(current['name'], self.test_session)
    
    def test_delete_session(self):
        """测试删除会话"""
        self.sm.create(self.test_session)
        result = self.sm.delete(self.test_session)
        self.assertTrue(result['success'])
        sessions = self.sm.list_sessions()
        self.assertNotIn(self.test_session, [s['name'] for s in sessions])


class TestSystemMonitor(unittest.TestCase):
    """系统监控测试"""
    
    def setUp(self):
        from monitor import SystemMonitor
        self.mon = SystemMonitor()
    
    def test_get_cpu_usage(self):
        """测试获取 CPU 使用率"""
        cpu = self.mon.get_cpu_usage(interval=0.1)
        self.assertIn('current', cpu)
        self.assertIn('cores', cpu)
        self.assertIsInstance(cpu['current'], (int, float))
    
    def test_get_memory_usage(self):
        """测试获取内存使用情况"""
        mem = self.mon.get_memory_usage()
        self.assertIn('total', mem)
        self.assertIn('used', mem)
        self.assertIn('percent', mem)
    
    def test_get_disk_usage(self):
        """测试获取磁盘使用情况"""
        disk = self.mon.get_disk_usage()
        self.assertIn('total', disk)
        self.assertIn('used', disk)
        self.assertIn('percent', disk)
    
    def test_get_network_stats(self):
        """测试获取网络统计"""
        net = self.mon.get_network_stats()
        self.assertIn('bytes_sent', net)
        self.assertIn('bytes_recv', net)
    
    def test_get_system_info(self):
        """测试获取系统信息"""
        info = self.mon.get_system_info()
        self.assertIn('platform', info)
        self.assertIn('uptime', info)
    
    def test_get_all(self):
        """测试获取全部监控数据"""
        all_data = self.mon.get_all()
        self.assertIn('cpu', all_data)
        self.assertIn('memory', all_data)
        self.assertIn('disk', all_data)
        self.assertIn('network', all_data)
    
    def test_check_alerts(self):
        """测试告警检查"""
        alerts = self.mon.check_alerts()
        self.assertIsInstance(alerts, list)


class TestLogManager(unittest.TestCase):
    """日志管理测试"""
    
    def setUp(self):
        from logs import LogManager
        import tempfile
        self.temp_dir = tempfile.mkdtemp()
        self.lm = LogManager(self.temp_dir)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log(self):
        """测试记录日志"""
        self.lm.log('Test message', level='INFO')
        logs = self.lm.tail(lines=1)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['message'], 'Test message')
    
    def test_tail(self):
        """测试获取日志末尾"""
        for i in range(5):
            self.lm.log(f'Message {i}', level='INFO')
        logs = self.lm.tail(lines=3)
        self.assertEqual(len(logs), 3)
    
    def test_search(self):
        """测试搜索日志"""
        # 清空之前的日志
        self.lm.clear()
        
        self.lm.log('Error occurred', level='ERROR')
        self.lm.log('Info message', level='INFO')
        
        errors = self.lm.search('', level='ERROR')
        self.assertTrue(len(errors) >= 1)
        self.assertEqual(errors[0]['level'], 'ERROR')
    
    def test_get_stats(self):
        """测试获取统计信息"""
        self.lm.log('Test', level='INFO')
        self.lm.log('Error', level='ERROR')
        
        stats = self.lm.get_stats()
        self.assertIn('total_lines', stats)
        self.assertIn('by_level', stats)
    
    def test_clear(self):
        """测试清空日志"""
        self.lm.log('Test', level='INFO')
        result = self.lm.clear()
        self.assertTrue(result['success'])
        logs = self.lm.tail()
        self.assertEqual(len(logs), 0)


class TestCLI(unittest.TestCase):
    """CLI 测试"""
    
    def test_help(self):
        """测试帮助信息"""
        import subprocess
        result = subprocess.run(
            ['python3', str(Path(__file__).parent.parent / 'bin' / 'claw-ex.py'), '--help'],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn('claw-ex', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
