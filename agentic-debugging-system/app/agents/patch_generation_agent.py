from app.llm_client import call_llm


class PatchGenerationAgent:
    def run(
        self,
        task_prompt: str,
        code: str,
        tests: list[str],
        failure_analysis: str,
        hypothesis: str,
    ) -> str:
        prompt = f"""
You are the Patch Generation Agent.

Fix the Python code.

Rules:
- Return only Python code
- No markdown
- No explanation
- Minimal fix
- Do not change tests

Task:
{task_prompt}

Code:
{code}

Failure Analysis:
{failure_analysis[:800]}

Hypothesis:
{hypothesis[:1000]}
"""
        response = call_llm(prompt, model="qwen2.5-coder:7b")

        if response == "LLM_FAILED":
            return "LLM_FAILED"

        return response.replace("```python", "").replace("```", "").strip()