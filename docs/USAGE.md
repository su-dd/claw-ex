# claw-ex 使用文档

## 📦 快速开始

```bash
# 查看帮助
python3 claw-ex.py --help

# 查看版本
python3 claw-ex.py --version

# 禁用颜色输出 (适用于管道/日志)
python3 claw-ex.py --no-color task list
```

## 📋 命令详解

### 1. env - 环境管理

#### 列出所有环境
```bash
python3 claw-ex.py env list
```

输出示例:
```
📦 环境列表:

┌───────────────┬──────┬───────────────┬─────────────────────┐
│名称             │描述    │状态             │创建时间                 │
├───────────────┼──────┼───────────────┼─────────────────────┤
│dev            │开发环境  │★ 默认          │2026-03-20 11:39:13  │
│prod           │生产环境  │● 当前          │2026-03-20 11:39:15  │
└───────────────┴──────┴───────────────┴─────────────────────┘

共 2 个环境
```

状态标记:
- `● 当前` - 当前激活的环境
- `★ 默认` - 默认环境（启动时使用）

#### 创建新环境
```bash
python3 claw-ex.py env create <name> [description]
```

参数:
- `name` - 环境名称（必需），只能包含字母、数字、下划线和连字符
- `description` - 环境描述（可选）

示例:
```bash
# 创建开发环境
python3 claw-ex.py env create dev "开发环境"

# 创建测试环境
python3 claw-ex.py env create test

# 创建生产环境
python3 claw-ex.py env create prod "生产环境配置"
```

输出示例:
```
📦 创建环境：dev

✅ 环境 "dev" 创建成功

提示：使用 claw-ex env switch <name> 切换到新环境
```

#### 切换环境
```bash
python3 claw-ex.py env switch <name>
```

参数:
- `name` - 要切换到的环境名称

示例:
```bash
# 切换到生产环境
python3 claw-ex.py env switch prod

# 切换回开发环境
python3 claw-ex.py env switch dev
```

输出示例:
```
🔄 切换环境：prod

✅ 已从环境 "dev" 切换到 "prod"

┌──────┬─────────────────────┐
│属性    │值                    │
├──────┼─────────────────────┤
│环境名称  │prod                 │
│描述    │生产环境                 │
│创建时间  │2026-03-20 11:39:15  │
└──────┴─────────────────────┘
```

#### 显示系统信息
```bash
python3 claw-ex.py env info
```

#### 检查环境配置
```bash
python3 claw-ex.py env check
```

#### 环境配置文件

环境配置存储在 `~/.openclaw/envs/` 目录:

```
~/.openclaw/envs/
├── environments.json    # 环境索引（所有环境列表）
├── active_env.json      # 当前激活的环境
├── dev.json             # dev 环境配置
├── prod.json            # prod 环境配置
└── ...
```

环境配置文件格式:
```json
{
  "name": "dev",
  "description": "开发环境",
  "created_at": "2026-03-20T11:39:13.123456",
  "updated_at": "2026-03-20T11:39:13.123456",
  "variables": {
    "API_URL": "http://localhost:3000",
    "DEBUG": "true"
  }
}
```

### 2. agent - Agent 管理

#### 列出所有 Agent
```bash
python3 claw-ex.py agent list
```

输出示例:
```
🤖 Agent 列表:

┌─────────────────────┬─────┬────────┬─────┐
│ID                   │名称   │状态      │部门   │
├─────────────────────┼─────┼────────┼─────┤
│agent:shangshu:main  │尚书省  │active  │尚书省  │
│agent:gongbu:main    │工部   │active  │工部   │
└─────────────────────┴─────┴────────┴─────┘
```

#### 查看 Agent 状态
```bash
python3 claw-ex.py agent status <agent-id>
```

### 3. task - 任务管理

#### 列出所有任务
```bash
python3 claw-ex.py task list
```

输出示例:
```
📋 任务列表:

┌──────────────────┬────────────────┬───────┬────┬────────┐
│任务 ID             │标题              │状态     │部门  │优先级     │
├──────────────────┼────────────────┼───────┼────┼────────┤
│JJC-20260320-001  │系统架构设计          │Done   │工部  │high    │
│JJC-20260320-002  │claw-ex 终端程序开发  │Doing  │工部  │high    │
└──────────────────┴────────────────┴───────┴────┴────────┘
```

#### 查看任务详情
```bash
python3 claw-ex.py task show JJC-20260320-002
```

### 4. session - 会话管理

#### 列出所有会话
```bash
python3 claw-ex.py session list
```

### 5. config - 配置管理

#### 列出所有配置
```bash
python3 claw-ex.py config list
```

## 🎨 输出格式

### 表格输出 (默认)
所有列表命令默认使用表格格式，支持 Unicode 边框。

### 颜色支持
- 🟢 绿色：成功、活跃、完成
- 🟡 黄色：进行中、中等优先级
- 🔴 红色：高优先级、错误、失败
- 🔵 蓝色：标题、信息
- ⚪ 灰色：低优先级、非活跃

禁用颜色：`--no-color` 选项

## 📁 项目结构

```
claw-ex/
├── claw-ex.py          # 主程序 (Python 版本)
├── claw-ex.js          # 主程序 (Node.js 版本，需 Node 环境)
├── README.md           # 项目说明
├── USAGE.md            # 使用文档 (本文件)
└── package.json        # Node.js 配置 (可选)
```

## 🔧 扩展开发

### 添加新命令

1. 在 `COMMANDS` 字典中添加新命令:
```python
COMMANDS = {
    'newcmd': {
        'description': '新命令说明',
        'subcommands': {
            'sub1': function_handler
        }
    }
}
```

2. 实现命令处理函数:
```python
def cmd_newcmd_sub1():
    print(c_cyan('\n新命令输出\n'))
    # 实现逻辑
```

3. 在 `main()` 函数中添加参数处理逻辑

### 颜色工具

```python
from claw-ex import c_cyan, c_yellow, c_green, c_red, c_gray, c_bold

print(c_cyan('青色文本'))
print(c_green('成功消息'))
print(c_red('错误消息'))
```

### 表格工具

```python
from claw-ex import create_table

headers = ['列 1', '列 2', '列 3']
rows = [
    ['值 1', '值 2', '值 3'],
    ['值 4', '值 5', '值 6']
]
print(create_table(headers, rows))
```

## 🛠 技术细节

### 跨平台支持
- ✅ Linux (已测试)
- ✅ macOS (兼容)
- ✅ Windows (需要 Python 3.8+)

### 依赖
- Python 3.8+
- 无外部依赖 (使用标准库)

### 性能
- 启动时间：< 50ms
- 内存占用：< 10MB

## 📮 尚书省对接

当前版本为演示版本，使用模拟数据。对接真实 API 需要:

1. 实现 API 客户端模块
2. 添加认证机制
3. 替换模拟数据为 API 调用
4. 添加错误处理和重试逻辑

### API 接口规划

```python
# 任务 API
GET  /api/tasks          # 列出任务
GET  /api/tasks/{id}     # 获取任务详情
POST /api/tasks          # 创建任务
PATCH /api/tasks/{id}    # 更新任务

# Agent API
GET  /api/agents         # 列出 Agent
GET  /api/agents/{id}    # 获取 Agent 状态

# 会话 API
GET  /api/sessions       # 列出会话
DELETE /api/sessions/{id} # 关闭会话
```

## ❓ 常见问题

### Q: 颜色显示异常？
A: 使用 `--no-color` 选项禁用颜色，或检查终端是否支持 ANSI 颜色。

### Q: 如何集成到脚本？
A: 使用 `--no-color` 选项，配合管道使用:
```bash
python3 claw-ex.py --no-color task list | grep "Doing"
```

### Q: 如何自定义输出格式？
A: 修改 `create_table()` 函数或添加 JSON 输出选项。

## 📜 许可证

MIT License - 工部开发

---

**工部 · 尚书省任务管理工具**

版本：v0.2.0  
最后更新：2026-03-20

### 版本历史

- **v0.2.0** (2026-03-20) - 新增环境管理功能
  - ✨ 新增 `env create` 命令：创建新环境
  - ✨ 新增 `env switch` 命令：切换环境
  - ✨ 环境配置持久化存储
  - ✨ 增强 `env list` 显示环境状态

- **v0.1.0** (2026-03-20) - 初始版本
  - 基础命令：env list/info/check
  - Agent 管理、任务管理、会话管理
  - 表格输出、颜色支持
