# 🐾 claw-ex React UI

claw-ex 的 React 前端界面，基于 React 18 + Ant Design 5 + Vite 构建。

## 📋 技术栈

- **框架**: React 18
- **UI 组件库**: Ant Design 5.x
- **构建工具**: Vite 5.x
- **HTTP 客户端**: Axios
- **实时通信**: WebSocket (原生)
- **状态管理**: React Hooks (useState, useEffect, useContext)

## 🚀 快速开始

### 前置要求

- Node.js >= 18.x
- npm >= 9.x
- Python 3.8+ (后端 API)

### 安装依赖

```bash
cd /home/sul/.openclaw/workspace-gongbu/claw-ex/claw-ex-react-ui

# 安装前端依赖
npm install
```

### 启动服务

#### 方式 1：分别启动（推荐开发使用）

**终端 1 - 启动后端 API**:
```bash
cd /home/sul/.openclaw/workspace-gongbu/claw-ex/claw-ex-webui
python3 server.py
```

**终端 2 - 启动前端**:
```bash
cd /home/sul/.openclaw/workspace-gongbu/claw-ex/claw-ex-react-ui
npm run dev
```

#### 方式 2：使用启动脚本

```bash
./start.sh
```

### 访问地址

- **前端开发服务器**: http://localhost:5173
- **后端 API**: http://localhost:8000

## 📦 功能模块

### 1. 任务监控面板 (MonitorPanel)

**路径**: `/` 或点击左侧菜单"任务监控"

**功能**:
- ✅ 统计卡片：总会话数、活跃会话、Token 消耗、总成本
- ✅ 会话列表表格（支持状态标记）
- ✅ 实时监控模式（WebSocket 自动推送）
- ✅ 会话详情查看
- ✅ 自动轮询备份（WebSocket 不可用时）

**API 端点**:
- `GET /api/monitor/list` - 获取会话列表
- `GET /api/monitor/:id` - 获取会话详情
- `WebSocket /ws` - 实时更新推送

### 2. 环境管理 (EnvManager)

**路径**: `/env` 或点击左侧菜单"环境管理"

**功能**:
- ✅ 环境列表展示（当前/默认标记）
- ✅ 创建新环境
- ✅ 切换环境（带确认）
- ✅ 删除环境（带确认）
- ✅ 空状态处理

**API 端点**:
- `GET /api/env/list` - 列出环境
- `POST /api/env/create` - 创建环境
- `POST /api/env/switch` - 切换环境
- `DELETE /api/env/:name` - 删除环境
- `GET /api/env/:name` - 获取环境详情

### 3. Agent 配置管理 (AgentConfig)

**路径**: `/agent` 或点击左侧菜单"Agent 配置"

**功能**:
- ✅ Agent 列表（配置状态指示）
- ✅ 配置文件切换（models.json / auth-profiles.json）
- ✅ 配置树形展示
- ✅ 字段类型标记（🔒敏感 / ✏️可编辑 / 👁️只读）
- ✅ 敏感字段脱敏显示
- ✅ 配置验证功能
- ✅ 备份历史查看与恢复

**API 端点**:
- `GET /api/agent/list` - 列出 Agent
- `GET /api/agent/:name/config/:file` - 获取配置
- `PUT /api/agent/:name/config/:file` - 更新配置
- `POST /api/agent/:name/validate` - 验证配置
- `GET /api/agent/:name/backup` - 获取备份列表
- `POST /api/agent/:name/restore` - 恢复备份

### 4. 任务管理 (TaskManager)

**路径**: `/task` 或点击左侧菜单"任务管理"

**功能**:
- ✅ 任务列表（支持状态/部门筛选）
- ✅ 创建任务
- ✅ 任务详情查看
- ✅ 更新任务状态
- ✅ 优先级标记
- ✅ 删除任务

**API 端点**:
- `GET /api/task/list` - 获取任务列表
- `GET /api/task/:id` - 获取任务详情
- `POST /api/task/create` - 创建任务
- `PUT /api/task/:id` - 更新任务
- `DELETE /api/task/:id` - 删除任务

## 🗂 项目结构

```
claw-ex-react-ui/
├── src/
│   ├── main.jsx              # 应用入口
│   ├── App.jsx               # 根组件（含侧边栏导航）
│   ├── App.css               # 全局样式
│   ├── index.css             # 基础样式
│   ├── api/
│   │   └── index.js          # API 调用封装
│   ├── pages/
│   │   ├── MonitorPanel.jsx  # 监控面板
│   │   ├── EnvManager.jsx    # 环境管理
│   │   ├── AgentConfig.jsx   # Agent 配置
│   │   └── TaskManager.jsx   # 任务管理
│   ├── utils/
│   │   └── websocket.js      # WebSocket 管理
│   └── hooks/                # 自定义 Hooks（预留）
├── public/
├── index.html
├── package.json
├── vite.config.js
├── README.md
└── start.sh                  # 启动脚本
```

## 🔧 开发指南

### 前端开发

```bash
# 开发模式（热重载）
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview

# 代码检查
npm run lint
```

### API 调用示例

```javascript
import { envAPI, agentAPI, monitorAPI, taskAPI } from './api';

// 环境管理
const envs = await envAPI.list();
await envAPI.create('prod', '生产环境');
await envAPI.switch('dev');
await envAPI.delete('test');

// Agent 配置
const agents = await agentAPI.list();
const config = await agentAPI.getConfig('gongbu', 'models.json');
await agentAPI.updateConfig('gongbu', 'models.json', newData);
await agentAPI.validate('gongbu', 'models.json');

// 任务监控
const sessions = await monitorAPI.list();
const detail = await monitorAPI.detail('session-123');

// 任务管理
const tasks = await taskAPI.list({ status: 'doing' });
await taskAPI.create({ title: '新任务', department: 'gongbu' });
await taskAPI.update('task-123', { status: 'done' });
```

### WebSocket 使用

```javascript
import { getWebSocketManager } from './utils/websocket';

const ws = getWebSocketManager();

// 订阅会话更新
ws.on('event:session_update', (data) => {
  console.log('会话更新:', data);
});

// 连接
ws.connect();

// 断开
ws.disconnect();
```

## 🌐 生产部署

### 构建

```bash
npm run build
```

输出目录：`dist/`

### Nginx 配置示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/claw-ex-react-ui/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 🧪 API 测试

使用后端项目中的测试脚本：

```bash
cd ../claw-ex-webui
./api-test.sh
```

或手动测试：

```bash
# 环境管理
curl http://localhost:8000/api/env/list
curl -X POST http://localhost:8000/api/env/create -H "Content-Type: application/json" -d '{"name":"test","description":"测试环境"}'

# Agent 配置
curl http://localhost:8000/api/agent/list
curl http://localhost:8000/api/agent/gongbu/config/models.json

# 任务监控
curl http://localhost:8000/api/monitor/list
curl http://localhost:8000/api/task/list
```

## ⚠️ 注意事项

1. **后端依赖**: 本前端项目依赖 `claw-ex-webui/server.py` 提供后端 API，请先启动后端服务
2. **CORS**: 开发模式下已配置 CORS，生产环境请使用 Nginx 反向代理
3. **WebSocket**: 实时监控功能需要后端支持 WebSocket，如不可用会自动降级为轮询
4. **敏感信息**: Agent 配置中的敏感字段（key/secret/token 等）会自动脱敏且不可编辑

## 📝 后续优化

### 短期
- [ ] 添加用户认证/授权
- [ ] 完善表单验证
- [ ] 添加错误边界处理
- [ ] 优化加载状态

### 中期
- [ ] 添加日志查看功能
- [ ] 添加数据可视化图表（ECharts）
- [ ] 支持多语言（i18n）
- [ ] 添加快捷键支持

### 长期
- [ ] 移动端适配
- [ ] PWA 支持（离线使用）
- [ ] 主题定制
- [ ] 插件系统

## 📮 任务信息

- **任务 ID**: JJC-20260320-007
- **任务名称**: claw-ex 开发 React 前端界面
- **执行部门**: 工部
- **技术栈**: React 18 + Ant Design 5 + Vite
- **项目位置**: `/home/sul/.openclaw/workspace-gongbu/claw-ex/claw-ex-react-ui/`

---

工部尚书 敬上
2026-03-20
