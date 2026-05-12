# Agentic Debugging System using Runtime Feedback

## Overview

This project presents an Agentic Debugging System that autonomously detects and repairs software bugs using runtime feedback and multiple AI agents. The system follows an iterative debugging workflow where failing code is analyzed, repaired, and re-tested until the issue is fixed or the maximum repair attempts are reached.

The project was implemented using Python, Ollama-based Large Language Models (LLMs), automated testing, and multi-agent coordination.

---

# Features

- Multi-agent debugging workflow
- Runtime feedback driven repair
- Iterative patch generation and validation
- Coverage analysis after successful repair
- Automatic test generation
- Support for local and cloud-based Ollama models
- Evaluation using MBPP benchmark dataset

---

# System Architecture

## Core Debugging Loop

```text
Test Execution
      ↓
Failure Analysis Agent
      ↓
Hypothesis Agent
      ↓
Patch Generation Agent
      ↓
Re-run Tests
      ↓
Repeat until success or max attempts
```
## Post-Success Validation
```text
Coverage Analysis Agent
      ↓
Test Generation Agent
      ↓
Run additional generated tests
```
## Agents

| Agent                   | Responsibility                                           |
| ----------------------- | -------------------------------------------------------- |
| Failure Analysis Agent  | Analyzes failing tests, stack traces, and runtime errors |
| Hypothesis Agent        | Identifies possible root causes and repair strategy      |
| Patch Generation Agent  | Generates and applies code fixes                         |
| Coverage Analysis Agent | Evaluates test coverage after repair                     |
| Test Generation Agent   | Generates additional validation tests                    |


# Dataset 
---
The system uses the MBPP (Mostly Basic Programming Problems) dataset.

Injected bug types include:

- Operator changes
- Boundary-condition errors
- Boolean logic modifications
- Loop-range errors
- Equality-condition modifications

---

# Technologies Used
---
- Python
- Ollama
- Pytest
- Coverage.py
- Large Language Models (LLMs)
---
# Models Tested:
---
- Mistral
- Ministral-3:8b-cloud
- DeepSeek-Coder
- Qwen2.5-Coder
- Devstral-small-2:24b-cloud
---

# Folder Structure
```text
agentic-debugging-system/
│
├── app/
│   ├── agents/
│   ├── tools/
│   ├── orchestrator.py
│   └── llm_client.py
│
├── experiments/
│   └── run_batch_experiment.py
│
├── data/
│   ├── raw/
│   └── results/
│
├── venv/
│
├── requirements.txt
└── README.md
```
# Installation

## Clone Repository

```bash
git clone <repository-url>
cd agentic-debugging-system
```

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Virtual Environment

### Windows CMD

```bash
venv\Scripts\activate
```

### PowerShell

```bash
.\venv\Scripts\Activate.ps1
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Running Experiments

## Run with Cloud Model

```bash
python -m experiments.run_batch_experiment --model ministral-3:8b-cloud --target 300 --max-attempts 3
```

## Run with Local Model

```bash
python -m experiments.run_batch_experiment --model mistral:latest --target 300 --max-attempts 3
```

## Run with DeepSeek

```bash
python -m experiments.run_batch_experiment --model deepseek-coder:latest --target 300 --max-attempts 3
```

## Run with Qwen

```bash
python -m experiments.run_batch_experiment --model qwen2.5-coder:7b --target 300 --max-attempts 3
```

---

# Experimental Results

| Metric | Value |
|---|---|
| Total Tasks Evaluated | 300 |
| Successfully Repaired | 265 |
| Failed Repairs | 35 |
| Success Rate | 88.3% |
| Average Repair Attempts | 2.04 |
| Average Runtime per Task | 23.43 sec |
| Average LLM Calls per Task | 4 |

The results demonstrate that iterative debugging using runtime feedback improves software repair reliability compared to one-time AI code generation approaches.

---

# Key Contributions

- Multi-agent autonomous debugging workflow
- Runtime-driven iterative repair loop
- Coverage analysis after successful repair
- Automatic test generation for validation
- Support for both local and cloud-based LLMs
- Large-scale evaluation on 300 debugging tasks

---

# Limitations

- Runtime latency increases due to repeated LLM calls
- The system currently supports mainly Python-based debugging tasks
- Generated patches may still fail on unseen edge cases
- Large-scale evaluations can become computationally expensive

---

# Future Work

- Hybrid debugging using rule-based repair for simple bugs and LLM reasoning for complex bugs
- Parallel execution for faster evaluation
- Multi-file debugging support
- Improved memory and planning mechanisms
- Formal verification for repaired code
- Support for additional programming languages

