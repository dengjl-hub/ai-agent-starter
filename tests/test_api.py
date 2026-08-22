"""FastAPI 接口测试 —— 使用 mock，不需要真实 API Key。"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# 确保在导入 app 前设置环境变量
os.environ.setdefault("LLM_API_KEY", "test-key-for-tests")


@pytest.fixture
def client():
    """创建测试客户端。"""
    # 重置全局单例，避免测试间状态污染
    import ai_agent_starter.services.llm_client as llm_module
    import ai_agent_starter.services.token_tracker as tracker_module

    llm_module._client = None
    tracker_module._tracker = None

    from ai_agent_starter.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_llm_response():
    """构造一个真实的 ChatResponse 对象用于 mock。"""
    from ai_agent_starter.models.schemas import ChatResponse, TokenUsage

    return ChatResponse(
        id="mock-id",
        model="test-model",
        message={"role": "assistant", "content": "这是测试回复"},
        usage=TokenUsage(prompt_tokens=50, completion_tokens=20, total_tokens=70),
        cost_usd=0.0001,
        finish_reason="stop",
    )


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data

    def test_openapi_docs_available(self, client):
        resp = client.get("/docs")
        assert resp.status_code == 200


class TestChatEndpoint:
    def test_chat_basic(self, client, mock_llm_response):
        with patch(
            "ai_agent_starter.services.llm_client.LLMClient.chat",
            new_callable=AsyncMock,
            return_value=mock_llm_response,
        ):
            resp = client.post(
                "/api/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "你好"}
                    ]
                },
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["message"]["content"] == "这是测试回复"
            assert data["usage"]["total_tokens"] == 70

    def test_chat_empty_messages_rejected(self, client):
        resp = client.post("/api/chat", json={"messages": []})
        assert resp.status_code == 422  # Pydantic 校验失败

    def test_chat_invalid_temperature(self, client):
        resp = client.post(
            "/api/chat",
            json={
                "messages": [{"role": "user", "content": "hi"}],
                "temperature": 3.0,
            },
        )
        assert resp.status_code == 422


class TestCostEndpoint:
    def test_cost_summary(self, client):
        resp = client.get("/api/cost/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_calls" in data
        assert "total_cost_usd" in data
        assert "by_model" in data


class TestStructuredEndpoint:
    def test_code_review_endpoint(self, client):
        """测试代码审查接口（mock LLM 调用）。"""
        from ai_agent_starter.models.schemas import (
            CodeIssue,
            CodeReviewResult,
            Severity,
        )

        mock_result = CodeReviewResult(
            summary="代码有几个问题",
            score=75,
            issues=[
                CodeIssue(
                    severity=Severity.HIGH,
                    category="security",
                    line=3,
                    description="SQL注入风险",
                    suggestion="使用参数化查询",
                )
            ],
            positive_points=["命名清晰"],
        )

        with patch(
            "ai_agent_starter.services.llm_client.LLMClient.code_review",
            new_callable=AsyncMock,
            return_value=mock_result,
        ):
            resp = client.post(
                "/api/structured/code-review",
                json={"code": "print('hello')", "language": "python"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["score"] == 75
            assert len(data["issues"]) == 1
            assert data["issues"][0]["category"] == "security"

    def test_smart_chat_endpoint(self, client, mock_llm_response):
        with patch(
            "ai_agent_starter.services.llm_client.LLMClient.smart_chat",
            new_callable=AsyncMock,
            return_value=mock_llm_response,
        ):
            resp = client.post(
                "/api/structured/smart-chat",
                json={"message": "你好"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert "model_used" in data
            assert "answer" in data
