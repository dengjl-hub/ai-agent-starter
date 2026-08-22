"""大模型客户端封装 —— W2 的核心模块。

学习点：
1. OpenAI 兼容 SDK 的使用（一套代码切换 DeepSeek / 硅基流动 / OpenAI / 通义 / Kimi）
2. Function Calling 多轮执行循环（Agent 的最小内核）
3. 结构化输出（Structured Output / JSON Mode）
4. Token 成本实时计算与记录
5. 模型路由：根据问题复杂度选择不同价位的模型（降本增效）
6. 错误处理与重试

设计原则：
- 对上层屏蔽 SDK 细节，提供简洁的业务接口
- 每次调用都返回 usage 和 cost，让成本可见
- 支持同步和异步两种调用方式
"""

from __future__ import annotations

import json
import uuid
from typing import Any, TypeVar

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from pydantic import BaseModel, ValidationError

from ai_agent_starter.config import Settings, get_settings
from ai_agent_starter.models.schemas import (
    ChatMessage,
    ChatResponse,
    ChatRole,
    CodeReviewResult,
    TokenUsage,
    ToolCallRequest,
    ToolCallResponse,
    ToolCallStep,
)
from ai_agent_starter.services.token_tracker import get_token_tracker
from ai_agent_starter.services.tools import execute_tool, get_tool_schemas

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    """大模型客户端，封装 OpenAI 兼容 API 的常用操作。"""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        if not self.settings.llm_api_key:
            raise ValueError(
                "未配置 LLM_API_KEY！请复制 .env.example 为 .env 并填入 API Key。"
            )

        self.client = AsyncOpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url,
            timeout=self.settings.request_timeout,
        )
        self.tracker = get_token_tracker()

    # ============================================================
    #  内部工具方法
    # ============================================================

    def _calc_cost(self, model: str, usage: TokenUsage) -> float:
        """根据模型单价计算本次调用成本（美元）。"""
        input_price, output_price = self.settings.get_pricing(model)
        cost = (
            usage.prompt_tokens * input_price / 1_000_000
            + usage.completion_tokens * output_price / 1_000_000
        )
        return round(cost, 6)

    @staticmethod
    def _parse_usage(completion: ChatCompletion) -> TokenUsage:
        """从 SDK 响应中提取 Token 用量。"""
        u = completion.usage
        if u is None:
            return TokenUsage()
        return TokenUsage(
            prompt_tokens=u.prompt_tokens,
            completion_tokens=u.completion_tokens,
            total_tokens=u.total_tokens,
        )

    @staticmethod
    def _to_sdk_messages(messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """将内部消息模型转换为 SDK 所需的 dict 格式。"""
        result = []
        for msg in messages:
            m: dict[str, Any] = {"role": msg.role.value}
            if msg.content is not None:
                m["content"] = msg.content
            if msg.name is not None:
                m["name"] = msg.name
            if msg.tool_calls is not None:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id is not None:
                m["tool_call_id"] = msg.tool_call_id
            result.append(m)
        return result

    # ============================================================
    #  1. 基础对话
    # ============================================================

    async def chat(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        endpoint: str = "chat",
    ) -> ChatResponse:
        """基础对话接口。

        Args:
            messages: 对话历史
            model: 指定模型，None 则用默认模型
            temperature: 温度参数
            max_tokens: 最大输出 token
            endpoint: 调用来源标识（用于成本统计分类）
        """
        use_model = model or self.settings.llm_model
        sdk_messages = self._to_sdk_messages(messages)

        completion = await self.client.chat.completions.create(
            model=use_model,
            messages=sdk_messages,
            temperature=temperature
            if temperature is not None
            else self.settings.temperature,
            max_tokens=max_tokens or self.settings.max_tokens,
        )

        usage = self._parse_usage(completion)
        cost = self._calc_cost(use_model, usage)
        await self.tracker.record(use_model, usage, cost, endpoint=endpoint)

        choice = completion.choices[0]
        return ChatResponse(
            id=completion.id or str(uuid.uuid4()),
            model=use_model,
            message=ChatMessage(
                role=ChatRole.ASSISTANT,
                content=choice.message.content or "",
            ),
            usage=usage,
            cost_usd=cost,
            finish_reason=choice.finish_reason,
        )

    # ============================================================
    #  2. Function Calling（Agent 最小内核）
    # ============================================================

    async def chat_with_tools(
        self,
        request: ToolCallRequest,
    ) -> ToolCallResponse:
        """带工具调用的多轮对话 —— 这就是 Agent 的最小内核。

        执行流程：
        1. 把用户消息 + 工具 schema 发给 LLM
        2. LLM 决定是否调用工具
        3. 如果调用工具，执行工具并把结果返回给 LLM
        4. 重复 2-3，直到 LLM 给出最终回答或达到最大轮次

        这个循环是 LangGraph / AutoGen 等框架的底层原理，
        W5 学 LangGraph 时你会发现它本质上就是这个循环的图编排版本。
        """
        use_model = request.model or self.settings.llm_model
        tools = get_tool_schemas(request.tools)
        sdk_messages = self._to_sdk_messages(request.messages)

        steps: list[ToolCallStep] = []
        total_usage = TokenUsage()
        total_cost = 0.0
        step_count = 0
        response_id = str(uuid.uuid4())

        for turn in range(request.max_turns):
            step_count += 1

            # 调用 LLM（带工具定义）
            completion = await self.client.chat.completions.create(
                model=use_model,
                messages=sdk_messages,
                tools=tools if tools else None,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
            )

            usage = self._parse_usage(completion)
            cost = self._calc_cost(use_model, usage)
            total_usage.prompt_tokens += usage.prompt_tokens
            total_usage.completion_tokens += usage.completion_tokens
            total_usage.total_tokens += usage.total_tokens
            total_cost = round(total_cost + cost, 6)
            await self.tracker.record(
                use_model, usage, cost, endpoint="chat_with_tools"
            )

            if completion.id:
                response_id = completion.id

            choice = completion.choices[0]
            msg = choice.message

            # 情况 1：LLM 没有调用工具，给出了最终回答
            if not msg.tool_calls:
                steps.append(
                    ToolCallStep(
                        step=step_count,
                        type="assistant_message",
                        content=msg.content or "",
                    )
                )
                return ToolCallResponse(
                    id=response_id,
                    model=use_model,
                    final_answer=msg.content or "",
                    steps=steps,
                    usage=total_usage,
                    cost_usd=total_cost,
                )

            # 情况 2：LLM 请求调用工具
            # 先把 assistant 的工具调用请求加入消息历史
            sdk_messages.append(
                {
                    "role": "assistant",
                    "content": msg.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in msg.tool_calls
                    ],
                }
            )

            # 逐个执行工具调用
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                steps.append(
                    ToolCallStep(
                        step=step_count,
                        type="tool_call",
                        tool_name=tool_name,
                        tool_args=tool_args,
                    )
                )

                # 执行工具
                tool_result = await execute_tool(tool_name, tool_args)

                steps.append(
                    ToolCallStep(
                        step=step_count,
                        type="tool_result",
                        tool_name=tool_name,
                        tool_result=tool_result,
                    )
                )

                # 把工具结果加入消息历史
                sdk_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": tool_result,
                    }
                )

        # 达到最大轮次，强制返回
        return ToolCallResponse(
            id=response_id,
            model=use_model,
            final_answer="(达到最大执行轮次，以下是最后一次回复)\n"
            + (msg.content or ""),
            steps=steps,
            usage=total_usage,
            cost_usd=total_cost,
        )

    # ============================================================
    #  3. 结构化输出
    # ============================================================

    async def structured_chat(
        self,
        messages: list[ChatMessage],
        response_model: type[T],
        model: str | None = None,
        endpoint: str = "structured",
    ) -> T:
        """结构化输出：强制 LLM 返回符合 Pydantic 模型的 JSON。

        实现方式：使用 OpenAI 兼容接口的 JSON Object 模式，
        并用 Pydantic 校验返回结果。JSON Object 模式比 JSON Schema
        在不同兼容服务商上的支持更广。

        Args:
            response_model: Pydantic 模型类，定义期望的输出结构
        """
        use_model = model or self.settings.llm_model
        sdk_messages = self._to_sdk_messages(messages)

        request_messages = list(sdk_messages)
        for attempt in range(2):
            completion = await self.client.chat.completions.create(
                model=use_model,
                messages=request_messages,
                response_format={"type": "json_object"},
                temperature=0.1,  # 结构化输出用低温度更稳定
                max_tokens=self.settings.max_tokens,
            )

            usage = self._parse_usage(completion)
            cost = self._calc_cost(use_model, usage)
            await self.tracker.record(use_model, usage, cost, endpoint=endpoint)

            content = completion.choices[0].message.content or "{}"
            try:
                data = json.loads(content)
                return response_model.model_validate(data)
            except (json.JSONDecodeError, ValidationError) as error:
                if attempt == 1:
                    raise
                request_messages.extend(
                    [
                        {"role": "assistant", "content": content},
                        {
                            "role": "user",
                            "content": (
                                "上一次返回未通过结构校验。请只返回修正后的 JSON，"
                                f"确保完全符合要求。具体错误：{error}"
                            ),
                        },
                    ]
                )

    async def code_review(self, code: str, language: str = "python") -> CodeReviewResult:
        """代码审查（结构化输出的具体应用场景）。

        这是 W9-W16 旗舰项目的雏形：让 LLM 按结构化格式输出代码审查结果。
        """
        messages = [
            ChatMessage(
                role=ChatRole.SYSTEM,
                content=(
                    "你是一位资深代码审查专家。请对用户提供的代码进行严格审查，"
                    "从安全性、性能、代码风格、潜在bug、最佳实践等维度找出问题。"
                    "务必返回结构化的 JSON 结果。每个 issues 元素必须包含 severity、"
                    "category、line、description、suggestion、code_snippet；category "
                    "只能是 security、performance、style、bug 或 best_practice。"
                ),
            ),
            ChatMessage(
                role=ChatRole.USER,
                content=f"请审查以下 {language} 代码：\n\n```{language}\n{code}\n```",
            ),
        ]
        return await self.structured_chat(
            messages, CodeReviewResult, endpoint="code_review"
        )

    # ============================================================
    #  4. 模型路由（降本增效）
    # ============================================================

    async def smart_chat(
        self,
        message: str,
        model: str | None = None,
        endpoint: str = "smart_chat",
    ) -> ChatResponse:
        """智能路由：先用便宜模型判断问题复杂度，再决定用哪个模型。

        降本增效的核心手段之一：
        - 简单问题（闲聊、事实查询）→ 便宜模型（deepseek-chat）
        - 复杂问题（推理、代码、分析）→ 强模型（deepseek-reasoner）

        实际生产中可以用更精细的路由策略（分类器模型、语义缓存等），
        这里演示最基础的思路。
        """
        # 如果手动指定了模型，直接使用
        if model:
            return await self.chat(
                [ChatMessage(role=ChatRole.USER, content=message)],
                model=model,
                endpoint=endpoint,
            )

        # 用便宜模型做路由判断
        router_messages = [
            ChatMessage(
                role=ChatRole.SYSTEM,
                content=(
                    "你是一个问题复杂度分类器。判断用户问题是 simple 还是 complex。\n"
                    "simple: 闲聊、简单事实查询、翻译、摘要、格式转换\n"
                    "complex: 数学推理、代码编写/审查、多步分析、创意写作、专业咨询\n"
                    "只回答 simple 或 complex，不要其他内容。"
                ),
            ),
            ChatMessage(role=ChatRole.USER, content=message),
        ]

        router_resp = await self.chat(
            router_messages,
            model=self.settings.llm_model_fast,
            temperature=0.0,
            max_tokens=10,
            endpoint="router",
        )

        decision = router_resp.message.content.strip().lower()
        use_model = (
            self.settings.llm_model_smart
            if "complex" in decision
            else self.settings.llm_model_fast
        )

        # 用选定的模型回答
        return await self.chat(
            [ChatMessage(role=ChatRole.USER, content=message)],
            model=use_model,
            endpoint=endpoint,
        )


# 全局单例
_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    """获取全局 LLMClient 单例。"""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
