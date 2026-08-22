"""配置模块测试。"""

from __future__ import annotations

from ai_agent_starter.config import Settings, get_settings


def test_settings_defaults(monkeypatch):
    """测试默认配置值（清除环境变量干扰）。"""
    for key in ["LLM_BASE_URL", "LLM_MODEL", "LLM_API_KEY"]:
        monkeypatch.delenv(key, raising=False)
    s = Settings(llm_api_key="test")
    assert s.llm_base_url == "https://api.deepseek.com"
    assert s.llm_model == "deepseek-chat"
    assert s.temperature == 0.7
    assert s.max_tokens == 2048
    assert s.app_port == 8000


def test_settings_pricing():
    """测试模型价格查询。"""
    s = Settings(llm_api_key="test")
    input_price, output_price = s.get_pricing("deepseek-chat")
    assert input_price == 0.27
    assert output_price == 1.10

    # 未知模型返回 0
    assert s.get_pricing("unknown-model") == (0.0, 0.0)


def test_settings_validation():
    """测试配置校验。"""
    import pytest
    from pydantic import ValidationError

    # temperature 超出范围应报错
    with pytest.raises(ValidationError):
        Settings(llm_api_key="test", temperature=3.0)

    # max_tokens 太小应报错
    with pytest.raises(ValidationError):
        Settings(llm_api_key="test", max_tokens=0)


def test_get_settings_cached():
    """测试 get_settings 是单例。"""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
