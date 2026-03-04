## Installation

### Requirements
- Python 3.10+
- git
- GitHub CLI (`gh`) authenticated

Authenticate GitHub CLI:

gh auth login


### Setup Python environment

From the repository root:

python -m venv venv
venv\Scripts\Activate


### Run the Agent

python github_repo_agent/agent.py review --range HEAD~1..HEAD