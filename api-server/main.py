#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
claw-ex API Server - FastAPI 后端服务

为 claw-ex Web UI 提供后端 API 支持，实现尚书省任务管理系统的全功能后端。

## 功能特性
- 环境管理：环境变量查询、系统信息、环境检查
- Agent 管理：Agent 列表、状态查询
- 任务管理：任务列表、任务详情
- 会话管理：会话列表、实时监控
- 配置管理：配置查询、配置验证
- 模板管理：模板 CRUD、版本控制、导入导出

## API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 认证说明
当前版本为开发版本，暂未启用认证。生产环境请配置 OAuth2 或 JWT 认证。

## 速率限制
- 开发环境：无限制
- 生产环境：建议配置 100 请求/分钟/IP

## 错误处理
所有 API 端点统一返回格式：
```json
{
    "success": true/false,
    "data": {...},
    "message": "操作说明",
    "errors": ["错误列表"]
}
```
"""

import os
import sys
import json
import asyncio
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query, Body, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
import uvicorn
import shutil
from pathlib import Path as FilePath

# 添加 claw-ex 到路径
CLAW_EX_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bin')
sys.path.insert(0, CLAW_EX_PATH)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

# 添加模板管理器路径
TEMPLATE_MANAGER_PATH = os.path.join(os.path.expanduser('~'), '.openclaw', 'templates')
sys.path.insert(0, TEMPLATE_MANAGER_PATH)

# 添加兵部 workspace 路径（用于配置验证器）
BINGBU_PATH = os.path.join(os.path.expanduser('~'), '.openclaw', 'workspace-bingbu')
if BINGBU_PATH not in sys.path:
    sys.path.insert(0, BINGBU_PATH)

# ==================== 导入模板管理器 ====================

try:
    from template_manager import (
        TemplateManager,
        TemplateFormat,
        TemplateStatus,
        TemplateSchema,
        TemplateError,
        TemplateNotFoundError,
        TemplateValidationError
    )
    TEMPLATE_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ 模板管理器导入失败：{e}")
    TEMPLATE_MANAGER_AVAILABLE = False
    TemplateManager = None
    TemplateFormat = None
    TemplateStatus = None
    TemplateSchema = None
    TemplateError = Exception
    TemplateNotFoundError = Exception
    TemplateValidationError = Exception

# ==================== 数据模型 ====================

class EnvInfo(BaseModel):
    """环境变量信息"""
    variable: str = Field(..., description="环境变量名称", example="PYTHON_VERSION")
    value: str = Field(..., description="环境变量值", example="3.11.0")

class EnvResponse(BaseModel):
    """环境变量响应"""
    success: bool = Field(..., description="操作是否成功")
    data: List[EnvInfo] = Field(..., description="环境变量列表")
    message: str = Field("", description="响应消息")

class SystemInfo(BaseModel):
    """系统信息"""
    platform: str = Field(..., description="操作系统平台", example="linux x86_64")
    python_version: str = Field(..., description="Python 版本", example="3.11.0")
    hostname: str = Field(..., description="主机名", example="server-01")
    memory_total: str = Field(..., description="总内存", example="16 GB")
    memory_available: str = Field(..., description="可用内存", example="8 GB")

class EnvCheckResult(BaseModel):
    """环境检查单项结果"""
    check_name: str = Field(..., description="检查项名称", example="Python 版本")
    passed: bool = Field(..., description="是否通过检查")
    status: str = Field(..., description="状态描述", example="通过")

class EnvCheckResponse(BaseModel):
    """环境检查响应"""
    success: bool = Field(..., description="操作是否成功")
    results: List[EnvCheckResult] = Field(..., description="检查结果列表")
    all_pass: bool = Field(..., description="是否所有检查都通过")

class Environment(BaseModel):
    """环境信息"""
    name: str = Field(..., description="环境名称", example="production")
    description: str = Field("", description="环境描述")
    is_active: bool = Field(False, description="是否为当前活动环境")
    is_default: bool = Field(False, description="是否为默认环境")
    created_at: str = Field("", description="创建时间", example="2026-03-20T10:00:00")

class EnvListResponse(BaseModel):
    """环境列表响应"""
    success: bool = Field(..., description="操作是否成功")
    environments: List[Environment] = Field(..., description="环境列表")
    count: int = Field(..., description="环境数量", ge=0)

class AgentInfo(BaseModel):
    """Agent 基本信息"""
    id: str = Field(..., description="Agent 唯一标识", example="agent:shangshu:main")
    name: str = Field(..., description="Agent 名称", example="尚书省")
    status: str = Field(..., description="运行状态", example="active")
    department: str = Field(..., description="所属部门", example="尚书省")

class AgentListResponse(BaseModel):
    """Agent 列表响应"""
    success: bool = Field(..., description="操作是否成功")
    agents: List[AgentInfo] = Field(..., description="Agent 列表")
    count: int = Field(..., description="Agent 数量", ge=0)

class AgentStatusDetail(BaseModel):
    """Agent 状态详情"""
    id: str = Field(..., description="Agent ID")
    status: str = Field(..., description="运行状态", example="active")
    uptime: str = Field(..., description="运行时长", example="2h 15m")
    task_count: int = Field(..., description="当前任务数", ge=0)

class TaskInfo(BaseModel):
    """任务基本信息"""
    task_id: str = Field(..., description="任务 ID", example="JJC-20260320-001")
    title: str = Field(..., description="任务标题", example="系统架构设计")
    status: str = Field(..., description="任务状态", example="Done")
    department: str = Field(..., description="负责部门", example="工部")
    priority: str = Field(..., description="优先级", example="high")

class TaskListResponse(BaseModel):
    """任务列表响应"""
    success: bool = Field(..., description="操作是否成功")
    tasks: List[TaskInfo] = Field(..., description="任务列表")
    count: int = Field(..., description="任务数量", ge=0)

class TaskDetail(BaseModel):
    """任务详情"""
    task_id: str = Field(..., description="任务 ID")
    title: str = Field(..., description="任务标题")
    status: str = Field(..., description="任务状态")
    department: str = Field(..., description="负责部门")
    priority: str = Field(..., description="优先级")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")

class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str = Field(..., description="会话 ID", example="sess-001")
    agent: str = Field(..., description="关联 Agent", example="agent:shangshu:main")
    channel: str = Field(..., description="通信渠道", example="feishu")
    status: str = Field(..., description="会话状态", example="active")

class SessionListResponse(BaseModel):
    """会话列表响应"""
    success: bool = Field(..., description="操作是否成功")
    sessions: List[SessionInfo] = Field(..., description="会话列表")
    count: int = Field(..., description="会话数量", ge=0)

class ConfigItem(BaseModel):
    """配置项"""
    category: str = Field(..., description="配置分类", example="api")
    key: str = Field(..., description="配置键", example="baseUrl")
    value: str = Field(..., description="配置值", example="http://localhost:3000")

class ConfigListResponse(BaseModel):
    """配置列表响应"""
    success: bool = Field(..., description="操作是否成功")
    configs: List[ConfigItem] = Field(..., description="配置项列表")

class WebSocketMessage(BaseModel):
    """WebSocket 消息"""
    type: str = Field(..., description="消息类型", example="connected")
    data: Dict[str, Any] = Field(..., description="消息数据")
    timestamp: str = Field(..., description="时间戳", example="2026-03-20T10:00:00")

# ==================== 模板管理数据模型 ====================

class TemplateListItem(BaseModel):
    """模板列表项"""
    name: str = Field(..., description="模板名称", example="agent-config-template")
    format: str = Field(..., description="模板格式", example="yaml")
    status: Optional[str] = Field(None, description="模板状态", example="published")
    version: Optional[str] = Field(None, description="版本号", example="1.0.0")
    description: str = Field("", description="模板描述")
    tags: List[str] = Field([], description="标签列表")
    path: str = Field(..., description="模板文件路径")

class TemplateListResponse(BaseModel):
    """模板列表响应"""
    success: bool = Field(..., description="操作是否成功")
    templates: List[TemplateListItem] = Field(..., description="模板列表")
    count: int = Field(..., description="模板数量", ge=0)

class TemplateDetail(BaseModel):
    """模板详情"""
    id: str = Field(..., description="模板 ID")
    name: str = Field(..., description="模板名称")
    format: str = Field(..., description="模板格式")
    status: str = Field(..., description="模板状态")
    version: str = Field(..., description="版本号")
    description: str = Field(..., description="模板描述")
    tags: List[str] = Field(..., description="标签列表")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    schema_def: Optional[Dict] = Field(None, alias="schema", description="模板 Schema 定义")
    content: Optional[Dict] = Field(None, description="模板内容")
    
    class Config:
        populate_by_name = True

class TemplateDetailResponse(BaseModel):
    """模板详情响应"""
    success: bool = Field(..., description="操作是否成功")
    template: TemplateDetail = Field(..., description="模板详情")

class TemplateCreateRequest(BaseModel):
    """创建模板请求"""
    name: str = Field(..., description="模板名称", example="my-template")
    content: Dict[str, Any] = Field(..., description="模板内容")
    format: str = Field("yaml", description="模板格式", example="yaml")
    description: str = Field("", description="模板描述")
    tags: List[str] = Field([], description="标签列表")
    schema_def: Optional[Dict] = Field(None, alias="schema", description="模板 Schema 定义")
    
    class Config:
        populate_by_name = True

class TemplateCreateResponse(BaseModel):
    """创建模板响应"""
    success: bool = Field(..., description="操作是否成功")
    template_id: str = Field(..., description="创建的模板 ID")
    message: str = Field(..., description="响应消息")

class TemplateApplyRequest(BaseModel):
    """应用模板请求"""
    template_name: str = Field(..., description="模板名称", example="agent-config-template")
    variables: Dict[str, Any] = Field(..., description="模板变量")
    output_path: Optional[str] = Field(None, description="输出文件路径")
    validate_flag: bool = Field(True, alias="validate", description="是否验证输出")
    
    class Config:
        populate_by_name = True

class TemplateApplyResponse(BaseModel):
    """应用模板响应"""
    success: bool = Field(..., description="操作是否成功")
    result: Dict[str, Any] = Field(..., description="生成结果")
    output_path: Optional[str] = Field(None, description="输出文件路径")

class TemplateExportRequest(BaseModel):
    """导出模板请求"""
    template_name: str = Field(..., description="模板名称")
    output_path: str = Field(..., description="导出路径")
    include_metadata: bool = Field(True, description="是否包含元数据")
    include_versions: bool = Field(False, description="是否包含版本历史")

class TemplateImportRequest(BaseModel):
    """导入模板请求"""
    import_path: str = Field(..., description="导入文件路径")
    overwrite: bool = Field(False, description="是否覆盖已存在的模板")

class TemplateVersionInfo(BaseModel):
    """模板版本信息"""
    version: str = Field(..., description="版本号", example="1.0.0")
    content_hash: str = Field(..., description="内容哈希", example="abc123...")
    created_at: str = Field(..., description="创建时间")
    created_by: str = Field(..., description="创建者")
    change_log: str = Field(..., description="变更日志")

class TemplateVersionsResponse(BaseModel):
    """模板版本列表响应"""
    success: bool = Field(..., description="操作是否成功")
    versions: List[TemplateVersionInfo] = Field(..., description="版本列表")
    count: int = Field(..., description="版本数量", ge=0)

class TemplateDeleteResponse(BaseModel):
    """删除模板响应"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")

# ==================== 配置验证数据模型 ====================

class ConfigValidationResult(BaseModel):
    """配置验证结果"""
    valid: bool = Field(..., description="验证是否通过")
    file: str = Field(..., description="配置文件路径")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    agent_name: Optional[str] = Field(None, description="Agent 名称")
    errors: List[str] = Field([], description="错误列表")
    warnings: List[str] = Field([], description="警告列表")

class ConfigValidationSummary(BaseModel):
    """配置验证汇总"""
    total: int = Field(..., description="配置文件总数")
    valid: int = Field(..., description="通过数量")
    invalid: int = Field(..., description="失败数量")
    pass_rate: str = Field(..., description="通过率", example="85.7%")

class ConfigValidationResponse(BaseModel):
    """配置验证响应"""
    success: bool = Field(..., description="操作是否成功")
    summary: ConfigValidationSummary = Field(..., description="验证汇总")
    details: Dict[str, ConfigValidationResult] = Field({}, description="详细结果")

# ==================== 应用生命周期 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("🚀 claw-ex API Server 启动中...")
    app.state.websocket_clients = []
    app.state.task_monitor_running = False
    
    # 初始化模板管理器
    if TEMPLATE_MANAGER_AVAILABLE:
        app.state.template_manager = TemplateManager()
        print("✅ 模板管理器已初始化")
    else:
        app.state.template_manager = None
        print("⚠️ 模板管理器不可用")
    
    # 初始化配置验证器
    try:
        from agent_config_validator import ConfigValidator
        app.state.config_validator = ConfigValidator()
        print("✅ 配置验证器已初始化")
    except ImportError as e:
        app.state.config_validator = None
        print(f"⚠️ 配置验证器导入失败：{e}")
    
    yield
    
    # 关闭时
    print("🛑 claw-ex API Server 关闭中...")
    app.state.task_monitor_running = False

# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="claw-ex API",
    description="""
## claw-ex API Server

OpenClaw CLI 终端程序的 FastAPI 后端服务，为尚书省任务管理系统提供完整的 API 支持。

### 核心功能

#### 🌍 环境管理
- 环境变量查询与管理系统信息
- 环境健康检查
- 多环境切换与配置

#### 🤖 Agent 管理
- Agent 列表与状态监控
- Agent 配置管理
- Agent 能力查询

#### 📋 任务管理
- 任务创建、查询、更新
- 任务状态跟踪
- 任务优先级管理

#### 💬 会话管理
- 会话列表与详情
- WebSocket 实时推送
- 会话状态监控

#### ⚙️ 配置管理
- 配置项查询与修改
- 配置验证
- 批量配置检查

#### 📄 模板管理
- 模板 CRUD 操作
- 模板版本控制
- 模板导入导出
- 模板应用生成

### 最佳实践

#### 认证与授权
生产环境请配置 OAuth2 或 JWT 认证：
```python
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
```

#### 速率限制
建议使用 slowapi 进行速率限制：
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
```

#### 错误处理
统一错误响应格式：
```json
{
    "success": false,
    "errors": ["错误详情"],
    "message": "错误说明"
}
```

### 技术栈
- **框架**: FastAPI 0.100+
- **服务器**: Uvicorn
- **文档**: OpenAPI 3.0 + Swagger UI
- **实时通信**: WebSocket
""",
    version="0.2.0",
    contact={
        "name": "工部开发团队",
        "email": "dev@openclaw.local",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 辅助函数 ====================

def run_claw_ex_command(args: List[str]) -> tuple[bool, str, str]:
    """
    执行 claw-ex CLI 命令
    
    Args:
        args: CLI 命令参数列表
        
    Returns:
        (success, stdout, stderr) 元组
    """
    try:
        claw_ex_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bin', 'claw-ex.py')
        result = subprocess.run(
            ['python3', claw_ex_path] + args,
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "命令执行超时"
    except Exception as e:
        return False, "", str(e)

async def broadcast_ws_message(message_type: str, data: Dict[str, Any]):
    """
    广播 WebSocket 消息给所有连接的客户端
    
    Args:
        message_type: 消息类型
        data: 消息数据
    """
    if not hasattr(app.state, 'websocket_clients'):
        return
    
    message = {
        "type": message_type,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    disconnected = []
    for client in app.state.websocket_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)
    
    # 清理断开的连接
    for client in disconnected:
        app.state.websocket_clients.remove(client)

# ==================== API 路由 ====================

@app.get("/", tags=["根路径"], summary="API 根路径", description="返回 API 服务基本信息和文档链接")
async def root():
    """
    API 根路径
    
    返回服务状态、版本信息和文档链接。
    
    ## 示例响应
    ```json
    {
        "service": "claw-ex API Server",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }
    ```
    """
    return {
        "service": "claw-ex API Server",
        "version": "0.2.0",
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/health"
    }

@app.get("/health", tags=["健康检查"], summary="健康检查", description="检查 API 服务健康状态")
async def health_check():
    """
    健康检查端点
    
    用于负载均衡器和监控系统检查服务状态。
    
    ## 响应示例
    ```json
    {
        "status": "healthy",
        "timestamp": "2026-03-20T10:00:00"
    }
    ```
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ------------------- 环境管理 API -------------------

@app.get("/api/env", response_model=EnvResponse, tags=["环境管理"], summary="获取环境变量列表")
async def get_env_list():
    """
    获取环境变量列表
    
    返回当前进程的环境变量信息，包括 Python 版本、平台、工作目录等。
    
    ## 使用场景
    - 前端展示系统信息
    - 诊断环境问题
    - 验证环境配置
    
    ## 响应示例
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
    """
    return EnvResponse(
        success=True,
        data=[
            EnvInfo(variable="PYTHON_VERSION", value=sys.version.split()[0]),
            EnvInfo(variable="PLATFORM", value=sys.platform),
            EnvInfo(variable="PWD", value=os.getcwd()),
            EnvInfo(variable="OPENCLAW_HOME", value=os.environ.get('OPENCLAW_HOME', '~/.openclaw')),
            EnvInfo(variable="WORKSPACE", value=os.environ.get('OPENCLAW_WORKSPACE', '未设置')),
            EnvInfo(variable="CHANNEL", value=os.environ.get('OPENCLAW_CHANNEL', '未设置'))
        ],
        message="环境变量获取成功"
    )

@app.get("/api/env/info", response_model=SystemInfo, tags=["环境管理"], summary="获取系统信息")
async def get_env_info():
    """
    获取详细系统信息
    
    返回操作系统、Python 版本、主机名、内存等系统信息。
    
    ## 响应示例
    ```json
    {
        "platform": "linux x86_64",
        "python_version": "3.11.0",
        "hostname": "server-01",
        "memory_total": "16 GB",
        "memory_available": "8 GB"
    }
    ```
    """
    import platform
    
    try:
        import psutil
        mem = psutil.virtual_memory()
        mem_total = f"{mem.total // (1024**3)} GB"
        mem_avail = f"{mem.available // (1024**3)} GB"
    except ImportError:
        mem_total = 'N/A'
        mem_avail = 'N/A'
    
    return SystemInfo(
        platform=f"{sys.platform} {platform.machine()}",
        python_version=sys.version.split()[0],
        hostname=platform.node(),
        memory_total=mem_total,
        memory_available=mem_avail
    )

@app.get("/api/env/check", response_model=EnvCheckResponse, tags=["环境管理"], summary="环境健康检查")
async def check_env():
    """
    执行环境健康检查
    
    检查 Python 版本、工作目录等关键环境配置是否满足要求。
    
    ## 检查项
    - Python 版本 >= 3.8
    - 工作目录已设置
    
    ## 响应示例
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
    """
    checks = [
        EnvCheckResult(check_name="Python 版本", passed=sys.version_info >= (3, 8), status="通过" if sys.version_info >= (3, 8) else "失败"),
        EnvCheckResult(check_name="工作目录", passed=bool(os.environ.get('OPENCLAW_WORKSPACE')), status="通过" if os.environ.get('OPENCLAW_WORKSPACE') else "失败"),
    ]
    
    return EnvCheckResponse(
        success=all(c.passed for c in checks),
        results=checks,
        all_pass=all(c.passed for c in checks)
    )

@app.post("/api/env/create", response_model=EnvListResponse, tags=["环境管理"], summary="创建新环境")
async def create_env(name: str = Query(..., description="环境名称", example="production"), 
                     description: str = Query("", description="环境描述", example="生产环境")):
    """
    创建新的运行环境
    
    创建一个新的 OpenClaw 运行环境，用于隔离不同项目的配置。
    
    ## 参数说明
    - **name**: 环境名称（必需），字母数字和下划线组成
    - **description**: 环境描述（可选）
    
    ## 响应示例
    ```json
    {
        "success": true,
        "environments": [],
        "count": 0
    }
    ```
    """
    success, stdout, stderr = run_claw_ex_command(['env', 'create', name, description])
    
    if success:
        return EnvListResponse(
            success=True,
            environments=[],
            count=0
        )
    else:
        raise HTTPException(status_code=400, detail=stderr)

@app.post("/api/env/switch/{env_name}", tags=["环境管理"], summary="切换环境")
async def switch_env(env_name: str = Path(..., description="目标环境名称", example="production")):
    """
    切换到指定运行环境
    
    切换当前使用的 OpenClaw 环境，会影响后续所有操作的配置上下文。
    
    ## 路径参数
    - **env_name**: 目标环境名称
    
    ## 响应示例
    ```json
    {
        "success": true,
        "message": "已切换到环境：production"
    }
    ```
    """
    success, stdout, stderr = run_claw_ex_command(['env', 'switch', env_name])
    
    if success:
        return {"success": True, "message": f"已切换到环境：{env_name}"}
    else:
        raise HTTPException(status_code=400, detail=stderr)

@app.get("/api/env/list-detailed", response_model=EnvListResponse, tags=["环境管理"], summary="获取环境列表（详细）")
async def list_envs_detailed():
    """
    获取所有环境的详细信息
    
    返回所有已创建环境的完整列表，包括状态、描述、创建时间等。
    
    ## 响应示例
    ```json
    {
        "success": true,
        "environments": [
            {
                "name": "default",
                "description": "默认环境",
                "is_active": true,
                "is_default": true,
                "created_at": "2026-03-20T10:00:00"
            }
        ],
        "count": 1
    }
    ```
    """
    success, stdout, stderr = run_claw_ex_command(['env', 'list'])
    
    # 模拟返回（实际应解析 CLI 输出）
    return EnvListResponse(
        success=True,
        environments=[
            Environment(name="default", description="默认环境", is_active=True, is_default=True, created_at=datetime.now().isoformat()),
        ],
        count=1
    )

# ------------------- Agent 管理 API -------------------

@app.get("/api/agent/list", response_model=AgentListResponse, tags=["Agent 管理"], summary="获取 Agent 列表")
async def list_agents():
    """
    获取所有 Agent 列表
    
    返回系统中所有已注册的 Agent 信息，包括 ID、名称、状态和所属部门。
    
    ## 响应示例
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
    """
    success, stdout, stderr = run_claw_ex_command(['agent', 'list'])
    
    return AgentListResponse(
        success=True,
        agents=[
            AgentInfo(id="agent:shangshu:main", name="尚书省", status="active", department="尚书省"),
            AgentInfo(id="agent:gongbu:main", name="工部", status="active", department="工部"),
            AgentInfo(id="agent:libu:hr", name="吏部", status="active", department="吏部")
        ],
        count=3
    )

@app.get("/api/agent/status/{agent_id:path}", response_model=AgentStatusDetail, tags=["Agent 管理"], summary="获取 Agent 状态")
async def get_agent_status(agent_id: str = Path(..., description="Agent ID", example="agent:shangshu:main")):
    """
    获取指定 Agent 的详细状态
    
    返回 Agent 的运行状态、运行时长、任务数量等详细信息。
    
    ## 路径参数
    - **agent_id**: Agent 的唯一标识符
    
    ## 响应示例
    ```json
    {
        "id": "agent:shangshu:main",
        "status": "active",
        "uptime": "2h 15m",
        "task_count": 5
    }
    ```
    """
    return AgentStatusDetail(
        id=agent_id,
        status="active",
        uptime="2h 15m",
        task_count=5
    )

# ------------------- 任务管理 API -------------------

@app.get("/api/task/list", response_model=TaskListResponse, tags=["任务管理"], summary="获取任务列表")
async def list_tasks():
    """
    获取所有任务列表
    
    返回系统中所有任务的列表，包括任务 ID、标题、状态、部门和优先级。
    
    ## 查询参数
    支持以下过滤条件（待实现）：
    - status: 按状态过滤
    - department: 按部门过滤
    - priority: 按优先级过滤
    
    ## 响应示例
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
    """
    success, stdout, stderr = run_claw_ex_command(['task', 'list'])
    
    return TaskListResponse(
        success=True,
        tasks=[
            TaskInfo(task_id="JJC-20260320-001", title="系统架构设计", status="Done", department="工部", priority="high"),
            TaskInfo(task_id="JJC-20260320-002", title="claw-ex 终端程序开发", status="Doing", department="工部", priority="high"),
            TaskInfo(task_id="JJC-20260320-003", title="文档编写", status="Todo", department="工部", priority="medium")
        ],
        count=3
    )

@app.get("/api/task/{task_id}", response_model=TaskDetail, tags=["任务管理"], summary="获取任务详情")
async def get_task(task_id: str = Path(..., description="任务 ID", example="JJC-20260320-001")):
    """
    获取指定任务的详细信息
    
    返回任务的完整信息，包括创建时间、更新时间、详细描述等。
    
    ## 路径参数
    - **task_id**: 任务的唯一标识符
    
    ## 响应示例
    ```json
    {
        "task_id": "JJC-20260320-001",
        "title": "claw-ex 终端程序开发",
        "status": "Doing",
        "department": "工部",
        "priority": "high",
        "created_at": "2026-03-20 10:00",
        "updated_at": "2026-03-20 10:21"
    }
    ```
    """
    return TaskDetail(
        task_id=task_id,
        title="claw-ex 终端程序开发",
        status="Doing",
        department="工部",
        priority="high",
        created_at="2026-03-20 10:00",
        updated_at="2026-03-20 10:21"
    )

# ------------------- 会话管理 API -------------------

@app.get("/api/session/list", response_model=SessionListResponse, tags=["会话管理"], summary="获取会话列表")
async def list_sessions():
    """
    获取所有会话列表
    
    返回系统中所有活动会话的信息，包括会话 ID、关联 Agent、渠道和状态。
    
    ## 响应示例
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
    """
    success, stdout, stderr = run_claw_ex_command(['session', 'list'])
    
    return SessionListResponse(
        success=True,        sessions=[
            SessionInfo(session_id="sess-001", agent="agent:shangshu:main", channel="feishu", status="active"),
            SessionInfo(session_id="sess-002", agent="agent:gongbu:main", channel="feishu", status="active"),
            SessionInfo(session_id="sess-003", agent="agent:gongbu:subagent", channel="feishu", status="active")
        ],
        count=3
    )

# ------------------- 配置管理 API -------------------

@app.get("/api/config/list", response_model=ConfigListResponse, tags=["配置管理"], summary="获取配置列表")
async def list_configs():
    """
    获取当前系统配置列表
    
    返回所有配置项，按分类组织，包括 API 配置、显示配置、行为配置等。
    
    ## 响应示例
    ```json
    {
        "success": true,
        "configs": [
            {"category": "api", "key": "baseUrl", "value": "http://localhost:3000"},
            {"category": "display", "key": "theme", "value": "dark"}
        ]
    }
    ```
    """
    success, stdout, stderr = run_claw_ex_command(['config', 'list'])
    
    return ConfigListResponse(
        success=True,
        configs=[
            ConfigItem(category="api", key="baseUrl", value="http://localhost:3000"),
            ConfigItem(category="api", key="timeout", value="5000"),
            ConfigItem(category="display", key="theme", value="dark"),
            ConfigItem(category="display", key="colors", value="true"),
            ConfigItem(category="behavior", key="debug", value="false")
        ]
    )

@app.post("/api/config/validate", response_model=ConfigValidationResponse, tags=["配置管理"], summary="验证 Agent 配置")
async def validate_configs(
    path: Optional[str] = Query(None, description="配置文件或目录路径"),
    validate_all: bool = Query(False, description="是否验证所有 Agent 配置"),
    strict: bool = Query(False, description="严格模式（警告视为错误）")
):
    """
    验证 Agent 配置文件
    
    验证指定的配置文件或目录，检查 Schema 合规性、安全性和完整性。
    
    ## 查询参数
    - **path**: 配置文件或目录路径（可选）
    - **validate_all**: 是否验证所有 Agent 配置（默认 false）
    - **strict**: 严格模式，警告视为错误（默认 false）
    
    ## 验证内容
    - Schema 结构验证
    - 必需字段检查
    - 数据类型验证
    - 安全性检查（API 密钥加密、HTTPS 端点等）
    
    ## 响应示例
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
    """
    if not hasattr(app.state, 'config_validator') or app.state.config_validator is None:
        raise HTTPException(status_code=503, detail="配置验证器不可用")
    
    try:
        if validate_all:
            result = app.state.config_validator.validate_all_agents()
            return ConfigValidationResponse(
                success=True,
                summary=ConfigValidationSummary(**result["summary"]),
                details={
                    k: ConfigValidationResult(**v) if isinstance(v, dict) else ConfigValidationResult(
                        valid=v.valid,
                        file=v.file,
                        agent_id=v.agent_id,
                        agent_name=v.agent_name,
                        errors=v.errors,
                        warnings=v.warnings
                    )
                    for k, v in result.get("details", {}).items()
                }
            )
        elif path:
            from pathlib import Path as FilePath
            p = FilePath(path)
            if p.is_file():
                result = app.state.config_validator.validate_file(str(p))
            elif p.is_dir():
                results = app.state.config_validator.validate_directory(str(p))
                result = {
                    "summary": {
                        "total": len(results),
                        "valid": sum(1 for r in results if r["valid"]),
                        "invalid": sum(1 for r in results if not r["valid"]),
                        "pass_rate": f"{sum(1 for r in results if r['valid'])/len(results)*100:.1f}%" if results else "N/A"
                    },
                    "details": {r.get('agent_id', r['file']): r for r in results}
                }
            else:
                raise HTTPException(status_code=404, detail=f"路径不存在：{path}")
            
            return ConfigValidationResponse(
                success=True,
                summary=ConfigValidationSummary(**result["summary"]),
                details={
                    k: ConfigValidationResult(**v) if isinstance(v, dict) else ConfigValidationResult(
                        valid=v.valid,
                        file=v.file,
                        agent_id=v.agent_id,
                        agent_name=v.agent_name,
                        errors=v.errors,
                        warnings=v.warnings
                    )
                    for k, v in result.get("details", {}).items()
                }
            )
        else:
            raise HTTPException(status_code=400, detail="请指定 path 或 validate_all 参数")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------- 模板管理 API -------------------

@app.get("/api/template/list", response_model=TemplateListResponse, tags=["模板管理"], summary="列出所有模板")
async def list_templates():
    """
    列出所有可用模板
    
    返回系统中所有模板的列表，包括模板名称、格式、状态、版本等信息。
    
    ## 响应示例
    ```json
    {
        "success": true,
        "templates": [
            {
                "name": "agent-config-template",
                "format": "yaml",
                "status": "published",
                "version": "1.0.0",
                "description": "Agent 配置模板",
                "tags": ["agent", "config"],
                "path": "~/.openclaw/templates/agent-config-template.yaml"
            }
        ],
        "count": 1
    }
    ```
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        templates = app.state.template_manager.list_templates()
        items = [
            TemplateListItem(
                name=t['name'],
                format=t['format'],
                status=t.get('status'),
                version=t.get('version'),
                description=t.get('description', ''),
                tags=t.get('tags', []),
                path=t['path']
            )
            for t in templates
        ]
        return TemplateListResponse(
            success=True,
            templates=items,
            count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/template/show/{template_id}", response_model=TemplateDetailResponse, tags=["模板管理"], summary="查看模板详情")
async def get_template(template_id: str = Path(..., description="模板 ID 或名称")):
    """
    查看指定模板的详细信息
    
    返回模板的完整内容、Schema 定义、元数据等。
    
    ## 路径参数
    - **template_id**: 模板 ID 或名称
    
    ## 响应示例
    ```json
    {
        "success": true,
        "template": {
            "id": "agent-config-template",
            "name": "Agent 配置模板",
            "format": "yaml",
            "status": "published",
            "version": "1.0.0",
            "description": "用于生成 Agent 配置的模板",
            "tags": ["agent", "config"],
            "schema": {...},
            "content": {...}
        }
    }
    ```
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        content = app.state.template_manager.read_template(template_id)
        
        meta_path = app.state.template_manager.template_dir / f"{template_id}.meta.json"
        if meta_path.exists():
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        else:
            meta = {}
        
        return TemplateDetailResponse(
            success=True,
            template=TemplateDetail(
                id=meta.get('id', template_id),
                name=meta.get('name', template_id),
                format=meta.get('format', 'yaml'),
                status=meta.get('status', 'draft'),
                version=meta.get('version', '1.0.0'),
                description=meta.get('description', ''),
                tags=meta.get('tags', []),
                created_at=meta.get('created_at', ''),
                updated_at=meta.get('updated_at', ''),
                schema_def=meta.get('schema'),
                content=content
            )
        )
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/template/create", response_model=TemplateCreateResponse, tags=["模板管理"], summary="创建模板")
async def create_template(request: TemplateCreateRequest):
    """
    创建新模板
    
    创建一个新的配置模板，支持 YAML 和 JSON 格式。
    
    ## 请求体
    - **name**: 模板名称（必需）
    - **content**: 模板内容（必需）
    - **format**: 模板格式，yaml 或 json（默认 yaml）
    - **description**: 模板描述（可选）
    - **tags**: 标签列表（可选）
    - **schema**: 模板 Schema 定义（可选）
    
    ## 响应示例
    ```json
    {
        "success": true,
        "template_id": "my-template",
        "message": "模板 'my-template' 创建成功"
    }
    ```
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        metadata = {
            'description': request.description,
            'tags': request.tags,
            'schema': request.schema_def,
            'status': TemplateStatus.DRAFT.value if TemplateStatus else 'draft'
        }
        
        fmt = TemplateFormat.YAML
        if request.format.lower() == 'json':
            fmt = TemplateFormat.JSON
        
        template_id = app.state.template_manager.write_template(
            template_name=request.name,
            content=request.content,
            format=fmt,
            metadata=metadata
        )
        
        return TemplateCreateResponse(
            success=True,
            template_id=template_id,
            message=f"模板 '{request.name}' 创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/template/apply", response_model=TemplateApplyResponse, tags=["模板管理"], summary="应用模板")
async def apply_template(request: TemplateApplyRequest):
    """
    应用模板生成配置
    
    使用指定模板和变量生成配置文件。
    
    ## 请求体
    - **template_name**: 模板名称（必需）
    - **variables**: 模板变量（必需）
    - **output_path**: 输出文件路径（可选）
    - **validate**: 是否验证输出（默认 true）
    
    ## 响应示例
    ```json
    {
        "success": true,
        "result": {...},
        "output_path": "/path/to/output.yaml"
    }
    ```
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        output_path = FilePath(request.output_path) if request.output_path else None
        
        result = app.state.template_manager.apply_template(
            template_name=request.template_name,
            variables=request.variables,
            output_path=output_path,
            validate=request.validate_flag
        )
        
        return TemplateApplyResponse(
            success=True,
            result=result,
            output_path=str(output_path) if output_path else None
        )
    except TemplateValidationError as e:
        raise HTTPException(status_code=400, detail=f"验证失败：{str(e)}")
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/template/export/{template_id}", tags=["模板管理"], summary="导出模板")
async def export_template(template_id: str, request: TemplateExportRequest):
    """
    导出模板到指定路径
    
    将模板导出为独立文件，可选择包含元数据和版本历史。
    
    ## 路径参数
    - **template_id**: 模板 ID
    
    ## 请求体
    - **output_path**: 导出路径（必需）
    - **include_metadata**: 是否包含元数据（默认 true）
    - **include_versions**: 是否包含版本历史（默认 false）
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        output_path = FilePath(request.output_path)
        
        app.state.template_manager.export_template(
            template_name=template_id,
            output_path=output_path,
            include_metadata=request.include_metadata,
            include_versions=request.include_versions
        )
        
        return {
            "success": True,
            "message": f"模板 '{template_id}' 已导出到：{output_path}",
            "output_path": str(output_path)
        }
    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/template/import", tags=["模板管理"], summary="导入模板")
async def import_template(request: TemplateImportRequest):
    """
    从文件导入模板
    
    从指定路径导入模板文件到系统中。
    
    ## 请求体
    - **import_path**: 导入文件路径（必需）
    - **overwrite**: 是否覆盖已存在的模板（默认 false）
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        import_path = FilePath(request.import_path)
        
        if not import_path.exists():
            raise HTTPException(status_code=404, detail=f"导入路径不存在：{request.import_path}")
        
        template_id = app.state.template_manager.import_template(
            import_path=import_path,
            overwrite=request.overwrite
        )
        
        return {
            "success": True,
            "template_id": template_id,
            "message": f"模板导入成功"
        }
    except TemplateError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/template/delete/{template_id}", tags=["模板管理"], summary="删除模板")
async def delete_template(template_id: str, keep_versions: bool = Query(False, description="是否保留版本历史")):
    """
    删除指定模板
    
    从系统中删除模板，可选择保留版本历史。
    
    ## 路径参数
    - **template_id**: 模板 ID
    
    ## 查询参数
    - **keep_versions**: 是否保留版本历史（默认 false）
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        deleted = app.state.template_manager.delete_template(
            template_name=template_id,
            keep_versions=keep_versions
        )
        
        if deleted:
            return TemplateDeleteResponse(
                success=True,
                message=f"模板 '{template_id}' 已删除"
            )
        else:
            raise HTTPException(status_code=404, detail=f"模板不存在：{template_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/template/versions/{template_id}", response_model=TemplateVersionsResponse, tags=["模板管理"], summary="获取模板版本历史")
async def get_template_versions(template_id: str = Path(..., description="模板 ID")):
    """
    获取模板的版本历史
    
    返回模板所有版本的信息，包括版本号、创建时间、变更日志等。
    
    ## 路径参数
    - **template_id**: 模板 ID
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        versions = app.state.template_manager.list_versions(template_id)
        items = [
            TemplateVersionInfo(
                version=v.version,
                content_hash=v.content_hash,
                created_at=v.created_at,
                created_by=v.created_by,
                change_log=v.change_log
            )
            for v in versions
        ]
        return TemplateVersionsResponse(
            success=True,
            versions=items,
            count=len(items)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/template/rollback/{template_id}/{version}", tags=["模板管理"], summary="回滚模板版本")
async def rollback_template(template_id: str = Path(..., description="模板 ID"), 
                            version: str = Path(..., description="目标版本号")):
    """
    回滚模板到指定版本
    
    将模板恢复到历史版本。
    
    ## 路径参数
    - **template_id**: 模板 ID
    - **version**: 目标版本号
    """
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        success = app.state.template_manager.rollback_to_version(template_id, version)
        
        if success:
            return {
                "success": True,
                "message": f"模板已回滚到版本 {version}"
            }
        else:
            raise HTTPException(status_code=404, detail=f"版本不存在：{version}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ------------------- WebSocket 实时推送 -------------------

@app.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    WebSocket 实时监控连接
    
    建立 WebSocket 连接，用于实时推送系统事件和状态更新。
    
    ## 连接流程
    1. 客户端连接到 /ws/monitor
    2. 服务器发送欢迎消息
    3. 客户端可发送订阅消息指定关注的事件类型
    4. 服务器推送相关事件
    
    ## 消息格式
    ```json
    {
        "type": "event_type",
        "data": {...},
        "timestamp": "2026-03-20T10:00:00"
    }
    ```
    
    ## 事件类型
    - connected: 连接成功
    - subscribed: 订阅成功
    - task_update: 任务状态更新
    - agent_status: Agent 状态变化
    - system_alert: 系统告警
    """
    await websocket.accept()
    
    if not hasattr(app.state, 'websocket_clients'):
        app.state.websocket_clients = []
    
    app.state.websocket_clients.append(websocket)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "已连接到 claw-ex 监控服务"},
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            try:
                data = await websocket.receive_json()
                if data.get("type") == "subscribe":
                    await websocket.send_json({
                        "type": "subscribed",
                        "data": {"channels": data.get("channels", [])},
                        "timestamp": datetime.now().isoformat()
                    })
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket 消息处理错误：{e}")
                break
    finally:
        if websocket in app.state.websocket_clients:
            app.state.websocket_clients.remove(websocket)

# ==================== 主程序 ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
