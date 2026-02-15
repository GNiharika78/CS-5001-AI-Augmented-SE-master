# from __future__ import annotations

# from pathlib import Path
# from typing import Any, Callable

# from .llm import OllamaLLM
# from .prompt_manager import PromptManager
# from .tools import Tools
# from .types import AgentConfig, RunResult
# from .utils import strip_code_fences

# class Agent:
#     def __init__(self, cfg: AgentConfig):
#         self.cfg = cfg
#         self.repo = Path(cfg.repo).resolve()
#         self.tools = Tools(self.repo)
#         self.prompt_manager = PromptManager()
        
#         # Default prompt variants
#         self.planning_variant = 'default'
#         self.code_gen_variant = 'default'

#     def _log(self, message: Any) -> None:
#         if self.cfg.verbose:
#             print(message)

#     def _llm(self) -> OllamaLLM:
#         return OllamaLLM(
#             model=self.cfg.model,
#             host=self.cfg.host,
#             temperature=self.cfg.temperature,
#         )

#     def _call_llm(self, prompt: str) -> str:
#         return self._llm().generate(prompt)

#     def _multi_step_chain(self) -> Callable[[str], str]:
#         try:
#             from langchain_core.runnables import RunnableLambda
#         except Exception:
#             return self._call_llm

#         return RunnableLambda(self._call_llm).invoke

#     def create_program(self, desc: str, module_path: str) -> RunResult:
#         """Create a program module.
        
#         Steps:
#         1) produce a plan
#         2) draft code
#         3) write to disk
#         """
#         run = self._multi_step_chain()

#         # Plan
#         p1 = self.prompt_manager.get_prompt(
#             'planning',
#             self.planning_variant,
#             desc=desc,
#             module_path=module_path
#         )
#         self._log(p1)
#         plan = run(p1).strip()
#         if not plan:
#             return RunResult(False, "Model returned empty plan.")

#         # Draft code
#         p2 = self.prompt_manager.get_prompt(
#             'code_generation',
#             self.code_gen_variant,
#             desc=desc,
#             module_path=module_path,
#             plan=plan
#         )
#         self._log(p2)
#         draft_raw = run(p2)
#         self._log(draft_raw)
#         draft = strip_code_fences(draft_raw)
#         if not draft.strip():
#             return RunResult(False, "Model returned empty module draft.")

#         final_code = draft.rstrip() + "\n"
#         self.tools.write(module_path, final_code)
#         return RunResult(True, f"Wrote module: {module_path}")

#     def commit_and_push(self, message: str, push: bool) -> RunResult:
#         ok, out = self.tools.git_commit(message)
#         if not ok:
#             return RunResult(False, out)

#         if push:
#             ok2, out2 = self.tools.git_push()
#             if not ok2:
#                 return RunResult(False, "Commit succeeded, but push failed:\n" + out2)
#             return RunResult(True, "Commit and push succeeded.")

#         return RunResult(True, "Commit succeeded.")

#     def list_available_prompts(self) -> dict[str, list[str]]:
#         """List all available prompt tasks and their variants."""
#         tasks = self.prompt_manager.list_available_tasks()
#         result = {}
#         for task in tasks:
#             result[task] = self.prompt_manager.list_variants(task)
#         return result
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable

from .llm import OllamaLLM
from .prompt_manager import PromptManager
from .tools import Tools
from .types import AgentConfig, RunResult
from .utils import strip_code_fences


# Matches: "- path/to/file.ext: purpose text..."
_FILE_LINE_RE = re.compile(
    r"^\s*-\s*(?P<path>[A-Za-z0-9_.\-/]+)\s*:\s*(?P<purpose>.+?)\s*$"
)


def _is_unsafe_path(path: str) -> bool:
    """Block absolute paths and parent traversal."""
    p = Path(path)
    if p.is_absolute():
        return True
    if ".." in p.parts:
        return True
    # Also block home-like shortcuts
    if path.startswith("~"):
        return True
    return False


def _parse_files_from_plan(plan_text: str) -> list[tuple[str, str]]:
    """
    Extract a file list from the plan.

    Expected in plan:
        FILES:
        - README.md: how to run
        - requirements.txt: dependencies
        - src/main.py: entry point
        - src/utils/weather.py: API calls
    Returns:
        [(path, purpose), ...]
    """
    lines = plan_text.splitlines()
    files: list[tuple[str, str]] = []

    in_files = False
    for line in lines:
        if line.strip().upper() == "FILES:":
            in_files = True
            continue

        if in_files:
            m = _FILE_LINE_RE.match(line)
            if m:
                files.append((m.group("path"), m.group("purpose").strip()))
                continue

            # If we hit a non-bullet non-empty line, assume FILES section ended
            if line.strip() and not line.lstrip().startswith("-"):
                break

    return files


def _fallback_files(module_path: str) -> list[tuple[str, str]]:
    """
    Baseline scaffolding if planner doesn't output FILES.
    Keep it minimal but assignment-compliant.
    """
    files: list[tuple[str, str]] = [
        ("README.md", "Project overview and run instructions"),
        ("requirements.txt", "Python dependencies"),
        (module_path, "Main entry point"),
    ]
    return files


class Agent:
    def __init__(self, cfg: AgentConfig):
        self.cfg = cfg
        self.repo = Path(cfg.repo).resolve()
        self.tools = Tools(self.repo)
        self.prompt_manager = PromptManager()

        # Default prompt variants
        self.planning_variant = "default"
        self.code_gen_variant = "default"

    def _log(self, message: Any) -> None:
        if self.cfg.verbose:
            print(message)

    def _llm(self) -> OllamaLLM:
        return OllamaLLM(
            model=self.cfg.model,
            host=self.cfg.host,
            temperature=self.cfg.temperature,
        )

    def _call_llm(self, prompt: str) -> str:
        return self._llm().generate(prompt)

    def _multi_step_chain(self) -> Callable[[str], str]:
        """
        If langchain_core is available, use RunnableLambda.invoke to match the
        existing code style; else just call Ollama directly.
        """
        try:
            from langchain_core.runnables import RunnableLambda
        except Exception:
            return self._call_llm

        return RunnableLambda(self._call_llm).invoke

    def create_program(self, desc: str, module_path: str) -> RunResult:
        """
        Multi-file project generation.

        Steps:
        1) Produce a plan
        2) Extract file list (FILES section) from the plan
        3) Generate each file (one file per LLM call)
        4) Write all files to disk
        """
        run = self._multi_step_chain()

        # 1) Plan
        p1 = self.prompt_manager.get_prompt(
            "planning",
            self.planning_variant,
            desc=desc,
            module_path=module_path,
        )
        self._log(p1)

        plan = run(p1).strip()
        if not plan:
            return RunResult(False, "Model returned empty plan.")

        # 2) Determine files to generate
        files = _parse_files_from_plan(plan)
        if not files:
            # If planner doesn't provide files, still generate minimum scaffolding
            files = _fallback_files(module_path)

        # Safety check planned files
        for path, _purpose in files:
            if _is_unsafe_path(path):
                return RunResult(False, f"Refusing unsafe path in planned files: {path}")

        wrote: list[str] = []

        # 3) Generate each file
        for target_path, target_purpose in files:
            # Build prompt for this file
            # NOTE: your YAML may not yet include target_path/target_purpose.
            # PromptManager should ignore unknown variables if not referenced,
            # but if it fails, you must update the YAML to include these fields.
            try:
                p2 = self.prompt_manager.get_prompt(
                    "code_generation",
                    self.code_gen_variant,
                    desc=desc,
                    module_path=module_path,
                    plan=plan,
                    target_path=target_path,
                    target_purpose=target_purpose,
                    file_tree="\n".join([f"- {p}: {s}" for p, s in files]),
                )
            except TypeError:
                # If PromptManager doesn't accept extra variables, fall back
                p2 = self.prompt_manager.get_prompt(
                    "code_generation",
                    self.code_gen_variant,
                    desc=desc,
                    module_path=module_path,
                    plan=plan,
                )

                # Add a small hard instruction so we still generate per-file.
                p2 = (
                    p2
                    + "\n\n"
                    + f"Generate ONLY the file: {target_path}\n"
                    + f"Purpose: {target_purpose}\n"
                    + "Do not generate or reference other files.\n"
                )

            self._log(p2)

            draft_raw = run(p2)
            self._log(draft_raw)

            draft = strip_code_fences(draft_raw)
            if not draft.strip():
                return RunResult(False, f"Model returned empty draft for file: {target_path}")

            content = draft.rstrip() + "\n"

            # 4) Write file
            self.tools.write(target_path, content)
            wrote.append(target_path)

        return RunResult(True, "Wrote files:\n" + "\n".join(f"- {p}" for p in wrote))

    def commit_and_push(self, message: str, push: bool) -> RunResult:
        ok, out = self.tools.git_commit(message)
        if not ok:
            return RunResult(False, out)

        if push:
            ok2, out2 = self.tools.git_push()
            if not ok2:
                return RunResult(False, "Commit succeeded, but push failed:\n" + out2)
            return RunResult(True, "Commit and push succeeded.")

        return RunResult(True, "Commit succeeded.")

    def list_available_prompts(self) -> dict[str, list[str]]:
        """List all available prompt tasks and their variants."""
        tasks = self.prompt_manager.list_available_tasks()
        result: dict[str, list[str]] = {}
        for task in tasks:
            result[task] = self.prompt_manager.list_variants(task)
        return result
