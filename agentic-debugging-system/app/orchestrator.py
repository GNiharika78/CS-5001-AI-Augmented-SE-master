import json
import time
from pathlib import Path

from app.tools.test_runner import run_tests
from app.tools.coverage_runner import run_coverage

from app.llm_client import reset_llm_call_count, get_llm_call_count

from app.agents.failure_analysis_agent import FailureAnalysisAgent
from app.agents.hypothesis_agent import HypothesisAgent
from app.agents.patch_generation_agent import PatchGenerationAgent
from app.agents.test_generation_agent import TestGenerationAgent
from app.agents.coverage_analysis_agent import CoverageAnalysisAgent


class DebuggingOrchestrator:
    def __init__(self, max_attempts=3):
        self.max_attempts = max_attempts

        self.failure_agent = FailureAnalysisAgent()
        self.hypothesis_agent = HypothesisAgent()
        self.patch_agent = PatchGenerationAgent()

        self.coverage_agent = CoverageAnalysisAgent()
        self.test_generation_agent = TestGenerationAgent()

    def run(self, task, buggy_code, bug_type):
        reset_llm_call_count()

        task_start = time.time()
        code = buggy_code
        tests = task["test_list"]
        history = []

        print("\n==============================")
        print(f"Task ID: {task['task_id']}")
        print(f"Bug Type: {bug_type}")
        print("==============================")

        for attempt in range(1, self.max_attempts + 1):
            attempt_start = time.time()

            print(f"\nAttempt {attempt}: Running tests...")

            result = run_tests(code, tests)

            print("Test run complete.")
            print("Tests Passed:", result["passed"])

            record = {
                "attempt": attempt,
                "planning": "Planning is performed by Failure Analysis and Hypothesis Agents using runtime evidence.",
                "code_before_patch": code,
                "tests_passed_before_patch": result["passed"],
                "test_output": result["output"],
                "failure": None,
                "hypothesis": None,
                "patched_code": None,
                "decision": None,
                "duration_seconds": None,
            }

            if result["passed"]:
                print("✅ Repaired. No patch needed in this attempt.")

                record["decision"] = "stop_success"
                record["duration_seconds"] = round(time.time() - attempt_start, 2)
                history.append(record)

                post = self.post_success(task, code, tests)

                return self.result(
                    task=task,
                    bug_type=bug_type,
                    code=code,
                    status="repaired",
                    history=history,
                    post=post,
                    start=task_start,
                )

            print("Tests failed.")
            print("Calling Failure Analysis Agent...")

            failure = self.failure_agent.run(
                task["prompt"],
                code,
                result["output"],
            )

            print("Failure Analysis Agent finished.")

            if failure == "LLM_FAILED":
                print("❌ Failure Analysis Agent failed due to LLM issue.")

                record["decision"] = "failed_during_failure_analysis"
                record["duration_seconds"] = round(time.time() - attempt_start, 2)
                history.append(record)

                return self.result(
                    task=task,
                    bug_type=bug_type,
                    code=code,
                    status="failed_llm",
                    history=history,
                    post=None,
                    start=task_start,
                )

            print("Calling Hypothesis Agent...")

            hypothesis = self.hypothesis_agent.run(
                task["prompt"],
                code,
                failure,
            )

            print("Hypothesis Agent finished.")

            if hypothesis == "LLM_FAILED":
                print("❌ Hypothesis Agent failed due to LLM issue.")

                record["failure"] = failure
                record["decision"] = "failed_during_hypothesis"
                record["duration_seconds"] = round(time.time() - attempt_start, 2)
                history.append(record)

                return self.result(
                    task=task,
                    bug_type=bug_type,
                    code=code,
                    status="failed_llm",
                    history=history,
                    post=None,
                    start=task_start,
                )

            print("Calling Patch Generation Agent...")

            patched = self.patch_agent.run(
                task["prompt"],
                code,
                tests,
                failure,
                hypothesis,
            )

            print("Patch Generation Agent finished.")

            if patched == "LLM_FAILED":
                print("❌ Patch Generation Agent failed due to LLM issue.")

                record["failure"] = failure
                record["hypothesis"] = hypothesis
                record["decision"] = "failed_during_patch_generation"
                record["duration_seconds"] = round(time.time() - attempt_start, 2)
                history.append(record)

                return self.result(
                    task=task,
                    bug_type=bug_type,
                    code=code,
                    status="failed_llm",
                    history=history,
                    post=None,
                    start=task_start,
                )

            record["failure"] = failure
            record["hypothesis"] = hypothesis
            record["patched_code"] = patched
            record["decision"] = "patch_and_retry"
            record["duration_seconds"] = round(time.time() - attempt_start, 2)

            history.append(record)

            print("Patch generated.")
            print("Decision: patch_and_retry")
            print("Attempt Duration:", record["duration_seconds"], "seconds")

            code = patched

        print("\nMax attempts reached. Running final validation...")

        final_start = time.time()
        final = run_tests(code, tests)

        print("Final validation complete.")
        print("Final Tests Passed:", final["passed"])

        status = "repaired" if final["passed"] else "failed"

        history.append(
            {
                "attempt": self.max_attempts + 1,
                "planning": "Final validation after maximum repair attempts.",
                "code_before_patch": code,
                "tests_passed_before_patch": final["passed"],
                "test_output": final["output"],
                "failure": None,
                "hypothesis": None,
                "patched_code": None,
                "decision": "final_validation",
                "duration_seconds": round(time.time() - final_start, 2),
            }
        )

        post = None
        if status == "repaired":
            post = self.post_success(task, code, tests)

        return self.result(
            task=task,
            bug_type=bug_type,
            code=code,
            status=status,
            history=history,
            post=post,
            start=task_start,
        )

    def post_success(self, task, code, tests):
        print("Running post-success coverage analysis...")

        coverage = run_coverage(code, tests)

        print("Calling Coverage Analysis Agent...")

        coverage_analysis = self.coverage_agent.run(
            task["prompt"],
            code,
            coverage["coverage_output"],
        )

        if coverage_analysis == "LLM_FAILED":
            coverage_analysis = "Coverage analysis failed."

        print("Calling Test Generation Agent...")

        generated_tests = self.test_generation_agent.run(
            task["prompt"],
            code,
            tests,
        )

        generated_test_result = None

        if generated_tests:
            print("Running original + generated tests...")

            generated_test_result = run_tests(
                code,
                tests + generated_tests,
            )

        return {
            "coverage_tests_passed": coverage.get("tests_passed"),
            "coverage_output": coverage.get("coverage_output"),
            "coverage_analysis": coverage_analysis,
            "generated_tests": generated_tests,
            "generated_tests_count": len(generated_tests),
            "generated_tests_passed": (
                generated_test_result["passed"]
                if generated_test_result
                else None
            ),
            "generated_test_output": (
                generated_test_result["output"]
                if generated_test_result
                else None
            ),
        }

    def result(self, task, bug_type, code, status, history, post, start):
        return {
            "task_id": task["task_id"],
            "task_prompt": task["prompt"],
            "bug_type": bug_type,
            "status": status,
            "final_code": code,
            "attempts": len(history),
            "llm_calls": get_llm_call_count(),
            "duration": round(time.time() - start, 2),
            "memory_type": "episodic_attempt_history",
            "history": history,
            "post": post,
        }


def save_result(result: dict, path: str = "data/results/run_result.json"):
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )