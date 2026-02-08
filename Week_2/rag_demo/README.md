# RAG Demo Codebase (Ollama + FAISS)
This is a minimal, local Retrieval-Augmented Generation (RAG) demo.

## Prerequisites
- Ollama installed and running
- Pull models:
  - Embeddings: `ollama pull nomic-embed-text`
  - Chat: `ollama pull ministral-3:3b-cloud`

## Install Python dependencies
```bash
pip install -r requirements.txt
```

## Build the index
```bash
python rag.py build --data_dir ./data_code_translation_log --index_dir ./rag_index
```

## Ask questions (with citations)
```bash
python rag.py ask --index_dir ./rag_index --model ministral-3:3b-cloud --top_k 5
```

## Files
- `rag.py` : builds index and runs Q&A loop
- `data_code_translation_log/` : sample code translation error logs 
- `data_project_info/` : project info
- `requirements.txt`
