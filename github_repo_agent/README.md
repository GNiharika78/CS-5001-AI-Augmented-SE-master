# Personalized GitHub Repository Agent (CLI)

## Requirements (real tool use)
- git
- gh (GitHub CLI) authenticated (`gh auth login`)
- Python 3.10+

## Install
From repo root:
```bash
chmod +x agent/agent.py
ln -sf "$PWD/agent/agent.py" /usr/local/bin/agent