import time

from src.agents.base_agent import BaseAgent
from src.models.schemas import AgentResult, SourceItem
from src.tools.web_search_tool import WebSearchTool


class WebAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("web_agent")
        self.web_tool = WebSearchTool()

    def _build_search_query(self, query: str) -> str:
        """
        Convert the user query into a stronger web search query.
        This helps reduce generic results and bias toward energy/policy sources.
        """
        preferred_domains = [
            "iea.org",
            "irena.org",
            "ec.europa.eu",
            "energy.ec.europa.eu",
            "eur-lex.europa.eu",
        ]

        domain_part = " OR ".join([f"site:{d}" for d in preferred_domains])

        return (
            f"{query} renewable energy economics emissions policy market analysis "
            f"({domain_part})"
        )

    def _is_relevant_result(self, title: str, snippet: str, url: str) -> bool:
        """
        Lightweight filtering to reduce obviously generic or weak results.
        """
        text = f"{title} {snippet} {url}".lower()

        strong_keywords = [
            "renewable",
            "energy",
            "emissions",
            "policy",
            "electricity",
            "solar",
            "wind",
            "decarbonization",
            "clean energy",
            "grid",
        ]

        weak_keywords = [
            "global risks report",
            "global shifts",
            "well-being",
            "geopolitical instability",
        ]

        has_strong = any(k in text for k in strong_keywords)
        has_weak = any(k in text for k in weak_keywords)

        return has_strong and not has_weak

    def run(self, query: str) -> AgentResult:
        start = time.perf_counter()

        try:
            search_query = self._build_search_query(query)
            raw_results = self.web_tool.search(query=search_query, top_k=5)

            sources = []

            for item in raw_results.get("results", []):
                title = item.get("title", "untitled")
                snippet = item.get("content", "") or item.get("snippet", "")
                url = item.get("url", "")

                if not self._is_relevant_result(title, snippet, url):
                    continue

                sources.append(
                    SourceItem(
                        source_type="web",
                        title=title,
                        snippet=snippet[:300] + "..." if len(snippet) > 300 else snippet,
                        score=0.0,
                        metadata={
                            "url": url,
                            "search_query": search_query,
                        },
                    )
                )

            # fallback: if filtering removed everything, use the raw top 3
            if not sources:
                for item in raw_results.get("results", [])[:3]:
                    title = item.get("title", "untitled")
                    snippet = item.get("content", "") or item.get("snippet", "")
                    url = item.get("url", "")

                    sources.append(
                        SourceItem(
                            source_type="web",
                            title=title,
                            snippet=snippet[:300] + "..." if len(snippet) > 300 else snippet,
                            score=0.0,
                            metadata={
                                "url": url,
                                "search_query": search_query,
                            },
                        )
                    )

            latency_ms = (time.perf_counter() - start) * 1000

            return AgentResult(
                agent_name=self.name,
                query=query,
                summary="Retrieved live web search results for renewable-energy policy, economics, and market context.",
                sources=sources[:3],
                latency_ms=latency_ms,
                cost_usd=0.0,
                success=True,
            )

        except Exception as e:
            latency_ms = (time.perf_counter() - start) * 1000

            return AgentResult(
                agent_name=self.name,
                query=query,
                summary="Web search failed.",
                sources=[],
                latency_ms=latency_ms,
                cost_usd=0.0,
                success=False,
                error=str(e),
            )