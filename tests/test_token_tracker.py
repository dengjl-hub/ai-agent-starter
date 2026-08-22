"""Token 追踪器测试。"""

from __future__ import annotations

import json
import os

import pytest

from ai_agent_starter.models.schemas import TokenUsage
from ai_agent_starter.services.token_tracker import TokenTracker


@pytest.fixture
def tracker(tmp_path):
    """每个测试用独立的临时文件。"""
    storage = tmp_path / "test_usage.json"
    return TokenTracker(storage_file=str(storage))


@pytest.mark.asyncio
async def test_record_and_summary(tracker):
    usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    await tracker.record("test-model", usage, cost_usd=0.001, endpoint="test")

    summary = tracker.get_summary()
    assert summary["total_calls"] == 1
    assert summary["total_tokens"] == 150
    assert summary["total_cost_usd"] == 0.001
    assert "test-model" in summary["by_model"]


@pytest.mark.asyncio
async def test_multiple_records(tracker):
    for i in range(3):
        usage = TokenUsage(
            prompt_tokens=10 * (i + 1),
            completion_tokens=5 * (i + 1),
            total_tokens=15 * (i + 1),
        )
        await tracker.record("model-a", usage, cost_usd=0.001 * (i + 1))

    summary = tracker.get_summary()
    assert summary["total_calls"] == 3
    assert summary["total_tokens"] == 15 + 30 + 45
    assert summary["by_model"]["model-a"]["calls"] == 3


@pytest.mark.asyncio
async def test_persistence(tmp_path):
    """测试重启后数据不丢失。"""
    storage = tmp_path / "persist_test.json"

    t1 = TokenTracker(storage_file=str(storage))
    usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    await t1.record("model-x", usage, cost_usd=0.005)

    # 创建新实例，应从文件加载
    t2 = TokenTracker(storage_file=str(storage))
    summary = t2.get_summary()
    assert summary["total_calls"] == 1
    assert summary["total_tokens"] == 150


def test_empty_summary(tracker):
    summary = tracker.get_summary()
    assert summary["total_calls"] == 0
    assert summary["total_cost_usd"] == 0.0


def test_reset(tracker):
    # 先加一条记录（同步方式直接操作内部状态）
    tracker._records.append(
        {
            "timestamp": "2026-01-01T00:00:00",
            "date": "2026-01-01",
            "model": "test",
            "endpoint": "test",
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "cost_usd": 0.001,
        }
    )
    tracker.reset()
    assert tracker.get_summary()["total_calls"] == 0
