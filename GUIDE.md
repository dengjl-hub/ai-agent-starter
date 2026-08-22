# 操作指南：从零运行 AI Agent Starter

> 本指南覆盖 W1（Python 工程化）和 W2（大模型 API 实战）的全部内容。
> 每一步都经过验证，按顺序执行即可跑通。

---

## 目录

1. [前置准备](#1-前置准备)
2. [环境搭建（三选一）](#2-环境搭建三选一)
   - 方案 A：本地环境（推荐，最快）
   - 方案 B：GitHub Codespaces（云端，零本地配置）
   - 方案 C：Docker
3. [获取 API Key](#3-获取-api-key推荐-deepseek)
4. [验证环境](#4-验证环境)
5. [运行单元测试](#5-运行单元测试不需要-api-key)
6. [启动 FastAPI 服务](#6-启动-fastapi-服务)
7. [运行示例脚本](#7-运行示例脚本需要-api-key)
8. [代码学习导读](#8-代码学习导读w1w2-知识点对照)
9. [课后练习](#9-课后练习)
10. [常见问题](#10-常见问题)

---

## 1. 前置准备

### 你需要什么

| 项 | 要求 | 说明 |
|----|------|------|
| Python | 3.11 或更高 | 检查命令：`python3 --version` |
| 网络 | 能访问大模型 API | DeepSeek 在国内可直连，无需梯子 |
| API Key | 至少一个 | DeepSeek 注册送 500 万 token，足够完成本项目 |
| 编辑器 | VS Code / PyCharm 任意 | 推荐 VS Code |

### 关于 Python 版本

本项目使用了 Python 3.11+ 的语法（如 `X | Y` 联合类型）。如果你的系统 Python 版本低于 3.11，有以下选择：

- **方案 A**：用 [uv](https://docs.astral.sh/uv/) 自动管理 Python 版本（推荐）
- **方案 B**：用 conda/miniconda 创建 3.12 环境
- **方案 C**：用 GitHub Codespaces（自带 Python 3.12）

检查当前版本：
```bash
python3 --version
# 如果输出 Python 3.11.x 或更高，直接进入下一步
```

---

## 2. 环境搭建（三选一）

### 方案 A：本地环境（推荐）

#### 步骤 1：安装 uv

uv 是 2025-2026 年最快的 Python 包管理器（Rust 编写，比 pip 快 10-100 倍），同时能管理 Python 版本。

**Linux / macOS：**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # 或 source ~/.zshrc
```

**Windows（PowerShell）：**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

验证安装：
```bash
uv --version
# 应输出 uv 0.x.x
```

#### 步骤 2：进入项目目录

```bash
cd ai-agent-starter
```

#### 步骤 3：创建虚拟环境并安装依赖

```bash
# 创建虚拟环境（uv 会自动下载合适的 Python 版本）
uv venv

# 激活虚拟环境
# Linux / macOS:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate

# 安装项目依赖（含开发依赖）
uv pip install -e ".[dev]"
```

> `[dev]` 会额外安装 pytest、ruff 等开发工具。
> `-e` 表示可编辑安装，修改源码后无需重新安装。

#### 步骤 4：验证安装

```bash
python -c "import fastapi; import openai; import pydantic; print('所有依赖安装成功')"
# 应输出：所有依赖安装成功
```

---

### 方案 B：GitHub Codespaces（云端，零本地配置）

如果你不想在本地装任何东西，可以用 GitHub Codespaces 在云端开发：

#### 步骤 1：创建 GitHub 仓库

1. 在 GitHub 上新建一个仓库（比如叫 `ai-agent-starter`）
2. 把本项目的所有文件上传到仓库

```bash
# 在项目目录下执行
git init
git add .
git commit -m "init: AI Agent Starter W1/W2"
git branch -M main
git remote add origin https://github.com/你的用户名/ai-agent-starter.git
git push -u origin main
```

#### 步骤 2：启动 Codespace

1. 在 GitHub 仓库页面，点击绿色的 **「Code」** 按钮
2. 切换到 **「Codespaces」** 标签
3. 点击 **「Create codespace on main」**
4. 等待 1-2 分钟，浏览器中会打开一个 VS Code 界面

项目已配置 `.devcontainer/devcontainer.json`，Codespace 启动时会自动：
- 使用 Python 3.12 环境
- 安装 uv 和所有依赖
- 转发 8000 端口

#### 步骤 3：完成安装

Codespace 启动后，在终端中执行：

```bash
uv pip install -e ".[dev]"
```

> GitHub Codespaces 每月免费额度：60 小时（2 核机型），足够学习使用。

---

### 方案 C：Docker

如果你熟悉 Docker，可以用容器运行：

```bash
# 构建镜像
docker build -f docker/Dockerfile -t ai-agent-starter .

# 运行容器（需要先创建 .env 文件）
cp .env.example .env
# 编辑 .env 填入 API Key

docker run -d \
  --name ai-agent \
  -p 8000:8000 \
  --env-file .env \
  -v $(pwd)/token_usage.json:/app/token_usage.json \
  ai-agent-starter

# 查看日志
docker logs -f ai-agent

# 进入容器运行示例
docker exec -it ai-agent bash
python examples/01_basic_chat.py
```

---

## 3. 获取 API Key（推荐 DeepSeek）

本项目推荐使用 DeepSeek，原因：
- 国内直连，无需梯子
- 价格极低（deepseek-chat 输入 ¥1/百万 token，约为 GPT-4o 的 1/100）
- 新用户注册送 500 万 token（足够完成本项目全部示例和测试）
- 完全兼容 OpenAI SDK

### 步骤

1. 打开 https://platform.deepseek.com/
2. 注册账号（手机号即可）
3. 登录后，左侧菜单点击 **「API Keys」**
4. 点击 **「创建 API Key」**，复制生成的 key（只显示一次，务必保存）
5. 在项目根目录创建 `.env` 文件：

```bash
cp .env.example .env
```

6. 编辑 `.env`，填入你的 Key：

```env
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=sk-你的key在这里
LLM_MODEL=deepseek-chat
```

### 备选：硅基流动（有免费模型）

如果不想花钱，可以用硅基流动的免费模型：

1. 打开 https://cloud.siliconflow.cn/ 注册
2. 在「密钥管理」中创建 API Key
3. `.env` 配置改为：

```env
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_API_KEY=sk-你的key
LLM_MODEL=Qwen/Qwen2.5-7B-Instruct
LLM_MODEL_FAST=Qwen/Qwen2.5-7B-Instruct
LLM_MODEL_SMART=Qwen/Qwen2.5-72B-Instruct
```

> 注意：免费模型能力较弱，Function Calling 和结构化输出可能不如 DeepSeek 稳定。
> 建议主要用 DeepSeek，硅基流动作为备选。

---

## 4. 验证环境

### 检查 1：Python 和依赖

```bash
python --version
# Python 3.11.x 或更高

python -c "from ai_agent_starter.main import app; print('FastAPI 应用加载成功')"
# 应输出：FastAPI 应用加载成功
```

### 检查 2：配置加载

```bash
python -c "
from ai_agent_starter.config import get_settings
s = get_settings()
print(f'Base URL: {s.llm_base_url}')
print(f'Model: {s.llm_model}')
print(f'API Key 已配置: {bool(s.llm_api_key)}')
"
```

应输出类似：
```
Base URL: https://api.deepseek.com
Model: deepseek-chat
API Key 已配置: True
```

如果 `API Key 已配置: False`，检查 `.env` 文件是否在项目根目录、Key 是否正确。

---

## 5. 运行单元测试（不需要 API Key）

单元测试全部使用 mock，**不消耗任何 API 额度**，可以放心运行：

```bash
# 运行全部测试
pytest -v

# 带覆盖率
pytest -v --cov=ai_agent_starter

# 只运行某个测试文件
pytest tests/test_tools.py -v
```

预期输出（全部通过）：
```
tests/test_config.py::test_settings_defaults PASSED
tests/test_config.py::test_settings_pricing PASSED
tests/test_config.py::test_settings_validation PASSED
tests/test_config.py::test_get_settings_cached PASSED
tests/test_tools.py::TestCalculator::test_basic_addition PASSED
...
========================= 20 passed in 0.5s =========================
```

**学习提示**：阅读 `tests/` 目录是理解代码行为的最快方式。每个测试用例都在告诉你"这个函数应该怎么用、输入输出是什么"。

---

## 6. 启动 FastAPI 服务

```bash
# 开发模式（热重载，修改代码自动重启）
uvicorn ai_agent_starter.main:app --reload --host 0.0.0.0 --port 8000
```

启动后你会看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

### 6.1 访问交互式 API 文档

打开浏览器访问：**http://localhost:8000/docs**

你会看到 Swagger UI 界面，列出所有 API 接口。可以直接在页面上测试：

1. 找到 **POST /api/chat**，点击 「Try it out」
2. 把 Request body 改为：
```json
{
  "messages": [
    {"role": "user", "content": "用一句话解释什么是微服务"}
  ]
}
```
3. 点击 「Execute」
4. 下方会显示响应，包含 LLM 回复、Token 用量和成本

### 6.2 用 curl 测试

```bash
# 基础对话
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "你好"}]}'

# Agent 工具调用
curl -X POST http://localhost:8000/api/agent/tool-call \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "帮我算 (123+456)*2 等于多少，顺便告诉我现在几点"}]
  }'

# 代码审查（结构化输出）
curl -X POST http://localhost:8000/api/structured/code-review \
  -H "Content-Type: application/json" \
  -d '{"code": "exec(input())", "language": "python"}'

# 智能路由（降本增效）
curl -X POST http://localhost:8000/api/structured/smart-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "解释一下 CAP 定理"}'

# 查看成本汇总
curl http://localhost:8000/api/cost/summary
```

### 6.3 健康检查

```bash
curl http://localhost:8000/
# {"status":"ok","version":"0.1.0",...}
```

---

## 7. 运行示例脚本（需要 API Key）

示例脚本在 `examples/` 目录下，按编号顺序学习。每个脚本都有详细注释。

> 运行前确保已激活虚拟环境并配置好 `.env`。

### 示例 01：基础对话

```bash
python examples/01_basic_chat.py
```

你将看到：
- 单轮对话（system + user）
- 多轮对话（带上下文记忆）
- Token 用量和成本统计

**学习重点**：
- `messages` 列表的 role 机制
- 多轮对话的上下文是怎么传递的（把历史消息全部带上）
- 每次调用的 Token 用量和成本

### 示例 02：Function Calling（Agent 最小内核）

```bash
python examples/02_function_calling.py
```

你将看到 Agent 自动完成以下任务：
- 数学计算（调用 calculator 工具）
- 查询时间（调用 get_current_time 工具）
- 查询天气（调用 get_weather 工具，访问外部 API）
- 组合问题（调用多个工具）
- 不需要工具的问题（直接回答）

**学习重点**：
- 观察 `steps` 输出，理解 Agent 的"思考→行动→观察"循环
- 这就是 LangGraph/AutoGen 等框架的底层原理
- 阅读 `llm_client.py` 的 `chat_with_tools` 方法，这是整个项目最重要的代码

### 示例 03：结构化输出

```bash
python examples/03_structured_output.py
```

你将看到：
- LLM 对一段有 bug 的代码进行审查
- 返回严格的 JSON 格式（含评分、问题列表、修复建议）
- 用 Rich 表格渲染结果

**学习重点**：
- `response_format` 的 JSON Object 模式生成结构化输出
- Pydantic 模型校验 LLM 返回
- 这是 W9-W16 旗舰项目（代码审查 Multi-Agent）的雏形

### 示例 04：Prompt Engineering 五种模式

```bash
python examples/04_prompt_patterns.py
```

你将看到 5 种核心 Prompt 模式的对比：
1. Role Prompting（角色设定）
2. Few-shot Prompting（少样本示例）
3. Chain of Thought（思维链）
4. Self-Consistency（自洽性，多次采样）
5. ReAct（推理+行动）

**学习重点**：
- 不同模式的适用场景
- ReAct 模式和 Function Calling 的关系

### 示例 05：成本控制

```bash
python examples/05_cost_control.py
```

你将看到：
- 模型路由：简单问题用便宜模型，复杂问题用强模型
- 按模型/按日期的成本汇总
- 8 种生产环境成本优化手段

**学习重点**：
- 降本增效是 Agent 落地的核心商业指标
- 面试时可以讲的成本优化话术

---

## 8. 代码学习导读（W1/W2 知识点对照）

建议按以下顺序阅读代码，每个文件都有详细注释：

### W1：Python 工程化

| 顺序 | 文件 | 学什么 |
|------|------|--------|
| 1 | `pyproject.toml` | 现代 Python 项目配置：依赖声明、构建系统、工具配置 |
| 2 | `config.py` | pydantic-settings：类型安全的配置管理，12-Factor 原则 |
| 3 | `models/schemas.py` | Pydantic v2 模型定义、字段校验、枚举、嵌套模型 |
| 4 | `main.py` | FastAPI 应用结构、路由注册、生命周期管理 |
| 5 | `api/routes_chat.py` | 最简单的 API 路由，理解请求/响应模型 |
| 6 | `tests/test_config.py` | pytest 基础：如何写测试、如何断言 |
| 7 | `tests/test_api.py` | FastAPI 测试：TestClient + mock |

### W2：大模型 API 实战

| 顺序 | 文件 | 学什么 |
|------|------|--------|
| 1 | `services/llm_client.py` → `chat()` | 最基础的 LLM 调用封装 |
| 2 | `services/token_tracker.py` | Token 用量追踪与持久化 |
| 3 | `services/tools.py` | Function Calling 工具定义与注册 |
| 4 | `services/llm_client.py` → `chat_with_tools()` | **核心**：Agent 多轮工具调用循环 |
| 5 | `services/llm_client.py` → `structured_chat()` | JSON Object + Pydantic 结构化输出 |
| 6 | `services/llm_client.py` → `smart_chat()` | 模型路由（降本增效） |
| 7 | `examples/04_prompt_patterns.py` | Prompt Engineering 模式 |
| 8 | `tests/test_llm_client.py` | 如何 mock LLM 调用做单元测试 |

### 关键代码：Agent 最小内核

`services/llm_client.py` 的 `chat_with_tools` 方法是整个项目最重要的 50 行代码。它的逻辑：

```
用户提问
  ↓
LLM 判断是否需要工具
  ├── 不需要 → 返回最终回答
  └── 需要 → 执行工具 → 把结果返回给 LLM → 回到判断
                                    （循环最多 max_turns 次）
```

理解了这个循环，你就理解了所有 Agent 框架的底层原理。LangGraph 本质上是把这个循环用"图"的方式编排，支持更复杂的分支、并行和人工介入。

---

## 9. 课后练习

完成上述内容后，尝试以下练习来巩固：

### W1 练习

1. **新增一个 API 接口**：在 `api/` 下新增 `routes_echo.py`，实现一个 POST `/api/echo` 接口，接收 `{"message": "xxx"}`，返回 `{"echo": "xxx", "length": 3}`。
2. **新增一个 Pydantic 模型**：在 `schemas.py` 中新增一个 `UserProfile` 模型（含 name、age、email 字段，加校验：age 必须 0-150，email 必须包含 @）。
3. **写测试**：为你新增的接口和模型写单元测试。

### W2 练习

1. **新增一个工具**：在 `tools.py` 中新增一个 `search_wikipedia` 工具，调用维基百科 API 搜索词条。注册到 `TOOL_REGISTRY`，然后用示例 02 测试。
2. **新增一个结构化输出场景**：定义一个 `MeetingMinutes` Pydantic 模型（会议纪要：主题、参会人、决议、待办事项列表），写一个 API 接口接收会议文本，返回结构化纪要。
3. **优化模型路由**：当前的 `smart_chat` 用 LLM 做分类器，尝试改为基于规则的路由（如检测问号数量、关键词匹配），对比成本和准确率。
4. **加预算控制**：在 `TokenTracker` 中增加日预算功能，当日花费超过阈值时拒绝调用并返回告警。

---

## 10. 常见问题

### Q1：启动时报错 "未配置 LLM_API_KEY"

确保你在项目根目录创建了 `.env` 文件（不是 `.env.example`），并且文件中填入了真实的 API Key。

```bash
# 确认 .env 文件存在
cat .env | grep LLM_API_KEY
# 应输出：LLM_API_KEY=sk-xxxx
```

### Q2：调用 API 时报 401 Unauthorized

- 检查 API Key 是否正确（有没有多余的空格或引号）
- 检查 Key 是否已过期/被删除
- DeepSeek 平台查看余额是否用完

### Q3：调用 API 时报连接超时

- DeepSeek 在国内可直连，如果超时检查网络
- 硅基流动偶尔不稳定，重试即可
- 可以在 `.env` 中增大 `REQUEST_TIMEOUT=120`

### Q4：pytest 报 "ModuleNotFoundError"

确保你在项目根目录下执行，并且已安装项目：
```bash
pip install -e ".[dev]"
# 或
uv pip install -e ".[dev]"
```

### Q5：天气工具查询失败

`get_weather` 使用 wttr.in 免费 API，该服务偶尔不稳定。如果失败不影响其他功能，可以：
- 稍后重试
- 或忽略这个工具，其他工具（计算器、时间）不依赖外部服务

### Q6：DeepSeek 的 deepseek-reasoner 模型返回很慢

这是正常的。reasoner 是推理模型，会先进行长链思考再输出，响应时间可能 10-30 秒。示例 05 中复杂问题会路由到它。如果不想等，可以在 `.env` 中把 `LLM_MODEL_SMART` 也设为 `deepseek-chat`。

### Q7：如何查看我花了多少钱？

```bash
# 通过 API 查看
curl http://localhost:8000/api/cost/summary

# 或直接查看记录文件
cat token_usage.json
```

DeepSeek 平台也可以查看官方用量统计。完成本项目全部示例大约消耗 50-100 万 token，费用约 ¥0.5-2。

### Q8：Windows 上 uv 安装后找不到命令

重启终端，或手动把 uv 添加到 PATH。默认安装路径是 `%USERPROFILE%\.local\bin`。

---

## 下一步

完成 W1/W2 后，你将进入：

- **W3-W4**：LangChain/LangGraph 基础 + 向量数据库与 RAG
- **W5-W8**：LangGraph 高级编排 + MCP 协议 + A2A 协议 + 长效记忆
- **W9-W16**：旗舰项目——AI 代码审查 Multi-Agent 平台

等你完成本项目并指示后，我会生成 W3-W4 的项目。
