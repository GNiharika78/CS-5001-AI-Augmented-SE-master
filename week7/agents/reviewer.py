from __future__ import annotations

import re
from typing import Any, Dict, List

from protocols.a2a import A2AMessage


def _truncate(text: str, limit: int = 120000) -> str:
    data = text.encode("utf-8", errors="replace")
    if len(data) <= limit:
        return text
    return data[:limit].decode("utf-8", errors="replace") + "\n...<truncated>..."


class ReviewerAgent:
    def __init__(self, mcp_client) -> None:
        self.mcp = mcp_client
        self.name = "reviewer"

    def handle(self, message: A2AMessage) -> Dict[str, Any]:
        if message.task == "review_changes":
            return self._review_changes(message.payload)
        if message.task == "improve_existing_fetch":
            return self._fetch_existing(message.payload)
        raise ValueError(f"Reviewer cannot handle task: {message.task}")

    def _review_changes(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.mcp.call("git", "ensure_git_repo"):
            raise RuntimeError("Not inside a git repository")

        base = payload.get("base")
        commit_range = payload.get("commit_range")

        if base:
            diff = self.mcp.call("git", "git_diff_base", base=base)
            files = self.mcp.call("git", "git_changed_files_base", base=base)
            scope = {"mode": "base", "base": base}
        else:
            diff = self.mcp.call("git", "git_diff_range", commit_range=commit_range)
            files = self.mcp.call("git", "git_changed_files_range", commit_range=commit_range)
            scope = {"mode": "range", "range": commit_range}

        diff_excerpt = _truncate(diff)
        issues = self._detect_issues(diff_excerpt)
        risk = self._risk(diff_excerpt, files, issues)
        change_type = self._classify(files, diff_excerpt)

        evidence = [{"kind": "diff-signal", "text": i["evidence"]} for i in issues]

        return {
            "review": {
                "scope": scope,
                "changed_files": files,
                "diff_bytes": len(diff.encode("utf-8", errors="replace")),
                "diff_excerpt": diff_excerpt,
                "change_type": change_type,
                "risk": risk,
                "issues": issues,
                "evidence": evidence,
            }
        }

    def _fetch_existing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        kind = payload["kind"]
        number = int(payload["number"])
        if kind == "issue":
            data = self.mcp.call("github", "gh_issue_view", number=number)
        else:
            data = self.mcp.call("github", "gh_pr_view", number=number)
        return {"kind": kind, "number": number, "existing": data}

    def _classify(self, files: List[str], diff_text: str) -> str:
        if files and all(f.lower().endswith((".md", ".rst")) for f in files):
            return "docs"
        if re.search(r"\+\s*(def |class |function )", diff_text):
            return "feature"
        if "refactor" in diff_text.lower():
            return "refactor"
        return "chore"

    def _risk(self, diff_text: str, files: List[str], issues: List[Dict[str, str]]) -> str:
        if any(i["type"] == "security" for i in issues):
            return "high"
        if len(files) > 8 or diff_text.count("\n") > 600:
            return "medium"
        return "low"

    def _detect_issues(self, diff_text: str) -> List[Dict[str, str]]:
        issues: List[Dict[str, str]] = []

        if re.search(r"\+\s*print\(", diff_text):
            issues.append({
                "type": "quality",
                "title": "Debug prints added",
                "evidence": "Found `print(...)` in added lines.",
                "suggestion": "Replace debug prints with structured logging."
            })

        if re.search(r"\+\s*(password|secret|token)\s*=", diff_text, re.IGNORECASE):
            issues.append({
                "type": "security",
                "title": "Potential secret in code",
                "evidence": "Found assignment to password/secret/token in added lines.",
                "suggestion": "Move secrets to environment variables or a secret manager."
            })

        if re.search(r"\+\s*except\s*:\s*$", diff_text, re.MULTILINE):
            issues.append({
                "type": "reliability",
                "title": "Bare except added",
                "evidence": "Found bare `except:` in added lines.",
                "suggestion": "Catch specific exceptions."
            })

        return issues