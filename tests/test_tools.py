"""工具模块测试（不需要 API Key）。"""

from __future__ import annotations

import pytest

from ai_agent_starter.services.tools import (
    TOOL_REGISTRY,
    calculator,
    execute_tool,
    get_current_time,
    get_system_info,
    get_tool_schemas,
)


class TestCalculator:
    def test_basic_addition(self):
        assert "= 5" in calculator("2+3")

    def test_complex_expression(self):
        result = calculator("(2+3)*4")
        assert "= 20" in result

    def test_power(self):
        result = calculator("2^10")
        assert "= 1024" in result

    def test_invalid_characters(self):
        result = calculator("__import__('os').system('ls')")
        assert "非法字符" in result

    def test_division_by_zero(self):
        result = calculator("1/0")
        assert "错误" in result or "Error" in result


class TestGetTime:
    def test_returns_time_string(self):
        result = get_current_time()
        assert "当前时间" in result
        assert "20" in result  # 年份


class TestGetSystemInfo:
    def test_returns_system_info(self):
        result = get_system_info()
        assert "Python" in result


class TestToolRegistry:
    def test_all_tools_have_schema(self):
        for name, tool in TOOL_REGISTRY.items():
            assert "schema" in tool
            assert "function" in tool
            assert tool["schema"]["function"]["name"] == name

    def test_get_tool_schemas_all(self):
        schemas = get_tool_schemas()
        assert len(schemas) == len(TOOL_REGISTRY)

    def test_get_tool_schemas_selected(self):
        schemas = get_tool_schemas(["calculator"])
        assert len(schemas) == 1
        assert schemas[0]["function"]["name"] == "calculator"

    def test_get_tool_schemas_unknown_ignored(self):
        schemas = get_tool_schemas(["calculator", "nonexistent"])
        assert len(schemas) == 1


@pytest.mark.asyncio
async def test_execute_unknown_tool():
    result = await execute_tool("nonexistent", {})
    assert "未知工具" in result


@pytest.mark.asyncio
async def test_execute_calculator_tool():
    result = await execute_tool("calculator", {"expression": "2+3"})
    assert "= 5" in result


@pytest.mark.asyncio
async def test_execute_tool_with_bad_args():
    result = await execute_tool("calculator", {"wrong_arg": "test"})
    assert "失败" in result or "错误" in result
