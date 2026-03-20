# claw-ex API 文档

## 概述

claw-ex 提供 Python API 和 CLI 两种使用方式，支持 OpenClaw 系统的进程管理、会话管理、系统监控和日志管理。

## 快速开始

```python
from claw_ex import (
    EnvironmentChecker,
    ProcessManager,
    SessionManager,
    SystemMonitor,
    LogManager
)
```

---

## 1. 环境检测 (EnvironmentChecker)

### 初始化

```python
from claw_ex import EnvironmentChecker

checker = EnvironmentChecker()
```

### 方法

#### `check_all() -> Dict`
执行全部环境检查

```python
results = checker.check_all()
# 返回：
# {
#     'Python 环境': [...],
#     'OpenClaw 环境': [...],
#     '系统环境': [...]
# }
```

#### `generate_config() -> Dict`
生成配置文件

```python
config = checker.generate_config()
```

#### `get_summary() -> Dict`
获取检查摘要

```python
summary = checker.get_summary()
# 返回：{'total': 10, 'passed': 8, 'failed': 2, 'health_rate': '80.0%'}
```

---

## 2. 进程管理 (ProcessManager)

### 初始化

```python
from claw_ex import ProcessManager

pm = ProcessManager()
```

### 方法

#### `start(name, command, args=None, workdir=None, env=None) -> Dict`
启动进程

```python
result = pm.start(
    name='main-agent',
    command='python3',
    args=['agent.py', '--config', 'prod.yaml'],
    workdir='/path/to/workspace'
)
# 返回：{'success': True, 'pid': 12345, 'message': '进程 main-agent 已启动'}
```

#### `stop(name, timeout=10) -> Dict`
停止进程

```python
result = pm.stop('main-agent')
# 返回：{'success': True, 'message': '进程 main-agent 已停止'}
```

#### `restart(name) -> Dict`
重启进程

```python
result = pm.restart('main-agent')
```

#### `status(name) -> Dict`
获取进程状态

```python
status = pm.status('main-agent')
# 返回：
# {
#     'exists': True,
#     'name': 'main-agent',
#     'pid': 12345,
#     'status': 'running',
#     'cpu': 2.5,
#     'memory': '128.5 MB',
#     'started': '2026-03-20T10:00:00'
# }
```

#### `list_all() -> List[Dict]`
列出所有进程

```python
processes = pm.list_all()
```

#### `cleanup() -> Dict`
清理僵尸进程记录

```python
result = pm.cleanup()
```

---

## 3. 会话管理 (SessionManager)

### 初始化

```python
from claw_ex import SessionManager

sm = SessionManager()
```

### 方法

#### `create(name, metadata=None) -> Dict`
创建会话

```python
result = sm.create('dev-session', metadata={'env': 'development'})
# 返回：{'success': True, 'session_id': 'abc12345', 'message': '会话 dev-session 已创建'}
```

#### `delete(name) -> Dict`
删除会话

```python
result = sm.delete('dev-session')
```

#### `switch(name) -> Dict`
切换会话

```python
result = sm.switch('prod-session')
```

#### `list_sessions() -> List[Dict]`
列出所有会话

```python
sessions = sm.list_sessions()
# 返回：
# [
#     {'name': 'dev-session', 'id': 'abc12345', 'active': True, ...},
#     {'name': 'prod-session', 'id': 'def67890', 'active': False, ...}
# ]
```

#### `get_current() -> Dict`
获取当前会话

```python
current = sm.get_current()
```

#### `set_context(name, context) -> Dict`
设置会话上下文

```python
sm.set_context('dev-session', {'workspace': '/path/to/dev'})
```

#### `get_context(name) -> Dict`
获取会话上下文

```python
context = sm.get_context('dev-session')
```

#### `set_variable(name, key, value) -> Dict`
设置会话变量

```python
sm.set_variable('dev-session', 'api_key', 'xxx')
```

#### `get_variable(name, key, default=None) -> Any`
获取会话变量

```python
api_key = sm.get_variable('dev-session', 'api_key')
```

---

## 4. 系统监控 (SystemMonitor)

### 初始化

```python
from claw_ex import SystemMonitor

mon = SystemMonitor()
```

### 方法

#### `get_cpu_usage(interval=1.0) -> Dict`
获取 CPU 使用率

```python
cpu = mon.get_cpu_usage()
# 返回：
# {
#     'current': 25.5,
#     'per_core': [20.0, 30.0, 25.0, 27.0],
#     'cores': 4,
#     'logical_cores': 8,
#     'frequency': {'current': 2400, 'min': 800, 'max': 3200}
# }
```

#### `get_memory_usage() -> Dict`
获取内存使用情况

```python
mem = mon.get_memory_usage()
# 返回：
# {
#     'total': 16.0,
#     'used': 8.5,
#     'available': 7.5,
#     'percent': 53.1,
#     'swap': {'total': 4.0, 'used': 0.5, 'percent': 12.5}
# }
```

#### `get_disk_usage(path='/') -> Dict`
获取磁盘使用情况

```python
disk = mon.get_disk_usage()
# 返回：
# {
#     'total': 500.0,
#     'used': 250.0,
#     'free': 250.0,
#     'percent': 50.0,
#     'partitions': [...]
# }
```

#### `get_network_stats() -> Dict`
获取网络统计

```python
net = mon.get_network_stats()
# 返回：
# {
#     'bytes_sent': 1024000,
#     'bytes_recv': 2048000,
#     'interfaces': {...}
# }
```

#### `get_process_list() -> List[Dict]`
获取进程列表

```python
processes = mon.get_process_list()
```

#### `get_top_processes(n=10, by='cpu') -> List[Dict]`
获取资源占用最高的进程

```python
top_cpu = mon.get_top_processes(by='cpu')
top_mem = mon.get_top_processes(by='memory')
```

#### `get_system_info() -> Dict`
获取系统信息

```python
info = mon.get_system_info()
```

#### `get_all() -> Dict`
获取所有监控数据

```python
all_data = mon.get_all()
```

#### `check_alerts(thresholds=None) -> List[Dict]`
检查告警

```python
alerts = mon.check_alerts()
# 返回：
# [
#     {'level': 'WARNING', 'type': 'cpu', 'message': 'CPU 使用率过高：85.0%', ...}
# ]
```

---

## 5. 日志管理 (LogManager)

### 初始化

```python
from claw_ex import LogManager

lm = LogManager()  # 默认日志目录
lm = LogManager('/custom/log/path')  # 自定义日志目录
```

### 方法

#### `log(message, level='INFO', source='claw-ex', metadata=None)`
记录日志

```python
lm.log('Application started', level='INFO')
lm.log('Connection failed', level='ERROR', metadata={'host': 'localhost'})
```

#### `tail(lines=20, level=None) -> List[Dict]`
获取日志末尾

```python
recent = lm.tail(lines=50)
errors = lm.tail(lines=20, level='ERROR')
```

#### `search(keyword, level=None, source=None, start_time=None, end_time=None) -> List[Dict]`
搜索日志

```python
# 搜索包含关键词的日志
results = lm.search('connection')

# 搜索特定级别的错误
errors = lm.search('', level='ERROR')

# 搜索时间范围内的日志
logs = lm.search(
    'timeout',
    start_time='2026-03-20T00:00:00',
    end_time='2026-03-20T23:59:59'
)
```

#### `get_stats() -> Dict`
获取日志统计

```python
stats = lm.get_stats()
# 返回：
# {
#     'total_lines': 1000,
#     'by_level': {'INFO': 800, 'WARNING': 150, 'ERROR': 50},
#     'by_source': {'claw-ex': 500, 'agent': 500},
#     'file_size': 102400,
#     'rotated_files': 5
# }
```

#### `clear() -> Dict`
清空日志

```python
result = lm.clear()
# 返回：{'success': True, 'count': 1000, 'message': '已清空 1000 条日志'}
```

#### `export(output_path, level=None, start_time=None, end_time=None) -> Dict`
导出日志

```python
result = lm.export('/path/to/export.log', level='ERROR')
```

#### `cleanup(retention_days=30) -> Dict`
清理旧日志

```python
result = lm.cleanup(retention_days=7)
```

#### `get_recent_errors(hours=24) -> List[Dict]`
获取最近的错误日志

```python
errors = lm.get_recent_errors(hours=1)
```

#### `get_recent_warnings(hours=24) -> List[Dict]`
获取最近的警告日志

```python
warnings = lm.get_recent_warnings()
```

---

## CLI 使用

```bash
# 环境检测
claw-ex env check
claw-ex env init

# 进程管理
claw-ex process start my-agent python3 agent.py
claw-ex process stop my-agent
claw-ex process list
claw-ex process status my-agent

# 会话管理
claw-ex session create dev
claw-ex session list
claw-ex session switch dev
claw-ex session delete dev

# 系统监控
claw-ex monitor system
claw-ex monitor watch -i 2

# 日志管理
claw-ex logs tail -n 50
claw-ex logs search "error" --level ERROR
claw-ex logs clear
```

---

## 错误处理

所有方法都返回包含 `success` 字段的字典，失败时包含 `error` 字段：

```python
result = pm.start('agent', 'python3', ['agent.py'])
if not result['success']:
    print(f"启动失败：{result['error']}")
else:
    print(f"启动成功，PID: {result['pid']}")
```

---

## 配置

配置文件位于 `~/.openclaw/claw-ex/config.json`

```json
{
  "version": "0.1.0",
  "process": {
    "auto_restart": true,
    "health_check_interval": 30,
    "max_restarts": 3
  },
  "monitor": {
    "cpu_threshold": 80,
    "memory_threshold": 90,
    "disk_threshold": 85
  },
  "logs": {
    "level": "INFO",
    "max_size_mb": 100,
    "retention_days": 30
  }
}
```
