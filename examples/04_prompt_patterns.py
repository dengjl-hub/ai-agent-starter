"""示例 04：Prompt Engineering 常用模式。

运行方式：
    python 04_prompt_patterns.py

学习目标（W2）：
- 掌握 5 种核心 Prompt 模式：
  1. Role Prompting（角色设定）
  2. Few-shot Prompting（少样本示例）
  3. Chain of Thought（思维链）
  4. Self-Consistency（自洽性）
  5. ReAct（推理+行动，Agent 的核心模式）
- 对比不同模式的效果差异
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel

from ai_agent_starter.models.schemas import ChatMessage, ChatRole
from ai_agent_starter.services.llm_client import LLMClient

console = Console()


async def ask(client: LLMClient, system: str, user: str, label: str):
    """发送请求并打印结果。"""
    console.print(f"\n[bold cyan]--- {label} ---[/bold cyan]")
    resp = await client.chat(
        messages=[
            ChatMessage(role=ChatRole.SYSTEM, content=system),
            ChatMessage(role=ChatRole.USER, content=user),
        ],
        temperature=0.3,
    )
    console.print(resp.message.content)
    console.print(
        f"[dim]tokens={resp.usage.total_tokens}, cost=${resp.cost_usd:.6f}[/dim]"
    )
    return resp.message.content


async def main():
    console.print(Panel.fit("示例 04：Prompt Engineering 五种模式", style="bold cyan"))

    client = LLMClient()

    # ---- 1. Role Prompting（角色设定）----
    await ask(
        client,
        system="你是一位有20年经验的资深分布式系统架构师，擅长用通俗易懂的方式解释复杂概念。",
        user="用生活化的比喻解释什么是 CAP 定理？",
        label="模式1: Role Prompting（角色设定）",
    )

    # ---- 2. Few-shot Prompting（少样本示例）----
    await ask(
        client,
        system=(
            "你是一个文本分类器。将用户反馈分类为：bug报告 / 功能请求 / 使用咨询 / 投诉。\n\n"
            "示例：\n"
            "输入：登录页面点击按钮没反应 → bug报告\n"
            "输入：能不能加个暗黑模式？ → 功能请求\n"
            "输入：怎么导出PDF？ → 使用咨询\n"
            "输入：等了三天客服都没人回！ → 投诉"
        ),
        user="输入：每次保存大文件就会闪退，错误码0x800",
        label="模式2: Few-shot Prompting（少样本示例）",
    )

    # ---- 3. Chain of Thought（思维链）----
    await ask(
        client,
        system="你是一个数学解题助手。请一步步思考，把推理过程写出来，最后给出答案。",
        user=(
            "一个水池有两个进水管和一个出水管。"
            "A管单独注满需要6小时，B管单独注满需要8小时，"
            "出水管C单独放完需要12小时。"
            "三管同时开，多久能注满水池？"
        ),
        label="模式3: Chain of Thought（思维链）",
    )

    # ---- 4. Self-Consistency（自洽性检查）----
    console.print(
        "\n[bold cyan]--- 模式4: Self-Consistency（自洽性，多次采样取一致） ---[/bold cyan]"
    )
    question = "一个农夫有17只羊，除了9只以外都死了，还剩几只羊？"
    answers = []
    for i in range(3):
        resp = await client.chat(
            messages=[
                ChatMessage(
                    role=ChatRole.SYSTEM,
                    content="请仔细思考后回答，先分析再给答案。",
                ),
                ChatMessage(role=ChatRole.USER, content=question),
            ],
            temperature=0.7,
        )
        answers.append(resp.message.content)
        console.print(f"  第{i+1}次回答: {resp.message.content[-50:]}")
    console.print(
        "[dim]自洽性思路：多次采样，取多数一致的答案。"
        "生产中可用代码解析最终答案并投票。[/dim]"
    )

    # ---- 5. ReAct 模式（推理+行动，Agent 核心）----
    await ask(
        client,
        system=(
            "你使用 ReAct 模式回答问题，格式如下：\n"
            "Thought: 思考下一步该做什么\n"
            "Action: 要采取的行动\n"
            "Observation: 行动结果\n"
            "...（重复以上步骤）\n"
            "Thought: 我已经知道答案\n"
            "Final Answer: 最终答案\n\n"
            "可用的行动：\n"
            "- calculate[表达式]: 数学计算\n"
            "- search[关键词]: 搜索信息\n"
            "- compare[事物A vs 事物B]: 对比"
        ),
        user="如果一辆车以60km/h行驶2.5小时，再以80km/h行驶1.5小时，总路程是多少？",
        label="模式5: ReAct（推理+行动，Agent 的核心模式）",
    )

    console.print(
        "\n[bold yellow]提示:[/bold yellow] ReAct 模式就是 Function Calling 的前身。"
        "现代 Agent 框架把 Thought/Action/Observation 循环自动化了，"
        "你在示例02中看到的就是它的工程实现。"
    )


if __name__ == "__main__":
    asyncio.run(main())
