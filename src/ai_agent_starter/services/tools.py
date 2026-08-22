"""内置 Function Calling 工具集。

学习点（W2）：
- Function Calling 的核心：把自然语言意图映射到确定性函数调用
- 工具定义遵循 OpenAI function calling schema（tools 参数）
- 每个工具包含：JSON Schema 描述 + Python 实现函数
- 工具应该是无副作用的只读操作（学习阶段），生产环境需加权限控制
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any

import httpx

# ============================================================
#  工具实现
# ============================================================


def calculator(expression: str) -> str:
    """安全的数学计算器 —— 只允许数字和基本运算符。

    为什么不用 eval？安全！eval 可以执行任意代码，生产环境绝对禁止。
    这里用白名单字符校验 + eval 的受限方式仅作演示，
    更严谨的做法是用 ast.literal_eval 或专门的表达式解析库。
    """
    allowed = set("0123456789+-*/().%^e ")
    if not all(c in allowed for c in expression):
        return f"错误：表达式包含非法字符: {expression}"
    try:
        # 将 ^ 替换为 **（幂运算）
        expression = expression.replace("^", "**")
        result = eval(expression, {"__builtins__": {}}, {"math": math})  # noqa: S307
        return f"计算结果: {expression} = {result}"
    except Exception as e:
        return f"计算错误: {e}"


def get_current_time() -> str:
    """获取当前日期和时间。"""
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S %A')}"


async def get_weather(city: str) -> str:
    """查询城市天气（使用 wttr.in 免费 API，无需 Key）。

    注意：这是一个异步工具，演示如何在 Function Calling 中调用外部 HTTP API。
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # wttr.in 返回简洁格式
            resp = await client.get(f"https://wttr.in/{city}?format=j1")
            resp.raise_for_status()
            data = resp.json()

            current = data.get("current_condition", [{}])[0]
            area = data.get("nearest_area", [{}])[0]
            city_name = area.get("areaName", [{}])[0].get("value", city)
            country = area.get("country", [{}])[0].get("value", "")

            temp_c = current.get("temp_C", "N/A")
            feels_like = current.get("FeelsLikeC", "N/A")
            humidity = current.get("humidity", "N/A")
            desc = current.get("weatherDesc", [{}])[0].get("value", "N/A")
            wind = current.get("windspeedKmph", "N/A")

            return (
                f"{city_name}, {country} 当前天气:\n"
                f"  天气: {desc}\n"
                f"  温度: {temp_c}°C（体感 {feels_like}°C）\n"
                f"  湿度: {humidity}%\n"
                f"  风速: {wind} km/h"
            )
    except httpx.HTTPStatusError as e:
        return f"天气查询失败: HTTP {e.response.status_code}"
    except Exception as e:
        return f"天气查询出错: {e}"


def get_system_info() -> str:
    """获取当前运行环境的系统信息（演示工具）。"""
    import platform
    import sys

    return (
        f"系统信息:\n"
        f"  OS: {platform.system()} {platform.release()}\n"
        f"  Python: {sys.version.split()[0]}\n"
        f"  机器: {platform.machine()}\n"
        f"  主机名: {platform.node()}"
    )


# ============================================================
#  工具注册表：工具名 -> (实现函数, OpenAI function schema)
# ============================================================

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "calculator": {
        "function": calculator,
        "is_async": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "calculator",
                "description": "数学计算器。输入数学表达式（如 '2+3*4'、'(1+2)^3'），返回计算结果。支持 +、-、*、/、%、^（幂）和括号。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "要计算的数学表达式，例如 '(1+2)*3^2'",
                        }
                    },
                    "required": ["expression"],
                },
            },
        },
    },
    "get_current_time": {
        "function": get_current_time,
        "is_async": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_current_time",
                "description": "获取当前的日期和时间。当用户询问'现在几点'、'今天日期'等时间相关问题时使用。",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    },
    "get_weather": {
        "function": get_weather,
        "is_async": True,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的当前天气情况，包括温度、湿度、天气状况、风速等。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，中文或英文均可，例如 '上海'、'Beijing'、'Shenzhen'",
                        }
                    },
                    "required": ["city"],
                },
            },
        },
    },
    "get_system_info": {
        "function": get_system_info,
        "is_async": False,
        "schema": {
            "type": "function",
            "function": {
                "name": "get_system_info",
                "description": "获取当前运行环境的系统信息，包括操作系统、Python版本、机器架构等。",
                "parameters": {"type": "object", "properties": {}},
            },
        },
    },
}


def get_tool_schemas(tool_names: list[str] | None = None) -> list[dict[str, Any]]:
    """获取指定工具的 OpenAI schema 列表。

    Args:
        tool_names: 工具名称列表，None 表示返回全部工具。
    """
    if tool_names is None:
        return [v["schema"] for v in TOOL_REGISTRY.values()]
    return [
        TOOL_REGISTRY[name]["schema"]
        for name in tool_names
        if name in TOOL_REGISTRY
    ]


async def execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """执行指定工具并返回结果字符串。

    支持同步和异步工具函数的统一调用。
    """
    if name not in TOOL_REGISTRY:
        return json.dumps({"error": f"未知工具: {name}"}, ensure_ascii=False)

    tool = TOOL_REGISTRY[name]
    func = tool["function"]

    try:
        if tool["is_async"]:
            result = await func(**arguments)
        else:
            result = func(**arguments)
        return str(result)
    except Exception as e:
        return json.dumps(
            {"error": f"工具 {name} 执行失败: {e}"}, ensure_ascii=False
        )
