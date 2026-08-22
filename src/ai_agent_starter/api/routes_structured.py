"""结构化输出路由。"""

from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from ai_agent_starter.models.schemas import ChatMessage, ChatRole, CodeReviewResult
from ai_agent_starter.services.llm_client import get_llm_client

router = APIRouter(prefix="/api/structured", tags=["结构化输出"])


class CodeReviewHttpRequest(BaseModel):
    """HTTP 请求体：代码审查。"""

    code: str = Field(..., min_length=1, description="要审查的代码")
    language: str = Field(default="python", description="编程语言")


@router.post(
    "/code-review",
    response_model=CodeReviewResult,
    summary="代码审查（结构化输出）",
)
async def code_review(request: CodeReviewHttpRequest) -> CodeReviewResult:
    """对代码进行审查，返回结构化的审查结果。

    返回字段包括：总结、评分、问题列表（含严重程度/类别/行号/建议）、代码亮点。
    这是 W9-W16 旗舰项目的 API 雏形。
    """
    try:
        client = get_llm_client()
        return await client.code_review(request.code, request.language)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"代码审查失败: {e}")


class SmartChatRequest(BaseModel):
    """HTTP 请求体：智能路由对话。"""

    message: str = Field(..., min_length=1)
    model: str | None = Field(default=None, description="强制指定模型（跳过路由）")


class SmartChatResponse(BaseModel):
    """HTTP 响应：智能路由对话结果。"""

    model_used: str
    answer: str
    cost_usd: float
    total_tokens: int


@router.post(
    "/smart-chat",
    response_model=SmartChatResponse,
    summary="智能路由对话（降本增效演示）",
)
async def smart_chat(request: SmartChatRequest) -> SmartChatResponse:
    """自动判断问题复杂度，选择合适的模型。

    - 简单问题 → 便宜模型（deepseek-chat）
    - 复杂问题 → 强模型（deepseek-reasoner）
    """
    try:
        client = get_llm_client()
        resp = await client.smart_chat(request.message, model=request.model)
        return SmartChatResponse(
            model_used=resp.model,
            answer=resp.message.content or "",
            cost_usd=resp.cost_usd,
            total_tokens=resp.usage.total_tokens,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {e}")
