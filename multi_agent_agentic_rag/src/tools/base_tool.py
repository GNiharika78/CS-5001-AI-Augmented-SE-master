from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, query: str) -> Dict[str, Any]:
        raise NotImplementedError