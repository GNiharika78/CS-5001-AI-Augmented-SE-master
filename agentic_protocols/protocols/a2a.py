from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import uuid


@dataclass
class A2AMessage:
    sender: str
    recipient: str
    task: str
    payload: Dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class A2ABus:
    """
    Simple local A2A-style message bus.
    Agents exchange structured messages through this bus.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, Any] = {}

    def register(self, agent_name: str, agent: Any) -> None:
        self._agents[agent_name] = agent

    def send(self, message: A2AMessage) -> Dict[str, Any]:
        if message.recipient not in self._agents:
            raise ValueError(f"Unknown recipient: {message.recipient}")
        agent = self._agents[message.recipient]
        return agent.handle(message)