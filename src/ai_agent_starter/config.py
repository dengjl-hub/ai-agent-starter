"""应用配置模块 —— 使用 pydantic-settings 从环境变量 / .env 文件加载配置。

学习点（W1）：
- 12-Factor App 配置原则：配置与代码分离
- Pydantic BaseSettings 自动类型转换与校验
- 敏感信息（API Key）通过环境变量注入，不硬编码
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，所有字段均可通过环境变量或 .env 文件覆盖。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- 大模型配置 ----------
    llm_base_url: str = Field(
        default="https://api.deepseek.com",
        description="OpenAI 兼容的 API Base URL",
    )
    llm_api_key: str = Field(
        default="",
        description="API Key（从 .env 或环境变量读取，切勿硬编码）",
    )
    llm_model: str = Field(
        default="deepseek-chat",
        description="默认模型名称",
    )
    # 备用模型：用于模型路由演示
    llm_model_fast: str = Field(default="deepseek-chat", description="快速/便宜模型")
    llm_model_smart: str = Field(
        default="deepseek-reasoner", description="推理能力强的模型"
    )

    # ---------- 生成参数 ----------
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1, le=128000)
    request_timeout: float = Field(default=60.0, description="单次请求超时秒数")

    # ---------- 服务配置 ----------
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: Literal["debug", "info", "warning", "error"] = Field(default="info")

    # ---------- Token 成本统计 ----------
    token_tracker_file: str = Field(
        default="token_usage.json",
        description="Token 用量持久化文件路径",
    )

    # ---------- 各模型单价（美元 / 1M tokens，2026-08 参考价）----------
    # DeepSeek: https://api-docs.deepseek.com/quick_start/pricing
    # 注意：价格会变动，这里仅作学习演示，生产环境应从配置中心或 API 获取
    model_pricing: dict[str, dict[str, float]] = Field(
        default_factory=lambda: {
            "deepseek-chat": {"input": 0.27, "output": 1.10},
            "deepseek-reasoner": {"input": 0.55, "output": 2.19},
            "gpt-4o-mini": {"input": 0.15, "output": 0.60},
            "gpt-4o": {"input": 2.50, "output": 10.00},
            "Qwen/Qwen2.5-7B-Instruct": {"input": 0.0, "output": 0.0},
            "Qwen/Qwen2.5-72B-Instruct": {"input": 0.90, "output": 0.90},
        },
        description="各模型 input/output 单价（USD per 1M tokens）",
    )

    def get_pricing(self, model: str) -> tuple[float, float]:
        """获取指定模型的 (input_price, output_price)，未知模型返回 (0, 0)。"""
        pricing = self.model_pricing.get(model, {"input": 0.0, "output": 0.0})
        return pricing["input"], pricing["output"]


@lru_cache
def get_settings() -> Settings:
    """单例模式获取配置（lru_cache 保证全局唯一）。"""
    return Settings()
