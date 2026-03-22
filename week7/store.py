from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class DraftStore:
    def __init__(self, root: str = ".agent_protocol") -> None:
        self.root = root
        os.makedirs(self.root, exist_ok=True)
        self.review_path = os.path.join(self.root, "last_review.json")
        self.draft_path = os.path.join(self.root, "draft.json")

    def save_review(self, payload: Dict[str, Any]) -> None:
        with open(self.review_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load_review(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.review_path):
            return None
        with open(self.review_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_draft(self, payload: Dict[str, Any]) -> None:
        with open(self.draft_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def load_draft(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.draft_path):
            return None
        with open(self.draft_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def clear_draft(self) -> None:
        if os.path.exists(self.draft_path):
            os.remove(self.draft_path)