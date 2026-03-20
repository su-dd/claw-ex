#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
claw-ex API Server - FastAPI 后端服务
为 claw-ex Web UI 提供后端 API 支持
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
    variable: str
    value: str

class EnvResponse(BaseModel):
    success: bool
    data: List[EnvInfo]
    message: str = ""

class SystemInfo(BaseModel):
    platform: str
    python_version: str
    hostname: str
    memory_total: str
    memory_available: str

class EnvCheckResult(BaseModel):
    check_name: str
    passed: bool
    status: str

class EnvCheckResponse(BaseModel):
    success: bool
    results: List[EnvCheckResult]
    all_pass: bool

class Environment(BaseModel):
    name: str
    description: str = ""
    is_active: bool = False
    is_default: bool = False
    created_at: str = ""

class EnvListResponse(BaseModel):
    success: bool
    environments: List[Environment]
    count: int

class AgentInfo(BaseModel):
    id: str
    name: str
    status: str
    department: str

class AgentListResponse(BaseModel):
    success: bool
    agents: List[AgentInfo]
    count: int

class AgentStatusDetail(BaseModel):
    id: str
    status: str
    uptime: str
    task_count: int

class TaskInfo(BaseModel):
    task_id: str
    title: str
    status: str
    department: str
    priority: str

class TaskListResponse(BaseModel):
    success: bool
    tasks: List[TaskInfo]
    count: int

class TaskDetail(BaseModel):
    task_id: str
    title: str
    status: str
    department: str
    priority: str
    created_at: str
    updated_at: str

class SessionInfo(BaseModel):
    session_id: str
    agent: str
    channel: str
    status: str

class SessionListResponse(BaseModel):
    success: bool
    sessions: List[SessionInfo]
    count: int

class ConfigItem(BaseModel):
    category: str
    key: str
    value: str

class ConfigListResponse(BaseModel):
    success: bool
    configs: List[ConfigItem]

class WebSocketMessage(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: str

# ==================== 模板管理数据模型 ====================

class TemplateListItem(BaseModel):
    name: str
    format: str
    status: Optional[str] = None
    version: Optional[str] = None
    description: str = ""
    tags: List[str] = []
    path: str

class TemplateListResponse(BaseModel):
    success: bool
    templates: List[TemplateListItem]
    count: int

class TemplateDetail(BaseModel):
    id: str
    name: str
    format: str
    status: str
    version: str
    description: str
    tags: List[str]
    created_at: str
    updated_at: str
    schema_def: Optional[Dict] = Field(None, alias="schema")
    content: Optional[Dict] = None
    
    class Config:
        populate_by_name = True

class TemplateDetailResponse(BaseModel):
    success: bool
    template: TemplateDetail

class TemplateCreateRequest(BaseModel):
    name: str
    content: Dict[str, Any]
    format: str = "yaml"
    description: str = ""
    tags: List[str] = []
    schema_def: Optional[Dict] = Field(None, alias="schema")
    
    class Config:
        populate_by_name = True

class TemplateCreateResponse(BaseModel):
    success: bool
    template_id: str
    message: str

class TemplateApplyRequest(BaseModel):
    template_name: str
    variables: Dict[str, Any]
    output_path: Optional[str] = None
    validate_flag: bool = Field(True, alias="validate")
    
    class Config:
        populate_by_name = True

class TemplateApplyResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    output_path: Optional[str] = None

class TemplateExportRequest(BaseModel):
    template_name: str
    output_path: str
    include_metadata: bool = True
    include_versions: bool = False

class TemplateImportRequest(BaseModel):
    import_path: str
    overwrite: bool = False

class TemplateVersionInfo(BaseModel):
    version: str
    content_hash: str
    created_at: str
    created_by: str
    change_log: str

class TemplateVersionsResponse(BaseModel):
    success: bool
    versions: List[TemplateVersionInfo]
    count: int

class TemplateDeleteResponse(BaseModel):
    success: bool
    message: str

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
    
    yield
    
    # 关闭时
    print("🛑 claw-ex API Server 关闭中...")
    app.state.task_monitor_running = False

# ==================== FastAPI 应用 ====================

app = FastAPI(
    title="claw-ex API",
    description="OpenClaw CLI 终端程序的 FastAPI 后端服务",
    version="0.1.0",
    lifespan=lifespan
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
    """执行 claw-ex CLI 命令"""
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
    """广播 WebSocket 消息给所有连接的客户端"""
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

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "service": "claw-ex API Server",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# ------------------- 环境管理 API -------------------

@app.get("/api/env", response_model=EnvResponse)
async def get_env_list():
    """获取环境变量列表"""
    # 直接返回环境变量，不调用 CLI（避免模块依赖问题）
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

@app.get("/api/env/info", response_model=SystemInfo)
async def get_env_info():
    """获取系统信息"""
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

@app.get("/api/env/check", response_model=EnvCheckResponse)
async def check_env():
    """环境检查"""
    checks = [
        EnvCheckResult(check_name="Python 版本", passed=sys.version_info >= (3, 8), status="通过" if sys.version_info >= (3, 8) else "失败"),
        EnvCheckResult(check_name="工作目录", passed=bool(os.environ.get('OPENCLAW_WORKSPACE')), status="通过" if os.environ.get('OPENCLAW_WORKSPACE') else "失败"),
    ]
    
    return EnvCheckResponse(
        success=all(c.passed for c in checks),
        results=checks,
        all_pass=all(c.passed for c in checks)
    )

@app.post("/api/env/create", response_model=EnvListResponse)
async def create_env(name: str = Query(...), description: str = Query("")):
    """创建新环境"""
    success, stdout, stderr = run_claw_ex_command(['env', 'create', name, description])
    
    if success:
        return EnvListResponse(
            success=True,
            environments=[],
            count=0
        )
    else:
        raise HTTPException(status_code=400, detail=stderr)

@app.post("/api/env/switch/{env_name}")
async def switch_env(env_name: str):
    """切换环境"""
    success, stdout, stderr = run_claw_ex_command(['env', 'switch', env_name])
    
    if success:
        return {"success": True, "message": f"已切换到环境：{env_name}"}
    else:
        raise HTTPException(status_code=400, detail=stderr)

@app.get("/api/env/list-detailed", response_model=EnvListResponse)
async def list_envs_detailed():
    """获取环境列表（详细）"""
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

@app.get("/api/agent/list", response_model=AgentListResponse)
async def list_agents():
    """获取 Agent 列表"""
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

@app.get("/api/agent/status/{agent_id:path}", response_model=AgentStatusDetail)
async def get_agent_status(agent_id: str):
    """获取 Agent 状态"""
    return AgentStatusDetail(
        id=agent_id,
        status="active",
        uptime="2h 15m",
        task_count=5
    )

# ------------------- 任务管理 API -------------------

@app.get("/api/task/list", response_model=TaskListResponse)
async def list_tasks():
    """获取任务列表"""
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

@app.get("/api/task/{task_id}", response_model=TaskDetail)
async def get_task(task_id: str):
    """获取任务详情"""
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

@app.get("/api/session/list", response_model=SessionListResponse)
async def list_sessions():
    """获取会话列表"""
    success, stdout, stderr = run_claw_ex_command(['session', 'list'])
    
    return SessionListResponse(
        success=True,
        sessions=[
            SessionInfo(session_id="sess-001", agent="agent:shangshu:main", channel="feishu", status="active"),
            SessionInfo(session_id="sess-002", agent="agent:gongbu:main", channel="feishu", status="active"),
            SessionInfo(session_id="sess-003", agent="agent:gongbu:subagent", channel="feishu", status="active")
        ],
        count=3
    )

# ------------------- 配置管理 API -------------------

@app.get("/api/config/list", response_model=ConfigListResponse)
async def list_configs():
    """获取配置列表"""
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

# ------------------- 模板管理 API -------------------

@app.get("/api/template/list", response_model=TemplateListResponse)
async def list_templates():
    """列出所有模板"""
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

@app.get("/api/template/show/{template_id}", response_model=TemplateDetailResponse)
async def get_template(template_id: str = Path(..., description="模板 ID 或名称")):
    """查看模板详情"""
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        # 尝试读取模板
        content = app.state.template_manager.read_template(template_id)
        
        # 获取元数据
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

@app.post("/api/template/create", response_model=TemplateCreateResponse)
async def create_template(request: TemplateCreateRequest):
    """创建模板"""
    if not TEMPLATE_MANAGER_AVAILABLE or not app.state.template_manager:
        raise HTTPException(status_code=503, detail="模板管理器不可用")
    
    try:
        # 准备元数据
        metadata = {
            'description': request.description,
            'tags': request.tags,
            'schema': request.schema_def,
            'status': TemplateStatus.DRAFT.value if TemplateStatus else 'draft'
        }
        
        # 确定格式
        fmt = TemplateFormat.YAML
        if request.format.lower() == 'json':
            fmt = TemplateFormat.JSON
        
        # 写入模板
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

@app.post("/api/template/apply", response_model=TemplateApplyResponse)
async def apply_template(request: TemplateApplyRequest):
    """应用模板生成配置"""
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

@app.post("/api/template/export/{template_id}")
async def export_template(template_id: str, request: TemplateExportRequest):
    """导出模板"""
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

@app.post("/api/template/import")
async def import_template(request: TemplateImportRequest):
    """导入模板"""
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

@app.delete("/api/template/delete/{template_id}")
async def delete_template(template_id: str, keep_versions: bool = Query(False)):
    """删除模板"""
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

@app.get("/api/template/versions/{template_id}", response_model=TemplateVersionsResponse)
async def get_template_versions(template_id: str):
    """获取模板版本历史"""
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

@app.post("/api/template/rollback/{template_id}/{version}")
async def rollback_template(template_id: str, version: str):
    """回滚模板到指定版本"""
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
    """WebSocket 实时监控连接"""
    await websocket.accept()
    
    if not hasattr(app.state, 'websocket_clients'):
        app.state.websocket_clients = []
    
    app.state.websocket_clients.append(websocket)
    
    try:
        # 发送欢迎消息
        await websocket.send_json({
            "type": "connected",
            "data": {"message": "已连接到 claw-ex 监控服务"},
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持连接并监听客户端消息
        while True:
            try:
                data = await websocket.receive_json()
                # 处理客户端消息（如订阅特定事件）
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
