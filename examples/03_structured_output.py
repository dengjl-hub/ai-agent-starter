"""示例 03：结构化输出 —— 让 LLM 返回可靠的 JSON。

运行方式：
    python 03_structured_output.py

学习目标（W2）：
- 理解为什么"在 prompt 里说请返回 JSON"不可靠
- 学会用 response_format + JSON Schema 强制结构化输出
- 用 Pydantic 模型校验 LLM 输出
- 代码审查场景的实际应用
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ai_agent_starter.models.schemas import (
    ChatMessage,
    ChatRole,
    CodeIssue,
    CodeReviewResult,
    Severity,
)
from ai_agent_starter.services.llm_client import LLMClient

console = Console()


# 一段有问题的代码（故意写了几个 bug 让 LLM 审查）
SAMPLE_CODE = """
def process_users(users):
    # SQL 注入风险
    query = "SELECT * FROM users WHERE name = '" + users + "'"
    cursor.execute(query)

    # 裸 except
    try:
        result = 100 / len(users)
    except:
        pass

    # 可变默认参数
    def add_item(item, lst=[]):
        lst.append(item)
        return lst

    # 未使用的变量
    unused_var = 42

    return result
"""


async def main():
    console.print(Panel.fit("示例 03：结构化输出（代码审查）", style="bold cyan"))

    client = LLMClient()

    console.print("[bold yellow]待审查代码:[/bold yellow]")
    console.print(SAMPLE_CODE)

    console.print("\n[bold yellow]正在调用 LLM 进行审查...[/bold yellow]")
    result: CodeReviewResult = await client.code_review(SAMPLE_CODE, "python")

    # 展示结构化结果
    console.print(f"\n[bold green]审查总结:[/bold green] {result.summary}")
    console.print(f"[bold green]代码评分:[/bold green] {result.score}/100")

    if result.positive_points:
        console.print("\n[bold green]代码亮点:[/bold green]")
        for point in result.positive_points:
            console.print(f"  ✓ {point}")

    if result.issues:
        table = Table(title="发现的问题", show_lines=True)
        table.add_column("严重程度", style="bold", width=8)
        table.add_column("类别", width=12)
        table.add_column("行号", width=6)
        table.add_column("问题描述")
        table.add_column("修复建议")

        severity_style = {
            Severity.CRITICAL: "bold red",
            Severity.HIGH: "red",
            Severity.MEDIUM: "yellow",
            Severity.LOW: "dim",
            Severity.INFO: "blue",
        }

        for issue in result.issues:
            style = severity_style.get(issue.severity, "")
            table.add_row(
                f"[{style}]{issue.severity.value}[/{style}]",
                issue.category,
                str(issue.line) if issue.line else "-",
                issue.description,
                issue.suggestion,
            )
        console.print(table)

    # 展示原始 JSON（验证输出确实是结构化的）
    console.print("\n[bold yellow]原始 JSON 输出（前500字符）:[/bold yellow]")
    json_str = result.model_dump_json(indent=2)
    console.print_json(json_str[:500] + ("..." if len(json_str) > 500 else ""))


if __name__ == "__main__":
    asyncio.run(main())
