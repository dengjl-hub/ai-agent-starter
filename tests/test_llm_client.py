"""LLMClient 单元测试 —— mock OpenAI SDK，不消耗真实 API 额度。"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ai_agent_starter.config import Settings
from ai_agent_starter.models.schemas import (
    ChatMessage,
    ChatRole,
    CodeReviewResult,
    TokenUsage,
    ToolCallRequest,
)
from ai_agent_starter.services.llm_client import LLMClient


@pytest.fixture
def client(tmp_path):
    """创建使用临时文件的 LLMClient。"""
    settings = Settings(
        llm_api_key="test-key",
        llm_base_url="https://api.test.example.com",
        llm_model="test-model",
        llm_model_fast="test-fast",
        llm_model_smart="test-smart",
        token_tracker_file=str(tmp_path / "test_usage.json"),
    )
    return LLMClient(settings=settings)


def make_mock_completion(
    content="测试回复",
    prompt_tokens=50,
    completion_tokens=20,
    tool_calls=None,
    finish_reason="stop",
):
    """构造 mock completion。"""
    usage = MagicMock()
    usage.prompt_tokens = prompt_tokens
    usage.completion_tokens = completion_tokens
    usage.total_tokens = prompt_tokens + completion_tokens

    message = MagicMock()
    message.content = content if not tool_calls else None
    message.tool_calls = tool_calls

    choice = MagicMock()
    choice.message = message
    choice.finish_reason = finish_reason

    completion = MagicMock()
    completion.id = "mock-id"
    completion.choices = [choice]
    completion.usage = usage
    return completion


class TestCostCalculation:
    def test_cost_calc_known_model(self, client):
        usage = TokenUsage(prompt_tokens=1_000_000, completion_tokens=1_000_000)
        cost = client._calc_cost("deepseek-chat", usage)
        # input: 0.27/M, output: 1.10/M
        assert cost == round(0.27 + 1.10, 6)

    def test_cost_calc_unknown_model(self, client):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=100)
        cost = client._calc_cost("unknown-model", usage)
        assert cost == 0.0


class TestChat:
    @pytest.mark.asyncio
    async def test_chat_basic(self, client):
        mock_completion = make_mock_completion(content="你好！")
        client.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        resp = await client.chat(
            messages=[ChatMessage(role=ChatRole.USER, content="你好")]
        )

        assert resp.message.content == "你好！"
        assert resp.usage.total_tokens == 70
        assert resp.model == "test-model"
        assert resp.cost_usd >= 0.0

    @pytest.mark.asyncio
    async def test_chat_with_system_message(self, client):
        mock_completion = make_mock_completion()
        client.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        resp = await client.chat(
            messages=[
                ChatMessage(role=ChatRole.SYSTEM, content="你是助手"),
                ChatMessage(role=ChatRole.USER, content="hi"),
            ]
        )
        assert resp.message.content == "测试回复"

        # 验证传给 SDK 的 messages 格式正确
        call_kwargs = client.client.chat.completions.create.call_args.kwargs
        sdk_messages = call_kwargs["messages"]
        assert sdk_messages[0]["role"] == "system"
        assert sdk_messages[1]["role"] == "user"


class TestChatWithTools:
    @pytest.mark.asyncio
    async def test_no_tool_call_needed(self, client):
        """LLM 直接回答，不调用工具。"""
        mock_completion = make_mock_completion(content="直接回答")
        client.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        resp = await client.chat_with_tools(
            ToolCallRequest(
                messages=[ChatMessage(role=ChatRole.USER, content="你好")]
            )
        )

        assert resp.final_answer == "直接回答"
        assert len(resp.steps) == 1
        assert resp.steps[0].type == "assistant_message"

    @pytest.mark.asyncio
    async def test_tool_call_executed(self, client):
        """LLM 调用 calculator 工具，然后给出最终回答。"""
        # 第一轮：LLM 请求调用工具
        tool_call = MagicMock()
        tool_call.id = "call_1"
        tool_call.function.name = "calculator"
        tool_call.function.arguments = json.dumps({"expression": "2+3"})

        first_completion = make_mock_completion(
            content=None,
            tool_calls=[tool_call],
            finish_reason="tool_calls",
        )

        # 第二轮：LLM 给出最终回答
        second_completion = make_mock_completion(
            content="2+3=5",
            prompt_tokens=80,
            completion_tokens=10,
        )

        client.client.chat.completions.create = AsyncMock(
            side_effect=[first_completion, second_completion]
        )

        resp = await client.chat_with_tools(
            ToolCallRequest(
                messages=[
                    ChatMessage(
                        role=ChatRole.USER, content="帮我算 2+3 等于多少"
                    )
                ]
            )
        )

        assert "5" in resp.final_answer
        # 应该有 tool_call 和 tool_result 步骤
        step_types = [s.type for s in resp.steps]
        assert "tool_call" in step_types
        assert "tool_result" in step_types

        # 验证工具确实被执行了
        tool_result_step = next(
            s for s in resp.steps if s.type == "tool_result"
        )
        assert "= 5" in tool_result_step.tool_result

    @pytest.mark.asyncio
    async def test_max_turns_reached(self, client):
        """达到最大轮次后应强制返回。"""
        # 每轮都请求调用工具，永不给出最终回答
        tool_call = MagicMock()
        tool_call.id = "call_1"
        tool_call.function.name = "get_current_time"
        tool_call.function.arguments = "{}"

        looping_completion = make_mock_completion(
            content=None,
            tool_calls=[tool_call],
            finish_reason="tool_calls",
        )

        client.client.chat.completions.create = AsyncMock(
            return_value=looping_completion
        )

        resp = await client.chat_with_tools(
            ToolCallRequest(
                messages=[
                    ChatMessage(role=ChatRole.USER, content="现在几点？")
                ],
                max_turns=2,
            )
        )

        # 应该执行了 2 轮
        assert len([s for s in resp.steps if s.type == "tool_call"]) == 2


class TestStructuredChat:
    def test_code_issue_category_defaults_when_omitted(self):
        issue = CodeReviewResult.model_validate(
            {
                "summary": "需要改进",
                "issues": [
                    {
                        "severity": "high",
                        "description": "存在问题",
                        "suggestion": "修复问题",
                    }
                ],
            }
        ).issues[0]

        assert issue.category == "best_practice"

    @pytest.mark.asyncio
    async def test_code_review_structured(self, client):
        """测试结构化输出解析。"""
        review_json = json.dumps(
            {
                "summary": "代码质量一般",
                "score": 60,
                "issues": [
                    {
                        "severity": "high",
                        "category": "security",
                        "line": 10,
                        "description": "SQL注入",
                        "suggestion": "参数化查询",
                        "code_snippet": None,
                    }
                ],
                "positive_points": ["结构清晰"],
            }
        )
        mock_completion = make_mock_completion(content=review_json)
        client.client.chat.completions.create = AsyncMock(return_value=mock_completion)

        result = await client.code_review("bad code here")

        assert isinstance(result, CodeReviewResult)
        assert result.score == 60
        assert len(result.issues) == 1
        assert result.issues[0].category == "security"

        call_kwargs = client.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_structured_chat_retries_invalid_response(self, client):
        invalid_json = json.dumps(
            {
                "summary": "需要改进",
                "score": 50,
                "issues": [{"severity": "high", "description": "缺少类别"}],
            }
        )
        valid_json = json.dumps(
            {
                "summary": "已修正",
                "score": 80,
                "issues": [
                    {
                        "severity": "high",
                        "category": "bug",
                        "description": "问题",
                        "suggestion": "修复",
                    }
                ],
            }
        )
        client.client.chat.completions.create = AsyncMock(
            side_effect=[
                make_mock_completion(content=invalid_json),
                make_mock_completion(content=valid_json),
            ]
        )

        result = await client.structured_chat(
            [ChatMessage(role=ChatRole.USER, content="返回审查结果")],
            CodeReviewResult,
        )

        assert result.score == 80
        assert client.client.chat.completions.create.await_count == 2
        retry_messages = client.client.chat.completions.create.call_args_list[1].kwargs[
            "messages"
        ]
        assert "未通过结构校验" in retry_messages[-1]["content"]


class TestMessageConversion:
    def test_to_sdk_messages(self, client):
        messages = [
            ChatMessage(role=ChatRole.SYSTEM, content="system prompt"),
            ChatMessage(role=ChatRole.USER, content="hello"),
            ChatMessage(
                role=ChatRole.ASSISTANT,
                content=None,
                tool_calls=[{"id": "1", "type": "function"}],
            ),
            ChatMessage(
                role=ChatRole.TOOL,
                content="result",
                tool_call_id="1",
            ),
        ]
        sdk_msgs = client._to_sdk_messages(messages)
        assert len(sdk_msgs) == 4
        assert sdk_msgs[0]["role"] == "system"
        assert sdk_msgs[2]["tool_calls"] == [{"id": "1", "type": "function"}]
        assert sdk_msgs[3]["tool_call_id"] == "1"
