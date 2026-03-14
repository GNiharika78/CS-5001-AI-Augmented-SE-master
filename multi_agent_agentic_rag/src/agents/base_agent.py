from __future__ import annotations

from abc import ABC, abstractmethod
from src.models.schemas import AgentResult


class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, query: str) -> AgentResult:
        raise NotImplementedError