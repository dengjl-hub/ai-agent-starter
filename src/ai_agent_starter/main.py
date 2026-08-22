"""FastAPI 应用入口。

学习点（W1）：
- FastAPI 应用结构、路由注册、生命周期管理
- Pydantic 自动校验 + 自动生成 OpenAPI 文档
- 异步接口设计
- 健康检查、成本统计等运维接口

启动方式：
    uvicorn ai_agent_starter.main:app --reload --host 0.0.0.0 --port 8000
    或：python -m ai_agent_starter.main
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from ai_agent_starter import __version__
from ai_agent_starter.api.routes_chat import router as chat_router
from ai_agent_starter.api.routes_tools import router as tools_router
from ai_agent_starter.api.routes_structured import router as structured_router
from ai_agent_starter.models.schemas import HealthResponse
from ai_agent_starter.services.token_tracker import get_token_tracker


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期：启动和关闭时的钩子。"""
    # 启动时：初始化 Token 追踪器
    tracker = get_token_tracker()
    print(f"[启动] AI Agent Starter v{__version__}")
    print(f"[启动] Token 追踪器已加载，历史记录 {len(tracker._records)} 条")
    yield
    # 关闭时：可在这里做清理工作
    print("[关闭] 应用已停止")


app = FastAPI(
    title="AI Agent Starter",
    description=(
        "W1-W2 实战项目：Python 工程化 + 大模型 API 全栈基础\n\n"
        "- 基础对话（多轮、多模型切换、成本统计）\n"
        "- Function Calling（Agent 最小内核）\n"
        "- 结构化输出（代码审查）\n"
        "- 智能模型路由（降本增效）\n"
        "- Token 用量追踪\n\n"
        "启动后访问 /docs 查看交互式 API 文档。"
    ),
    version=__version__,
    lifespan=lifespan,
)

# 注册路由
app.include_router(chat_router)
app.include_router(tools_router)
app.include_router(structured_router)


@app.get("/", response_model=HealthResponse, tags=["系统"], summary="健康检查")
async def health() -> HealthResponse:
    """健康检查接口。"""
    return HealthResponse(version=__version__)


@app.get("/api/cost/summary", tags=["系统"], summary="Token 成本汇总")
async def cost_summary() -> dict:
    """查看 Token 用量与成本汇总。"""
    return get_token_tracker().get_summary()


if __name__ == "__main__":
    import uvicorn

    from ai_agent_starter.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "ai_agent_starter.main:app",
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.log_level,
        reload=True,
    )
