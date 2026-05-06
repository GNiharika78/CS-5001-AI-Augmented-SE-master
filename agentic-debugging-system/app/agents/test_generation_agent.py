from app.llm_client import call_llm


class TestGenerationAgent:
    def run(self, task_prompt: str, code: str, existing_tests: list[str]) -> list[str]:
        prompt = f"""
You are a Test Generation Agent.

Generate 3 additional Python assert statements to test edge cases.

Rules:
- Return only assert statements.
- No markdown.
- No explanation.
- No imports.
- Do not define functions.
- Use the same function name from the code.
- Avoid duplicating existing tests.

Task:
{task_prompt}

Code:
{code}

Existing Tests:
{existing_tests[:3]}

Generate tests for:
1. Normal case
2. Edge case
3. Boundary or unusual input
"""
        response = call_llm(
            prompt,
            max_tokens=256,
        )

        if response == "LLM_FAILED":
            return []

        tests = []

        for line in response.splitlines():
            line = line.strip()

            if line.startswith("assert "):
                tests.append(line)

        return tests[:3]