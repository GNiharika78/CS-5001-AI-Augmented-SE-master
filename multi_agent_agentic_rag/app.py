import shutil
import textwrap

from dotenv import load_dotenv
from rich import print

from src.agents.coordinator_agent import CoordinatorAgent


def main() -> None:
    load_dotenv()

    coordinator = CoordinatorAgent()

    print("\n[bold cyan]Multi-Agent Agentic RAG System[/bold cyan]")
    print("Type a question or type 'exit' to quit.\n")

    while True:
        query = input("\nEnter your query: ").strip()

        if not query:
            print("[bold red]Please enter a non-empty query.[/bold red]")
            continue

        if query.lower() in ["exit", "quit"]:
            print("\n[bold red]Exiting system.[/bold red]")
            break

        response, trace_path = coordinator.run(query)

        terminal_width = shutil.get_terminal_size().columns
        separator = "=" * terminal_width

        print(f"\n[bold cyan]{separator}[/bold cyan]")
        print("[bold cyan]Selected Agents:[/bold cyan]")
        for agent in response.selected_agents:
            print(f"- {agent}")

        print("\n[bold green]Agent Outputs:[/bold green]")
        for result in response.agent_results:
            print(f"\n[bold]{result.agent_name}[/bold]")
            print(f"Summary: {result.summary}")
            print(f"Latency: {result.latency_ms:.2f} ms | Cost: ${result.cost_usd:.4f}")

            if not result.success:
                print(f"[bold red]Error:[/bold red] {result.error}")
                continue

            if not result.sources:
                print("  - No sources returned")
                continue

            max_sources = 4 if result.agent_name == "sql_agent" else 2
            for source in result.sources[:max_sources]:
                print(f"  - {source.title}")

                wrapped_snippet = textwrap.fill(
                    source.snippet,
                    width=max(40, terminal_width - 6),
                )
                print(textwrap.indent(wrapped_snippet, "    "))

                url = source.metadata.get("url") if source.metadata else None
                if url:
                    wrapped_url = textwrap.fill(
                        f"URL: {url}",
                        width=max(40, terminal_width - 6),
                    )
                    print(textwrap.indent(wrapped_url, "    "))

        print(f"\n[bold magenta]{separator}[/bold magenta]")
        print("[bold magenta]Final Response:[/bold magenta]")

        wrapped_response = textwrap.fill(
            response.synthesized_answer,
            width=max(50, terminal_width - 2),
            replace_whitespace=False,
            drop_whitespace=False,
        )
        print(wrapped_response)

        print(f"\n[bold yellow]{separator}[/bold yellow]")
        print(f"[bold yellow]Total Cost:[/bold yellow] ${response.total_cost_usd:.4f}")
        print(f"[bold yellow]Total Latency:[/bold yellow] {response.total_latency_ms:.2f} ms")
        print(f"[bold yellow]Trace Saved At:[/bold yellow] {trace_path}")
        print(f"[bold yellow]{separator}[/bold yellow]")


if __name__ == "__main__":
    main()