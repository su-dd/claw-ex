#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
claw-ex API Server 集成测试
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# ==================== 基础端点测试 ====================

def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "claw-ex API Server"
    assert data["status"] == "running"

def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

# ==================== 环境管理 API 测试 ====================

def test_get_env_list():
    """测试获取环境变量列表"""
    response = client.get("/api/env")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)

def test_get_env_info():
    """测试获取系统信息"""
    response = client.get("/api/env/info")
    assert response.status_code == 200
    data = response.json()
    assert "platform" in data
    assert "python_version" in data
    assert "hostname" in data

def test_check_env():
    """测试环境检查"""
    response = client.get("/api/env/check")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "results" in data
    assert "all_pass" in data

def test_list_envs_detailed():
    """测试获取环境列表（详细）"""
    response = client.get("/api/env/list-detailed")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "environments" in data
    assert "count" in data

# ==================== Agent 管理 API 测试 ====================

def test_list_agents():
    """测试获取 Agent 列表"""
    response = client.get("/api/agent/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "agents" in data
    assert data["count"] == 3

def test_get_agent_status():
    """测试获取 Agent 状态"""
    response = client.get("/api/agent/status/agent:shangshu:main")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "status" in data
    assert data["id"] == "agent:shangshu:main"

# ==================== 任务管理 API 测试 ====================

def test_list_tasks():
    """测试获取任务列表"""
    response = client.get("/api/task/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "tasks" in data
    assert data["count"] == 3

def test_get_task():
    """测试获取任务详情"""
    response = client.get("/api/task/JJC-20260320-001")
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert "title" in data
    assert "status" in data

# ==================== 会话管理 API 测试 ====================

def test_list_sessions():
    """测试获取会话列表"""
    response = client.get("/api/session/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sessions" in data
    assert data["count"] == 3

# ==================== 配置管理 API 测试 ====================

def test_list_configs():
    """测试获取配置列表"""
    response = client.get("/api/config/list")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "configs" in data
    assert len(data["configs"]) > 0

# ==================== WebSocket 测试 ====================

def test_websocket_connection():
    """测试 WebSocket 连接"""
    from starlette.testclient import TestClient as StarletteTestClient
    
    # 使用支持 WebSocket 的测试客户端
    with StarletteTestClient(app) as test_client:
        with test_client.websocket_connect("/ws/monitor") as websocket:
            # 接收欢迎消息
            data = websocket.receive_json()
            assert data["type"] == "connected"
            assert "message" in data["data"]
            
            # 发送订阅消息
            websocket.send_json({
                "type": "subscribe",
                "channels": ["task", "agent"]
            })
            
            # 接收确认消息
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert "channels" in data["data"]

# ==================== 错误处理测试 ====================

def test_invalid_endpoint():
    """测试无效端点"""
    response = client.get("/api/invalid")
    assert response.status_code == 404

def test_method_not_allowed():
    """测试方法不允许"""
    response = client.post("/api/env")  # 应该是 GET
    assert response.status_code in [405, 422]

# ==================== 性能测试 ====================

def test_response_time():
    """测试响应时间"""
    import time
    
    start = time.time()
    response = client.get("/health")
    elapsed = time.time() - start
    
    assert response.status_code == 200
    assert elapsed < 1.0  # 响应时间应小于 1 秒

def test_concurrent_requests():
    """测试并发请求"""
    import concurrent.futures
    
    def make_request():
        return client.get("/health")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(10)]
        results = [f.result() for f in futures]
    
    assert all(r.status_code == 200 for r in results)

# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
