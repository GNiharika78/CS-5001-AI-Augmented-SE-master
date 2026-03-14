import time

from src.agents.sql_agent import SQLAgent
from src.agents.paper_agent import PaperAgent
from src.agents.web_agent import WebAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.agents.planner_agent import PlannerAgent
from src.llm.ollama_provider import OllamaProvider
from src.models.schemas import FinalResponse
from src.orchestration.execution_trace import ExecutionTracer
from src.utils.cost_tracker import CostTracker


class CoordinatorAgent:
    def __init__(self) -> None:
        self.sql_agent = SQLAgent()
        self.paper_agent = PaperAgent()
        self.web_agent = WebAgent()
        self.recommendation_agent = RecommendationAgent()
        self.planner_agent = PlannerAgent()
        self.synthesizer = SynthesizerAgent(provider=OllamaProvider())

    def route(self, query: str) -> list[str]:
        return self.planner_agent.run(query)

    def _summarize_sql_only(self, result, query: str) -> str:
        rows = [source.metadata for source in result.sources if source.metadata]

        if not rows:
            return (
                "1. Economic Impacts\n"
                "The SQL agent returned no structured evidence.\n\n"
                "2. Environmental Impacts\n"
                "The SQL agent returned no structured evidence.\n\n"
                "3. Recent Policy or Market Context\n"
                "No policy or market context was retrieved from structured data alone.\n\n"
                "4. Recommended Follow-up Reading\n"
                "Additional paper or web sources would be needed for follow-up reading."
            )

        renewable_sorted = sorted(rows, key=lambda x: x["renewable_share_pct"], reverse=True)
        emissions_sorted = sorted(rows, key=lambda x: x["co2_mt"], reverse=True)
        investment_sorted = sorted(rows, key=lambda x: x["renewable_investment_billion_usd"], reverse=True)

        highest_share = renewable_sorted[0]
        highest_emissions = emissions_sorted[0]
        highest_investment = investment_sorted[0]

        country_lines = []
        for row in rows:
            country_lines.append(
                f"- {row['country']}: renewable share {row['renewable_share_pct']}%, "
                f"CO2 emissions {row['co2_mt']} Mt, "
                f"renewable investment ${row['renewable_investment_billion_usd']}B, "
                f"clean-energy jobs {row['clean_energy_jobs_thousands']} thousand."
            )

        return (
            "1. Economic Impacts\n"
            f"The retrieved data indicates that {highest_investment['country']} had the highest renewable investment "
            f"(${highest_investment['renewable_investment_billion_usd']}B) in 2023. "
            "Across the available countries, investment and clean-energy jobs appear associated in the retrieved data, "
            "but causation is not established.\n\n"
            "2. Environmental Impacts\n"
            f"The retrieved data indicates that {highest_share['country']} had the highest renewable share "
            f"({highest_share['renewable_share_pct']}%), while {highest_emissions['country']} had the highest CO2 emissions "
            f"({highest_emissions['co2_mt']} Mt). The data supports comparison, but not causal conclusions.\n\n"
            "3. Recent Policy or Market Context\n"
            "Structured SQL data alone does not provide direct policy or market explanations for these differences.\n\n"
            "4. Recommended Follow-up Reading\n"
            "For policy interpretation and explanatory context, additional paper or web evidence should be consulted.\n\n"
            "Country comparison:\n"
            + "\n".join(country_lines)
        )

    def run(self, query: str) -> tuple[FinalResponse, str]:
        start = time.perf_counter()

        tracer = ExecutionTracer(query=query)
        cost_tracker = CostTracker()

        tracer.add_event("start", "coordinator", "Starting multi-agent workflow")

        selected_agents = self.route(query)
        tracer.set_selected_agents(selected_agents)
        tracer.add_event(
            "planning",
            "planner_agent",
            "Planner selected agents",
            {"selected_agents": selected_agents},
        )

        results = []

        for agent_name in selected_agents:
            tracer.add_event("agent_start", agent_name, f"Running {agent_name}")

            if agent_name == "sql_agent":
                result = self.sql_agent.run(query)
            elif agent_name == "paper_agent":
                result = self.paper_agent.run(query)
            elif agent_name == "web_agent":
                result = self.web_agent.run(query)
            elif agent_name == "recommendation_agent":
                result = self.recommendation_agent.run(query)
            else:
                continue

            results.append(result)
            cost_tracker.add(result.cost_usd)

            tracer.add_event(
                "agent_finish",
                agent_name,
                f"Finished {agent_name}",
                {
                    "latency_ms": result.latency_ms,
                    "cost_usd": result.cost_usd,
                    "sources_count": len(result.sources),
                    "success": result.success,
                    "error": result.error,
                },
            )

        if selected_agents == ["sql_agent"]:
            synthesized_answer = self._summarize_sql_only(results[0], query)
            tracer.add_event(
                "synthesis",
                "coordinator",
                "Generated deterministic SQL-only synthesis",
            )
        else:
            synthesized_answer = self.synthesizer.run(query, results)
            tracer.add_event(
                "synthesis",
                "synthesizer_agent",
                "Generated dynamic LLM synthesis",
            )

        total_latency_ms = (time.perf_counter() - start) * 1000
        trace_path = tracer.save()

        response = FinalResponse(
            query=query,
            selected_agents=selected_agents,
            agent_results=results,
            synthesized_answer=synthesized_answer,
            total_cost_usd=cost_tracker.get_total(),
            total_latency_ms=total_latency_ms,
        )

        return response, trace_path