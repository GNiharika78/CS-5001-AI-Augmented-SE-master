from app.tools.mbpp_loader import load_mbpp_task
from app.tools.bug_injector import inject_bug
from app.orchestrator import DebuggingOrchestrator, save_result


def main():
    task_id = 11

    task = load_mbpp_task(task_id)

    original_code = task["code"]
    buggy_code, bug_type = inject_bug(original_code)

    print("Task ID:", task["task_id"])
    print("Bug Type:", bug_type)

    if bug_type == "no_injectable_bug":
        print("No injectable bug found.")
        return

    orchestrator = DebuggingOrchestrator(max_attempts=2)

    result = orchestrator.run(
        task=task,
        buggy_code=buggy_code,
        bug_type=bug_type
    )

    save_result(result)

    print("\nFinal Status:", result["status"])
    print("Attempts:", result["attempts"])
    print("Saved to data/results/run_result.json")


if __name__ == "__main__":
    main()