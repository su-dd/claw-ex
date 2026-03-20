# claw-ex · OpenClaw 终端管理工具

兵部开发的 OpenClaw 系统集成与进程管理终端程序。

## 📋 功能特性

### 1. 环境检测与配置
- OpenClaw Gateway 状态检测
- 工作空间环境验证
- 依赖项检查
- 配置文件生成

### 2. 进程管理
- 启动/停止 Agent 进程
- 进程健康监控
- 自动重启守护
- 进程树管理

### 3. 会话管理
- 创建新会话
- 列出活跃会话
- 切换会话上下文
- 会话状态持久化

### 4. 系统资源监控
- CPU 使用率实时监控
- 内存占用分析
- 网络流量统计
- 磁盘 I/O 监控

### 5. 日志收集
- 实时日志流
- 日志级别过滤
- 日志搜索与归档
- 异常日志告警

## 🚀 快速开始

### 安装依赖

```bash
pip3 install psutil
```

### 基本使用

```bash
# 环境检测
python3 bin/claw-ex.py env check

# 启动 Agent
python3 bin/claw-ex.py process start --name main-agent

# 查看进程状态
python3 bin/claw-ex.py process list

# 系统监控
python3 bin/claw-ex.py monitor system

# 会话管理
python3 bin/claw-ex.py session create --name dev-session
python3 bin/claw-ex.py session list

# 日志查看
python3 bin/claw-ex.py logs tail --lines 50
```

## 📁 项目结构

```
claw-ex/
├── bin/
│   └── claw-ex.py          # 主 CLI 入口
├── src/
│   ├── __init__.py
│   ├── env.py              # 环境检测模块
│   ├── process.py          # 进程管理模块
│   ├── session.py          # 会话管理模块
│   ├── monitor.py          # 系统监控模块
│   └── logs.py             # 日志管理模块
├── docs/
│   └── API.md              # API 文档
├── tests/
│   └── test_claw_ex.py     # 单元测试
├── config/
│   └── default.yaml        # 默认配置
└── README.md
```

## 🔧 API 参考

### 进程管理 API

```python
from src.process import ProcessManager

pm = ProcessManager()
pm.start('agent', '/path/to/agent', args=['--config', 'prod.yaml'])
pm.stop('agent')
pm.status('agent')
pm.list_all()
```

### 系统监控 API

```python
from src.monitor import SystemMonitor

mon = SystemMonitor()
cpu = mon.get_cpu_usage()
mem = mon.get_memory_usage()
net = mon.get_network_stats()
```

### 会话管理 API

```python
from src.session import SessionManager

sm = SessionManager()
sm.create('dev')
sm.switch('dev')
sm.list_sessions()
```

## 📊 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| CPU | 处理器使用率 | > 80% |
| Memory | 内存占用 | > 90% |
| Disk | 磁盘使用率 | > 85% |
| Network | 网络延迟 | > 500ms |

## 🛡️ 安全考虑

- 进程权限隔离
- 配置文件加密存储
- 日志脱敏处理
- 会话令牌轮换

## 📝 许可证

MIT License - OpenClaw Team
