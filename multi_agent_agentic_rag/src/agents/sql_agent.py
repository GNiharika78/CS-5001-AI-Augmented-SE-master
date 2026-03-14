import time

from src.agents.base_agent import BaseAgent
from src.models.schemas import AgentResult, SourceItem
from src.tools.sql_tool import SQLTool


class SQLAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__("sql_agent")
        self.sql_tool = SQLTool()

    def _build_sql_query(self, query: str) -> str:
        q = query.lower()

        base_query = """
        SELECT
            r.country,
            r.year,
            r.renewable_share_pct,
            e.co2_mt,
            ec.renewable_investment_billion_usd,
            ec.clean_energy_jobs_thousands
        FROM renewable_adoption r
        JOIN emissions e
            ON r.country = e.country AND r.year = e.year
        JOIN economic_indicators ec
            ON r.country = ec.country AND r.year = ec.year
        WHERE r.year = 2023
        """

        if "compare" in q or "across" in q or "countries" in q:
            return base_query + " ORDER BY r.country ASC"

        if "job" in q or "jobs" in q or "employment" in q:
            return base_query + " ORDER BY ec.clean_energy_jobs_thousands DESC"

        if "investment" in q or "investments" in q:
            return base_query + " ORDER BY ec.renewable_investment_billion_usd DESC"

        if "emission" in q or "emissions" in q or "co2" in q:
            return base_query + " ORDER BY e.co2_mt DESC"

        if "share" in q or "renewable share" in q:
            return base_query + " ORDER BY r.renewable_share_pct DESC"

        return base_query + " ORDER BY r.renewable_share_pct DESC"

    def run(self, query: str) -> AgentResult:
        start = time.perf_counter()

        sql_query = self._build_sql_query(query)
        rows = self.sql_tool.run_query(sql_query)

        sources = []
        for row in rows:
            country, year, share, co2_mt, investment, jobs = row
            sources.append(
                SourceItem(
                    source_type="sql",
                    title=f"{country} energy indicators ({year})",
                    snippet=(
                        f"{country} had {share}% renewable share in {year}, "
                        f"CO2 emissions of {co2_mt} Mt, renewable investment of "
                        f"${investment}B, and {jobs} thousand clean-energy jobs."
                    ),
                    score=0.95,
                    metadata={
                        "country": country,
                        "year": year,
                        "renewable_share_pct": share,
                        "co2_mt": co2_mt,
                        "renewable_investment_billion_usd": investment,
                        "clean_energy_jobs_thousands": jobs,
                        "sql_query": sql_query.strip(),
                    },
                )
            )

        latency_ms = (time.perf_counter() - start) * 1000

        return AgentResult(
            agent_name=self.name,
            query=query,
            summary="Retrieved structured renewable, emissions, investment, and jobs statistics from the SQL database.",
            sources=sources,
            latency_ms=latency_ms,
            cost_usd=0.0,
        )