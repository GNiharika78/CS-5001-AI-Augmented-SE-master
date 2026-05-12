from app.llm_client import call_llm


class FailureAnalysisAgent:
    def run(
        self,
        task_prompt: str,
        code: str,
        test_output: str,
        model: str,
    ) -> str:

        prompt = f"""
You are a Failure Analysis Agent.

Task:
{task_prompt}

Code:
{code}

Test Output:
{test_output[:1000]}

Return:
1. What failed
2. Evidence
3. Failure type
4. Suspected location
"""

        return call_llm(
            prompt,
            model=model,
            max_tokens=256,
        )