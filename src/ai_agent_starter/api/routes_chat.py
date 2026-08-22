"""基础对话路由。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ai_agent_starter.models.schemas import ChatRequest, ChatResponse
from ai_agent_starter.services.llm_client import get_llm_client

router = APIRouter(prefix="/api/chat", tags=["对话"])


@router.post("", response_model=ChatResponse, summary="基础对话")
async def chat(request: ChatRequest) -> ChatResponse:
    """发送对话消息，获取 LLM 回复。

    - 支持多轮对话（传入 messages 列表）
    - 可指定模型、温度、max_tokens
    - 返回 Token 用量和成本
    """
    try:
        client = get_llm_client()
        return await client.chat(
            messages=request.messages,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM 调用失败: {e}")
