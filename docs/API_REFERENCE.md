# claw-ex API 参考文档

> **版本**: 0.2.0  
> **最后更新**: 2026-03-20  
> **维护团队**: 工部开发团队

## 目录

- [概述](#概述)
- [快速开始](#快速开始)
- [认证说明](#认证说明)
- [API 端点](#api-端点)
  - [根路径](#根路径)
  - [健康检查](#健康检查)
  - [环境管理](#环境管理)
  - [Agent 管理](#agent-管理)
  - [任务管理](#任务管理)
  - [会话管理](#会话管理)
  - [配置管理](#配置管理)
  - [模板管理](#模板管理)
- [WebSocket 实时推送](#websocket-实时推送)
- [错误处理](#错误处理)
- [最佳实践](#最佳实践)

---

## 概述

claw-ex API 是 OpenClaw CLI 终端程序的 FastAPI 后端服务，为尚书省任务管理系统提供完整的 RESTful API 支持。

### 基础信息

- **Base URL**: `http://localhost:8000`
- **API 文档**: `/docs` (Swagger UI), `/redoc` (ReDoc)
- **OpenAPI JSON**: `/openapi.json`
- **版本**: 0.2.0

### 响应格式

所有 API 端点统一返回 JSON 格式：

```json
{
    "success": true,
    "data": {...},
    "message": "操作说明",
    "errors": []
}
```

### 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 429 | 请求频率超限 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

---

## 快速开始

### 启动 API 服务

```bash
cd /home/sul/workspace/claw-ex/api-server
python3 main.py
```

或使用 Uvicorn：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 测试连接

```bash
curl http://localhost:8000/health
```

### 查看文档

浏览器访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 认证说明

当前版本为开发版本，暂未启用认证。**生产环境必须配置认证**。

### 推荐方案

#### OAuth2 + JWT

```python
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/api/protected")
async def protected(token: str = Depends(oauth2_scheme)):
    # 验证 token
    pass
```

#### API Key

```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.get("/api/protected")
async def protected(api_key: str = Security(api_key_header)):
    if api_key != EXPECTED_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## API 端点

### 根路径

#### `GET /`

API 根路径，返回服务信息和文档链接。

**响应示例**:
```json
{
    "service": "claw-ex API Server",
    "version": "0.2.0",
    "status": "running",
    "docs": "/docs",
    "redoc": "/redoc",
    "openapi": "/openapi.json",
    "health": "/health"
}
```

---

### 健康检查

#### `GET /health`

检查 API 服务健康状态，用于负载均衡器和监控系统。

**响应示例**:
```json
{
    "status": "healthy",
    "timestamp": "2026-03-20T10:00:00"
}
```

---

### 环境管理

#### `GET /api/env`

获取环境变量列表。

**响应示例**:
```json
{
    "success": true,
    "data": [
        {"variable": "PYTHON_VERSION", "value": "3.11.0"},
        {"variable": "PLATFORM", "value": "linux"},
        {"variable": "WORKSPACE", "value": "/home/user/workspace"}
    ],
    "message": "环境变量获取成功"
}
```

#### `GET /api/env/info`

获取详细系统信息。

**响应示例**:
```json
{
    "platform": "linux x86_64",
    "python_version": "3.11.0",
    "hostname": "server-01",
    "memory_total": "16 GB",
    "memory_available": "8 GB"
}
```

#### `GET /api/env/check`

执行环境健康检查。

**响应示例**:
```json
{
    "success": true,
    "results": [
        {"check_name": "Python 版本", "passed": true, "status": "通过"},
        {"check_name": "工作目录", "passed": true, "status": "通过"}
    ],
    "all_pass": true
}
```

#### `POST /api/env/create`

创建新的运行环境。

**参数**:
- `name` (query, 必需): 环境名称
- `description` (query, 可选): 环境描述

**示例**:
```bash
curl -X POST "http://localhost:8000/api/env/create?name=production&description=生产环境"
```

#### `POST /api/env/switch/{env_name}`

切换到指定运行环境。

**路径参数**:
- `env_name`: 目标环境名称

**示例**:
```bash
curl -X POST "http://localhost:8000/api/env/switch/production"
```

#### `GET /api/env/list-detailed`

获取所有环境的详细信息。

---

### Agent 管理

#### `GET /api/agent/list`

获取所有 Agent 列表。

**响应示例**:
```json
{
    "success": true,
    "agents": [
        {
            "id": "agent:shangshu:main",
            "name": "尚书省",
            "status": "active",
            "department": "尚书省"
        }
    ],
    "count": 3
}
```

#### `GET /api/agent/status/{agent_id}`

获取指定 Agent 的详细状态。

**路径参数**:
- `agent_id`: Agent 的唯一标识符

**响应示例**:
```json
{
    "id": "agent:shangshu:main",
    "status": "active",
    "uptime": "2h 15m",
    "task_count": 5
}
```

---

### 任务管理

#### `GET /api/task/list`

获取所有任务列表。

**响应示例**:
```json
{
    "success": true,
    "tasks": [
        {
            "task_id": "JJC-20260320-001",
            "title": "系统架构设计",
            "status": "Done",
            "department": "工部",
            "priority": "high"
        }
    ],
    "count": 3
}
```

#### `GET /api/task/{task_id}`

获取指定任务的详细信息。

**路径参数**:
- `task_id`: 任务的唯一标识符

---

### 会话管理

#### `GET /api/session/list`

获取所有会话列表。

**响应示例**:
```json
{
    "success": true,
    "sessions": [
        {
            "session_id": "sess-001",
            "agent": "agent:shangshu:main",
            "channel": "feishu",
            "status": "active"
        }
    ],
    "count": 3
}
```

---

### 配置管理

#### `GET /api/config/list`

获取当前系统配置列表。

**响应示例**:
```json
{
    "success": true,
    "configs": [
        {"category": "api", "key": "baseUrl", "value": "http://localhost:3000"},
        {"category": "display", "key": "theme", "value": "dark"}
    ]
}
```

#### `POST /api/config/validate`

验证 Agent 配置文件。

**查询参数**:
- `path` (可选): 配置文件或目录路径
- `validate_all` (可选): 是否验证所有 Agent 配置
- `strict` (可选): 严格模式（警告视为错误）

**请求示例**:
```bash
# 验证所有 Agent
curl -X POST "http://localhost:8000/api/config/validate?validate_all=true"

# 验证指定文件
curl -X POST "http://localhost:8000/api/config/validate?path=/path/to/config.json"
```

**响应示例**:
```json
{
    "success": true,
    "summary": {
        "total": 3,
        "valid": 2,
        "invalid": 1,
        "pass_rate": "66.7%"
    },
    "details": {
        "agent:shangshu:main": {
            "valid": true,
            "file": "~/.openclaw/agents/shangshu.json",
            "errors": [],
            "warnings": []
        }
    }
}
```

---

### 模板管理

#### `GET /api/template/list`

列出所有可用模板。

#### `GET /api/template/show/{template_id}`

查看指定模板的详细信息。

#### `POST /api/template/create`

创建新模板。

**请求体**:
```json
{
    "name": "my-template",
    "content": {...},
    "format": "yaml",
    "description": "模板描述",
    "tags": ["agent", "config"],
    "schema": {...}
}
```

#### `POST /api/template/apply`

应用模板生成配置。

**请求体**:
```json
{
    "template_name": "agent-config-template",
    "variables": {"agent_name": "尚书省"},
    "output_path": "/path/to/output.yaml",
    "validate": true
}
```

#### `POST /api/template/export/{template_id}`

导出模板到指定路径。

#### `POST /api/template/import`

从文件导入模板。

#### `DELETE /api/template/delete/{template_id}`

删除指定模板。

#### `GET /api/template/versions/{template_id}`

获取模板的版本历史。

#### `POST /api/template/rollback/{template_id}/{version}`

回滚模板到指定版本。

---

## WebSocket 实时推送

### `WS /ws/monitor`

建立 WebSocket 连接，用于实时推送系统事件和状态更新。

### 连接流程

1. 客户端连接到 `ws://localhost:8000/ws/monitor`
2. 服务器发送欢迎消息
3. 客户端可发送订阅消息指定关注的事件类型
4. 服务器推送相关事件

### 消息格式

```json
{
    "type": "event_type",
    "data": {...},
    "timestamp": "2026-03-20T10:00:00"
}
```

### 事件类型

| 类型 | 说明 |
|------|------|
| `connected` | 连接成功 |
| `subscribed` | 订阅成功 |
| `task_update` | 任务状态更新 |
| `agent_status` | Agent 状态变化 |
| `system_alert` | 系统告警 |

### 客户端示例

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/monitor');

ws.onopen = () => {
    console.log('Connected to monitor');
    // 订阅特定事件
    ws.send(JSON.stringify({
        type: 'subscribe',
        channels: ['task_update', 'agent_status']
    }));
};

ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received:', message);
};
```

---

## 错误处理

### 错误响应格式

```json
{
    "detail": "错误详情"
}
```

### 常见错误

#### 400 Bad Request
```json
{
    "detail": "请求参数错误：缺少必需字段 name"
}
```

#### 404 Not Found
```json
{
    "detail": "资源不存在：模板 'unknown-template'"
}
```

#### 500 Internal Server Error
```json
{
    "detail": "服务器内部错误：数据库连接失败"
}
```

#### 503 Service Unavailable
```json
{
    "detail": "服务不可用：模板管理器未初始化"
}
```

---

## 最佳实践

### 1. 速率限制

生产环境建议使用 slowapi 进行速率限制：

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/protected")
@limiter.limit("100/minute")
async def protected(request: Request):
    pass
```

### 2. 日志记录

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("claw-ex")
```

### 3. 配置管理

使用环境变量管理敏感配置：

```python
import os

DATABASE_URL = os.getenv("DATABASE_URL")
API_KEY = os.getenv("API_KEY")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
```

### 4. 健康检查

实现深度健康检查：

```python
@app.get("/health/deep")
async def deep_health_check():
    checks = {}
    
    # 检查数据库连接
    try:
        # db.ping()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
    
    # 检查外部 API
    try:
        # requests.get(external_api)
        checks["external_api"] = "ok"
    except Exception as e:
        checks["external_api"] = f"error: {e}"
    
    all_healthy = all(v == "ok" for v in checks.values())
    
    return {
        "status": "healthy" if all_healthy else "unhealthy",
        "checks": checks
    }
```

### 5. API 版本控制

使用 URL 前缀进行版本控制：

```python
app_v1 = FastAPI(title="claw-ex API v1")
app_v2 = FastAPI(title="claw-ex API v2")

# 注册路由
# app_v1.include_router(...)
# app_v2.include_router(...)
```

---

## 附录

### A. 数据模型

#### Environment
```json
{
    "name": "production",
    "description": "生产环境",
    "is_active": true,
    "is_default": false,
    "created_at": "2026-03-20T10:00:00"
}
```

#### AgentInfo
```json
{
    "id": "agent:shangshu:main",
    "name": "尚书省",
    "status": "active",
    "department": "尚书省"
}
```

#### TaskInfo
```json
{
    "task_id": "JJC-20260320-001",
    "title": "系统架构设计",
    "status": "Done",
    "department": "工部",
    "priority": "high"
}
```

### B. CLI 命令参考

```bash
# 验证所有 Agent 配置
python3 bin/claw-ex.py config validate --all

# 验证单个文件
python3 bin/claw-ex.py config validate config.json

# 严格模式
python3 bin/claw-ex.py config validate --all --strict

# JSON 输出
python3 bin/claw-ex.py config validate --all --json
```

---

**文档生成**: 工部开发团队  
**最后更新**: 2026-03-20
