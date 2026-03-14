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

        print("\n[bold cyan]Selected Agents:[/bold cyan]")
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
                print(f"    {source.snippet}")

                url = source.metadata.get("url") if source.metadata else None
                if url:
                    print(f"    URL: {url}")

        print("\n[bold magenta]Final Response:[/bold magenta]")
        print(response.synthesized_answer)

        print(f"\n[bold yellow]Total Cost:[/bold yellow] ${response.total_cost_usd:.4f}")
        print(f"[bold yellow]Total Latency:[/bold yellow] {response.total_latency_ms:.2f} ms")
        print(f"[bold yellow]Trace Saved At:[/bold yellow] {trace_path}")


if __name__ == "__main__":
    main()