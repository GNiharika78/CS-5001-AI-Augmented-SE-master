from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional


class DraftStore:
    def __init__(self, root: str = ".agent_protocol", artifacts_root: str = "test_artifacts") -> None:
        self.root = root
        self.artifacts_root = artifacts_root

        os.makedirs(self.root, exist_ok=True)
        os.makedirs(self.artifacts_root, exist_ok=True)

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

    def save_named_artifact(self, filename: str, payload: Dict[str, Any]) -> str:
        """
        Save a committed test artifact for professor review.
        Example: review_no_action.json, review_security_issue.json
        """
        if not filename.endswith(".json"):
            filename += ".json"

        path = os.path.join(self.artifacts_root, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return path