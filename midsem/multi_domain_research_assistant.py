import os
import re
import math
import json
import sqlite3
import textwrap
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Any, Tuple
from urllib.parse import quote_plus
from urllib.request import urlopen, Request
import xml.etree.ElementTree as ET


# ============================================================
# Multi-Domain Research Assistant (Single-file implementation)
# Use case implemented from Agentic RAG survey paper.
#
# Workflow:
#   Agent 1 -> Economic statistics via SQL queries
#   Agent 2 -> Academic papers via semantic-ish ranking
#   Agent 3 -> Recent news / policy via web RSS search
#   Agent 4 -> Recommendations via lightweight relevance scoring
#   Orchestrator -> merges all outputs into one final response
#
# Notes:
# - No paid API keys required.
# - Uses SQLite for structured stats.
# - Uses arXiv API for papers.
# - Uses Google News RSS for current news headlines.
# - Semantic search is implemented with lightweight token overlap
#   scoring to keep this runnable anywhere.
# ============================================================


# -----------------------------
# Data Models
# -----------------------------
@dataclass
class EconomicRecord:
    metric: str
    region: str
    year: int
    value: float
    unit: str
    source: str


@dataclass
class PaperRecord:
    title: str
    summary: str
    authors: List[str]
    published: str
    link: str
    score: float


@dataclass
class NewsRecord:
    title: str
    link: str
    published: str
    source: str
    summary: str
    score: float


@dataclass
class RecommendationRecord:
    title: str
    category: str
    reason: str
    score: float


# -----------------------------
# Utility Functions
# -----------------------------
def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


STOPWORDS = {
    "the", "is", "are", "a", "an", "of", "to", "in", "for", "on", "and",
    "or", "with", "what", "how", "has", "have", "had", "been", "this", "that",
    "it", "its", "their", "from", "by", "as", "at", "into", "about", "than",
    "over", "under", "across", "recent", "latest"
}


def tokenize(text: str) -> List[str]:
    return [t for t in normalize_text(text).split() if t not in STOPWORDS and len(t) > 2]



def overlap_score(query: str, document: str) -> float:
    q = set(tokenize(query))
    d = set(tokenize(document))
    if not q or not d:
        return 0.0
    inter = len(q & d)
    denom = math.sqrt(len(q) * len(d))
    return inter / denom if denom else 0.0



def safe_fetch(url: str, timeout: int = 20) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="ignore")



def shorten(text: str, width: int = 220) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return textwrap.shorten(text, width=width, placeholder="...")


# -----------------------------
# Agent 1: SQL Economic Data Agent
# -----------------------------
class EconomicDataAgent:
    def __init__(self, db_path: str = "energy_economics.db") -> None:
        self.db_path = db_path
        self._ensure_database()

    def _ensure_database(self) -> None:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS renewable_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric TEXT NOT NULL,
                region TEXT NOT NULL,
                year INTEGER NOT NULL,
                value REAL NOT NULL,
                unit TEXT NOT NULL,
                source TEXT NOT NULL
            )
            """
        )

        cur.execute("SELECT COUNT(*) FROM renewable_stats")
        count = cur.fetchone()[0]
        if count == 0:
            seed_rows = [
                ("ghg_reduction", "Europe", 2015, 8.0, "%", "EU Policy Report (sample dataset)"),
                ("ghg_reduction", "Europe", 2020, 15.0, "%", "EU Policy Report (sample dataset)"),
                ("ghg_reduction", "Europe", 2024, 20.0, "%", "EU Policy Report (sample dataset)"),
                ("renewable_jobs", "Europe", 2024, 1_200_000, "jobs", "EU Labour / Energy Summary (sample dataset)"),
                ("solar_jobs", "Europe", 2024, 420_000, "jobs", "Sectoral Labour Summary (sample dataset)"),
                ("wind_jobs", "Europe", 2024, 510_000, "jobs", "Sectoral Labour Summary (sample dataset)"),
                ("renewable_investment", "Europe", 2022, 210.5, "billion_eur", "Energy Investment Monitor (sample dataset)"),
                ("renewable_investment", "Europe", 2023, 238.2, "billion_eur", "Energy Investment Monitor (sample dataset)"),
                ("renewable_investment", "Europe", 2024, 251.7, "billion_eur", "Energy Investment Monitor (sample dataset)"),
                ("storage_cost_pressure", "Europe", 2024, 14.3, "%", "Grid Storage Cost Analysis (sample dataset)"),
            ]
            cur.executemany(
                "INSERT INTO renewable_stats(metric, region, year, value, unit, source) VALUES (?, ?, ?, ?, ?, ?)",
                seed_rows,
            )
            conn.commit()

        conn.close()

    def run(self, query: str) -> Dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Hard-coded SQL patterns based on the use case.
        sql_map = {
            "ghg": """
                SELECT metric, region, year, value, unit, source
                FROM renewable_stats
                WHERE metric = 'ghg_reduction' AND region = 'Europe'
                ORDER BY year DESC
                LIMIT 3
            """,
            "jobs": """
                SELECT metric, region, year, value, unit, source
                FROM renewable_stats
                WHERE metric IN ('renewable_jobs', 'solar_jobs', 'wind_jobs') AND region = 'Europe'
                ORDER BY value DESC
            """,
            "investment": """
                SELECT metric, region, year, value, unit, source
                FROM renewable_stats
                WHERE metric = 'renewable_investment' AND region = 'Europe'
                ORDER BY year DESC
            """,
            "costs": """
                SELECT metric, region, year, value, unit, source
                FROM renewable_stats
                WHERE metric = 'storage_cost_pressure' AND region = 'Europe'
                ORDER BY year DESC
                LIMIT 1
            """,
        }

        buckets = {}
        for key, sql in sql_map.items():
            cur.execute(sql)
            rows = [EconomicRecord(**dict(row)) for row in cur.fetchall()]
            buckets[key] = rows

        conn.close()

        insights = []
        if buckets["ghg"]:
            latest = buckets["ghg"][0]
            insights.append(
                f"Greenhouse gas reduction in Europe reached about {latest.value:.0f}{latest.unit} by {latest.year}."
            )
        if buckets["jobs"]:
            total_jobs = next((x for x in buckets["jobs"] if x.metric == "renewable_jobs"), None)
            solar_jobs = next((x for x in buckets["jobs"] if x.metric == "solar_jobs"), None)
            wind_jobs = next((x for x in buckets["jobs"] if x.metric == "wind_jobs"), None)
            if total_jobs:
                insights.append(
                    f"Renewable energy supports roughly {int(total_jobs.value):,} jobs in Europe."
                )
            if solar_jobs and wind_jobs:
                insights.append(
                    f"Wind and solar are the strongest employment drivers, contributing about {int(wind_jobs.value):,} and {int(solar_jobs.value):,} jobs respectively."
                )
        if buckets["investment"]:
            latest_inv = buckets["investment"][0]
            insights.append(
                f"Renewable investment reached about €{latest_inv.value:.1f} billion in {latest_inv.year}."
            )
        if buckets["costs"]:
            storage = buckets["costs"][0]
            insights.append(
                f"Storage and grid integration costs remain a pressure point, with cost pressure estimated near {storage.value:.1f}{storage.unit}."
            )

        return {
            "agent": "EconomicDataAgent",
            "query": query,
            "records": {k: [asdict(x) for x in v] for k, v in buckets.items()},
            "insights": insights,
        }


# -----------------------------
# Agent 2: Academic Search Agent
# -----------------------------
class AcademicSearchAgent:
    def __init__(self, max_results: int = 8) -> None:
        self.max_results = max_results

    def fetch_arxiv(self, query: str) -> List[PaperRecord]:
        search_query = quote_plus(query)
        url = (
            "http://export.arxiv.org/api/query?"
            f"search_query=all:{search_query}&start=0&max_results={self.max_results}"
        )
        xml_text = safe_fetch(url)
        root = ET.fromstring(xml_text)

        ns = {
            "atom": "http://www.w3.org/2005/Atom"
        }

        results: List[PaperRecord] = []
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            summary = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            published = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()
            link = ""
            for link_el in entry.findall("atom:link", ns):
                href = link_el.attrib.get("href", "")
                rel = link_el.attrib.get("rel", "")
                if rel == "alternate":
                    link = href
                    break
            authors = [a.findtext("atom:name", default="", namespaces=ns) for a in entry.findall("atom:author", ns)]
            score = overlap_score(query, f"{title} {summary}")
            results.append(
                PaperRecord(
                    title=title,
                    summary=summary,
                    authors=authors,
                    published=published,
                    link=link,
                    score=score,
                )
            )

        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def run(self, query: str) -> Dict[str, Any]:
        academic_query = (
            "renewable energy adoption Europe economic impacts environmental impacts "
            "grid stability energy storage jobs emissions policy"
        )
        papers = self.fetch_arxiv(academic_query)
        insights = []
        for p in papers[:3]:
            insights.append(
                f"Paper: {p.title} | Insight: {shorten(p.summary, 180)}"
            )

        return {
            "agent": "AcademicSearchAgent",
            "query": query,
            "papers": [asdict(p) for p in papers[:5]],
            "insights": insights,
        }


# -----------------------------
# Agent 3: News / Policy Search Agent
# -----------------------------
class NewsPolicyAgent:
    def __init__(self, max_results: int = 8) -> None:
        self.max_results = max_results

    def fetch_google_news_rss(self, query: str) -> List[NewsRecord]:
        rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"
        xml_text = safe_fetch(rss_url)
        root = ET.fromstring(xml_text)

        items = root.findall("./channel/item")
        news: List[NewsRecord] = []
        for item in items[: self.max_results]:
            title = item.findtext("title", default="").strip()
            link = item.findtext("link", default="").strip()
            pub_date = item.findtext("pubDate", default="").strip()
            source_el = item.find("source")
            source_name = source_el.text.strip() if source_el is not None and source_el.text else "Unknown"
            description = item.findtext("description", default="").strip()
            score = overlap_score(query, f"{title} {description}")
            news.append(
                NewsRecord(
                    title=title,
                    link=link,
                    published=pub_date,
                    source=source_name,
                    summary=shorten(description, 180),
                    score=score,
                )
            )

        news.sort(key=lambda x: x.score, reverse=True)
        return news

    def run(self, query: str) -> Dict[str, Any]:
        news_query = "Europe renewable energy policy jobs emissions solar wind grid storage"
        items = self.fetch_google_news_rss(news_query)
        insights = []
        for item in items[:3]:
            insights.append(
                f"News: {item.title} ({item.source}) | {item.published}"
            )

        return {
            "agent": "NewsPolicyAgent",
            "query": query,
            "news": [asdict(x) for x in items[:5]],
            "insights": insights,
        }


# -----------------------------
# Agent 4: Recommendation Agent
# -----------------------------
class RecommendationAgent:
    def __init__(self) -> None:
        self.catalog = [
            {
                "title": "IEA Renewables Market Report",
                "category": "report",
                "description": "Market outlook for renewable capacity, investment, and policy developments.",
            },
            {
                "title": "European Green Deal Policy Tracker",
                "category": "policy",
                "description": "Policy measures linked to emissions reduction, energy transition, and climate targets.",
            },
            {
                "title": "Offshore Wind Outlook Europe",
                "category": "industry",
                "description": "Analysis of offshore wind deployment, jobs, and infrastructure bottlenecks.",
            },
            {
                "title": "Energy Storage and Grid Flexibility Review",
                "category": "technical",
                "description": "Covers storage costs, intermittency, and grid balancing challenges.",
            },
            {
                "title": "Renewable Employment in Europe Dashboard",
                "category": "data",
                "description": "Employment trends across solar, wind, and supporting clean energy sectors.",
            },
        ]

    def run(self, query: str, context_text: str) -> Dict[str, Any]:
        results: List[RecommendationRecord] = []
        full_context = f"{query} {context_text}"
        for item in self.catalog:
            score = overlap_score(full_context, f"{item['title']} {item['description']} {item['category']}")
            reason = shorten(item["description"], 120)
            results.append(
                RecommendationRecord(
                    title=item["title"],
                    category=item["category"],
                    reason=reason,
                    score=score,
                )
            )
        results.sort(key=lambda x: x.score, reverse=True)
        return {
            "agent": "RecommendationAgent",
            "query": query,
            "recommendations": [asdict(x) for x in results[:4]],
            "insights": [f"Recommended {r.title} ({r.category})" for r in results[:3]],
        }


# -----------------------------
# Orchestrator / Coordinator
# -----------------------------
class MultiDomainResearchAssistant:
    def __init__(self) -> None:
        self.economic_agent = EconomicDataAgent()
        self.academic_agent = AcademicSearchAgent()
        self.news_agent = NewsPolicyAgent()
        self.recommendation_agent = RecommendationAgent()

    def synthesize(self, user_query: str, econ: Dict[str, Any], acad: Dict[str, Any], news: Dict[str, Any], recs: Dict[str, Any]) -> str:
        econ_points = econ.get("insights", [])
        acad_points = acad.get("insights", [])
        news_points = news.get("insights", [])
        rec_points = recs.get("insights", [])

        paragraphs = []
        paragraphs.append("Integrated Response")
        paragraphs.append(
            "Adopting renewable energy in Europe appears to deliver both economic and environmental benefits, but the trade-offs are real and should not be ignored."
        )

        if econ_points:
            paragraphs.append(
                "Economic and environmental signals from the structured dataset suggest the transition is materially significant: "
                + " ".join(econ_points)
            )

        if acad_points:
            paragraphs.append(
                "Academic literature adds a more cautious view. The strongest recurring themes are emissions reduction, labor-market expansion, and unresolved constraints around intermittency, grid stability, and storage economics. Representative evidence includes: "
                + " ".join(acad_points)
            )

        if news_points:
            paragraphs.append(
                "Recent news and policy coverage shows the topic is still moving, which matters because this is not a finished transition. Recent signals include: "
                + " ".join(news_points)
            )

        if rec_points:
            paragraphs.append(
                "For deeper follow-up, the most relevant supporting resources are: " + "; ".join(rec_points) + "."
            )

        paragraphs.append(
            "Bottom line: Europe has gained emissions reductions, investment momentum, and job creation from renewable adoption, but the next bottleneck is system integration. Anyone claiming only upside is skipping the grid, storage, and cost side of the story."
        )

        return "\n\n".join(paragraphs)

    def run(self, user_query: str) -> Dict[str, Any]:
        econ = self.economic_agent.run(user_query)
        acad = self.academic_agent.run(user_query)
        news = self.news_agent.run(user_query)

        context_text = " ".join(econ.get("insights", []) + acad.get("insights", []) + news.get("insights", []))
        recs = self.recommendation_agent.run(user_query, context_text)

        final_response = self.synthesize(user_query, econ, acad, news, recs)

        return {
            "query": user_query,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "workflow": {
                "agent_1": econ,
                "agent_2": acad,
                "agent_3": news,
                "agent_4": recs,
            },
            "final_response": final_response,
        }


# -----------------------------
# CLI Runner
# -----------------------------
def print_section(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


if __name__ == "__main__":
    query = "What are the economic and environmental impacts of renewable energy adoption in Europe?"
    assistant = MultiDomainResearchAssistant()
    result = assistant.run(query)

    print_section("USER QUERY")
    print(result["query"])

    print_section("AGENT 1 - ECONOMIC DATA")
    print(json.dumps(result["workflow"]["agent_1"], indent=2))

    print_section("AGENT 2 - ACADEMIC SEARCH")
    print(json.dumps(result["workflow"]["agent_2"], indent=2))

    print_section("AGENT 3 - NEWS / POLICY")
    print(json.dumps(result["workflow"]["agent_3"], indent=2))

    print_section("AGENT 4 - RECOMMENDATIONS")
    print(json.dumps(result["workflow"]["agent_4"], indent=2))

    print_section("FINAL SYNTHESIZED RESPONSE")
    print(result["final_response"])
