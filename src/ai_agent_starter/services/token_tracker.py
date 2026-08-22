"""Token 用量与成本追踪器。

学习点（W2）：
- 成本意识：Agent 应用的核心商业指标之一是 Token 成本
- 持久化：将用量数据写入 JSON 文件，重启不丢失
- 线程安全：使用 asyncio.Lock 保证并发写入安全
- 这是后续 Agent 可观测性平台的雏形（W13 会扩展为完整 Dashboard）
"""

from __future__ import annotations

import json
import asyncio
from datetime import datetime, date
from pathlib import Path
from typing import Any

from ai_agent_starter.config import get_settings
from ai_agent_starter.models.schemas import TokenUsage


class TokenTracker:
    """Token 用量追踪器：记录每次 LLM 调用的用量与成本，支持按日/按模型聚合。"""

    def __init__(self, storage_file: str | None = None) -> None:
        settings = get_settings()
        self.storage_file = Path(storage_file or settings.token_tracker_file)
        self._lock = asyncio.Lock()
        self._records: list[dict[str, Any]] = self._load()

    def _load(self) -> list[dict[str, Any]]:
        """从磁盘加载历史记录。"""
        if self.storage_file.exists():
            try:
                data = json.loads(self.storage_file.read_text(encoding="utf-8"))
                return data.get("records", [])
            except (json.JSONDecodeError, KeyError):
                return []
        return []

    async def _save(self) -> None:
        """持久化到磁盘（调用方需持有锁）。"""
        self.storage_file.write_text(
            json.dumps(
                {"records": self._records, "updated_at": datetime.now().isoformat()},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    async def record(
        self,
        model: str,
        usage: TokenUsage,
        cost_usd: float,
        endpoint: str = "unknown",
    ) -> dict[str, Any]:
        """记录一次 LLM 调用。"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "date": date.today().isoformat(),
            "model": model,
            "endpoint": endpoint,
            "prompt_tokens": usage.prompt_tokens,
            "completion_tokens": usage.completion_tokens,
            "total_tokens": usage.total_tokens,
            "cost_usd": round(cost_usd, 6),
        }
        async with self._lock:
            self._records.append(record)
            await self._save()
        return record

    def get_summary(self) -> dict[str, Any]:
        """获取汇总统计。"""
        if not self._records:
            return {
                "total_calls": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "by_model": {},
                "by_date": {},
            }

        total_tokens = sum(r["total_tokens"] for r in self._records)
        total_cost = sum(r["cost_usd"] for r in self._records)

        by_model: dict[str, dict[str, Any]] = {}
        by_date: dict[str, dict[str, Any]] = {}

        for r in self._records:
            # 按模型聚合
            m = r["model"]
            if m not in by_model:
                by_model[m] = {
                    "calls": 0,
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                }
            by_model[m]["calls"] += 1
            by_model[m]["prompt_tokens"] += r["prompt_tokens"]
            by_model[m]["completion_tokens"] += r["completion_tokens"]
            by_model[m]["total_tokens"] += r["total_tokens"]
            by_model[m]["cost_usd"] = round(
                by_model[m]["cost_usd"] + r["cost_usd"], 6
            )

            # 按日期聚合
            d = r["date"]
            if d not in by_date:
                by_date[d] = {"calls": 0, "total_tokens": 0, "cost_usd": 0.0}
            by_date[d]["calls"] += 1
            by_date[d]["total_tokens"] += r["total_tokens"]
            by_date[d]["cost_usd"] = round(by_date[d]["cost_usd"] + r["cost_usd"], 6)

        return {
            "total_calls": len(self._records),
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "by_model": by_model,
            "by_date": by_date,
        }

    def reset(self) -> None:
        """清空所有记录。"""
        self._records.clear()
        if self.storage_file.exists():
            self.storage_file.unlink()


# 全局单例
_tracker: TokenTracker | None = None


def get_token_tracker() -> TokenTracker:
    """获取全局 TokenTracker 单例。"""
    global _tracker
    if _tracker is None:
        _tracker = TokenTracker()
    return _tracker
