#!/usr/bin/env python3
import argparse
import json
import os
import sys
from roles import Reviewer, Planner, Writer, Gatekeeper
from store import DraftStore

def die(msg: str, code: int = 1):
    print(msg, file=sys.stderr)
    sys.exit(code)

def main():
    parser = argparse.ArgumentParser(prog="agent", description="Personalized GitHub Repository Agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # review
    p_review = sub.add_parser("review", help="Review current branch changes or a commit range")
    g = p_review.add_mutually_exclusive_group(required=True)
    g.add_argument("--base", type=str, help="Base branch to diff against (e.g., main)")
    g.add_argument("--range", type=str, help="Commit range (e.g., HEAD~3..HEAD)")
    p_review.add_argument("--max-diff-bytes", type=int, default=120_000)

    # draft
    p_draft = sub.add_parser("draft", help="Draft an issue or PR (no creation without approval)")
    p_draft.add_argument("kind", choices=["issue", "pr"])
    p_draft.add_argument("--instruction", type=str, required=True)
    p_draft.add_argument("--evidence-from-review", action="store_true",
                         help="Use last review artifact as additional context if available")

    # improve
    p_improve = sub.add_parser("improve", help="Improve an existing GitHub issue or PR (suggestion only)")
    p_improve.add_argument("kind", choices=["issue", "pr"])
    p_improve.add_argument("--number", type=int, required=True)

    # approve
    p_approve = sub.add_parser("approve", help="Approve/reject the last draft (creates on GitHub only if yes)")
    p_approve.add_argument("--yes", action="store_true")
    p_approve.add_argument("--no", action="store_true")

    args = parser.parse_args()
    store = DraftStore()

    reviewer = Reviewer()
    planner = Planner()
    writer = Writer()
    gatekeeper = Gatekeeper()

    if args.cmd == "review":
        review_artifact = reviewer.review(base=args.base, commit_range=args.range, max_diff_bytes=args.max_diff_bytes)
        plan = planner.plan_from_review(review_artifact)
        output = {
            "review": review_artifact,
            "plan": plan,
        }
        store.save_review(output)
        print(json.dumps(output, indent=2))
        return

    if args.cmd == "draft":
        # Planning step: scope validation + required fields selection
        plan = planner.plan_draft(kind=args.kind, instruction=args.instruction, use_review=args.evidence_from_review, store=store)

        draft = writer.write_draft(plan=plan, store=store)
        reflection = gatekeeper.reflect(draft=draft)

        # Save draft + reflection. No GH creation here.
        store.save_draft({"plan": plan, "draft": draft, "reflection": reflection})
        print("[Planner] Scope validated.")
        print(f"[Writer] Draft {args.kind.upper()} created.")
        print(f"[Gatekeeper] Reflection verdict: {reflection['verdict']} – {reflection['summary']}")
        print("\n--- DRAFT (must approve to create) ---\n")
        print(draft["rendered"])
        print("\n--- REFLECTION ARTIFACT ---\n")
        print(json.dumps(reflection, indent=2))
        return

    if args.cmd == "improve":
        critique, improved = writer.improve_existing(kind=args.kind, number=args.number)
        reflection = gatekeeper.reflect_improvement(critique=critique, improved=improved)

        print(f"[Reviewer] {critique['headline']}")
        print("\n--- CRITIQUE ---\n")
        print(critique["rendered"])
        print("\n--- PROPOSED IMPROVED VERSION ---\n")
        print(improved["rendered"])
        print("\n--- REFLECTION ARTIFACT ---\n")
        print(json.dumps(reflection, indent=2))
        return

    if args.cmd == "approve":
        if args.yes == args.no:
            die("Provide exactly one: --yes or --no")

        payload = store.load_draft()
        if not payload:
            die("No draft found. Run `agent draft ...` first.")

        reflection = payload.get("reflection", {})
        verdict = reflection.get("verdict", "FAIL")

        if args.no:
            store.clear_draft()
            print("[Gatekeeper] Draft rejected. No changes made.")
            return

        # args.yes
        if verdict != "PASS":
            die(f"[Gatekeeper] Refusing to create. Reflection verdict is {verdict}. Fix the draft first.")

        created = gatekeeper.create_on_github(payload["draft"])
        store.clear_draft()
        print(created)
        return

if __name__ == "__main__":
    main()