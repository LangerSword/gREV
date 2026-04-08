---
title: gREV OpenEnv
emoji: 🛠️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
tags:
  - openenv
  - devops
  - ci-cd
  - python
  - debugging
  - pytest
  - code-review
short_description: OpenEnv environment where AI agents fix broken Python repos
---

# gREV — RepoRescueEnv

An [OpenEnv](https://github.com/openenv)-compliant environment where AI agents are dropped into broken Python repositories and must debug them until the full `pytest` suite passes.

**Live space:** `https://langersword-grev-openenv.hf.space`  
**Source:** [github.com/LangerSword/gREV](https://github.com/LangerSword/gREV)

---

## Quick start

```bash
# Reset to a task
curl -X POST https://langersword-grev-openenv.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy", "seed": 42}'

# Take an action
curl -X POST https://langersword-grev-openenv.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"action_type": "run_command", "command": "pytest"}'

# Get final score
curl -X POST https://langersword-grev-openenv.hf.space/grade
```

---

## Tasks

| Task | Difficulty | Bug type | Max steps | Reward range |
|------|-----------|----------|-----------|--------------|
| `easy` | Easy | Syntax error — missing colon, wrong indent | 8 | 0.0 – 1.0 |
| `medium` | Medium | Logic error — wrong return value, off-by-one | 8 | 0.0 – 1.0 |
| `hard` | Hard | Multi-file import/dependency mismatch | 8 | 0.0 – 1.0 |

Reward is fractional: `score = passing_tests / total_tests`. An agent that fixes 3 of 5 tests scores 0.6, not 0.0.

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/tasks` | List all tasks with metadata |
| `POST` | `/reset` | Start a new episode — body: `{"task_id": str, "seed": int}` |
| `POST` | `/step` | Take one action — body: Action JSON |
| `GET` | `/state` | Current environment state |
| `POST` | `/grade` | Final episode score |

---

## Action space

| `action_type` | Required fields | Description |
|---------------|-----------------|-------------|
| `run_command` | `command: str` | Run a shell command (e.g. `pytest`, `cat main.py`). Returns stdout + stderr. Timeout: 15s. |
| `edit_file` | `file_path: str`, `new_content: str` | Overwrite a file with new content. |

---

## Observation space

| Field | Type | Description |
|-------|------|-------------|
| `current_directory` | `str` | Working directory path |
| `directory_contents` | `list[str]` | Files in the workspace |
| `last_command_stdout` | `str` | Stdout from the last `run_command` |
| `last_command_stderr` | `str` | Stderr from the last `run_command` |
| `step` | `int` | Current step number |
| `done` | `bool` | Whether the episode has ended |

---

## Baseline scores

| Task | Model | Score | Notes |
|------|-------|-------|-------|
| easy | Qwen/Qwen2.5-72B-Instruct | ~0.85 | Finds syntax error in 1–2 steps |
| medium | Qwen/Qwen2.5-72B-Instruct | ~0.60 | Logic errors require reading test output carefully |
| hard | Qwen/Qwen2.5-72B-Instruct | ~0.35 | Multi-file tracing challenges frontier models |

---

## Run the baseline agent

```bash
export HF_TOKEN=hf_...
export ENV_URL=https://langersword-grev-openenv.hf.space
python inference.py
```
