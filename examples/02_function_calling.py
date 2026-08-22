"""示例 02：Function Calling —— Agent 的最小内核。

运行方式：
    python 02_function_calling.py

学习目标（W2）：
- 理解 Function Calling 的完整循环：LLM 决策 → 执行工具 → 返回结果 → LLM 总结
- 观察 Agent 的"推理链"（steps）
- 这就是 LangGraph / AutoGen 等框架的底层原理
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel

from ai_agent_starter.models.schemas import ChatMessage, ChatRole, ToolCallRequest
from ai_agent_starter.services.llm_client import LLMClient

console = Console()


async def ask_agent(client: LLMClient, question: str):
    """向 Agent 提问并展示完整执行过程。"""
    console.print(f"\n[bold cyan]👤 用户:[/bold cyan] {question}")

    resp = await client.chat_with_tools(
        ToolCallRequest(
            messages=[
                ChatMessage(
                    role=ChatRole.SYSTEM,
                    content=(
                        "你是一个有用的助手。当需要计算、查时间、查天气时，"
                        "请使用提供的工具。用中文回答。"
                    ),
                ),
                ChatMessage(role=ChatRole.USER, content=question),
            ],
            max_turns=5,
        )
    )

    # 展示执行步骤
    for step in resp.steps:
        if step.type == "assistant_message":
            console.print(f"[bold green]🤖 思考:[/bold green] {step.content}")
        elif step.type == "tool_call":
            console.print(
                f"[bold yellow]🔧 调用工具:[/bold yellow] {step.tool_name}"
                f"  参数: {step.tool_args}"
            )
        elif step.type == "tool_result":
            console.print(
                f"[dim]📎 工具返回:[/dim] {str(step.tool_result)[:200]}"
            )

    console.print(
        f"\n[bold green]✅ 最终回答:[/bold green] {resp.final_answer}"
    )
    console.print(
        f"[dim]💰 模型={resp.model}, tokens={resp.usage.total_tokens}, "
        f"cost=${resp.cost_usd:.6f}[/dim]"
    )


async def main():
    console.print(Panel.fit("示例 02：Function Calling（Agent 最小内核）", style="bold cyan"))

    client = LLMClient()

    # 场景 1：数学计算（LLM 自己可能算错，交给计算器工具）
    await ask_agent(client, "帮我算一下 (234 + 567) * 89 / 3 等于多少？")

    # 场景 2：查询时间
    await ask_agent(client, "现在几点了？今天是星期几？")

    # 场景 3：查询天气
    await ask_agent(client, "上海今天天气怎么样？")

    # 场景 4：组合问题（需要多个工具）
    await ask_agent(
        client,
        "我想知道北京现在的天气，然后帮我算一下 25 的 3 次方是多少。",
    )

    # 场景 5：不需要工具的问题（LLM 直接回答）
    await ask_agent(client, "什么是面向对象编程？")


if __name__ == "__main__":
    asyncio.run(main())
