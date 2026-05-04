from app.llm_client import call_llm


class TestGenerationAgent:
    def run(self, task_prompt: str, code: str, existing_tests: list[str]) -> list[str]:
        prompt = f"""
Generate 2 Python assert tests.

Rules:
- Only assert statements
- No explanation

Task:
{task_prompt}

Code:
{code}
"""
        response = call_llm(prompt, model="qwen2.5-coder:7b")

        if response == "LLM_FAILED":
            return []

        tests = []
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("assert"):
                tests.append(line)

        return tests[:2]