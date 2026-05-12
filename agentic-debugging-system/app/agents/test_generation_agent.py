from app.llm_client import call_llm


class TestGenerationAgent:
    def run(
        self,
        task_prompt: str,
        code: str,
        existing_tests: list[str],
        model: str,
    ) -> list[str]:

        prompt = f"""
You are a Test Generation Agent.

Generate 3 additional Python assert statements.

Rules:
- Return only assert statements
- No markdown
- No explanation
- No imports
- Do not define functions
- Avoid duplicate tests

Task:
{task_prompt}

Code:
{code}

Existing Tests:
{existing_tests[:3]}
"""

        response = call_llm(
            prompt,
            model=model,
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