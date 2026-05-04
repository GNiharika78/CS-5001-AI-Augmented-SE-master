from app.llm_client import call_llm


class HypothesisAgent:
    def run(self, task_prompt: str, code: str, failure_analysis: str) -> str:
        prompt = f"""
You are the Hypothesis Agent.

Task:
{task_prompt}

Code:
{code}

Failure Analysis:
{failure_analysis[:1200]}

Return:

1. Failing behavior:
2. Evidence:
3. Root cause:
4. Why this explains failure:
5. Repair plan:
6. Confidence (0 to 1):
"""
        return call_llm(prompt, model="qwen2.5-coder:7b")