from __future__ import annotations

from typing import Any, Dict

from protocols.a2a import A2AMessage


class GatekeeperAgent:
    def __init__(self, mcp_client) -> None:
        self.mcp = mcp_client
        self.name = "gatekeeper"

    def handle(self, message: A2AMessage) -> Dict[str, Any]:
        if message.task == "reflect_draft":
            return self._reflect_draft(message.payload)
        if message.task == "approve_and_create":
            return self._approve_and_create(message.payload)
        if message.task == "reflect_improvement":
            return self._reflect_improvement(message.payload)
        raise ValueError(f"Gatekeeper cannot handle task: {message.task}")

    def _reflect_draft(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload["draft"]

        issues = []
        missing = []
        for field in draft.get("required_fields", []):
            if field not in draft.get("fields", {}) or not str(draft["fields"][field]).strip():
                missing.append(field)
        if missing:
            issues.append(f"Missing required fields: {', '.join(missing)}")

        evidence = draft.get("evidence", [])
        if not evidence:
            issues.append("Missing evidence references (diff hunks / file reads).")

        if draft.get("kind") == "pr":
            if not draft["fields"].get("test_plan", "").strip():
                issues.append("Missing test plan.")

        verdict = "PASS" if not issues else "FAIL"
        return {
            "reflection": {
                "verdict": verdict,
                "summary": "All checks satisfied." if verdict == "PASS" else issues[0],
                "checks": {
                    "missing_required_fields": missing,
                    "has_evidence": bool(evidence),
                    "has_test_plan_if_pr": (draft.get("kind") != "pr") or bool(draft["fields"].get("test_plan", "").strip()),
                    "issues": issues,
                }
            }
        }

    def _approve_and_create(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        draft = payload["draft"]
        approved = payload["approved"]

        if not approved:
            return {"result": "[Gatekeeper] Draft rejected. No changes made."}

        kind = draft["kind"]
        title = draft["fields"]["title"]
        body = draft["rendered"]

        if kind == "issue":
            url = self.mcp.call("github", "gh_issue_create", title=title, body=body)
            return {"result": f"[Tool] GitHub API call successful.\n{url}"}

        url = self.mcp.call(
            "github",
            "gh_pr_create",
            title=title,
            body=body,
            base=draft.get("gh", {}).get("base", "main")
        )
        return {"result": f"[Tool] GitHub API call successful.\n{url}"}

    def _reflect_improvement(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        critique = payload["critique"]
        improved = payload["improved"]

        issues = []
        if not critique.get("points"):
            issues.append("Critique lacks specific points.")
        if "Acceptance Criteria" not in improved.get("rendered", "") and "Acceptance criteria" not in improved.get("rendered", ""):
            issues.append("Improved version lacks acceptance criteria section.")

        verdict = "PASS" if not issues else "FAIL"
        return {
            "reflection": {
                "verdict": verdict,
                "summary": "OK" if verdict == "PASS" else issues[0],
                "issues": issues,
            }
        }