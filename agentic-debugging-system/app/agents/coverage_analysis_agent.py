from app.llm_client import call_llm


class CoverageAnalysisAgent:
    def run(self, task_prompt: str, code: str, coverage_output: str, model: str) -> str:
        prompt = f"""
You are a Coverage Analysis Agent.

Analyze the test coverage report for the repaired code.

Task:
{task_prompt}

Code:
{code}

Coverage Report:
{coverage_output[:1000]}

Return:
1. Coverage summary
2. Missing or weakly tested cases
3. Suggested additional tests
"""
        return call_llm(
            prompt,
            model=model,
            max_tokens=256,
        )