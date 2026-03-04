from typing import Dict, Any, List

def reflect_draft(draft: Dict[str, Any]) -> Dict[str, Any]:
    issues: List[str] = []
    required_fields = draft.get("required_fields", [])
    missing = [f for f in required_fields if f not in draft.get("fields", {}) or not str(draft["fields"][f]).strip()]
    if missing:
        issues.append(f"Missing required fields: {', '.join(missing)}")

    # Evidence requirement: must cite diff/file reads for decisions and problem statements
    evidence = draft.get("evidence", [])
    if not evidence:
        issues.append("Missing evidence references (diff hunks / file reads).")

    if draft.get("kind") == "pr":
        # PR must include test plan
        tp = draft.get("fields", {}).get("test_plan", "")
        if not tp.strip():
            issues.append("Missing test plan.")

    verdict = "PASS" if not issues else "FAIL"
    summary = "All checks satisfied." if verdict == "PASS" else issues[0]

    return {
        "verdict": verdict,
        "summary": summary,
        "checks": {
            "missing_required_fields": missing,
            "has_evidence": bool(evidence),
            "has_test_plan_if_pr": (draft.get("kind") != "pr") or bool(draft.get("fields", {}).get("test_plan", "").strip()),
            "issues": issues,
        }
    }

def reflect_improvement(critique: Dict[str, Any], improved: Dict[str, Any]) -> Dict[str, Any]:
    issues = []
    if not critique.get("points"):
        issues.append("Critique lacks specific points.")
    if "Acceptance criteria" not in improved.get("rendered", "") and "Acceptance Criteria" not in improved.get("rendered", ""):
        issues.append("Improved version lacks acceptance criteria section.")

    verdict = "PASS" if not issues else "FAIL"
    return {"verdict": verdict, "summary": "OK" if verdict == "PASS" else issues[0], "issues": issues}