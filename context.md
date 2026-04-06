# 🛠️ gREV: Scaler x Meta/HF Hackathon Master Plan
**Deadline:** April 8, 2026
**Tech Stack:** Python 3.10+, Pydantic, Subprocess, Pytest, Docker
**Workflow:** VS Code + Copilot (Manual Control > Agentic Hallucination)

## 📌 The Concept: "RepoRescueEnv"
A fully authentic, OpenEnv-compliant local developer sandbox. The AI agent is dropped into a broken Python repository and must use terminal commands (`subprocess`) and file edits to debug the code until the `pytest` suite passes perfectly.

---

## ⚖️ Hackathon Compliance & Scoring Checklist
To maximize points and avoid the automated validation script landmines, we must strictly adhere to these architectural rules:
- [x] **Real-World Utility (30%):** We use real Python code, real `pytest` traces, and real shell commands. No toy/fake bash scripts.
- [x] **Task & Grader Quality (25%):** Deterministic grading based on `pytest` exit codes.
- [ ] **Meaningful Reward Shaping (20%):** *CRITICAL:* We must parse the `pytest` output string (e.g., "2 failed, 3 passed") to award fractional points (0.6).
- [ ] **Clean State Management (15%):** *CRITICAL:* `reset()` must use `shutil.rmtree()` and `shutil.copytree()` to violently wipe the `/tmp/workspace` every episode to prevent state-bleed.
- [ ] **Sandbox Safety:** *CRITICAL:* All `subprocess.run()` calls must have a strict `timeout=15` parameter to prevent infinite loops from hanging the Hugging Face Space.
- [ ] **Offline Capable:** Do not rely on `pip install` hitting the internet during execution to avoid network flakiness disqualifications.

---

## 🗺️ Directory Architecture
```text
grev_project/
├── openenv.yaml           # OpenEnv manifest
├── inference.py           # Baseline OpenAI client script
├── Dockerfile             # Container definition for HF Spaces
├── requirements.txt       # Dependencies
├── grev/                  # Core module
│   ├── __init__.py
│   ├── models.py          # Pydantic data contracts
│   └── env.py             # OpenEnv state machine engine
└── tasks/                 # Read-only broken repositories
    ├── easy/              # Syntax error task
    ├── medium/            # Logic error task
    └── hard/              # Dependency mismatch task
