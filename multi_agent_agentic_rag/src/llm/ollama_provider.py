# src/llm/ollama_provider.py
import ollama

from src.llm.base_provider import BaseLLMProvider


class OllamaProvider(BaseLLMProvider):
    def __init__(self, model: str = "phi3") -> None:
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response["message"]["content"]