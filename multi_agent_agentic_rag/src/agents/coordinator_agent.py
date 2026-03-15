import asyncio
import time

from src.agents.sql_agent import SQLAgent
from src.agents.paper_agent import PaperAgent
from src.agents.web_agent import WebAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.synthesizer_agent import SynthesizerAgent
from src.agents.planner_agent import PlannerAgent
from src.llm.ollama_provider import OllamaProvider
from src.models.schemas import FinalResponse, AgentResult
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

    async def _run_agent_async(self, agent_name: str, query: str) -> AgentResult:
        if agent_name == "sql_agent":
            return await asyncio.to_thread(self.sql_agent.run, query)
        if agent_name == "paper_agent":
            return await asyncio.to_thread(self.paper_agent.run, query)
        if agent_name == "web_agent":
            return await asyncio.to_thread(self.web_agent.run, query)
        if agent_name == "recommendation_agent":
            return await asyncio.to_thread(self.recommendation_agent.run, query)

        raise ValueError(f"Unknown agent: {agent_name}")

    def _build_recommendation_query(self, user_query: str, results: list[AgentResult]) -> str:
        """
        Make recommendation retrieval depend on already retrieved evidence.
        """
        titles = []
        for result in results:
            for source in result.sources[:2]:
                titles.append(source.title)

        evidence_context = "; ".join(titles[:6])

        return (
            f"{user_query}. Recommend follow-up reading and related reports based on these retrieved sources: "
            f"{evidence_context}"
        )

    def _looks_like_prompt_leak(self, text: str) -> bool:
        leak_markers = [
            "Evidence collected from specialized agents:",
            "Required sections exactly:",
            "Rules:",
            "User query:",
            "Source count:",
            "Agent: Academic Paper Search Agent",
            "Agent: Web Search Agent",
            "Agent: Recommendation Agent",
        ]
        lowered = text.lower()
        return any(marker.lower() in lowered for marker in leak_markers)

    def _fallback_summary(self, query: str, results: list[AgentResult]) -> str:
        sections = {
            "Economic Impacts": [],
            "Environmental Impacts": [],
            "Recent Policy or Market Context": [],
            "Recommended Follow-up Reading": [],
        }

        for result in results:
            if result.agent_name == "sql_agent":
                for source in result.sources[:4]:
                    sections["Economic Impacts"].append(source.snippet)
                    sections["Environmental Impacts"].append(source.snippet)

            elif result.agent_name == "paper_agent":
                for source in result.sources[:2]:
                    sections["Recent Policy or Market Context"].append(source.snippet)
                    sections["Recommended Follow-up Reading"].append(source.title)

            elif result.agent_name == "web_agent":
                for source in result.sources[:2]:
                    sections["Recent Policy or Market Context"].append(source.snippet)
                    sections["Recommended Follow-up Reading"].append(source.title)

            elif result.agent_name == "recommendation_agent":
                for source in result.sources[:4]:
                    sections["Recommended Follow-up Reading"].append(source.title)

        def format_section(title: str, items: list[str], limit: int) -> str:
            if not items:
                return f"{title}\nEvidence is limited."
            unique_items = []
            seen = set()
            for item in items:
                if item not in seen:
                    unique_items.append(item)
                    seen.add(item)
            return f"{title}\n" + "\n".join(f"- {item}" for item in unique_items[:limit])

        return (
            format_section("1. Economic Impacts", sections["Economic Impacts"], 2)
            + "\n\n"
            + format_section("2. Environmental Impacts", sections["Environmental Impacts"], 2)
            + "\n\n"
            + format_section("3. Recent Policy or Market Context", sections["Recent Policy or Market Context"], 2)
            + "\n\n"
            + format_section("4. Recommended Follow-up Reading", sections["Recommended Follow-up Reading"], 4)
        )

    async def _run_async(self, query: str) -> tuple[FinalResponse, str]:
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

        results: list[AgentResult] = []

        # Run primary retrieval agents in parallel first
        parallel_agents = [a for a in selected_agents if a != "recommendation_agent"]

        tasks = []
        for agent_name in parallel_agents:
            tracer.add_event("agent_start", agent_name, f"Running {agent_name} in parallel")
            tasks.append(self._run_agent_async(agent_name, query))

        if tasks:
            parallel_results = await asyncio.gather(*tasks)

            for agent_name, result in zip(parallel_agents, parallel_results):
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

        # Run recommendation agent after retrieval so it can use earlier evidence
        if "recommendation_agent" in selected_agents:
            tracer.add_event(
                "agent_start",
                "recommendation_agent",
                "Running recommendation agent with evidence-aware query",
            )

            recommendation_query = self._build_recommendation_query(query, results)
            recommendation_result = await self._run_agent_async("recommendation_agent", recommendation_query)

            results.append(recommendation_result)
            cost_tracker.add(recommendation_result.cost_usd)

            tracer.add_event(
                "agent_finish",
                "recommendation_agent",
                "Finished recommendation_agent",
                {
                    "latency_ms": recommendation_result.latency_ms,
                    "cost_usd": recommendation_result.cost_usd,
                    "sources_count": len(recommendation_result.sources),
                    "success": recommendation_result.success,
                    "error": recommendation_result.error,
                },
            )

        # LLM synthesis with fallback if the model leaks the prompt
        synthesized_answer = await asyncio.to_thread(self.synthesizer.run, query, results)

        if self._looks_like_prompt_leak(synthesized_answer):
            tracer.add_event(
                "synthesis_fallback",
                "coordinator",
                "LLM output leaked prompt; using fallback summary",
            )
            synthesized_answer = self._fallback_summary(query, results)
        else:
            tracer.add_event("synthesis", "synthesizer_agent", "Generated dynamic LLM synthesis")

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

    def run(self, query: str) -> tuple[FinalResponse, str]:
        return asyncio.run(self._run_async(query))