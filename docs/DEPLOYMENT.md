# claw-ex 部署与构建文档

## 📋 目录

1. [系统要求](#系统要求)
2. [安装步骤](#安装步骤)
3. [配置说明](#配置说明)
4. [构建打包](#构建打包)
5. [部署流程](#部署流程)
6. [运维指南](#运维指南)
7. [故障排查](#故障排查)

---

## 系统要求

### 最低要求

- **Python**: 3.8+
- **内存**: 2 GB
- **磁盘**: 100 MB
- **操作系统**: Linux / macOS / Windows

### 推荐配置

- **Python**: 3.10+
- **内存**: 4 GB
- **磁盘**: 500 MB
- **操作系统**: Linux (Ubuntu 20.04+ / CentOS 7+)

### 依赖项

```bash
# 核心依赖
pip3 install psutil

# 可选依赖（开发/测试）
pip3 install pytest
```

---

## 安装步骤

### 1. 克隆/下载项目

```bash
# 从 Git 仓库克隆
git clone https://github.com/openclaw/claw-ex.git
cd claw-ex

# 或直接下载解压
wget https://github.com/openclaw/claw-ex/archive/main.zip
unzip main.zip
cd claw-ex-main
```

### 2. 安装依赖

```bash
# 安装核心依赖
pip3 install psutil

# 验证安装
python3 -c "import psutil; print(psutil.__version__)"
```

### 3. 设置执行权限

```bash
chmod +x bin/claw-ex.py
```

### 4. 验证安装

```bash
# 查看帮助
python3 bin/claw-ex.py --help

# 环境检查
python3 bin/claw-ex.py env check
```

### 5. (可选) 创建系统链接

```bash
# 创建符号链接到系统路径
sudo ln -s $(pwd)/bin/claw-ex.py /usr/local/bin/claw-ex

# 验证
claw-ex --help
```

---

## 配置说明

### 配置文件位置

```
~/.openclaw/claw-ex/config.json
```

### 配置示例

```json
{
  "version": "0.1.0",
  "created_at": "2026-03-20T10:00:00",
  "openclaw_dir": "/home/user/.openclaw",
  "workspace_dir": "/home/user/.openclaw/workspace",
  
  "process": {
    "auto_restart": true,
    "health_check_interval": 30,
    "max_restarts": 3
  },
  
  "monitor": {
    "cpu_threshold": 80,
    "memory_threshold": 90,
    "disk_threshold": 85,
    "check_interval": 60
  },
  
  "logs": {
    "level": "INFO",
    "max_size_mb": 100,
    "retention_days": 30,
    "path": "/home/user/.openclaw/workspace/logs"
  },
  
  "sessions": {
    "default": "default",
    "path": "/home/user/.openclaw/workspace/sessions"
  }
}
```

### 配置项说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `process.auto_restart` | 进程异常退出时自动重启 | true |
| `process.health_check_interval` | 健康检查间隔 (秒) | 30 |
| `process.max_restarts` | 最大重启次数 | 3 |
| `monitor.cpu_threshold` | CPU 告警阈值 (%) | 80 |
| `monitor.memory_threshold` | 内存告警阈值 (%) | 90 |
| `monitor.disk_threshold` | 磁盘告警阈值 (%) | 85 |
| `logs.level` | 日志级别 | INFO |
| `logs.max_size_mb` | 日志文件最大大小 (MB) | 100 |
| `logs.retention_days` | 日志保留天数 | 30 |

---

## 构建打包

### 开发环境

```bash
# 运行测试
python3 -m unittest tests/test_claw_ex.py -v

# 代码检查
python3 -m py_compile src/*.py bin/*.py
```

### 生产打包

#### 方式一：Python 包

```bash
# 创建 setup.py
cat > setup.py << 'EOF'
from setuptools import setup, find_packages

setup(
    name='claw-ex',
    version='0.1.0',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    scripts=['bin/claw-ex.py'],
    install_requires=['psutil>=5.9.0'],
    python_requires='>=3.8',
)
EOF

# 构建
python3 setup.py sdist bdist_wheel

# 安装
pip3 install dist/claw_ex-0.1.0-py3-none-any.whl
```

#### 方式二：PyInstaller 打包

```bash
# 安装 PyInstaller
pip3 install pyinstaller

# 打包
pyinstaller --onefile --name claw-ex bin/claw-ex.py

# 产物位于 dist/claw-ex
```

#### 方式三：Docker 容器

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
RUN pip3 install psutil

# 复制代码
COPY src/ /app/src/
COPY bin/ /app/bin/

# 设置入口
ENTRYPOINT ["python3", "/app/bin/claw-ex.py"]
```

```bash
# 构建镜像
docker build -t openclaw/claw-ex:0.1.0 .

# 运行
docker run --rm openclaw/claw-ex:0.1.0 env check
```

---

## 部署流程

### 单机部署

```bash
# 1. 上传代码
scp -r claw-ex user@server:/opt/openclaw/

# 2. 安装依赖
ssh user@server "cd /opt/openclaw/claw-ex && pip3 install psutil"

# 3. 创建系统服务
sudo cat > /etc/systemd/system/claw-ex-monitor.service << 'EOF'
[Unit]
Description=claw-ex System Monitor
After=network.target

[Service]
Type=simple
User=openclaw
WorkingDirectory=/opt/openclaw/claw-ex
ExecStart=/usr/bin/python3 bin/claw-ex.py monitor watch -i 60
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 4. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable claw-ex-monitor
sudo systemctl start claw-ex-monitor

# 5. 验证状态
sudo systemctl status claw-ex-monitor
```

### Kubernetes 部署

```yaml
# claw-ex-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: claw-ex
  labels:
    app: claw-ex
spec:
  replicas: 1
  selector:
    matchLabels:
      app: claw-ex
  template:
    metadata:
      labels:
        app: claw-ex
    spec:
      containers:
      - name: claw-ex
        image: openclaw/claw-ex:0.1.0
        command: ["python3", "bin/claw-ex.py"]
        args: ["monitor", "watch", "-i", "60"]
        resources:
          requests:
            memory: "64Mi"
            cpu: "100m"
          limits:
            memory: "128Mi"
            cpu: "200m"
```

```bash
# 部署
kubectl apply -f claw-ex-deployment.yaml

# 查看状态
kubectl get pods -l app=claw-ex
```

---

## 运维指南

### 日常监控

```bash
# 查看系统状态
claw-ex monitor system

# 查看进程列表
claw-ex process list

# 查看最近错误日志
claw-ex logs tail -n 50 --level ERROR
```

### 日志管理

```bash
# 导出日志
claw-ex logs export /backup/logs-$(date +%Y%m%d).log

# 清理旧日志
claw-ex logs cleanup --retention-days 7

# 查看日志统计
claw-ex logs stats
```

### 会话管理

```bash
# 列出所有会话
claw-ex session list

# 切换会话
claw-ex session switch production

# 导出会话配置
claw-ex session export production /backup/session-prod.json
```

### 备份策略

```bash
#!/bin/bash
# backup-claw-ex.sh

BACKUP_DIR="/backup/claw-ex/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# 备份配置
cp -r ~/.openclaw/claw-ex $BACKUP_DIR/config

# 备份日志
cp -r ~/.openclaw/claw-ex/logs $BACKUP_DIR/logs

# 备份会话
cp -r ~/.openclaw/claw-ex/sessions $BACKUP_DIR/sessions

# 压缩
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "备份完成：$BACKUP_DIR.tar.gz"
```

---

## 故障排查

### 常见问题

#### 1. psutil 未安装

```bash
# 错误：ModuleNotFoundError: No module named 'psutil'
pip3 install psutil
```

#### 2. 权限不足

```bash
# 错误：Permission denied
chmod +x bin/claw-ex.py
# 或
sudo python3 bin/claw-ex.py env check
```

#### 3. 配置文件损坏

```bash
# 删除损坏的配置文件，重新生成
rm ~/.openclaw/claw-ex/config.json
claw-ex env init
```

#### 4. 进程无法启动

```bash
# 检查命令路径
which python3
# 使用绝对路径启动
claw-ex process start my-agent /usr/bin/python3 agent.py
```

#### 5. 日志文件过大

```bash
# 清理日志
claw-ex logs clear
# 或配置轮转
# 编辑 config.json 设置 max_size_mb
```

### 调试模式

```bash
# 启用详细输出
export CLAW_EX_DEBUG=1
python3 bin/claw-ex.py env check

# 查看内部状态
cat ~/.openclaw/claw-ex/processes/state.json
cat ~/.openclaw/claw-ex/sessions/state.json
```

### 性能优化

```bash
# 减少监控频率
# 编辑 config.json:
# "monitor": {"check_interval": 300}

# 减少日志缓存
# "logs": {"max_lines": 5000}

# 禁用不必要的功能
# 根据实际需求裁剪模块
```

---

## 升级指南

### 从旧版本升级

```bash
# 1. 备份配置
cp ~/.openclaw/claw-ex/config.json ~/.openclaw/claw-ex/config.json.bak

# 2. 更新代码
cd /opt/openclaw/claw-ex
git pull origin main

# 3. 更新依赖
pip3 install --upgrade psutil

# 4. 验证
claw-ex env check

# 5. 恢复配置（如有必要）
# 对比新旧配置，手动合并变更
```

### 版本兼容性

| claw-ex 版本 | Python 版本 | psutil 版本 |
|-------------|------------|-------------|
| 0.1.x | 3.8+ | 5.9+ |
| 0.2.x | 3.9+ | 5.9+ |

---

## 安全建议

1. **配置文件权限**: `chmod 600 ~/.openclaw/claw-ex/config.json`
2. **日志脱敏**: 避免在日志中记录敏感信息
3. **进程隔离**: 使用独立用户运行 Agent 进程
4. **定期审计**: 检查进程列表和会话配置
5. **备份策略**: 定期备份配置和重要数据

---

## 联系支持

- 文档：https://openclaw.com/docs/claw-ex
- 问题反馈：https://github.com/openclaw/claw-ex/issues
- 社区：https://discord.gg/openclaw
