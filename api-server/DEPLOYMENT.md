# 模板管理 API 部署文档

## 部署概述

本文档描述如何部署 claw-ex API 服务器的模板管理功能。

---

## 前置要求

### 系统要求
- Python 3.8+
- pip3
- Linux/macOS/WSL

### 依赖模块
- FastAPI
- uvicorn
- pydantic
- template_manager.py（位于 `~/.openclaw/templates/template_manager.py`）

---

## 安装步骤

### 1. 安装 Python 依赖

```bash
cd /home/sul/workspace/claw-ex/api-server

# 创建虚拟环境（如果还没有）
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装测试依赖（可选）
pip install pytest httpx
```

### 2. 验证 template_manager.py 可用

```bash
python3 -c "import sys; sys.path.insert(0, '/home/sul/.openclaw/templates'); from template_manager import TemplateManager; print('✅ 模板管理器可用')"
```

### 3. 启动 API 服务器

```bash
# 开发模式
python3 main.py

# 或使用 uvicorn（推荐）
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 验证部署

```bash
# 健康检查
curl http://localhost:8000/health

# 列出模板
curl http://localhost:8000/api/template/list

# 访问 Swagger UI
# 浏览器打开：http://localhost:8000/docs
```

---

## Docker 部署

### 使用 Docker Compose

```bash
# 构建并启动
docker-compose up --build

# 后台运行
docker-compose up -d

# 查看日志
docker-compose logs -f api-server

# 停止服务
docker-compose down
```

### 手动 Docker 部署

```bash
# 构建镜像
docker build -t claw-ex-api:latest .

# 运行容器
docker run -d \
  --name claw-ex-api \
  -p 8000:8000 \
  -v ~/.openclaw/templates:/root/.openclaw/templates \
  claw-ex-api:latest
```

---

## 生产环境部署

### 1. 使用 Gunicorn + Uvicorn

```bash
pip install gunicorn

gunicorn main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile /var/log/claw-ex/access.log \
  --error-logfile /var/log/claw-ex/error.log
```

### 2. 配置 Nginx 反向代理

创建 `/etc/nginx/sites-available/claw-ex-api`:

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态文件缓存
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_cache_valid 200 1h;
    }
}
```

启用站点：

```bash
sudo ln -s /etc/nginx/sites-available/claw-ex-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 3. 配置 HTTPS（Let's Encrypt）

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.example.com
```

### 4. 系统服务配置

创建 `/etc/systemd/system/claw-ex-api.service`:

```ini
[Unit]
Description=claw-ex API Server
After=network.target

[Service]
Type=simple
User=sul
WorkingDirectory=/home/sul/workspace/claw-ex/api-server
Environment="PATH=/home/sul/workspace/claw-ex/api-server/venv/bin"
ExecStart=/home/sul/workspace/claw-ex/api-server/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable claw-ex-api
sudo systemctl start claw-ex-api
sudo systemctl status claw-ex-api
```

---

## 监控与日志

### 查看日志

```bash
# 系统服务日志
sudo journalctl -u claw-ex-api -f

# Docker 日志
docker-compose logs -f

# 应用日志（如果配置了文件日志）
tail -f /var/log/claw-ex/access.log
tail -f /var/log/claw-ex/error.log
```

### 健康检查端点

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细状态（包括模板管理器）
curl http://localhost:8000/api/template/list
```

### 监控指标

建议监控以下指标：

| 指标 | 端点 | 告警阈值 |
|------|------|----------|
| API 响应时间 | Prometheus | > 500ms |
| 错误率 | 日志分析 | > 5% |
| CPU 使用率 | 系统监控 | > 80% |
| 内存使用率 | 系统监控 | > 90% |
| 磁盘空间 | 系统监控 | > 85% |

---

## 备份与恢复

### 备份模板

```bash
# 备份模板目录
tar -czf templates_backup_$(date +%Y%m%d).tar.gz ~/.openclaw/templates/

# 或使用导出 API
curl -X POST http://localhost:8000/api/template/export/all \
  -H "Content-Type: application/json" \
  -d '{"output_path": "/backup/templates"}'
```

### 恢复模板

```bash
# 解压备份
tar -xzf templates_backup_YYYYMMDD.tar.gz -C ~/

# 或使用导入 API
curl -X POST http://localhost:8000/api/template/import \
  -H "Content-Type: application/json" \
  -d '{"import_path": "/backup/templates", "overwrite": true}'
```

---

## 故障排查

### 常见问题

#### 1. 模板管理器不可用 (503)

**症状**: API 返回 `503 Service Unavailable`

**原因**: template_manager.py 未找到或导入失败

**解决**:
```bash
# 检查文件是否存在
ls -la ~/.openclaw/templates/template_manager.py

# 测试导入
python3 -c "from template_manager import TemplateManager"

# 检查 Python 路径
python3 -c "import sys; print('\\n'.join(sys.path))"
```

#### 2. 端口被占用 (98)

**症状**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或修改端口
uvicorn main:app --port 8001
```

#### 3. 权限问题

**症状**: `Permission denied` 写入模板

**解决**:
```bash
# 检查目录权限
ls -la ~/.openclaw/templates/

# 修复权限
chmod 755 ~/.openclaw/templates/
chown -R $USER:$USER ~/.openclaw/templates/
```

#### 4. 依赖缺失

**症状**: `ModuleNotFoundError`

**解决**:
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 性能优化

### 1. 启用缓存

在 Nginx 配置中添加：

```nginx
location /api/template/list {
    proxy_pass http://localhost:8000;
    proxy_cache_valid 200 5m;
}
```

### 2. 数据库优化（未来）

如果模板数量很大，考虑：
- 使用 SQLite/PostgreSQL 存储元数据
- 添加索引
- 实现分页查询

### 3. 异步处理

对于导出/导入等耗时操作，考虑：
- 使用 Celery 异步任务队列
- 返回任务 ID，客户端轮询状态

---

## 安全建议

### 1. 添加 API 认证

```python
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    # 验证 token
    if not validate_token(credentials.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials
```

### 2. 速率限制

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.get("/api/template/list")
@limiter.limit("100/minute")
async def list_templates(request: Request):
    ...
```

### 3. 输入验证

所有用户输入已经通过 Pydantic 模型验证，确保：
- 类型正确
- 长度限制
- 格式合规

---

## 升级指南

### 从旧版本升级

```bash
# 停止服务
sudo systemctl stop claw-ex-api

# 备份当前版本
cp -r /home/sul/workspace/claw-ex/api-server \
      /home/sul/workspace/claw-ex/api-server.backup

# 拉取新代码
cd /home/sul/workspace/claw-ex/api-server
git pull

# 安装新依赖
pip install -r requirements.txt

# 运行迁移（如果有）
# python migrate.py

# 重启服务
sudo systemctl start claw-ex-api
```

---

## 联系支持

- 文档：`/home/sul/workspace/claw-ex/api-server/TEMPLATE_API.md`
- API 文档：`http://localhost:8000/docs`
- 问题反馈：提交到工部
