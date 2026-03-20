# claw-ex API Server

FastAPI 后端服务，为 claw-ex Web UI 提供 API 支持。

## 📋 功能特性

- **RESTful API**: 完整的 claw-ex CLI 命令封装
- **WebSocket 实时推送**: 任务状态实时监控
- **CORS 支持**: 跨域访问配置
- **Docker 部署**: 容器化部署配置
- **OpenAPI 文档**: 自动生成的 Swagger UI

## 🚀 快速开始

### 本地开发

```bash
# 安装依赖
pip3 install -r requirements.txt

# 启动服务器
python3 main.py

# 或使用 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker 部署

```bash
# 开发模式
docker-compose up --build

# 生产模式（带 Nginx）
docker-compose --profile production up -d
```

## 📖 API 文档

启动服务后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔌 API 端点

### 基础端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | API 信息 |
| GET | `/health` | 健康检查 |

### 环境管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/env` | 获取环境变量 |
| GET | `/api/env/info` | 系统信息 |
| GET | `/api/env/check` | 环境检查 |
| POST | `/api/env/create?name=xxx&description=yyy` | 创建环境 |
| POST | `/api/env/switch/{env_name}` | 切换环境 |
| GET | `/api/env/list-detailed` | 环境列表（详细） |

### Agent 管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/agent/list` | Agent 列表 |
| GET | `/api/agent/status/{agent_id}` | Agent 状态 |

### 任务管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/task/list` | 任务列表 |
| GET | `/api/task/{task_id}` | 任务详情 |

### 会话管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/session/list` | 会话列表 |

### 配置管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config/list` | 配置列表 |

### WebSocket

| 路径 | 说明 |
|------|------|
| `/ws/monitor` | 实时监控连接 |

## 🔌 WebSocket 使用示例

```javascript
// 浏览器端连接
const ws = new WebSocket('ws://localhost:8000/ws/monitor');

ws.onopen = () => {
    console.log('已连接到监控服务');
    
    // 订阅特定事件
    ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['task', 'agent', 'system']
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('收到消息:', data);
};

ws.onerror = (error) => {
    console.error('WebSocket 错误:', error);
};

ws.onclose = () => {
    console.log('连接已关闭');
};
```

## 📁 项目结构

```
api-server/
├── main.py              # FastAPI 应用入口
├── requirements.txt     # Python 依赖
├── Dockerfile          # Docker 镜像配置
├── docker-compose.yml  # Docker 编排配置
├── nginx.conf          # Nginx 反向代理配置
└── README.md           # 本文档
```

## 🔧 配置选项

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ENVIRONMENT` | 运行环境 | `development` |
| `LOG_LEVEL` | 日志级别 | `info` |
| `CORS_ORIGINS` | 允许的源 | `*` |

### Docker 环境变量

在 `docker-compose.yml` 中配置：

```yaml
environment:
  - ENVIRONMENT=production
  - LOG_LEVEL=info
  - CORS_ORIGINS=http://localhost:3000
```

## 🧪 测试

### 健康检查

```bash
curl http://localhost:8000/health
```

### API 测试

```bash
# 获取环境变量
curl http://localhost:8000/api/env

# 获取任务列表
curl http://localhost:8000/api/task/list

# 获取 Agent 列表
curl http://localhost:8000/api/agent/list
```

## 🛡️ 安全考虑

### 生产环境建议

1. **限制 CORS 源**: 不要使用 `*`，指定具体域名
2. **启用 HTTPS**: 使用 Nginx 配置 SSL/TLS
3. **API 认证**: 添加 JWT 或 API Key 认证
4. **速率限制**: 防止 API 滥用
5. **日志审计**: 记录所有 API 请求

### 添加 API Key 认证（示例）

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return api_key

# 在路由中使用
@app.get("/api/protected", dependencies=[Depends(verify_api_key)])
async def protected_endpoint():
    ...
```

## 📊 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| CPU | 处理器使用率 | > 80% |
| Memory | 内存占用 | > 90% |
| Request Latency | 请求延迟 | > 500ms |
| Error Rate | 错误率 | > 5% |

## 🔄 扩展开发

### 添加新 API 端点

```python
@app.get("/api/new-endpoint")
async def new_endpoint():
    """新 API 端点"""
    return {"message": "Hello, World!"}
```

### 添加新的 WebSocket 事件

```python
async def broadcast_event(event_type: str, data: dict):
    await broadcast_ws_message(event_type, data)
```

## 📝 许可证

MIT License - OpenClaw Team
