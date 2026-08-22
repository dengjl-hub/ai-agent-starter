"""Pydantic 数据模型 —— 请求 / 响应 / 业务实体的结构化定义。

学习点（W1）：
- Pydantic v2 的模型定义、字段校验、序列化
- 与 FastAPI 自动生成 OpenAPI 文档的联动
- 结构化输出（W2）：用 Pydantic 模型约束 LLM 输出格式
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================
#  基础对话模型
# ============================================================


class ChatRole(str, Enum):
    """对话角色。"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class ChatMessage(BaseModel):
    """一条对话消息。"""

    role: ChatRole
    content: str | None = Field(default=None, description="消息文本内容")
    name: str | None = Field(default=None, description="可选的消息发送者名称")
    tool_calls: list[dict[str, Any]] | None = Field(
        default=None, description="Assistant 的工具调用请求"
    )
    tool_call_id: str | None = Field(
        default=None, description="Tool 角色对应的工具调用 ID"
    )


class ChatRequest(BaseModel):
    """对话请求。"""

    messages: list[ChatMessage] = Field(
        ..., min_length=1, description="对话历史，至少一条消息"
    )
    model: str | None = Field(
        default=None, description="指定模型，不传则使用默认模型"
    )
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, ge=1, le=128000)
    stream: bool = Field(default=False, description="是否流式返回")


class ChatResponse(BaseModel):
    """对话响应。"""

    id: str = Field(description="本次请求唯一 ID")
    model: str = Field(description="实际使用的模型")
    message: ChatMessage
    usage: TokenUsage = Field(description="Token 用量")
    cost_usd: float = Field(description="本次请求成本（美元）")
    finish_reason: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================
#  Token 用量与成本
# ============================================================


class TokenUsage(BaseModel):
    """Token 用量统计。"""

    prompt_tokens: int = Field(default=0, description="输入 token 数")
    completion_tokens: int = Field(default=0, description="输出 token 数")
    total_tokens: int = Field(default=0, description="总 token 数")


# ============================================================
#  Function Calling 模型
# ============================================================


class ToolCallRequest(BaseModel):
    """带工具的对话请求。"""

    messages: list[ChatMessage] = Field(..., min_length=1)
    tools: list[str] | None = Field(
        default=None,
        description="启用的工具名称列表，不传则启用全部内置工具",
    )
    model: str | None = None
    max_turns: int = Field(
        default=5, ge=1, le=10, description="Agent 最大自动执行轮次"
    )


class ToolCallStep(BaseModel):
    """Agent 执行过程中的一步（用于展示推理链）。"""

    step: int
    type: str = Field(description="assistant_message / tool_call / tool_result")
    content: str | None = None
    tool_name: str | None = None
    tool_args: dict[str, Any] | None = None
    tool_result: Any | None = None


class ToolCallResponse(BaseModel):
    """带工具的对话响应。"""

    id: str
    model: str
    final_answer: str = Field(description="Agent 最终回答")
    steps: list[ToolCallStep] = Field(
        default_factory=list, description="完整执行步骤（可观测性）"
    )
    usage: TokenUsage
    cost_usd: float
    created_at: datetime = Field(default_factory=datetime.now)


# ============================================================
#  结构化输出模型（W2 重点）
# ============================================================


class Severity(str, Enum):
    """问题严重程度。"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class CodeIssue(BaseModel):
    """单个代码问题（用于代码审查场景的结构化输出）。"""

    severity: Severity = Field(description="严重程度")
    category: str = Field(
        description="问题类别：security / performance / style / bug / best_practice"
    )
    line: int | None = Field(default=None, description="问题所在行号")
    description: str = Field(description="问题描述")
    suggestion: str = Field(description="修复建议")
    code_snippet: str | None = Field(default=None, description="相关代码片段")


class CodeReviewResult(BaseModel):
    """代码审查结果（结构化输出的目标格式）。"""

    summary: str = Field(description="整体审查总结")
    score: int = Field(
        default=100, ge=0, le=100, description="代码质量评分（0-100）"
    )
    issues: list[CodeIssue] = Field(default_factory=list)
    positive_points: list[str] = Field(
        default_factory=list, description="代码亮点"
    )


# ============================================================
#  通用 API 响应
# ============================================================


class HealthResponse(BaseModel):
    """健康检查响应。"""

    status: str = "ok"
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """错误响应。"""

    error: str
    detail: str | None = None
