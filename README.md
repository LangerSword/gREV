---
title: gREV OpenEnv
emoji: 🛠️
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
tags:
  - openenv
---

# gREV: OpenENV Environment that eases Github Action CI/CD Management

**gREV** is a specialized OpenEnv-compliant sandbox designed to evaluate AI agents on real-world DevOps and CI/CD tasks. Developed as part of the **Satoshi Lab (Next Tech Lab AP)** initiative, gREV provides a secure, deterministic arena for agents to explore, debug, and repair broken software repositories.

## 🚀 Overview

Unlike toy environments, gREV simulates a professional developer workflow. The agent is placed in a workspace containing a broken Python project and must utilize shell commands and file editing to restore the repository to a passing state (Reward = 1.0).

### Key Features:
- **OpenEnv Alpha Compliant**: Fully supports the latest multi-mode deployment and async lifecycle.
- **Deterministic Grading**: Integrated `pytest` scoring logic that converts test pass rates into fractional rewards.
- **Security First**: Absolute path resolution prevents agents from escaping the `/tmp/grev_workspace` sandbox.
- **Autonomous Ready**: Optimized for high-speed inference via Groq/Llama-3.

---

## 🏗️ Task Structure

The environment supports tiered difficulty levels. Each task is located in the `tasks/` directory:

- **Easy**: Simple syntax errors or logic bugs in a single file.
- **Medium**: Integration bugs across multiple modules.
- **Hard**: Complex dependency or configuration issues.

Upon calling `/reset`, the environment copies the selected task into a clean workspace, ensuring every evaluation starts from a known "broken" state.

---

## 🛠️ Setup & Deployment

### Local Development
To run the server locally on your Arch machine:
```bash
uv lock
python server/app.py
