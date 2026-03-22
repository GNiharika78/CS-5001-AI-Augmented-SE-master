from __future__ import annotations

import argparse
import json

from protocols.a2a import A2ABus, A2AMessage
from protocols.mcp import MCPClient
from tools.git_mcp_server import build_git_mcp_server
from tools.github_mcp_server import build_github_mcp_server
from agents.reviewer import ReviewerAgent
from agents.planner import PlannerAgent
from agents.writer import WriterAgent
from agents.gatekeeper import GatekeeperAgent
from store import DraftStore


def build_system():
    mcp = MCPClient()
    mcp.register_server(build_git_mcp_server())
    mcp.register_server(build_github_mcp_server())

    bus = A2ABus()
    bus.register("reviewer", ReviewerAgent(mcp))
    bus.register("planner", PlannerAgent())
    bus.register("writer", WriterAgent())
    bus.register("gatekeeper", GatekeeperAgent(mcp))
    return bus


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent", description="Protocol-based GitHub Repository Agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    review = sub.add_parser("review")
    g = review.add_mutually_exclusive_group(required=True)
    g.add_argument("--base", type=str)
    g.add_argument("--range", dest="commit_range", type=str)

    draft = sub.add_parser("draft")
    draft.add_argument("kind", choices=["issue", "pr"])
    draft.add_argument("--instruction", required=True)
    draft.add_argument("--evidence-from-review", action="store_true")

    approve = sub.add_parser("approve")
    approve.add_argument("--yes", action="store_true")
    approve.add_argument("--no", action="store_true")

    improve = sub.add_parser("improve")
    improve.add_argument("kind", choices=["issue", "pr"])
    improve.add_argument("--number", required=True, type=int)

    args = parser.parse_args()
    store = DraftStore()
    bus = build_system()

    if args.cmd == "review":
        review_result = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="reviewer",
            task="review_changes",
            payload={"base": args.base, "commit_range": args.commit_range},
        ))
        plan_result = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="planner",
            task="plan_from_review",
            payload=review_result,
        ))
        output = {**review_result, **plan_result}
        store.save_review(output)
        print(json.dumps(output, indent=2))
        return

    if args.cmd == "draft":
        plan_result = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="planner",
            task="plan_draft",
            payload={
                "kind": args.kind,
                "instruction": args.instruction,
                "use_review": args.evidence_from_review,
            },
        ))

        review = store.load_review()["review"] if args.evidence_from_review and store.load_review() else None

        draft_result = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="writer",
            task="write_draft",
            payload={"plan": plan_result["plan"], "review": review},
        ))

        reflection_result = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="gatekeeper",
            task="reflect_draft",
            payload=draft_result,
        ))

        payload = {**plan_result, **draft_result, **reflection_result}
        store.save_draft(payload)

        print("[Planner] Scope validated.")
        print(f"[Writer] Draft {args.kind.upper()} created.")
        print(f"[Gatekeeper] Reflection verdict: {payload['reflection']['verdict']} – {payload['reflection']['summary']}")
        print("\n--- DRAFT (must approve to create) ---\n")
        print(payload["draft"]["rendered"])
        print("\n--- REFLECTION ARTIFACT ---\n")
        print(json.dumps(payload["reflection"], indent=2))
        return

    if args.cmd == "approve":
        if args.yes == args.no:
            raise SystemExit("Provide exactly one of --yes or --no")

        payload = store.load_draft()
        if not payload:
            raise SystemExit("No draft found.")

        if args.no:
            print("[Gatekeeper] Draft rejected. No changes made.")
            store.clear_draft()
            return

        if payload["reflection"]["verdict"] != "PASS":
            raise SystemExit(f"[Gatekeeper] Refusing to create. Reflection verdict is {payload['reflection']['verdict']}.")

        result = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="gatekeeper",
            task="approve_and_create",
            payload={"draft": payload["draft"], "approved": True},
        ))
        print(result["result"])
        store.clear_draft()
        return

    if args.cmd == "improve":
        existing = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="reviewer",
            task="improve_existing_fetch",
            payload={"kind": args.kind, "number": args.number},
        ))

        improved = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="writer",
            task="improve_existing",
            payload=existing,
        ))

        reflection = bus.send(A2AMessage(
            sender="orchestrator",
            recipient="gatekeeper",
            task="reflect_improvement",
            payload=improved,
        ))

        print(f"[Reviewer] {improved['critique']['headline']}")
        print("\n--- CRITIQUE ---\n")
        print(improved["critique"]["rendered"])
        print("\n--- PROPOSED IMPROVED VERSION ---\n")
        print(improved["improved"]["rendered"])
        print("\n--- REFLECTION ARTIFACT ---\n")
        print(json.dumps(reflection["reflection"], indent=2))
        return


if __name__ == "__main__":
    main()