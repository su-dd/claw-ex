# 模板管理 API 文档

## 概述

模板管理 API 为 OpenClaw 配置模板提供完整的 HTTP 接口支持，基于 FastAPI 框架实现，封装了 `template_manager.py` 核心模块的功能。

**API 基础路径**: `http://localhost:8000/api/template`

**Swagger 文档**: `http://localhost:8000/docs`

**Redoc 文档**: `http://localhost:8000/redoc`

---

## 认证与授权

当前版本无需认证，生产环境建议添加 JWT 或 OAuth2 认证。

---

## 数据模型

### TemplateListItem
模板列表项
```json
{
  "name": "string",
  "format": "yaml|json",
  "status": "draft|active|deprecated|archived",
  "version": "string",
  "description": "string",
  "tags": ["string"],
  "path": "string"
}
```

### TemplateDetail
模板详情
```json
{
  "id": "string",
  "name": "string",
  "format": "yaml|json",
  "status": "string",
  "version": "string",
  "description": "string",
  "tags": ["string"],
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "schema": {"object"},
  "content": {"object"}
}
```

### TemplateVersionInfo
模板版本信息
```json
{
  "version": "string",
  "content_hash": "string",
  "created_at": "ISO8601",
  "created_by": "string",
  "change_log": "string"
}
```

---

## API 端点

### 1. 列出模板

**GET** `/api/template/list`

列出所有可用模板。

**响应示例**:
```json
{
  "success": true,
  "templates": [
    {
      "name": "agent_config",
      "format": "yaml",
      "status": "active",
      "version": "1.0.0",
      "description": "Agent 配置模板",
      "tags": ["agent", "config"],
      "path": "/home/user/.openclaw/templates/agent_config.yaml"
    }
  ],
  "count": 1
}
```

**状态码**:
- `200` - 成功
- `503` - 模板管理器不可用

---

### 2. 查看模板详情

**GET** `/api/template/show/{template_id}`

获取指定模板的详细信息和内容。

**路径参数**:
- `template_id` (string): 模板名称或 ID

**响应示例**:
```json
{
  "success": true,
  "template": {
    "id": "abc123",
    "name": "agent_config",
    "format": "yaml",
    "status": "active",
    "version": "1.0.0",
    "description": "Agent 配置模板",
    "tags": ["agent", "config"],
    "created_at": "2026-03-20T10:00:00",
    "updated_at": "2026-03-20T12:00:00",
    "schema": {
      "name": "agent_schema",
      "version": "1.0.0",
      "required_variables": ["agent_name", "department"]
    },
    "content": {
      "agent_name": "${agent_name}",
      "department": "${department}"
    }
  }
}
```

**状态码**:
- `200` - 成功
- `404` - 模板不存在
- `500` - 服务器错误

---

### 3. 创建模板

**POST** `/api/template/create`

创建新模板。

**请求体**:
```json
{
  "name": "my_template",
  "content": {
    "key": "${variable}"
  },
  "format": "yaml",
  "description": "模板描述",
  "tags": ["tag1", "tag2"],
  "schema": {
    "name": "my_schema",
    "version": "1.0.0",
    "required_variables": ["variable"],
    "optional_variables": [],
    "default_values": {},
    "variable_types": {},
    "constraints": {}
  }
}
```

**字段说明**:
- `name` (required): 模板名称
- `content` (required): 模板内容字典
- `format` (optional): 文件格式，`yaml` 或 `json`，默认 `yaml`
- `description` (optional): 模板描述
- `tags` (optional): 标签列表
- `schema` (optional): Schema 定义

**响应示例**:
```json
{
  "success": true,
  "template_id": "abc123def456",
  "message": "模板 'my_template' 创建成功"
}
```

**状态码**:
- `200` - 成功
- `400` - 请求参数错误
- `503` - 模板管理器不可用

---

### 4. 应用模板

**POST** `/api/template/apply`

应用模板生成实际配置（变量替换）。

**请求体**:
```json
{
  "template_name": "my_template",
  "variables": {
    "variable": "value"
  },
  "output_path": "/path/to/output.yaml",
  "validate": true
}
```

**字段说明**:
- `template_name` (required): 模板名称
- `variables` (required): 变量字典
- `output_path` (optional): 输出文件路径，不提供则返回内容
- `validate` (optional): 是否先验证模板，默认 `true`

**响应示例**:
```json
{
  "success": true,
  "result": {
    "key": "value"
  },
  "output_path": "/path/to/output.yaml"
}
```

**状态码**:
- `200` - 成功
- `400` - 验证失败
- `404` - 模板不存在
- `500` - 服务器错误

---

### 5. 导出模板

**POST** `/api/template/export/{template_id}`

导出模板到指定目录。

**路径参数**:
- `template_id` (string): 模板名称

**请求体**:
```json
{
  "template_name": "my_template",
  "output_path": "/path/to/export",
  "include_metadata": true,
  "include_versions": false
}
```

**字段说明**:
- `template_name` (required): 模板名称
- `output_path` (required): 导出目录路径
- `include_metadata` (optional): 是否包含元数据，默认 `true`
- `include_versions` (optional): 是否包含版本历史，默认 `false`

**响应示例**:
```json
{
  "success": true,
  "message": "模板 'my_template' 已导出到：/path/to/export",
  "output_path": "/path/to/export"
}
```

**状态码**:
- `200` - 成功
- `404` - 模板不存在
- `500` - 服务器错误

---

### 6. 导入模板

**POST** `/api/template/import`

从导出的目录导入模板。

**请求体**:
```json
{
  "import_path": "/path/to/exported/template",
  "overwrite": false
}
```

**字段说明**:
- `import_path` (required): 导入目录路径（必须包含 manifest.json）
- `overwrite` (optional): 是否覆盖现有模板，默认 `false`

**响应示例**:
```json
{
  "success": true,
  "template_id": "my_template",
  "message": "模板导入成功"
}
```

**状态码**:
- `200` - 成功
- `400` - 导入错误（模板已存在等）
- `404` - 导入路径不存在
- `500` - 服务器错误

---

### 7. 删除模板

**DELETE** `/api/template/delete/{template_id}`

删除指定模板。

**路径参数**:
- `template_id` (string): 模板名称

**查询参数**:
- `keep_versions` (boolean): 是否保留版本历史，默认 `false`

**响应示例**:
```json
{
  "success": true,
  "message": "模板 'my_template' 已删除"
}
```

**状态码**:
- `200` - 成功
- `404` - 模板不存在
- `500` - 服务器错误

---

### 8. 获取版本历史

**GET** `/api/template/versions/{template_id}`

获取模板的所有版本记录。

**路径参数**:
- `template_id` (string): 模板名称

**响应示例**:
```json
{
  "success": true,
  "versions": [
    {
      "version": "1.0.0",
      "content_hash": "abc123",
      "created_at": "2026-03-20T10:00:00",
      "created_by": "system",
      "change_log": "初始版本"
    },
    {
      "version": "1.0.1",
      "content_hash": "def456",
      "created_at": "2026-03-20T12:00:00",
      "created_by": "system",
      "change_log": "更新配置"
    }
  ],
  "count": 2
}
```

**状态码**:
- `200` - 成功
- `500` - 服务器错误

---

### 9. 回滚模板

**POST** `/api/template/rollback/{template_id}/{version}`

回滚模板到指定版本。

**路径参数**:
- `template_id` (string): 模板名称
- `version` (string): 目标版本号

**响应示例**:
```json
{
  "success": true,
  "message": "模板已回滚到版本 1.0.0"
}
```

**状态码**:
- `200` - 成功
- `404` - 版本不存在
- `500` - 服务器错误

---

## 使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. 创建模板
create_data = {
    "name": "test_agent",
    "content": {
        "name": "${agent_name}",
        "dept": "${department}"
    },
    "format": "yaml",
    "description": "测试模板"
}
response = requests.post(f"{BASE_URL}/api/template/create", json=create_data)
print(response.json())

# 2. 列出模板
response = requests.get(f"{BASE_URL}/api/template/list")
templates = response.json()["templates"]
print(f"找到 {len(templates)} 个模板")

# 3. 应用模板
apply_data = {
    "template_name": "test_agent",
    "variables": {
        "agent_name": "MyAgent",
        "department": "兵部"
    }
}
response = requests.post(f"{BASE_URL}/api/template/apply", json=apply_data)
result = response.json()["result"]
print(f"应用结果：{result}")

# 4. 删除模板
response = requests.delete(f"{BASE_URL}/api/template/delete/test_agent")
print(response.json())
```

### cURL 示例

```bash
# 创建模板
curl -X POST http://localhost:8000/api/template/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "curl_test",
    "content": {"key": "${value}"},
    "format": "yaml"
  }'

# 列出模板
curl http://localhost:8000/api/template/list

# 应用模板
curl -X POST http://localhost:8000/api/template/apply \
  -H "Content-Type: application/json" \
  -d '{
    "template_name": "curl_test",
    "variables": {"value": "test"}
  }'

# 删除模板
curl -X DELETE http://localhost:8000/api/template/delete/curl_test
```

---

## 错误处理

API 使用标准 HTTP 状态码表示操作结果：

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 / 验证失败 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用（模板管理器未初始化） |

错误响应格式：
```json
{
  "detail": "错误描述信息"
}
```

---

## 部署说明

### 前置要求

- Python 3.8+
- FastAPI
- uvicorn
- template_manager.py 模块

### 启动 API 服务器

```bash
cd /home/sul/workspace/claw-ex/api-server
source venv/bin/activate
python main.py
```

或使用 uvicorn 直接启动：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 生产环境部署

使用 Docker Compose：

```bash
docker-compose up -d
```

使用 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name api.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 测试

运行集成测试：

```bash
cd /home/sul/workspace/claw-ex/api-server
source venv/bin/activate
pip install pytest httpx
python -m pytest test_template_api.py -v
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-03-20 | 初始版本，实现所有模板管理端点 |

---

## 联系与支持

- 项目仓库：`/home/sul/workspace/claw-ex`
- API 文档：`http://localhost:8000/docs`
- 问题反馈：提交到工部
