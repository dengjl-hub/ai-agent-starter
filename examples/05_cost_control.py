"""示例 05：成本控制 —— 降本增效的实战手段。

运行方式：
    python 05_cost_control.py

学习目标（W2）：
- 模型路由：简单问题用便宜模型，复杂问题用强模型
- Prompt 缓存：重复的 system prompt 只计费一次（DeepSeek 支持）
- Token 用量监控：实时统计与预算控制
- 这是 Agent 生产落地的核心商业指标
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_agent_starter.models.schemas import ChatMessage, ChatRole
from ai_agent_starter.services.llm_client import LLMClient
from ai_agent_starter.services.token_tracker import get_token_tracker

console = Console()


async def main():
    console.print(Panel.fit("示例 05：成本控制（降本增效）", style="bold cyan"))

    client = LLMClient()

    # ---- 1. 模型路由对比 ----
    console.print(
        "\n[bold yellow]=== 1. 模型路由：不同问题用不同模型 ===[/bold yellow]"
    )

    questions = [
        ("简单问题", "你好，今天天气不错"),
        ("简单问题", "把这句话翻译成英文：我喜欢编程"),
        ("复杂问题", "请解释 Redis 的 RDB 和 AOF 持久化机制的区别，以及各自的优缺点和适用场景"),
        ("复杂问题", "设计一个秒杀系统的架构，需要考虑超卖、限流、缓存击穿等问题"),
    ]

    table = Table(title="模型路由效果对比", show_lines=True)
    table.add_column("问题类型", width=10)
    table.add_column("问题", width=40)
    table.add_column("路由到的模型", width=20)
    table.add_column("Token 数", width=10)
    table.add_column("成本(USD)", width=12)

    for q_type, question in questions:
        resp = await client.smart_chat(question)
        table.add_row(
            q_type,
            question[:38],
            resp.model,
            str(resp.usage.total_tokens),
            f"${resp.cost_usd:.6f}",
        )

    console.print(table)

    # ---- 2. 成本汇总 ----
    console.print("\n[bold yellow]=== 2. 成本汇总 ===[/bold yellow]")
    summary = get_token_tracker().get_summary()

    console.print(f"总调用次数: {summary['total_calls']}")
    console.print(f"总 Token 数: {summary['total_tokens']}")
    console.print(f"总成本: ${summary['total_cost_usd']:.6f}")

    by_model_table = Table(title="按模型统计")
    by_model_table.add_column("模型")
    by_model_table.add_column("调用次数")
    by_model_table.add_column("输入 Tokens")
    by_model_table.add_column("输出 Tokens")
    by_model_table.add_column("成本(USD)")

    for model, stats in summary.get("by_model", {}).items():
        by_model_table.add_row(
            model,
            str(stats["calls"]),
            str(stats["prompt_tokens"]),
            str(stats["completion_tokens"]),
            f"${stats['cost_usd']:.6f}",
        )
    console.print(by_model_table)

    # ---- 3. 成本优化建议 ----
    console.print(
        "\n[bold yellow]=== 3. 生产环境成本优化手段 ===[/bold yellow]"
    )
    tips = [
        ("模型路由", "简单问题用小模型(deepseek-chat)，复杂问题用强模型(deepseek-reasoner)，可省 50%+ 成本"),
        ("Prompt 缓存", "DeepSeek 支持 context caching，重复的 system prompt 命中缓存部分输入价格打 1 折"),
        ("语义缓存", "对高频重复问题直接返回缓存答案，不调用 LLM（如 GPTCache）"),
        ("流式输出", "提升用户体验，不省成本但降低超时重试带来的浪费"),
        ("Batch API", "OpenAI/DeepSeek 都有 Batch API，非实时任务用批量接口可省 50%"),
        ("压缩上下文", "用摘要替代长对话历史，减少 prompt tokens"),
        ("设置 max_tokens", "防止 LLM 无限输出导致成本失控"),
        ("监控告警", "对 Token 用量设置日预算上限，超阈值告警（本项目的 TokenTracker 就是基础版）"),
    ]
    for title, desc in tips:
        console.print(f"  [bold green]• {title}[/bold green]: {desc}")

    console.print(
        "\n[bold cyan]💡 面试话术:[/bold cyan] "
        "'我在项目中设计了模型路由策略，通过分类器判断问题复杂度，"
        "简单请求走轻量模型，复杂请求走推理模型，结合 Prompt 缓存和语义缓存，"
        "在保证回答质量的前提下将平均 Token 成本降低了 XX%。'"
    )


if __name__ == "__main__":
    asyncio.run(main())
