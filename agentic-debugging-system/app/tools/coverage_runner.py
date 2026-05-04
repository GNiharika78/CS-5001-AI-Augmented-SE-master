import subprocess
import tempfile
from pathlib import Path


def run_coverage(code: str, tests: list[str], timeout: int = 20) -> dict:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        solution_file = tmp_path / "solution.py"
        test_file = tmp_path / "test_solution.py"

        solution_file.write_text(code, encoding="utf-8")

        test_code = "from solution import *\n\n"

        for i, test in enumerate(tests):
            test_code += f"def test_case_{i}():\n"
            test_code += f"    {test}\n\n"

        test_file.write_text(test_code, encoding="utf-8")

        try:
            test_result = subprocess.run(
                ["python", "-m", "coverage", "run", "-m", "pytest", str(test_file), "-q"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            report_result = subprocess.run(
                ["python", "-m", "coverage", "report", "-m"],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            return {
                "tests_passed": test_result.returncode == 0,
                "test_output": test_result.stdout + "\n" + test_result.stderr,
                "coverage_output": report_result.stdout + "\n" + report_result.stderr,
            }

        except subprocess.TimeoutExpired as e:
            return {
                "tests_passed": False,
                "test_output": str(e),
                "coverage_output": "",
            }