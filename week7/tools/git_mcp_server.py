from __future__ import annotations

import subprocess
from typing import List

from protocols.mcp import MCPServer


def _run(cmd: List[str]) -> str:
    out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    return out.decode("utf-8", errors="replace")


def ensure_git_repo() -> bool:
    return _run(["git", "rev-parse", "--is-inside-work-tree"]).strip() == "true"


def git_diff_base(base: str) -> str:
    _run(["git", "fetch", "--all", "--prune"])
    merge_base = _run(["git", "merge-base", "HEAD", base]).strip()
    return _run(["git", "diff", f"{merge_base}..HEAD", "--"])


def git_changed_files_base(base: str) -> List[str]:
    _run(["git", "fetch", "--all", "--prune"])
    merge_base = _run(["git", "merge-base", "HEAD", base]).strip()
    out = _run(["git", "diff", "--name-only", f"{merge_base}..HEAD"])
    return [x.strip() for x in out.splitlines() if x.strip()]


def git_diff_range(commit_range: str) -> str:
    return _run(["git", "diff", commit_range, "--"])


def git_changed_files_range(commit_range: str) -> List[str]:
    out = _run(["git", "diff", "--name-only", commit_range])
    return [x.strip() for x in out.splitlines() if x.strip()]


def read_file(path: str, max_bytes: int = 40000) -> str:
    with open(path, "rb") as f:
        data = f.read(max_bytes + 1)
    if len(data) > max_bytes:
        return data[:max_bytes].decode("utf-8", errors="replace") + "\n...<truncated>..."
    return data.decode("utf-8", errors="replace")


def build_git_mcp_server() -> MCPServer:
    server = MCPServer("git")
    server.register_tool("ensure_git_repo", ensure_git_repo)
    server.register_tool("git_diff_base", git_diff_base)
    server.register_tool("git_changed_files_base", git_changed_files_base)
    server.register_tool("git_diff_range", git_diff_range)
    server.register_tool("git_changed_files_range", git_changed_files_range)
    server.register_tool("read_file", read_file)
    return server