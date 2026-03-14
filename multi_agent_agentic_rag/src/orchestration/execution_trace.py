import json
import os
import uuid

from src.models.schemas import RunTrace, RunTraceEvent


class ExecutionTracer:
    def __init__(self, query: str) -> None:
        self.trace = RunTrace(run_id=str(uuid.uuid4()), query=query)

    def add_event(
        self,
        event_type: str,
        component: str,
        message: str,
        metadata: dict | None = None,
    ) -> None:
        self.trace.events.append(
            RunTraceEvent(
                event_type=event_type,
                component=component,
                message=message,
                metadata=metadata or {},
            )
        )

    def set_selected_agents(self, agents: list[str]) -> None:
        self.trace.selected_agents = agents

    def save(self, output_dir: str = "runs") -> str:
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, f"{self.trace.run_id}.json")

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.trace.model_dump(), f, indent=2)

        return path