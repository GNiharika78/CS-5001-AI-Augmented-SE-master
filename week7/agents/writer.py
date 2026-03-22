from __future__ import annotations

from typing import Any, Dict, List

from protocols.a2a import A2AMessage


def truncate_title(text: str, max_len: int = 80) -> str:
    text = text.strip()
    if len(text) <= max_len:
        return text
    cut = text[:max_len].rstrip()
    if " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return cut + "..."


class WriterAgent:
    def __init__(self) -> None:
        self.name = "writer"

    def handle(self, message: A2AMessage) -> Dict[str, Any]:
        if message.task == "write_draft":
            return self._write_draft(message.payload)
        if message.task == "improve_existing":
            return self._improve_existing(message.payload)
        raise ValueError(f"Writer cannot handle task: {message.task}")

    def _write_draft(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        plan = payload["plan"]
        review = payload.get("review")

        evidence: List[Dict[str, str]] = []
        if review and plan.get("use_review"):
            evidence.append({"kind": "changed_files", "text": ", ".join(review.get("changed_files", []))})
            evidence.append({"kind": "diff_excerpt", "text": review.get("diff_excerpt", "")[:3000]})
            for ev in review.get("evidence", []):
                evidence.append(ev)

        if plan["kind"] == "issue":
            title = truncate_title(plan["instruction"])
            fields = {
                "title": title,
                "problem": f"{plan['instruction']}\n\n(Describe impact, who is affected, and current behavior.)",
                "evidence": self._render_evidence(evidence) if evidence else "No repo evidence attached (instruction-only draft).",
                "acceptance_criteria": self._issue_acceptance(plan["instruction"], evidence),
                "risk_level": self._infer_risk(evidence),
            }
            rendered = (
                f"# {fields['title']}\n\n"
                f"## Problem\n{fields['problem']}\n\n"
                f"## Evidence\n{fields['evidence']}\n\n"
                f"## Acceptance Criteria\n{fields['acceptance_criteria']}\n\n"
                f"## Risk Level\n**{fields['risk_level']}**\n"
            )
            return {
                "draft": {
                    "kind": "issue",
                    "fields": fields,
                    "required_fields": plan["required_fields"],
                    "evidence": evidence,
                    "rendered": rendered,
                    "gh": {"action": "issue_create"},
                }
            }

        title = truncate_title("PR: " + plan["instruction"] if not plan["instruction"].lower().startswith("pr") else plan["instruction"])
        files_affected = ""
        for e in evidence:
            if e["kind"] == "changed_files":
                files_affected = e["text"]

        fields = {
            "title": title,
            "summary": f"{plan['instruction']}\n\n(Explain what changed and why.)",
            "files_affected": files_affected or "(Unknown yet — run review first.)",
            "behavior_change": "- Describe user-visible behavior changes (or explicitly state: none)\n",
            "test_plan": "- [ ] Unit tests\n- [ ] Manual verification\n- [ ] Regression check\n",
            "risk_level": self._infer_risk(evidence),
        }
        rendered = (
            f"# {fields['title']}\n\n"
            f"## Summary\n{fields['summary']}\n\n"
            f"## Files Affected\n{fields['files_affected']}\n\n"
            f"## Behavior Change\n{fields['behavior_change']}\n\n"
            f"## Test Plan\n{fields['test_plan']}\n\n"
            f"## Risk Level\n**{fields['risk_level']}**\n"
        )
        return {
            "draft": {
                "kind": "pr",
                "fields": fields,
                "required_fields": plan["required_fields"],
                "evidence": evidence,
                "rendered": rendered,
                "gh": {"action": "pr_create", "base": "main"},
            }
        }

    def _improve_existing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        kind = payload["kind"]
        existing = payload["existing"]

        title = existing.get("title", "")
        body = existing.get("body", "") or ""
        url = existing.get("url", "")

        points = []
        if not title.strip():
            points.append("Missing or unclear title.")
        if not body.strip():
            points.append("Missing body/description.")
        if "acceptance" not in body.lower():
            points.append("No clear acceptance criteria.")
        if kind == "pr" and "test" not in body.lower():
            points.append("No explicit test plan.")

        critique = {
            "headline": f"{kind.upper()} lacks clarity." if points else f"{kind.upper()} is mostly clear.",
            "points": points,
            "rendered": "\n".join(f"- {p}" for p in points) if points else "- No major gaps detected.",
        }

        if kind == "issue":
            improved = (
                f"# {title or 'Improved Issue'}\n\n"
                f"## Problem\n(Rewrite current behavior, expected behavior, and impact.)\n\n"
                f"## Evidence\n- Link: {url}\n- Repro steps:\n  1.\n  2.\n  3.\n\n"
                f"## Acceptance Criteria\n"
                f"- [ ] Define expected behavior clearly\n"
                f"- [ ] Add or update tests\n"
                f"- [ ] Verify the issue is resolved without regression\n\n"
                f"## Risk Level\nLow / Medium / High (pick one and justify)\n"
            )
        else:
            files = existing.get("files", []) or []
            file_lines = "\n".join(f"- {f.get('path', '(unknown)')}" for f in files) if files else "(No file list available)"
            improved = (
                f"# {title or 'Improved PR'}\n\n"
                f"## Summary\n(What changed and why.)\n\n"
                f"## Files Affected\n{file_lines}\n\n"
                f"## Behavior Change\n- Before:\n- After:\n\n"
                f"## Acceptance Criteria\n"
                f"- [ ] PR description accurately reflects the changes\n"
                f"- [ ] Test steps are complete and reproducible\n"
                f"- [ ] Reviewers can validate behavior change clearly\n\n"
                f"## Test Plan\n"
                f"- [ ] Unit tests\n"
                f"- [ ] Manual verification steps\n"
                f"- [ ] Rollback or impact notes if needed\n\n"
                f"## Risk Level\nLow / Medium / High (pick one and justify)\n\n"
                f"## Reference\n- Link: {url}\n"
            )

        return {
            "critique": critique,
            "improved": {"rendered": improved},
        }

    def _issue_acceptance(self, instruction: str, evidence: List[Dict[str, str]]) -> str:
        blob = (instruction + "\n" + "\n".join(e.get("text", "") for e in evidence)).lower()
        if "token" in blob or "secret" in blob or "password" in blob:
            return (
                "- [ ] Remove hardcoded secret/token from source code\n"
                "- [ ] Load the secret from environment variables or a secret manager\n"
                "- [ ] Fail safely when the secret is missing\n"
                "- [ ] Confirm no committed secrets remain in the repository history\n"
            )
        return (
            "- [ ] Define expected behavior\n"
            "- [ ] Add or adjust tests\n"
            "- [ ] Confirm fix with repro steps\n"
        )

    def _infer_risk(self, evidence: List[Dict[str, str]]) -> str:
        blob = "\n".join(e.get("text", "") for e in evidence).lower()
        if any(k in blob for k in ["token", "secret", "password", "security"]):
            return "high"
        if "diff_excerpt" in [e["kind"] for e in evidence]:
            return "medium"
        return "low"

    def _render_evidence(self, evidence: List[Dict[str, str]]) -> str:
        return "\n".join(f"- **{e['kind']}**: {e['text'][:1500]}" for e in evidence)