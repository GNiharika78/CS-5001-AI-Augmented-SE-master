import time
import requests

LLM_CALL_COUNT = 0


def reset_llm_call_count():
    global LLM_CALL_COUNT
    LLM_CALL_COUNT = 0


def get_llm_call_count():
    return LLM_CALL_COUNT


def call_llm(
    prompt: str,
    model: str = "deepseek-coder:latest",
    retries: int = 2,
    timeout: int = 300,
    max_tokens: int = 256,
) -> str:
    global LLM_CALL_COUNT

    short_prompt = prompt[:3500]

    for attempt in range(1, retries + 1):
        try:
            LLM_CALL_COUNT += 1

            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": model,
                    "prompt": short_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0,
                        "num_predict": max_tokens,
                        "num_ctx": 2048,
                    },
                },
                timeout=timeout,
            )

            response.raise_for_status()
            return response.json()["response"].strip()

        except requests.exceptions.ReadTimeout:
            print(f"LLM timeout with {model}, attempt {attempt}/{retries}")
            time.sleep(5)

        except Exception as e:
            print(f"LLM error with {model}, attempt {attempt}/{retries}: {e}")
            time.sleep(5)

    return "LLM_FAILED"