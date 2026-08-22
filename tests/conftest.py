"""pytest 共享 fixtures。"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# 在导入项目模块前设置测试环境变量，避免初始化时报错
os.environ.setdefault("LLM_API_KEY", "test-key-for-unit-tests")
os.environ.setdefault("LLM_BASE_URL", "https://api.test.example.com")
os.environ.setdefault("LLM_MODEL", "test-model")


@pytest.fixture
def mock_settings():
    """提供测试用配置。"""
    from ai_agent_starter.config import Settings

    return Settings(
        llm_api_key="test-key",
        llm_base_url="https://api.test.example.com",
        llm_model="test-model",
        llm_model_fast="test-fast",
        llm_model_smart="test-smart",
        token_tracker_file="/tmp/test_token_usage.json",
    )


@pytest.fixture
def mock_openai_completion():
    """构造一个模拟的 OpenAI ChatCompletion 响应。"""

    def _make(
        content: str = "你好，这是测试回复。",
        prompt_tokens: int = 50,
        completion_tokens: int = 20,
        tool_calls=None,
        finish_reason: str = "stop",
    ):
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
        completion.id = "test-completion-id"
        completion.choices = [choice]
        completion.usage = usage
        return completion

    return _make
