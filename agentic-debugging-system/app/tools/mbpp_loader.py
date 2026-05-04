import json
from pathlib import Path


def load_all_mbpp_tasks(path: str = "data/raw/sanitized-mbpp.json") -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_mbpp_task(task_id: int, path: str = "data/raw/sanitized-mbpp.json") -> dict:
    data = load_all_mbpp_tasks(path)

    for task in data:
        if task["task_id"] == task_id:
            return task

    raise ValueError(f"Task ID {task_id} not found")