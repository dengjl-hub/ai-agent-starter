"""示例 01：基础对话 —— 多轮对话 + 多模型切换 + 成本统计。

运行方式：
    cd examples
    python 01_basic_chat.py

学习目标（W2）：
- 理解 messages 列表的 role 机制（system / user / assistant）
- 学会切换不同模型
- 观察 Token 用量和成本
"""

import asyncio
import sys
from pathlib import Path

# 把 src 目录加入 path（examples 目录下直接运行时需要）
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel

from ai_agent_starter.models.schemas import ChatMessage, ChatRole
from ai_agent_starter.services.llm_client import LLMClient
from ai_agent_starter.services.token_tracker import get_token_tracker

console = Console()


async def main():
    console.print(Panel.fit("示例 01：基础对话", style="bold cyan"))

    client = LLMClient()

    # ---- 1. 单轮对话 ----
    console.print("\n[bold yellow]=== 1. 单轮对话 ===[/bold yellow]")
    resp = await client.chat(
        messages=[
            ChatMessage(
                role=ChatRole.SYSTEM,
                content="你是一个简洁的技术助手，回答不超过3句话。",
            ),
            ChatMessage(
                role=ChatRole.USER,
                content="用一句话解释什么是 RAG（检索增强生成）？",
            ),
        ]
    )
    console.print(f"[模型] {resp.model}")
    console.print(f"[回复] {resp.message.content}")
    console.print(
        f"[用量] prompt={resp.usage.prompt_tokens}, "
        f"completion={resp.usage.completion_tokens}, "
        f"total={resp.usage.total_tokens}, cost=${resp.cost_usd:.6f}"
    )

    # ---- 2. 多轮对话（带上下文）----
    console.print("\n[bold yellow]=== 2. 多轮对话 ===[/bold yellow]")
    messages = [
        ChatMessage(
            role=ChatRole.SYSTEM,
            content="你是一个Python技术专家，回答简洁。",
        ),
        ChatMessage(role=ChatRole.USER, content="Python中列表和元组有什么区别？"),
    ]

    # 第一轮
    resp1 = await client.chat(messages)
    console.print(f"[Q] Python中列表和元组有什么区别？")
    console.print(f"[A] {resp1.message.content}")
    messages.append(resp1.message)

    # 第二轮（引用上文，LLM 能理解"它们"指的是什么）
    messages.append(
        ChatMessage(role=ChatRole.USER, content="它们各自的使用场景是什么？")
    )
    resp2 = await client.chat(messages)
    console.print(f"\n[Q] 它们各自的使用场景是什么？")
    console.print(f"[A] {resp2.message.content}")

    # 第三轮（独立问题）
    user_question = "广西2026年洪水是什么时候？"
    messages.append(
        ChatMessage(role=ChatRole.USER, content=user_question)
    )
    resp2 = await client.chat(messages)
    console.print(f"\n[Q] {user_question}")
    console.print(f"[A] {resp2.message.content}")

    # ---- 3. 成本汇总 ----
    console.print("\n[bold yellow]=== 3. 成本汇总 ===[/bold yellow]")
    summary = get_token_tracker().get_summary()
    console.print(
        f"总调用次数: {summary['total_calls']}\n"
        f"总 Token 数: {summary['total_tokens']}\n"
        f"总成本: ${summary['total_cost_usd']:.6f}"
    )
    for model, stats in summary.get("by_model", {}).items():
        console.print(
            f"  - {model}: {stats['calls']}次, "
            f"{stats['total_tokens']} tokens, ${stats['cost_usd']:.6f}"
        )


if __name__ == "__main__":
    asyncio.run(main())
