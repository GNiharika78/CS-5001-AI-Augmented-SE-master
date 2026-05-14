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
## Usage Examples

Review changes
python github_repo_agent/agent.py review --base main

Draft PR (no creation yet)
python github_repo_agent/agent.py draft pr --instruction "..." --evidence-from-review

Approve PR creation
python github_repo_agent/agent.py approve --yes

Improve an issue/PR
python github_repo_agent/agent.py improve issue --number 1
python github_repo_agent/agent.py improve pr --number 2
