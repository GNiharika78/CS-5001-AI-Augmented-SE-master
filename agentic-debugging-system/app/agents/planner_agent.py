from app.llm_client import call_llm


class PlannerAgent:
    def run(self, task_prompt: str, code: str, tests: list[str]) -> str:
        prompt = f"""
You are a Planner Agent.

Create a very short debugging plan.

Task:
{task_prompt}

Return only:
1. Expected behavior
2. Risky code area
3. Repair strategy
"""
        return call_llm(
            prompt,
            model="qwen2.5-coder:7b",
            timeout=180,
            max_tokens=160,
        )