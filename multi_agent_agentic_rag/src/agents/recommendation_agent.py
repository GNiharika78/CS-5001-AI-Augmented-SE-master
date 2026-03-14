import time

from src.agents.base_agent import BaseAgent
from src.models.schemas import AgentResult, SourceItem
from src.tools.recommendation_tool import RecommendationTool


class RecommendationAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("recommendation_agent")
        self.recommendation_tool = RecommendationTool()

    def run(self, query: str) -> AgentResult:
        start = time.perf_counter()

        raw_results = self.recommendation_tool.search(query=query, top_k=3)

        documents = raw_results.get("documents", [[]])[0]
        metadatas = raw_results.get("metadatas", [[]])[0]
        distances = raw_results.get("distances", [[]])

        if distances and distances[0]:
            dists = distances[0]
        else:
            dists = [0.0] * len(documents)

        sources = []
        for doc, meta, dist in zip(documents, metadatas, dists):
            score = max(0.0, 1.0 - float(dist)) if dist is not None else 0.8
            snippet = doc[:300] + "..." if len(doc) > 300 else doc

            sources.append(
                SourceItem(
                    source_type="recommendation",
                    title=meta.get("title", "unknown recommendation"),
                    snippet=snippet,
                    score=round(score, 3),
                    metadata=meta,
                )
            )

        latency_ms = (time.perf_counter() - start) * 1000

        return AgentResult(
            agent_name=self.name,
            query=query,
            summary="Retrieved semantically related reports, papers, and expert commentary recommendations.",
            sources=sources,
            latency_ms=latency_ms,
            cost_usd=0.0,
        )