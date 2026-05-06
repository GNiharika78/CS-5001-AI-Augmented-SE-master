from app.llm_client import call_llm


class CoverageAnalysisAgent:
    def run(self, task_prompt: str, code: str, coverage_output: str) -> str:
        prompt = f"""
Analyze coverage.

Coverage:
{coverage_output[:1000]}

Return:
1. Coverage summary
2. Missing cases
3. Test suggestions
"""
        return call_llm(prompt, model="ministral-3:8b-cloud")