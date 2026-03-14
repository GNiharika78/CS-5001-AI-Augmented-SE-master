from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SourceItem(BaseModel):
    source_type: str
    title: str
    snippet: str
    score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_name: str
    query: str
    summary: str
    sources: List[SourceItem] = Field(default_factory=list)
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    success: bool = True
    error: Optional[str] = None


class FinalResponse(BaseModel):
    query: str
    selected_agents: List[str]
    agent_results: List[AgentResult]
    synthesized_answer: str
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0


class RunTraceEvent(BaseModel):
    event_type: str
    component: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunTrace(BaseModel):
    run_id: str
    query: str
    selected_agents: List[str] = Field(default_factory=list)
    events: List[RunTraceEvent] = Field(default_factory=list)