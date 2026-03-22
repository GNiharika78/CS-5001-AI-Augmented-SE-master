from __future__ import annotations

from typing import Any, Dict

from protocols.a2a import A2AMessage


class PlannerAgent:
    def __init__(self) -> None:
        self.name = "planner"

    def handle(self, message: A2AMessage) -> Dict[str, Any]:
        if message.task == "plan_from_review":
            return self._plan_from_review(message.payload)
        if message.task == "plan_draft":
            return self._plan_draft(message.payload)
        raise ValueError(f"Planner cannot handle task: {message.task}")

    def _plan_from_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        review = payload["review"]
        issues = review.get("issues", [])
        risk = review.get("risk", "low")
        change_type = review.get("change_type", "chore")

        if any(i["type"] == "security" for i in issues):
            decision = "create_issue"
            justification = "Security-related signal found in diff; track and resolve explicitly."
        elif any(i["type"] in ("reliability", "performance") for i in issues) and risk in ("medium", "high"):
            decision = "create_issue"
            justification = "Correctness or performance concern found in reviewed changes."
        elif change_type in ("feature", "refactor") and risk in ("medium", "high"):
            decision = "create_pr"
            justification = "Change looks substantial enough for PR-level review."
        else:
            decision = "no_action"
            justification = "No strong risk signals detected beyond normal change review."

        return {
            "plan": {
                "decision": decision,
                "justification": justification,
                "must_reference_evidence": True,
                "recommended_kind": (
                    "issue" if decision == "create_issue"
                    else "pr" if decision == "create_pr"
                    else "none"
                ),
            }
        }

    def _plan_draft(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        kind = payload["kind"]
        instruction = payload["instruction"].strip()
        use_review = bool(payload.get("use_review", False))

        if kind == "issue":
            required_fields = ["title", "problem", "evidence", "acceptance_criteria", "risk_level"]
        else:
            required_fields = ["title", "summary", "files_affected", "behavior_change", "test_plan", "risk_level"]

        return {
            "plan": {
                "kind": kind,
                "instruction": instruction,
                "use_review": use_review,
                "required_fields": required_fields,
            }
        }