from src.models.schemas import AgentResult
from src.llm.base_provider import BaseLLMProvider


class SynthesizerAgent:
    def __init__(self, provider: BaseLLMProvider) -> None:
        self.name = "synthesizer_agent"
        self.provider = provider

    def _pretty_agent_name(self, agent_name: str) -> str:
        mapping = {
            "sql_agent": "SQL Retrieval Agent",
            "paper_agent": "Academic Paper Search Agent",
            "web_agent": "Web Search Agent",
            "recommendation_agent": "Recommendation Agent",
        }
        return mapping.get(agent_name, agent_name.replace("_", " ").title())

    def _build_prompt(self, query: str, results: list[AgentResult]) -> str:
        lines = []
        lines.append(f"User query: {query}")
        lines.append("")
        lines.append("Evidence collected from specialized agents:")

        total_sources = 0

        for result in results:
            agent_label = self._pretty_agent_name(result.agent_name)
            source_count = len(result.sources)
            total_sources += source_count

            lines.append(f"\nAgent: {agent_label}")
            lines.append(f"Success: {result.success}")
            lines.append(f"Summary: {result.summary}")
            lines.append(f"Source count: {source_count}")

            if result.error:
                lines.append(f"Error: {result.error}")

            if source_count == 0:
                lines.append("No sources were returned by this agent.")
            else:
                max_sources = 4 if result.agent_name == "sql_agent" else 1
                for idx, source in enumerate(result.sources[:max_sources], start=1):
                    lines.append(f"Source {idx}: {source.title}")
                    lines.append(f"Snippet {idx}: {source.snippet}")

        lines.append("")
        lines.append(f"Total evidence sources across all agents: {total_sources}")
        lines.append("")

        lines.append(
            "Write a grounded synthesis using only the evidence above.\n\n"
            "Required sections exactly:\n"
            "1. Economic Impacts\n"
            "2. Environmental Impacts\n"
            "3. Recent Policy or Market Context\n"
            "4. Recommended Follow-up Reading\n\n"
            "Rules:\n"
            "- Use only the evidence above.\n"
            "- Do not invent facts.\n"
            "- Do not use outside knowledge.\n"
            "- Do not claim an agent had no evidence if its source count is greater than 0.\n"
            "- Do not claim causation unless the evidence explicitly supports it.\n"
            "- Do not describe relationships as direct unless the evidence explicitly supports that.\n"
            "- Do not say investment caused jobs unless the evidence explicitly proves causation; say they are associated in the retrieved data.\n"
            "- Use phrases like 'the evidence suggests' or 'the retrieved data indicates'.\n"
            "- If an agent returned zero sources, say evidence from that source is limited.\n"
            "- Separate observed data from interpretation.\n"
            "- For SQL comparison queries, compare multiple countries when multiple SQL sources are provided.\n"
            "- Keep the final response concise, around under 180 words.\n"
            "- Do not add any extra sections beyond the four required sections.\n"
            "- If recommended reading is weak or missing, say so briefly.\n"
            "- When multiple SQL sources are provided, compare values directly and avoid mis-ranking countries.\n"
            "- If evidence for a section is missing, state briefly that the evidence is limited."
        )

        return "\n".join(lines)

    def run(self, query: str, results: list[AgentResult]) -> str:
        system_prompt = (
            "You are a careful synthesis agent in a multi-agent RAG system. "
            "Your job is to combine evidence from multiple agents into one grounded answer. "
            "Do not invent facts. Do not use outside knowledge. "
            "Be structured, concise, and explicit about uncertainty."
        )

        user_prompt = self._build_prompt(query, results)
        return self.provider.generate(system_prompt, user_prompt)