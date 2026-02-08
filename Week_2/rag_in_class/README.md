## README: Week_2/rag_in_class

This folder contains a small MBPP-style refactoring setup:

* **Input tasks** (original solutions)
* **Output tasks** (LLM-refactored solutions)
* **Pytest suites** to validate both
* A **LangChain + Ollama** refactoring script that generates refactored code and saves the model’s full output as explanations

---

## Repository layout

```
rag_in_class/
  zero_shot_refactor.py
  prompts/
    user_prompt.md
  dataset/
    input/
      tasks/                 # task_*.py (original)
      tests/                 # test_task_*.py + conftest.py
      pytest.ini
    outputs/
      tasks/                 # task_*.py (refactored output)
      explanations/          # task_*_model_output.md (full model output)
      tests/                 # test_task_*.py + conftest.py
      pytest.ini
  rag/
    build_rag_index.py
    rag_chat.py
```

---

## Prerequisites

### 1) Python environment

Python 3.12 is needed.

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2) Ollama

Make sure Ollama is installed and running:

```bash
ollama serve
```

Pull the model you want to use (default in the script is `devstral-small-2:24b-cloud`):

```bash
ollama pull devstral-small-2:24b-cloud
ollama pull nomic-embed-text
```



Optional: use a different model by setting an environment variable:


```bash
ollama pull ministral-3:8b-cloud

export OLLAMA_MODEL=ministral-3:8b-cloud
```

---

## Run tests on the original code (input)

From the `rag_in_class/` directory:

```bash
cd dataset/input
python -m pytest -q
```

If everything is set up correctly, these tests should pass on the original input tasks.

---

## Generate refactored code with Ollama + LangChain

From the `rag_in_class/` directory:

```bash
python zero_shot_refactor.py
```

Outputs produced:

* Refactored code: `dataset/outputs/tasks/task_<id>.py`
* Model output explanations: `dataset/outputs/explanations/task_<id>_model_output.md`

Optional configuration:

```bash
ollama pull ministral-3:8b-cloud
OLLAMA_MODEL=lministral-3:8b-cloud OLLAMA_TEMPERATURE=0.0 python zero_shot_refactor.py
```

---

## Run tests on the refactored code (outputs)

From the `rag_in_class/` directory:

```bash
cd dataset/outputs
python -m pytest -q 2>&1 | tee explanations/pytest_error_log.txt
```

This runs `dataset/outputs/tests/*` against `dataset/outputs/tasks/*`.

---

### 4) Build the FAISS index

From `rag_in_class/` root:

```bash
python rag/build_rag_index.py
```

This writes:
`dataset/outputs/rag_faiss_index/`

### 5) Start the RAG chat

```bash
python rag/rag_explain_chat.py
```

Example queries:

* `What are the common issues that the refactorings are failings?`
* `What did the model refactor correctly?`

---


## Common issues

### ImportError: cannot import tasks

Run pytest from the correct directory:

* `cd dataset/input` for input tests
* `cd dataset/outputs` for output tests

Both locations include a `pytest.ini` and `tests/conftest.py` to keep imports consistent.

### Ollama connection or model not found

Confirm Ollama is running:

```bash
ollama serve
```

Confirm the model exists:

```bash
ollama list
```

---

## What students are expected to do
## What students are expected to do

1. **Set up the environment**

* Create and activate a Python virtual environment.
* Install dependencies (`pip install -r requirements.txt`).
* Ensure Ollama is running and required models are pulled.

2. **Run the baseline (input) tests**

* Run pytest in `dataset/input/` to confirm the original tasks pass.
* Record the result (pass, fail, and which tasks fail if any).

3. **Generate refactored solutions**

* Run the refactoring script to generate files in `dataset/outputs/tasks/`.
* Confirm the script also produces explanation artifacts in `dataset/outputs/explanations/`.

4. **Test the refactored outputs**

* Run pytest in `dataset/outputs/` to check whether refactoring preserved behavior.
* Save logs for any failures into `dataset/outputs/error_logs/` (`python -m pytest -q 2>&1 | tee explanations/pytest_error_log.txt`).

5. **Build the RAG index (FAISS)**

* Run:

  * `python rag/build_rag_index.py`
* Confirm it creates `dataset/outputs/rag_faiss_index/`.

6. **Use the RAG chat to diagnose failures**

* Run:

  * `python rag/rag_explain_chat.py`
* Ask questions grounded in retrieved artifacts, for example:

  * “Why is task_315 failing?”
  * “What are the common issues that the refactorings are failings?”
  * “What did the model refactor correctly?”

7. **Update the prompt and rerun**

* Based on RAG findings, update `prompts/user_prompt.md` with a targeted change that addresses the failure mode.
* Re-run the refactor pipeline and re-run output tests.
* Repeat until outputs pass or you can justify the remaining failures with evidence from logs, tests, and code.

8. **Submit artifacts**

* The updated `prompts/user_prompt.md`
* **Make sure your final prompt is generic enough and not specific to certain problems. I will test against 60 more problems and expect at least 90% success rate.**
* A short reflection describing what the RAG chat retrieved and how it influenced the prompt update
