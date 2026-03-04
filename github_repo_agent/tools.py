import os
import subprocess
from typing import List, Optional

class ToolError(RuntimeError):
    pass

def run(cmd: List[str], cwd: Optional[str] = None) -> str:
    try:
        out = subprocess.check_output(cmd, cwd=cwd, stderr=subprocess.STDOUT)
        return out.decode("utf-8", errors="replace")
    except FileNotFoundError:
        raise ToolError(f"Missing tool: {cmd[0]} (not found in PATH)")
    except subprocess.CalledProcessError as e:
        raise ToolError(e.output.decode("utf-8", errors="replace"))

def ensure_git_repo():
    out = run(["git", "rev-parse", "--is-inside-work-tree"]).strip()
    if out != "true":
        raise ToolError("Not inside a git repository")

def git_diff_base(base: str) -> str:
    # Diff current HEAD vs merge-base with base
    run(["git", "fetch", "--all", "--prune"])
    merge_base = run(["git", "merge-base", "HEAD", base]).strip()
    return run(["git", "diff", f"{merge_base}..HEAD", "--"])

def git_diff_range(commit_range: str) -> str:
    return run(["git", "diff", commit_range, "--"])

def git_changed_files_base(base: str) -> List[str]:
    run(["git", "fetch", "--all", "--prune"])
    merge_base = run(["git", "merge-base", "HEAD", base]).strip()
    out = run(["git", "diff", "--name-only", f"{merge_base}..HEAD"])
    return [x.strip() for x in out.splitlines() if x.strip()]

def git_changed_files_range(commit_range: str) -> List[str]:
    out = run(["git", "diff", "--name-only", commit_range])
    return [x.strip() for x in out.splitlines() if x.strip()]

def read_file(path: str, max_bytes: int = 40_000) -> str:
    if not os.path.exists(path):
        raise ToolError(f"File not found: {path}")
    with open(path, "rb") as f:
        data = f.read(max_bytes + 1)
    if len(data) > max_bytes:
        return data[:max_bytes].decode("utf-8", errors="replace") + "\n...<truncated>..."
    return data.decode("utf-8", errors="replace")

# GitHub via gh CLI (real tool use)
def gh_issue_view(number: int) -> str:
    return run(["gh", "issue", "view", str(number), "--json", "title,body,labels,url,author,createdAt,updatedAt"])

def gh_pr_view(number: int) -> str:
    return run(["gh", "pr", "view", str(number), "--json", "title,body,files,url,author,createdAt,updatedAt"])

def gh_issue_create(title: str, body: str) -> str:
    return run(["gh", "issue", "create", "--title", title, "--body", body])

def gh_pr_create(title: str, body: str, base: str = "main") -> str:
    # Creates PR from current branch to base
    return run(["gh", "pr", "create", "--base", base, "--title", title, "--body", body])