from src.agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("planner_agent")

    def run(self, query: str) -> list[str]:
        q = query.lower()
        selected = set()

        has_latest = any(
            k in q for k in ["latest", "recent", "today", "current", "news", "update", "updates"]
        )
        has_policy = any(
            k in q for k in ["policy", "policies", "regulation", "regulations", "market", "markets"]
        )
        has_stats = any(
            k in q
            for k in [
                "compare",
                "trend",
                "trends",
                "statistics",
                "data",
                "jobs",
                "job creation",
                "investment data",
                "emissions",
                "share",
                "shares",
                "country",
                "countries",
            ]
        )
        has_research = any(
            k in q
            for k in [
                "study",
                "studies",
                "paper",
                "papers",
                "research",
                "evidence",
                "analysis",
                "impact",
                "impacts",
                "environmental",
                "economic",
            ]
        )
        has_recommendation = any(
            k in q
            for k in [
                "recommend",
                "recommendation",
                "suggest",
                "follow-up",
                "reading",
                "readings",
                "report",
                "reports",
                "commentary",
                "resources",
            ]
        )

        if has_stats:
            selected.add("sql_agent")

        if has_research or has_policy:
            selected.add("paper_agent")

        if has_latest or has_policy:
            selected.add("web_agent")

        if has_recommendation:
            selected.update(["recommendation_agent", "paper_agent"])

        if "impact" in q or "impacts" in q:
            selected.update(["sql_agent", "paper_agent"])

        if has_recommendation:
            selected.discard("sql_agent")

        if has_latest and has_policy:
            selected.update(["web_agent", "paper_agent"])

        if has_recommendation and not has_latest:
            selected.discard("web_agent")

        if not selected:
            selected.update(["paper_agent", "recommendation_agent"])

        preferred_order = [
            "sql_agent",
            "paper_agent",
            "web_agent",
            "recommendation_agent",
        ]

        return [agent for agent in preferred_order if agent in selected]