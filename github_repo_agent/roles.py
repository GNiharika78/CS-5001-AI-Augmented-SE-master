import json
import re
from typing import Any, Dict, List, Optional

from tools import (
    ToolError,
    ensure_git_repo,
    git_diff_base,
    git_diff_range,
    git_changed_files_base,
    git_changed_files_range,
    read_file,
    gh_issue_view,
    gh_pr_view,
    gh_issue_create,
    gh_pr_create,
)
from llm import LLM
from reflection import reflect_draft, reflect_improvement
from store import DraftStore

def truncate(s: str, max_bytes: int) -> str:
    b = s.encode("utf-8", errors="replace")
    if len(b) <= max_bytes:
        return s
    return b[:max_bytes].decode("utf-8", errors="replace") + "\n...<truncated>..."

def classify_change(diff_text: str, changed_files: List[str]) -> str:
    # Simple heuristics; deterministic.
    if any("test" in f.lower() for f in changed_files) and ("fix" in diff_text.lower() or "bug" in diff_text.lower()):
        return "bugfix"
    if any(f.lower().endswith((".md", ".rst")) for f in changed_files):
        return "docs"
    if "refactor" in diff_text.lower():
        return "refactor"
    if any(f.lower().endswith((".sql",)) for f in changed_files):
        return "data"
    # Feature signal: added endpoints/routes/components
    if re.search(r"\+\s*(def |class |function |\brouter\b|\broute\b|\bendpoint\b)", diff_text):
        return "feature"
    return "chore"

def risk_assessment(diff_text: str, changed_files: List[str]) -> str:
    # Deterministic heuristics.
    high_risk_files = ("auth", "payment", "billing", "crypto", "security", "permissions", "iam")
    if any(any(k in f.lower() for k in high_risk_files) for f in changed_files):
        return "high"
    if len(changed_files) > 25 or diff_text.count("\n") > 2000:
        return "high"
    if len(changed_files) > 8 or diff_text.count("\n") > 600:
        return "medium"
    if re.search(r"\+\s*TODO|\+\s*FIXME", diff_text):
        return "medium"
    return "low"

def detect_issues(diff_text: str, changed_files: List[str]) -> List[Dict[str, str]]:
    issues = []
    # Evidence must come from diff/file reads; so we reference patterns + include snippets.
    if re.search(r"\+\s*except\s*:\s*$", diff_text, re.MULTILINE):
        issues.append({
            "type": "reliability",
            "title": "Bare except added",
            "evidence": "Found `except:` added in diff (may swallow errors).",
            "suggestion": "Catch specific exceptions and log context."
        })
    if re.search(r"\+\s*print\(", diff_text):
        issues.append({
            "type": "quality",
            "title": "Debug prints added",
            "evidence": "Found `print(...)` added in diff.",
            "suggestion": "Use structured logger and appropriate log level."
        })
    if re.search(r"\+\s*(password|secret|token)\s*=", diff_text, re.IGNORECASE):
        issues.append({
            "type": "security",
            "title": "Potential secret in code",
            "evidence": "Found assignment to password/secret/token in added lines.",
            "suggestion": "Move secrets to env/secret manager and scrub history if needed."
        })
    if re.search(r"\+\s*eval\(|\+\s*exec\(", diff_text):
        issues.append({
            "type": "security",
            "title": "Dynamic code execution introduced",
            "evidence": "Found eval/exec added in diff.",
            "suggestion": "Avoid eval/exec; use safe parsers/whitelists."
        })
    if re.search(r"\+\s*SELECT\s+\*\s+FROM", diff_text, re.IGNORECASE):
        issues.append({
            "type": "performance",
            "title": "SELECT * introduced",
            "evidence": "Found `SELECT * FROM` in added SQL.",
            "suggestion": "Select explicit columns to reduce payload and avoid schema coupling."
        })
    return issues

class Reviewer:
    def review(self, base: Optional[str], commit_range: Optional[str], max_diff_bytes: int) -> Dict[str, Any]:
        ensure_git_repo()

        if base:
            diff = git_diff_base(base)
            files = git_changed_files_base(base)
            scope = {"mode": "base", "base": base}
        else:
            diff = git_diff_range(commit_range or "")
            files = git_changed_files_range(commit_range or "")
            scope = {"mode": "range", "range": commit_range}

        diff_t = truncate(diff, max_diff_bytes)
        change_type = classify_change(diff_t, files)
        risk = risk_assessment(diff_t, files)
        issues = detect_issues(diff_t, files)

        # Evidence anchors: include short diff excerpts around matched lines for at least 1-2 signals.
        evidence = []
        for isx in issues[:4]:
            evidence.append({"kind": "diff-signal", "text": isx["evidence"]})

        return {
            "scope": scope,
            "changed_files": files,
            "diff_bytes": len(diff.encode("utf-8", errors="replace")),
            "diff_excerpt": diff_t,
            "change_type": change_type,
            "risk": risk,
            "issues": issues,
            "evidence": evidence,
        }

class Planner:
    def plan_from_review(self, review: Dict[str, Any]) -> Dict[str, Any]:
        issues = review.get("issues", [])
        risk = review.get("risk", "low")
        change_type = review.get("change_type", "chore")

        # Decide action with evidence requirement.
        if any(i["type"] in ("security",) for i in issues):
            decision = "create_issue"
            justification = "Security-related signal found in diff; track and resolve explicitly."
        elif any(i["type"] in ("reliability", "performance") for i in issues) and risk in ("medium", "high"):
            decision = "create_issue"
            justification = "Medium/high risk with correctness/performance concerns; create issue for remediation."
        elif change_type in ("feature", "refactor") and risk in ("medium", "high"):
            decision = "create_pr"
            justification = "Large/medium-risk change suggests PR for structured review (tests + rollout notes)."
        else:
            decision = "no_action"
            justification = "No strong risk signals detected beyond normal change review."

        return {
            "decision": decision,
            "justification": justification,
            "must_reference_evidence": True,
            "recommended_kind": "issue" if decision == "create_issue" else ("pr" if decision == "create_pr" else "none"),
        }

    def plan_draft(self, kind: str, instruction: str, use_review: bool, store: DraftStore) -> Dict[str, Any]:
        plan = {
            "kind": kind,
            "instruction": instruction.strip(),
            "use_review": use_review,
            "required_fields": [],
        }
        if kind == "issue":
            plan["required_fields"] = ["title", "problem", "evidence", "acceptance_criteria", "risk_level"]
        else:
            plan["required_fields"] = ["title", "summary", "files_affected", "behavior_change", "test_plan", "risk_level"]
        # Guardrails: instruction must not be empty
        if not plan["instruction"]:
            raise ValueError("Instruction cannot be empty")
        # If user requested evidence from review but none exists, proceed without it (safe).
        if use_review and not store.load_review():
            plan["use_review"] = False
        return plan

class Writer:
    def __init__(self):
        self.llm = LLM()

    def _gather_evidence(self, store: DraftStore) -> List[Dict[str, str]]:
        ev = []
        last = store.load_review()
        if last and "review" in last:
            r = last["review"]
            ev.append({"kind": "changed_files", "text": ", ".join(r.get("changed_files", [])[:30])})
            # keep excerpt short; still evidence-based
            ev.append({"kind": "diff_excerpt", "text": truncate(r.get("diff_excerpt", ""), 6000)})
            for e in r.get("evidence", [])[:5]:
                ev.append({"kind": e.get("kind", "evidence"), "text": e.get("text", "")})
        return ev

    def write_draft(self, plan: Dict[str, Any], store: DraftStore) -> Dict[str, Any]:
        evidence = self._gather_evidence(store) if plan.get("use_review") else []

        # Template-based drafting (deterministic, evidence-first). No silent assumptions.
        if plan["kind"] == "issue":
            title = self._issue_title(plan["instruction"])
            risk = self._infer_risk_from_evidence(evidence)
            fields = {
                "title": title,
                "problem": f"{plan['instruction']}\n\n(Describe impact, who is affected, and current behavior.)",
                "evidence": self._render_evidence(evidence) if evidence else "No repo evidence attached (instruction-only draft).",
                "acceptance_criteria": "- [ ] Define expected behavior\n- [ ] Add/adjust tests\n- [ ] Confirm fix with repro steps\n",
                "risk_level": risk,
            }
            rendered = self._render_issue(fields)
            return {
                "kind": "issue",
                "fields": fields,
                "required_fields": plan["required_fields"],
                "evidence": evidence,
                "rendered": rendered,
                "gh": {"action": "issue_create"},
            }

        # PR
        title = self._pr_title(plan["instruction"])
        risk = self._infer_risk_from_evidence(evidence)
        files_affected = self._files_from_evidence(evidence)
        fields = {
            "title": title,
            "summary": f"{plan['instruction']}\n\n(Explain what changed and why.)",
            "files_affected": files_affected or "(Unknown yet — run review with --base/--range for file list.)",
            "behavior_change": "- Describe user-visible behavior changes (or explicitly state: none)\n",
            "test_plan": "- [ ] Unit tests\n- [ ] Integration test / manual steps\n- [ ] Regression areas\n",
            "risk_level": risk,
        }
        rendered = self._render_pr(fields)
        return {
            "kind": "pr",
            "fields": fields,
            "required_fields": plan["required_fields"],
            "evidence": evidence,
            "rendered": rendered,
            "gh": {"action": "pr_create", "base": "main"},
        }

    def improve_existing(self, kind: str, number: int):
        # Tool use only: fetch via gh
        if kind == "issue":
            raw = gh_issue_view(number)
            data = json.loads(raw)
            title, body, url = data.get("title", ""), data.get("body", "") or "", data.get("url", "")
            critique = self._critique_text(kind="issue", title=title, body=body, url=url)
            improved = self._improve_issue(title=title, body=body, url=url)
            return critique, improved

        raw = gh_pr_view(number)
        data = json.loads(raw)
        title, body, url = data.get("title", ""), data.get("body", "") or "", data.get("url", "")
        files = data.get("files", []) or []
        critique = self._critique_text(kind="pr", title=title, body=body, url=url, files=files)
        improved = self._improve_pr(title=title, body=body, url=url, files=files)
        return critique, improved

    # ---- helpers ----
    def _issue_title(self, instruction: str) -> str:
        s = instruction.strip().rstrip(".")
        return s[:80] if s else "Issue: (title needed)"

    def _pr_title(self, instruction: str) -> str:
        s = instruction.strip().rstrip(".")
        if not s.lower().startswith(("pr", "refactor", "fix", "feat", "chore")):
            s = "PR: " + s
        return s[:80]

    def _infer_risk_from_evidence(self, evidence: List[Dict[str, str]]) -> str:
        blob = "\n".join(e.get("text", "") for e in evidence).lower()
        if any(k in blob for k in ["auth", "payment", "billing", "security", "iam", "permissions"]):
            return "high"
        if "diff_excerpt" in [e.get("kind") for e in evidence]:
            # if we have diff evidence but it's large, call it medium
            if len(blob) > 5000:
                return "medium"
        return "low"

    def _files_from_evidence(self, evidence: List[Dict[str, str]]) -> str:
        for e in evidence:
            if e.get("kind") == "changed_files":
                return e.get("text", "")
        return ""

    def _render_evidence(self, evidence: List[Dict[str, str]]) -> str:
        out = []
        for e in evidence:
            out.append(f"- **{e['kind']}**: {e['text'][:1500]}")
        return "\n".join(out)

    def _render_issue(self, f: Dict[str, str]) -> str:
        return (
            f"# {f['title']}\n\n"
            f"## Problem\n{f['problem']}\n\n"
            f"## Evidence\n{f['evidence']}\n\n"
            f"## Acceptance Criteria\n{f['acceptance_criteria']}\n\n"
            f"## Risk Level\n**{f['risk_level']}**\n"
        )

    def _render_pr(self, f: Dict[str, str]) -> str:
        return (
            f"# {f['title']}\n\n"
            f"## Summary\n{f['summary']}\n\n"
            f"## Files Affected\n{f['files_affected']}\n\n"
            f"## Behavior Change\n{f['behavior_change']}\n\n"
            f"## Test Plan\n{f['test_plan']}\n\n"
            f"## Risk Level\n**{f['risk_level']}**\n"
        )

    def _critique_text(self, kind: str, title: str, body: str, url: str, files: Optional[list] = None) -> Dict[str, Any]:
        points = []
        if not title.strip():
            points.append("Missing/empty title.")
        if not body.strip():
            points.append("Missing description/body.")
        if "acceptance" not in body.lower():
            points.append("No clear acceptance criteria.")
        if kind == "pr" and ("test" not in body.lower()):
            points.append("No explicit test plan.")

        headline = f"{kind.upper()} lacks clarity." if points else f"{kind.upper()} is mostly clear."
        rendered = "\n".join(f"- {p}" for p in points) if points else "- No major gaps detected."
        if files is not None and kind == "pr" and not files:
            rendered += "\n- Files list missing from PR metadata (or GH returned none)."

        return {"headline": headline, "url": url, "points": points, "rendered": rendered}

    def _improve_issue(self, title: str, body: str, url: str) -> Dict[str, Any]:
        improved = (
            f"# {title.strip() or 'Issue: <fill title>'}\n\n"
            f"## Problem\n"
            f"(Rewrite in 2–4 sentences: current behavior, expected behavior, impact.)\n\n"
            f"## Evidence\n"
            f"- Link: {url}\n"
            f"- Repro steps:\n  1.\n  2.\n  3.\n\n"
            f"## Acceptance Criteria\n"
            f"- [ ] Given <context>, when <action>, then <expected outcome>\n"
            f"- [ ] Add tests covering <cases>\n"
            f"- [ ] Confirm no regression in <areas>\n\n"
            f"## Risk Level\n"
            f"Low / Medium / High (pick one and justify)\n"
        )
        return {"rendered": improved}

    def _improve_pr(self, title: str, body: str, url: str, files: list) -> Dict[str, Any]:
        file_lines = "\n".join(f"- {f.get('path','(unknown)')}" for f in files[:50]) if files else "(No file list available)"
        improved = (
            f"# {title.strip() or 'PR: <fill title>'}\n\n"
            f"## Summary\n"
            f"(What changed and why. Mention user/business impact.)\n\n"
            f"## Files Affected\n{file_lines}\n\n"
            f"## Behavior Change\n"
            f"- Before:\n- After:\n\n"
            f"## Test Plan\n"
            f"- [ ] Unit tests: (list)\n"
            f"- [ ] Manual steps: (commands, screenshots, curl, etc.)\n"
            f"- [ ] Rollback plan: (if applicable)\n\n"
            f"## Risk Level\n"
            f"Low / Medium / High (pick one and justify)\n\n"
            f"## Reference\n- Link: {url}\n"
        )
        return {"rendered": improved}

class Gatekeeper:
    def reflect(self, draft: Dict[str, Any]) -> Dict[str, Any]:
        return reflect_draft(draft)

    def reflect_improvement(self, critique: Dict[str, Any], improved: Dict[str, Any]) -> Dict[str, Any]:
        return reflect_improvement(critique, improved)

    def create_on_github(self, draft: Dict[str, Any]) -> str:
        # Enforce no silent creation unless explicit approve --yes already happened in agent.py
        kind = draft.get("kind")
        fields = draft.get("fields", {})
        title = fields.get("title", "").strip()
        body = draft.get("rendered", "").strip()
        if not title or not body:
            raise RuntimeError("Refusing to create: empty title/body")

        if kind == "issue":
            print("[Gatekeeper] Creating Issue...")
            out = gh_issue_create(title=title, body=body)
            return "[Tool] GitHub API call successful.\n" + out

        if kind == "pr":
            print("[Gatekeeper] Creating Pull Request...")
            base = draft.get("gh", {}).get("base", "main")
            out = gh_pr_create(title=title, body=body, base=base)
            return "[Tool] GitHub API call successful.\n" + out

        raise RuntimeError(f"Unknown draft kind: {kind}")