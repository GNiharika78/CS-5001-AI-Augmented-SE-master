#!/usr/bin/env python3
"""
Interactive RAG chat over FAISS index:
- retrieves relevant refactored code + error logs (+ tests if indexed)
- answers grounded questions about failures and next steps

Usage:
  python tools/rag_chat.py

Environment:
  OLLAMA_MODEL=devstral-small-2:24b-cloud
  OLLAMA_TEMPERATURE=0.0
  OLLAMA_EMBED_MODEL=nomic-embed-text
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


@dataclass(frozen=True)
class Paths:
    index_dir: Path


SYSTEM_RULES = """You are a debugging assistant for MBPP refactoring.

You must use the retrieved context (code, tests, error logs) to answer.
If the answer is not supported by retrieved context, say "I don't know".

When diagnosing, prioritize:
1) What the test asserts require
2) What the current refactored code actually does
3) What the error log indicates (traceback, assertion diff)

Output format:
- "Likely cause" (2 to 5 bullets)
- "Evidence" (cite file paths from retrieved snippets)
- "Fix options" (2 to 4 concrete options). Include whether to change code or prompt.
"""


def format_docs(docs: List[Document]) -> str:
    parts: List[str] = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unknown")
        typ = d.metadata.get("type", "unknown")
        text = d.page_content.strip()
        if len(text) > 1400:
            text = text[:1400] + "\n...[truncated]..."
        parts.append(f"[{i}] type={typ} source={src}\n{text}")
    return "\n\n".join(parts)


def main() -> None:
    dataset_root = Path("dataset").resolve()
    paths = Paths(index_dir=dataset_root / "outputs" / "rag_faiss_index")

    if not paths.index_dir.exists():
        raise SystemExit("Missing dataset/outputs/rag_faiss_index. Run tools/build_faiss_rag.py first.")

    embed_model = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    embeddings = OllamaEmbeddings(model=embed_model)
    vectordb = FAISS.load_local(str(paths.index_dir), embeddings, allow_dangerous_deserialization=True)

    llm_model = os.environ.get("OLLAMA_MODEL", "devstral-small-2:24b-cloud")
    llm_temp = float(os.environ.get("OLLAMA_TEMPERATURE", "0.0"))
    llm = ChatOllama(model=llm_model, temperature=llm_temp)

    chat_history: List[Tuple[str, str]] = []

    while True:
        user_q = input("\nYou: ").strip()
        if user_q.lower() in {"exit", "quit"}:
            break
        if not user_q:
            continue

        docs = vectordb.similarity_search(user_q, k=8)
        context = format_docs(docs)

        history_text = ""
        if chat_history:
            last = chat_history[-6:]
            history_text = "\n".join([f"User: {u}\nAssistant: {a}" for (u, a) in last])

        prompt = f"""{SYSTEM_RULES}

Recent chat (may be incomplete):
{history_text}

Retrieved context:
{context}

User question:
{user_q}
"""

        resp = llm.invoke(prompt)
        answer = resp.content if isinstance(resp.content, str) else str(resp.content)
        print(answer)
        chat_history.append((user_q, answer))


if __name__ == "__main__":
    main()

