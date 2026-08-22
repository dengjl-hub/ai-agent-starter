"""Function Calling 路由 —— Agent 最小内核的 HTTP 接口。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ai_agent_starter.models.schemas import ToolCallRequest, ToolCallResponse
from ai_agent_starter.services.llm_client import get_llm_client

router = APIRouter(prefix="/api/agent", tags=["Agent 工具调用"])


@router.post(
    "/tool-call",
    response_model=ToolCallResponse,
    summary="带工具调用的 Agent 对话",
)
async def tool_call(request: ToolCallRequest) -> ToolCallResponse:
    """Agent 自动判断是否需要调用工具，并执行多轮工具调用。

    内置工具：
    - calculator: 数学计算器
    - get_current_time: 获取当前时间
    - get_weather: 查询城市天气
    - get_system_info: 获取系统信息

    返回完整的执行步骤链（steps），可用于调试和可观测性。
    """
    try:
        client = get_llm_client()
        return await client.chat_with_tools(request)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent 执行失败: {e}")
