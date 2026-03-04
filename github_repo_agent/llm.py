import os
from typing import Optional

"""
This module intentionally supports "vibe coding" with any LLM.
Default mode is SAFE FALLBACK (no external calls): it produces structured drafts
using deterministic templates + repo evidence. That meets the assignment without
requiring API keys.

If you want a real LLM:
- Set LLM_PROVIDER=openai and OPENAI_API_KEY, etc.
- Implement call_llm() accordingly.
"""

class LLM:
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "none").lower()

    def call(self, system: str, user: str) -> str:
        if self.provider == "none":
            # No fabricated “analysis”. Return empty so caller uses templates.
            return ""
        # Placeholder: add your provider integration here.
        # Must be real tool use (actual HTTP call). If not implemented, fail fast.
        raise RuntimeError("LLM_PROVIDER is set but provider integration is not implemented.")