import subprocess
import tempfile
from pathlib import Path


def run_tests(code: str, tests: list[str], timeout: int = 20) -> dict:
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
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_file), "-q"],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            output = result.stdout + "\n" + result.stderr

            return {
                "passed": result.returncode == 0,
                "returncode": result.returncode,
                "output": output,
                "error_type": None,
            }

        except subprocess.TimeoutExpired as e:
            return {
                "passed": False,
                "returncode": -1,
                "output": str(e),
                "error_type": "timeout",
            }

        except Exception as e:
            return {
                "passed": False,
                "returncode": -1,
                "output": str(e),
                "error_type": "runner_error",
            }