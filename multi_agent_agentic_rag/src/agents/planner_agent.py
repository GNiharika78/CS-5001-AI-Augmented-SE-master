from src.agents.base_agent import BaseAgent


class PlannerAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("planner_agent")

    def run(self, query: str) -> list[str]:
        q = query.lower()

        scores = {
            "sql_agent": 0,
            "paper_agent": 0,
            "web_agent": 0,
            "recommendation_agent": 0,
        }

        # Structured-data intent
        for token in [
            "compare", "across", "countries", "country", "trend", "trends",
            "statistics", "data", "jobs", "employment", "investment",
            "investments", "emissions", "co2", "share", "shares"
        ]:
            if token in q:
                scores["sql_agent"] += 2

        # Research / analytical intent
        for token in [
            "study", "studies", "paper", "papers", "research", "evidence",
            "analysis", "impact", "impacts", "economic", "environmental"
        ]:
            if token in q:
                scores["paper_agent"] += 2

        # Current / policy / market intent
        for token in [
            "latest", "recent", "today", "current", "news", "update",
            "updates", "policy", "policies", "regulation", "regulations",
            "market", "markets"
        ]:
            if token in q:
                scores["web_agent"] += 2

        # Follow-up / recommendation intent
        for token in [
            "recommend", "recommendation", "suggest", "follow-up", "reading",
            "readings", "report", "reports", "commentary", "resource", "resources"
        ]:
            if token in q:
                scores["recommendation_agent"] += 2

        # Broad impacts questions generally need both structured + research evidence
        if "impact" in q or "impacts" in q:
            scores["sql_agent"] += 1
            scores["paper_agent"] += 1

        # Policy update questions should rarely be web-only
        if ("latest" in q or "recent" in q or "update" in q or "updates" in q) and (
            "policy" in q or "policies" in q or "market" in q
        ):
            scores["paper_agent"] += 1
            scores["web_agent"] += 1

        # Recommendation queries should focus on papers + recommendation agent
        if any(t in q for t in ["recommend", "follow-up", "reading", "report", "commentary"]):
            scores["recommendation_agent"] += 2
            scores["paper_agent"] += 1
            scores["sql_agent"] -= 2
            scores["web_agent"] -= 2

        # If recommendation query is also explicitly "latest", allow web back in
        if any(t in q for t in ["recommend", "follow-up", "reading"]) and any(
            t in q for t in ["latest", "recent", "current"]
        ):
            scores["web_agent"] += 2

        # Select agents with positive score
        selected = [agent for agent, score in scores.items() if score > 0]

        # Fallback
        if not selected:
            selected = ["paper_agent", "recommendation_agent"]

        preferred_order = [
            "sql_agent",
            "paper_agent",
            "web_agent",
            "recommendation_agent",
        ]
        return [agent for agent in preferred_order if agent in selected]