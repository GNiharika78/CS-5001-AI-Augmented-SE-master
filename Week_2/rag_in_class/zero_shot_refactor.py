from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage


# -------------------- Configuration --------------------

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "devstral-small-2:24b-cloud")
DEFAULT_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.0"))

TASK_PATTERN = re.compile(r"task_(\d+)\.py$")
TASK_GLOB = "task_*.py"
IMPL_PLACEHOLDER = "<<<IMPLEMENTATION>>>"

DATASET_ROOT = Path("dataset").resolve()
PROMPT_PATH = Path("prompts/user_prompt.md").resolve()


# -------------------- Paths --------------------

@dataclass(frozen=True)
class Paths:
    input_tasks: Path
    output_tasks: Path
    output_explanations: Path


# -------------------- Utilities --------------------

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def extract_task_id(path: Path) -> str | None:
    match = TASK_PATTERN.search(path.name)
    return match.group(1) if match else None


def iter_tasks(dir_path: Path) -> Iterable[Path]:
    for path in sorted(dir_path.glob(TASK_GLOB)):
        if path.is_file() and extract_task_id(path):
            yield path


def strip_code_fence(text: str) -> str:
    for pattern in (r"```python\s*(.*?)```", r"```\s*(.*?)```"):
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip() + "\n"
    return text.strip() + "\n"


def build_prompt(template: str, implementation: str) -> str:
    if IMPL_PLACEHOLDER in template:
        return template.replace(IMPL_PLACEHOLDER, implementation)
    return f"{template.rstrip()}\n\nImplementation file content:\n{implementation}\n"


# -------------------- Core Logic --------------------

def refactor_task(
    llm: ChatOllama,
    prompt_template: str,
    impl_path: Path,
    paths: Paths,
) -> None:
    task_id = extract_task_id(impl_path)
    if not task_id:
        return

    impl_code = read(impl_path)
    prompt = build_prompt(prompt_template, impl_code)

    response = llm.invoke([HumanMessage(content=prompt)])
    output = response.content if isinstance(response.content, str) else str(response.content)

    explanation_md = (
        f"# Model output for task_{task_id}\n\n"
        f"## Model\n- {DEFAULT_MODEL}\n\n"
        f"## Original Code:\n\n{impl_code}\n"
        f"## Refactored Code:\n\n{output}\n"
    )

    write(
        paths.output_explanations / f"task_{task_id}_model_output.md",
        explanation_md,
    )

    refactored_code = strip_code_fence(output)
    if len(refactored_code.strip()) < 10:
        raise ValueError(f"Model output too short for task {task_id}")

    write(
        paths.output_tasks / f"task_{task_id}.py",
        refactored_code,
    )


# -------------------- Entrypoint --------------------

def main() -> None:
    input_tasks = DATASET_ROOT / "input" / "tasks"
    output_tasks = DATASET_ROOT / "outputs" / "tasks"
    output_explanations = DATASET_ROOT / "outputs" / "explanations"

    if not input_tasks.exists():
        raise FileNotFoundError(f"Missing input tasks: {input_tasks}")
    if not PROMPT_PATH.exists():
        raise FileNotFoundError(f"Missing prompt file: {PROMPT_PATH}")

    prompt_template = read(PROMPT_PATH)

    output_tasks.mkdir(parents=True, exist_ok=True)
    output_explanations.mkdir(parents=True, exist_ok=True)
    (output_tasks / "__init__.py").touch(exist_ok=True)

    llm = ChatOllama(model=DEFAULT_MODEL, temperature=DEFAULT_TEMPERATURE)

    paths = Paths(
        input_tasks=input_tasks,
        output_tasks=output_tasks,
        output_explanations=output_explanations,
    )

    for task in iter_tasks(input_tasks):
        print(f"Refactoring task: {task.name}")
        refactor_task(llm, prompt_template, task, paths)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

