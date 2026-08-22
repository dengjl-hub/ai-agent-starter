# AI Agent Starter — W1/W2 实战项目

> Python 工程化 + 大模型 API 全栈基础：FastAPI + OpenAI 兼容 SDK + Function Calling + 结构化输出 + Token 成本控制

## 这是什么

这是职业规划学习计划中 **W1（Python 工程化）+ W2（大模型 API 实战）** 的配套项目。通过一个可运行的 FastAPI 服务和 5 个循序渐进的示例脚本，覆盖以下核心技能：

| 周次 | 技能点 | 对应代码 |
|------|--------|---------|
| W1 | FastAPI 异步 Web 框架 | `src/ai_agent_starter/api/`、`main.py` |
| W1 | Pydantic 数据校验与配置管理 | `models/schemas.py`、`config.py` |
| W1 | Python 项目结构与依赖管理（uv） | `pyproject.toml`、`src/` 布局 |
| W1 | 单元测试（pytest + mock） | `tests/` |
| W2 | OpenAI 兼容 SDK 多模型切换 | `services/llm_client.py` |
| W2 | Function Calling（Agent 最小内核） | `services/tools.py`、`llm_client.py` |
| W2 | 结构化输出（JSON Object + Pydantic） | `models/schemas.py`、`routes_structured.py` |
| W2 | Prompt Engineering 五种模式 | `examples/04_prompt_patterns.py` |
| W2 | Token 成本控制与模型路由 | `services/token_tracker.py`、`examples/05_cost_control.py` |

## 快速开始

```bash
# 1. 安装 uv（如果没有）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. 安装依赖
uv pip install -e ".[dev]"

# 3. 配置 API Key
cp .env.example .env
# 编辑 .env，填入你的 API Key（推荐 DeepSeek，新用户送 500 万 token）

# 4. 运行测试（不需要 API Key）
pytest -v

# 5. 启动服务
uvicorn ai_agent_starter.main:app --reload
# 打开 http://localhost:8000/docs 查看 API 文档

# 6. 运行示例（需要 API Key）
python examples/01_basic_chat.py
python examples/02_function_calling.py
```

**详细操作指南（含云平台环境搭建）请见 [GUIDE.md](./GUIDE.md)**

## 项目结构

```
ai-agent-starter/
├── GUIDE.md                          # 详细操作指南（从0开始，每步都有）
├── README.md
├── pyproject.toml                    # 项目配置与依赖（uv）
├── .env.example                      # 环境变量模板
├── .devcontainer/                    # GitHub Codespaces 云端开发配置
├── docker/                           # Docker 部署
├── src/ai_agent_starter/
│   ├── main.py                       # FastAPI 入口
│   ├── config.py                     # 配置管理（pydantic-settings）
│   ├── models/schemas.py             # Pydantic 数据模型
│   ├── api/
│   │   ├── routes_chat.py            # 基础对话 API
│   │   ├── routes_tools.py           # Function Calling API
│   │   └── routes_structured.py      # 结构化输出 API
│   └── services/
│       ├── llm_client.py             # LLM 客户端封装（核心）
│       ├── tools.py                  # 内置工具集
│       └── token_tracker.py          # Token 成本追踪
├── examples/
│   ├── 01_basic_chat.py              # 基础对话 + 多轮 + 成本统计
│   ├── 02_function_calling.py        # Agent 最小内核
│   ├── 03_structured_output.py       # 结构化输出（代码审查）
│   ├── 04_prompt_patterns.py         # Prompt 五种模式
│   └── 05_cost_control.py            # 成本控制与模型路由
└── tests/                            # 单元测试（可离线运行）
```

## 支持的大模型

本项目使用 OpenAI 兼容协议，一套代码切换所有主流模型：

| 提供商 | base_url | 推荐模型 | 成本 |
|--------|----------|---------|------|
| DeepSeek | `https://api.deepseek.com` | `deepseek-chat` | 输入 ¥1/百万token，极低 |
| 硅基流动 | `https://api.siliconflow.cn/v1` | `Qwen/Qwen2.5-7B-Instruct` | 免费额度 |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` | 较低 |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` | 有免费额度 |
| Kimi | `https://api.moonshot.cn/v1` | `moonshot-v1-8k` | 有免费额度 |
| 豆包 | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-pro` | 有免费额度 |

## API 接口一览

启动后访问 `/docs` 查看交互式文档：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 健康检查 |
| POST | `/api/chat` | 基础对话 |
| POST | `/api/agent/tool-call` | Agent 工具调用（多轮自动执行） |
| POST | `/api/structured/code-review` | 代码审查（结构化输出） |
| POST | `/api/structured/smart-chat` | 智能路由对话（降本增效） |
| GET | `/api/cost/summary` | Token 成本汇总 |

## 技术栈

- Python 3.11+
- FastAPI + Uvicorn（异步 Web）
- Pydantic v2（数据校验 + 结构化输出）
- OpenAI Python SDK v1+（大模型调用）
- uv（依赖管理，比 pip 快 10-100 倍）
- pytest + pytest-asyncio（测试）
- Ruff（代码检查）
"# ai-agent-starter" 
