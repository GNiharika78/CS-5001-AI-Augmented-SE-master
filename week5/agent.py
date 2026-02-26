#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Literal, Tuple

import typer
from pydantic import BaseModel, Field
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

app = typer.Typer(no_args_is_help=True)
console = Console()

AGENT_DIR = Path(".agent")
DRAFT_PATH = AGENT_DIR / "draft.json"
REFLECTION_PATH = AGENT_DIR / "reflection.json"

# -------------------------
# Tool Use (real tools only)
# -------------------------

class ToolError(RuntimeError):
    pass

def run_cmd(cmd: List[str], cwd: Optional[Path] = None) -> str:
    """Run a command and return stdout. Raises ToolError on non-zero exit."""
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError as e:
        raise ToolError(f"Command not found: {cmd[0]}") from e

    if proc.returncode != 0:
        raise ToolError(
            f"Command failed ({proc.returncode}): {' '.join(map(shlex.quote, cmd))}\n"
            f"STDERR:\n{proc.stderr.strip()}"
        )
    return proc.stdout

def git_diff(base: Optional[str] = None, commit_range: Optional[str] = None) -> str:
    if base and commit_range:
        raise ToolError("Provide either --base or --range, not both.")
    if base:
        return run_cmd(["git", "diff", f"{base}...HEAD", "--"])
    if commit_range:
        return run_cmd(["git", "diff", commit_range, "--"])
    # default: working tree changes
    return run_cmd(["git", "diff", "--"])

def git_changed_files(base: Optional[str] = None, commit_range: Optional[str] = None) -> List[str]:
    if base:
        out = run_cmd(["git", "diff", "--name-only", f"{base}...HEAD", "--"])
    elif commit_range:
        out = run_cmd(["git", "diff", "--name-only", commit_range, "--"])
    else:
        out = run_cmd(["git", "diff", "--name-only", "--"])
    return [x.strip() for x in out.splitlines() if x.strip()]

def read_file(path: str, max_bytes: int = 40_000) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise ToolError(f"File not found: {path}")
    data = p.read_bytes()
    data = data[:max_bytes]
    try:
        return data.decode("utf-8", errors="replace")
    except Exception:
        return data.decode(errors="replace")

def gh_view_issue(number: int) -> Dict[str, Any]:
    # Tool-grounded: uses gh CLI, no invented content
    out = run_cmd(["gh", "issue", "view", str(number), "--json", "number,title,body,url,labels,state"])
    return json.loads(out)

def gh_view_pr(number: int) -> Dict[str, Any]:
    out = run_cmd([
        "gh", "pr", "view", str(number),
        "--json", "number,title,body,url,labels,state,files,baseRefName,headRefName"
    ])
    return json.loads(out)

def gh_create_issue(title: str, body: str, labels: Optional[List[str]] = None) -> Dict[str, Any]:
    cmd = ["gh", "issue", "create", "--title", title, "--body", body]
    if labels:
        cmd += ["--label", ",".join(labels)]
    out = run_cmd(cmd)
    return {"url": out.strip()}

def gh_create_pr(title: str, body: str, base: Optional[str] = None, head: Optional[str] = None, draft: bool = False) -> Dict[str, Any]:
    cmd = ["gh", "pr", "create", "--title", title, "--body", body]
    if base:
        cmd += ["--base", base]
    if head:
        cmd += ["--head", head]
    if draft:
        cmd += ["--draft"]
    out = run_cmd(cmd)
    return {"url": out.strip()}

# -------------------------
# Models
# -------------------------

Risk = Literal["low", "medium", "high"]
Action = Literal["create_issue", "create_pr", "no_action"]
ChangeType = Literal["feature", "bugfix", "refactor", "docs", "test", "chore", "unknown"]

class ReviewFinding(BaseModel):
    category: str
    evidence: List[str] = Field(default_factory=list)
    suggestion: str

class ReviewReport(BaseModel):
    change_type: ChangeType
    risk: Risk
    findings: List[ReviewFinding]
    decision: Action
    decision_justification: List[str]
    changed_files: List[str] = Field(default_factory=list)

class Plan(BaseModel):
    goal: str
    steps: List[str]
    required_evidence: List[str]
    open_questions: List[str] = Field(default_factory=list)

class DraftType(BaseModel):
    kind: Literal["issue", "pr"]
    title: str
    body: str
    risk: Risk
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ReflectionArtifact(BaseModel):
    verdict: Literal["PASS", "FAIL"]
    reasons: List[str]
    missing_evidence: List[str] = Field(default_factory=list)
    missing_tests: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
    safety_notes: List[str] = Field(default_factory=list)

# -------------------------
# Multi-agent roles
# -------------------------

class Reviewer:
    """Analyzes diff and files. MUST cite evidence from tool outputs (diff lines / file snippets)."""

    def analyze(self, diff_text: str, changed_files: List[str]) -> ReviewReport:
        findings: List[ReviewFinding] = []

        # crude, evidence-first heuristics (replace with your preferred LLM calls if allowed)
        # We still remain grounded: evidence must come from diff or file reads.
        change_type: ChangeType = "unknown"
        risk: Risk = "low"

        # Determine change type
        if any(f.endswith(".md") for f in changed_files):
            change_type = "docs"
        if any(re.search(r"test|spec", f, re.IGNORECASE) for f in changed_files):
            change_type = "test"
        if any(re.search(r"refactor|cleanup", diff_text, re.IGNORECASE) for _ in [0]):
            change_type = "refactor"

        # Risk heuristics
        if any(re.search(r"(migrations?|schema|auth|payment|encryption)", diff_text, re.IGNORECASE) for _ in [0]):
            risk = "high"
        elif len(changed_files) > 15 or diff_text.count("\n") > 800:
            risk = "medium"

        # Evidence-based findings
        if "TODO" in diff_text:
            lines = [l for l in diff_text.splitlines() if "TODO" in l][:5]
            findings.append(ReviewFinding(
                category="quality",
                evidence=lines,
                suggestion="Resolve TODOs or convert them into tracked Issues with clear owners and acceptance criteria."
            ))

        # Detect missing input validation patterns (very basic)
        if re.search(r"request\.json|get_json\(|req\.body", diff_text, re.IGNORECASE) and not re.search(r"validate|schema|zod|joi|pydantic", diff_text, re.IGNORECASE):
            ev = []
            for l in diff_text.splitlines():
                if re.search(r"request\.json|get_json\(|req\.body", l, re.IGNORECASE):
                    ev.append(l.strip())
                    if len(ev) >= 5:
                        break
            findings.append(ReviewFinding(
                category="reliability",
                evidence=ev,
                suggestion="Add explicit input validation (schema-based) and negative tests for malformed payloads."
            ))
            risk = "medium" if risk == "low" else risk

        # Decide action (must justify with evidence)
        decision: Action = "no_action"
        justification: List[str] = []

        if findings:
            decision = "create_issue"
            justification.append("Findings detected that merit tracking.")
            justification.append(f"Evidence snippets: {findings[0].evidence[:2]}")
        else:
            justification.append("No high-signal issues detected from diff-based heuristics.")
            justification.append("Consider adding/confirming tests if this is behavior-changing code.")

        return ReviewReport(
            change_type=change_type,
            risk=risk,
            findings=findings,
            decision=decision,
            decision_justification=justification,
            changed_files=changed_files
        )

class Planner:
    """Planning pattern: create a plan BEFORE drafting."""
    def make_plan_from_review(self, review: ReviewReport, goal: str) -> Plan:
        steps = [
            "Confirm scope from changed files and diff evidence.",
            "Pick the best artifact type (Issue vs PR) based on action decision.",
            "Draft structured content with explicit evidence and acceptance criteria.",
            "Run Critic reflection check to catch missing evidence/tests/unsupported claims.",
            "Require human approval before any GitHub write."
        ]
        required_evidence = []
        if review.findings:
            required_evidence.append("At least 1-3 diff lines that demonstrate the problem.")
        if review.risk in ("medium", "high"):
            required_evidence.append("Explicit test plan (unit/integration/manual steps).")
        return Plan(goal=goal, steps=steps, required_evidence=required_evidence, open_questions=[])

    def make_plan_from_instruction(self, instruction: str) -> Plan:
        return Plan(
            goal=instruction.strip(),
            steps=[
                "Restate the instruction as a concrete outcome.",
                "Determine needed evidence: diff lines, file context, or reproducible steps.",
                "Draft Issue/PR in the required structure.",
                "Critic reflection: verify evidence, missing tests, unsupported claims.",
                "Require explicit approval before creation."
            ],
            required_evidence=["If based on repo changes, include diff/file evidence. If not, include reproduction steps or rationale."],
            open_questions=[]
        )

class Writer:
    """Drafts Issues/PRs. In a real 'vibe coding' version, you can call your chosen LLM here.
    This reference version is deterministic and evidence-driven to avoid hallucination.
    """

    def draft_issue_from_review(self, review: ReviewReport, plan: Plan) -> DraftType:
        title = self._suggest_title_from_review(review, kind="issue")
        evidence_block = self._format_evidence(review)
        acceptance = self._acceptance_criteria_from_findings(review)

        body = "\n".join([
            "## Problem",
            "The recent changes introduce or reveal a potential issue that should be tracked and addressed.",
            "",
            "## Evidence",
            evidence_block or "- (No direct evidence captured; revise by adding diff/file evidence.)",
            "",
            "## Acceptance Criteria",
            *[f"- {a}" for a in acceptance],
            "",
            "## Risk Level",
            f"- **{review.risk.upper()}**",
        ])

        return DraftType(kind="issue", title=title, body=body, risk=review.risk, metadata={"changed_files": review.changed_files})

    def draft_issue_from_instruction(self, instruction: str, risk: Risk = "medium") -> DraftType:
        title = instruction.strip()
        body = "\n".join([
            "## Problem",
            instruction.strip(),
            "",
            "## Evidence",
            "- Provide reproduction steps, logs, or relevant code references (diff/file links).",
            "",
            "## Acceptance Criteria",
            "- Define what “done” looks like with testable outcomes.",
            "",
            "## Risk Level",
            f"- **{risk.upper()}**",
        ])
        return DraftType(kind="issue", title=title, body=body, risk=risk)

    def draft_pr_from_instruction(self, instruction: str, files_affected: Optional[List[str]] = None, risk: Risk = "medium") -> DraftType:
        title = instruction.strip()
        files_affected = files_affected or []
        body = "\n".join([
            "## Summary",
            instruction.strip(),
            "",
            "## Files Affected",
            *([f"- {f}" for f in files_affected] if files_affected else ["- (To be filled after selecting changes)"]),
            "",
            "## Behavior Change",
            "- Describe what changes for users/systems (or state 'No behavior change' if refactor only).",
            "",
            "## Test Plan",
            "- [ ] Unit tests added/updated",
            "- [ ] Integration tests added/updated",
            "- [ ] Manual verification steps documented",
            "",
            "## Risk Level",
            f"- **{risk.upper()}**",
        ])
        return DraftType(kind="pr", title=title, body=body, risk=risk, metadata={"files_affected": files_affected})

    def improve_issue(self, issue: Dict[str, Any]) -> Tuple[List[str], DraftType]:
        critiques = []
        body = issue.get("body") or ""
        if len(body.strip()) < 80:
            critiques.append("Body is very short; likely missing context, evidence, or acceptance criteria.")
        if "Acceptance" not in body and "Criteria" not in body:
            critiques.append("No explicit acceptance criteria found.")
        if "Evidence" not in body:
            critiques.append("No evidence/repro steps found.")

        improved = "\n".join([
            f"## Problem\n{(body.strip() or '(Describe the problem clearly, including expected vs actual.)')}",
            "",
            "## Evidence",
            "- Reproduction steps:",
            "  1. ...",
            "  2. ...",
            "- Logs / screenshots:",
            "- Code references (files/lines):",
            "",
            "## Acceptance Criteria",
            "- [ ] ... (testable outcome)",
            "- [ ] ...",
            "",
            "## Risk Level",
            "- **MEDIUM**",
        ])
        return critiques, DraftType(kind="issue", title=issue.get("title", "Improved Issue"), body=improved, risk="medium", metadata={"number": issue.get("number"), "url": issue.get("url")})

    def improve_pr(self, pr: Dict[str, Any]) -> Tuple[List[str], DraftType]:
        critiques = []
        body = pr.get("body") or ""
        if "Test Plan" not in body:
            critiques.append("Missing a structured test plan.")
        if "Behavior" not in body:
            critiques.append("Behavior change section is missing/unclear.")
        files = [f.get("path") for f in (pr.get("files") or []) if f.get("path")]
        if not files:
            critiques.append("Files affected list is missing (should be enumerated).")

        improved = "\n".join([
            f"## Summary\n{(body.strip() or '(Summarize why this PR exists and what it does.)')}",
            "",
            "## Files Affected",
            *([f"- {p}" for p in files] if files else ["- (List the key files changed)"]),
            "",
            "## Behavior Change",
            "- (Explain user-visible/system-visible changes; or state 'No behavior change' if refactor.)",
            "",
            "## Test Plan",
            "- [ ] Unit tests:",
            "- [ ] Integration tests:",
            "- [ ] Manual verification steps:",
            "",
            "## Risk Level",
            "- **MEDIUM**",
        ])
        return critiques, DraftType(kind="pr", title=pr.get("title", "Improved PR"), body=improved, risk="medium", metadata={"number": pr.get("number"), "url": pr.get("url")})

    def _suggest_title_from_review(self, review: ReviewReport, kind: str) -> str:
        if review.findings:
            main_cat = review.findings[0].category
            return f"{'Track' if kind=='issue' else 'Fix'} {main_cat} concerns from recent changes"
        return "Review: no major issues detected"

    def _format_evidence(self, review: ReviewReport) -> str:
        lines: List[str] = []
        for f in review.findings:
            for ev in f.evidence[:3]:
                lines.append(f"- `{ev}`")
        return "\n".join(lines)

    def _acceptance_criteria_from_findings(self, review: ReviewReport) -> List[str]:
        if not review.findings:
            return ["Confirm no action required; add tests if behavior changes."]
        acc = []
        for f in review.findings:
            acc.append(f"Address: {f.suggestion}")
        acc.append("Add/confirm tests covering the affected paths.")
        return acc

class Critic:
    """Reflection pattern: produces an artifact that checks evidence, tests, unsupported claims, and gating."""
    def reflect(self, draft: DraftType, plan: Optional[Plan] = None) -> ReflectionArtifact:
        reasons: List[str] = []
        missing_evidence: List[str] = []
        missing_tests: List[str] = []
        unsupported: List[str] = []

        # Evidence check
        if "## Evidence" in draft.body:
            # If evidence section exists but is placeholder-y, fail.
            if re.search(r"Provide reproduction|To be filled|No direct evidence captured", draft.body, re.IGNORECASE):
                missing_evidence.append("Evidence section contains placeholders; add diff lines, file refs, or repro steps.")
        else:
            missing_evidence.append("No Evidence section found.")

        # Test plan check (required for PR; good practice for medium/high risk issues too)
        if draft.kind == "pr":
            if "## Test Plan" not in draft.body:
                missing_tests.append("PR missing Test Plan section.")
            elif re.search(r"Manual verification steps documented", draft.body) and "..." in draft.body:
                missing_tests.append("Test plan appears incomplete; add concrete commands/steps.")
        else:
            if draft.risk in ("medium", "high") and "Acceptance Criteria" in draft.body:
                # still require some testability
                if re.search(r"Define what “done” looks like", draft.body):
                    missing_tests.append("Acceptance Criteria are placeholders; make them testable.")

        # Unsupported claim check (simple heuristic)
        if re.search(r"reduces|improves|fixes|prevents", draft.body, re.IGNORECASE) and ("`" not in draft.body and "Reproduction" not in draft.body):
            unsupported.append("Contains improvement claims without concrete evidence or repro context.")

        if missing_evidence or missing_tests or unsupported:
            reasons.append("Draft not ready: missing evidence/tests or contains unsupported claims.")
            verdict: Literal["PASS", "FAIL"] = "FAIL"
        else:
            reasons.append("Draft appears evidence-backed and has required structure.")
            verdict = "PASS"

        return ReflectionArtifact(
            verdict=verdict,
            reasons=reasons,
            missing_evidence=missing_evidence,
            missing_tests=missing_tests,
            unsupported_claims=unsupported,
            safety_notes=["Human approval required before any GitHub write is executed."]
        )

class Gatekeeper:
    """Enforces: show draft, store it, require explicit approve/deny, and block creation if reflection FAIL."""
    def save_draft(self, draft: DraftType, plan: Optional[Plan], reflection: ReflectionArtifact) -> None:
        AGENT_DIR.mkdir(parents=True, exist_ok=True)
        DRAFT_PATH.write_text(draft.model_dump_json(indent=2))
        REFLECTION_PATH.write_text(reflection.model_dump_json(indent=2))

    def load(self) -> Tuple[DraftType, ReflectionArtifact]:
        if not DRAFT_PATH.exists() or not REFLECTION_PATH.exists():
            raise ToolError("No pending draft found. Run `agent draft ...` or `agent review ...` first.")
        draft = DraftType.model_validate_json(DRAFT_PATH.read_text())
        reflection = ReflectionArtifact.model_validate_json(REFLECTION_PATH.read_text())
        return draft, reflection

    def clear(self) -> None:
        if DRAFT_PATH.exists():
            DRAFT_PATH.unlink()
        if REFLECTION_PATH.exists():
            REFLECTION_PATH.unlink()

    def approve_and_create(self, yes: bool) -> None:
        draft, reflection = self.load()

        console.print(Panel.fit(f"[Gatekeeper] Reflection verdict: {reflection.verdict}", title="Gatekeeper"))

        if not yes:
            console.print("[Gatekeeper] Draft rejected. No changes made.")
            self.clear()
            return

        if reflection.verdict != "PASS":
            console.print("[Gatekeeper] Cannot create on GitHub because reflection verdict is FAIL.")
            console.print("Fix the draft (or rerun draft with better evidence/tests) and try again.")
            return

        # Creation happens here (real tool call)
        if draft.kind == "issue":
            console.print("[Gatekeeper] Creating GitHub Issue...")
            res = gh_create_issue(draft.title, draft.body, labels=["agent-generated"])
            console.print(f"[Tool] GitHub API call successful: {res['url']}")
        else:
            console.print("[Gatekeeper] Creating GitHub Pull Request...")
            res = gh_create_pr(draft.title, draft.body, draft=True)
            console.print(f"[Tool] GitHub API call successful: {res['url']}")

        self.clear()

# -------------------------
# CLI Commands
# -------------------------

def print_json(title: str, payload: Any) -> None:
    console.print(Panel.fit(Syntax(json.dumps(payload, indent=2), "json"), title=title))

@app.command()
def review(
    base: Optional[str] = typer.Option(None, "--base", help="Base branch to diff against (e.g. main)"),
    commit_range: Optional[str] = typer.Option(None, "--range", help="Commit range (e.g. HEAD~3..HEAD)"),
):
    """Task 1: Review changes from git diff and decide: create issue, create PR, or no action."""
    diff = git_diff(base=base, commit_range=commit_range)
    files = git_changed_files(base=base, commit_range=commit_range)

    reviewer = Reviewer()
    planner = Planner()
    writer = Writer()
    critic = Critic()
    gatekeeper = Gatekeeper()

    console.print("[Reviewer] Analyzing diff (tool-grounded)...")
    review_report = reviewer.analyze(diff, files)
    print_json("ReviewReport", review_report.model_dump())

    console.print("[Planner] Creating plan...")
    plan = planner.make_plan_from_review(review_report, goal="Respond to review decision with appropriate artifact.")
    print_json("Plan", plan.model_dump())

    # Decision -> draft (but DO NOT create)
    if review_report.decision == "create_issue":
        console.print("[Writer] Drafting Issue from review...")
        draft = writer.draft_issue_from_review(review_report, plan)
    elif review_report.decision == "create_pr":
        console.print("[Writer] Drafting PR from review...")
        draft = writer.draft_pr_from_instruction("Implement fix based on review findings.", files_affected=files, risk=review_report.risk)
    else:
        console.print("[Planner] Decision: no action required.")
        return

    console.print("[Gatekeeper] Running reflection...")
    reflection = critic.reflect(draft, plan=plan)

    print_json("Draft", draft.model_dump())
    print_json("ReflectionArtifact", reflection.model_dump())

    gatekeeper.save_draft(draft, plan, reflection)
    console.print("[Gatekeeper] Draft saved. Run `agent approve --yes` to create, or `agent approve --no` to abort.")

@app.command()
def draft(
    kind: str = typer.Argument(..., help="issue|pr"),
    instruction: str = typer.Option(..., "--instruction", help="Explicit instruction for drafting."),
):
    """Task 2: Draft an Issue or PR from explicit instruction (requires approval before creation)."""
    kind = kind.lower().strip()
    if kind not in ("issue", "pr"):
        raise typer.BadParameter("kind must be 'issue' or 'pr'")

    planner = Planner()
    writer = Writer()
    critic = Critic()
    gatekeeper = Gatekeeper()

    console.print("[Planner] Scope validated. Creating plan...")
    plan = planner.make_plan_from_instruction(instruction)
    print_json("Plan", plan.model_dump())

    files = git_changed_files()  # may be empty; still tool-grounded
    if kind == "issue":
        console.print("[Writer] Draft Issue created.")
        draft_obj = writer.draft_issue_from_instruction(instruction, risk="medium")
    else:
        console.print("[Writer] Draft PR created.")
        draft_obj = writer.draft_pr_from_instruction(instruction, files_affected=files, risk="medium")

    console.print("[Gatekeeper] Running reflection...")
    reflection = critic.reflect(draft_obj, plan=plan)

    print_json("Draft", draft_obj.model_dump())
    print_json("ReflectionArtifact", reflection.model_dump())

    gatekeeper.save_draft(draft_obj, plan, reflection)
    console.print("[Gatekeeper] Draft saved. Run `agent approve --yes` to create, or `agent approve --no` to abort.")

@app.command()
def approve(
    yes: Optional[bool] = typer.Option(
        None,
        "--yes",
        help="Approve the pending draft (creates only if reflection PASS).",
    ),
    no: Optional[bool] = typer.Option(
        None,
        "--no",
        help="Reject the pending draft (safe abort).",
    ),
):
    """Human approval gate. If YES and reflection PASS -> create on GitHub. If NO -> abort safely."""
    if yes and no:
        raise typer.BadParameter("Use only one: --yes or --no")
    if yes is None and no is None:
        raise typer.BadParameter("You must pass either --yes or --no")

    gatekeeper = Gatekeeper()
    gatekeeper.approve_and_create(yes=bool(yes))

@app.command()
def improve(
    kind: str = typer.Argument(..., help="issue|pr"),
    number: int = typer.Option(..., "--number", help="Issue/PR number to improve."),
):
    """Task 3: Improve an existing Issue or PR (critique first, then propose improved version)."""
    kind = kind.lower().strip()
    writer = Writer()
    critic = Critic()
    gatekeeper = Gatekeeper()

    if kind == "issue":
        console.print("[Tool] Fetching issue via gh...")
        issue = gh_view_issue(number)
        console.print("[Reviewer] Critiquing issue...")
        critiques, improved = writer.improve_issue(issue)
        print_json("Critiques", critiques)
        print_json("ProposedImprovedIssue", improved.model_dump())
    elif kind == "pr":
        console.print("[Tool] Fetching PR via gh...")
        pr = gh_view_pr(number)
        console.print("[Reviewer] Critiquing PR...")
        critiques, improved = writer.improve_pr(pr)
        print_json("Critiques", critiques)
        print_json("ProposedImprovedPR", improved.model_dump())
    else:
        raise typer.BadParameter("kind must be 'issue' or 'pr'")

    console.print("[Gatekeeper] Running reflection...")
    reflection = critic.reflect(improved)
    print_json("ReflectionArtifact", reflection.model_dump())

    gatekeeper.save_draft(improved, plan=None, reflection=reflection)
    console.print("[Gatekeeper] Improved draft saved. Approve to create a *new* Issue/PR if you want, or reject to abort.")
    console.print("Note: This tool does not silently edit existing Issues/PRs; it only proposes improvements.")

if __name__ == "__main__":
    app()