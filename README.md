🛠️ gREV — GitHub Review Environment (OpenEnv)

gREV is an OpenEnv-compliant environment designed to train AI agents to debug real-world GitHub Actions CI/CD failures.

It simulates a developer’s workflow: analyzing logs, identifying root causes, and fixing broken pipelines.

🎯 Motivation

CI/CD failures cost developers hours every week.

gREV transforms this into a structured environment where agents learn to:

Diagnose failures
Understand workflow YAML
Suggest fixes

It replicates the role of a DevOps engineer reviewing failing pipelines.

🧠 Environment Overview

Each episode:

Agent receives a broken workflow/log
Takes actions (analyze, classify, fix)
Receives feedback (reward signal)
Ends with a graded score
📦 Action Space
Action Type	Parameters	Description	Reward Signal
classify_error	error_type	Classify CI failure	+0.3 correct
identify_root_cause	text	Explain cause	+0.3 correct
suggest_fix	yaml_patch	Provide fix	+0.4 correct
noop	none	No operation	0
👁️ Observation Space
Field	Description
logs	CI/CD logs
workflow_yaml	GitHub Actions YAML
task_id	difficulty
step_count	current step
hints	optional hints
🧪 Tasks
🟢 Easy
Classify CI error type
Example: syntax error
🟡 Medium
Identify root cause in YAML
Example: wrong dependency version
🔴 Hard
Generate full corrected workflow YAML
📊 Reward System
Fractional scoring (0.0 → 1.0)
Based on:
correctness
completeness
final fix success
🚀 API Endpoints
Endpoint	Method	Description
/reset	POST	Start new episode
/step	POST	Take action
/state	GET	Current state
/grade	POST	Final evaluation
/health	GET	Health check
⚙️ Running Locally
docker build -t grev .
docker run -p 7860:7860 grev
🤖 Running Agent
python inference.py
📈 Baseline Scores
Task	Model	Score
Easy	Qwen2.5-72B	0.75
Medium	Qwen2.5-72B	0.55
Hard	Qwen2.5-72B	0.35
🧩 Tech Stack
FastAPI
Docker
OpenAI-compatible LLMs
Hugging Face Spaces
🏁 Compliance
✅ OpenEnv spec compliant
✅ HTTP-based interaction
✅ Deterministic grading
✅ Real-world CI/CD tasks

# gREV
OpenENV Environment that eases Github Action CI/CD Management
