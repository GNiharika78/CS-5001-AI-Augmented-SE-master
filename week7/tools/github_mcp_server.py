from __future__ import annotations

import json
import subprocess
from typing import List

from protocols.mcp import MCPServer


def _run(cmd: List[str]) -> str:
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.output.decode("utf-8", errors="replace"))


def gh_issue_create(title: str, body: str) -> str:
    return _run(["gh", "issue", "create", "--title", title, "--body", body]).strip()


def gh_pr_create(title: str, body: str, base: str = "main", head: str | None = None) -> str:
    cmd = ["gh", "pr", "create", "--base", base, "--title", title, "--body", body]
    if head:
        cmd.extend(["--head", head])
    return _run(cmd).strip()


def gh_issue_view(number: int) -> dict:
    raw = _run(["gh", "issue", "view", str(number), "--json", "title,body,url,labels"])
    return json.loads(raw)


def gh_pr_view(number: int) -> dict:
    raw = _run(["gh", "pr", "view", str(number), "--json", "title,body,url,files"])
    return json.loads(raw)


def build_github_mcp_server() -> MCPServer:
    server = MCPServer("github")
    server.register_tool("gh_issue_create", gh_issue_create)
    server.register_tool("gh_pr_create", gh_pr_create)
    server.register_tool("gh_issue_view", gh_issue_view)
    server.register_tool("gh_pr_view", gh_pr_view)
    return server