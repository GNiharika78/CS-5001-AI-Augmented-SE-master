from src.llm.base_provider import BaseLLMProvider


class MockProvider(BaseLLMProvider):
    """
    Mock LLM provider used for testing without calling a real model.
    """

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        return (
            "This is a mock response generated without calling a real LLM. "
            "The system prompt and user prompt were received successfully."
        )