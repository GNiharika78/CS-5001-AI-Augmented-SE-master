import json
import time
import argparse
from pathlib import Path

from app.tools.mbpp_loader import load_all_mbpp_tasks
from app.tools.bug_injector import inject_bug
from app.orchestrator import DebuggingOrchestrator


def save_json(data, path: str):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )


def safe_model_folder_name(model_name: str) -> str:
    return (
        model_name
        .replace(":", "_")
        .replace("/", "_")
        .replace("-", "_")
        .replace(".", "_")
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--model",
        required=True,
        help="Ollama model name, e.g., mistral:latest or ministral-3:8b-cloud",
    )

    parser.add_argument(
        "--target",
        type=int,
        default=300,
        help="Number of injectable tasks to evaluate",
    )

    parser.add_argument(
        "--max-attempts",
        type=int,
        default=2,
        help="Maximum repair attempts per task",
    )

    args = parser.parse_args()

    tasks = load_all_mbpp_tasks()

    target_evaluated_tasks = args.target
    evaluated_count = 0

    model_folder = safe_model_folder_name(args.model)
    output_dir = Path("data/results") / model_folder

    orchestrator = DebuggingOrchestrator(
        max_attempts=args.max_attempts,
        model=args.model,
    )

    results = []

    for index, task in enumerate(tasks, start=1):
        if evaluated_count >= target_evaluated_tasks:
            break

        print(f"\nScanning task {index} | task_id={task['task_id']}")

        original_code = task["code"]

        buggy_code, bug_type = inject_bug(
            original_code,
            seed=task["task_id"],
        )

        if buggy_code is None or bug_type is None or bug_type == "no_injectable_bug":
            print("Skipped: no injectable bug")
            continue

        print(f"Running task {evaluated_count + 1}/{target_evaluated_tasks}")
        print("Model:", args.model)
        print("Bug Type:", bug_type)

        result = orchestrator.run(
            task=task,
            buggy_code=buggy_code,
            bug_type=bug_type,
        )

        result["model"] = args.model

        results.append(result)
        evaluated_count += 1

        task_result_path = output_dir / "tasks" / f"task_{task['task_id']}.json"
        save_json(result, str(task_result_path))

        print("Status:", result["status"])
        print("Attempts:", result["attempts"])
        print("LLM Calls:", result.get("llm_calls"))
        print("Duration Seconds:", result.get("duration"))

        time.sleep(0.2)

    total = len(results)
    repaired = sum(1 for r in results if r["status"] == "repaired")
    failed = sum(1 for r in results if r["status"] == "failed")
    failed_llm = sum(1 for r in results if r["status"] == "failed_llm")

    avg_attempts = (
        sum(r["attempts"] for r in results) / total
        if total > 0
        else 0
    )

    avg_duration = (
        sum(r.get("duration", 0) for r in results) / total
        if total > 0
        else 0
    )

    avg_llm_calls = (
        sum(r.get("llm_calls", 0) for r in results) / total
        if total > 0
        else 0
    )

    bug_type_summary = {}

    for result in results:
        bug_type = result["bug_type"]

        if bug_type not in bug_type_summary:
            bug_type_summary[bug_type] = {
                "total": 0,
                "repaired": 0,
                "failed": 0,
                "failed_llm": 0,
            }

        bug_type_summary[bug_type]["total"] += 1

        if result["status"] == "repaired":
            bug_type_summary[bug_type]["repaired"] += 1
        elif result["status"] == "failed_llm":
            bug_type_summary[bug_type]["failed_llm"] += 1
        else:
            bug_type_summary[bug_type]["failed"] += 1

    summary = {
        "model": args.model,
        "target_evaluated_tasks": target_evaluated_tasks,
        "total_evaluated_tasks": total,
        "repaired": repaired,
        "failed": failed,
        "failed_llm": failed_llm,
        "success_rate": repaired / total if total > 0 else 0,
        "average_attempts": avg_attempts,
        "average_duration_seconds": avg_duration,
        "average_llm_calls": avg_llm_calls,
        "bug_type_summary": bug_type_summary,
    }

    save_json(results, str(output_dir / "batch_results.json"))
    save_json(summary, str(output_dir / "summary.json"))

    print("\n===== SUMMARY =====")
    print("Model:", args.model)
    print("Output Folder:", output_dir)
    print("Target:", target_evaluated_tasks)
    print("Total:", total)
    print("Repaired:", repaired)
    print("Failed:", failed)
    print("Failed LLM:", failed_llm)
    print("Success Rate:", summary["success_rate"])
    print("Average Attempts:", summary["average_attempts"])
    print("Average Duration Seconds:", summary["average_duration_seconds"])
    print("Average LLM Calls:", summary["average_llm_calls"])
    print("Saved summary to", output_dir / "summary.json")


if __name__ == "__main__":
    main()