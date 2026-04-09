"""gREV environment implementation — RepoRescueEnv."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

try:
    from openenv.core.env_server.interfaces import Environment
except ImportError:
    from openenv_core.env_server.interfaces import Environment

try:
    from grev.models import GrevAction, GrevObservation, GrevState
except ImportError:
    from models import GrevAction, GrevObservation, GrevState


WORKSPACE_DIR = "/tmp/grev_workspace"

# Task configurations
TASK_CONFIGS = {
    "easy": {"max_steps": 12},
    "medium": {"max_steps": 16},
    "hard": {"max_steps": 20},
}


class gREVEnv(Environment):
    """OpenEnv-compliant environment for broken repository repair."""

    def __init__(self, **kwargs):
        self._task_level: str = "easy"
        self._step_count: int = 0
        self._max_steps: int = 12
        self._done: bool = False
        self._last_reward: float = 0.0
        self._cumulative_reward: float = 0.0
        self._idr_scores: List[float] = []
        self._strategy_scores: List[float] = []

    @property
    def state(self) -> GrevState:
        """Expose full environment state."""
        return GrevState(
            task_level=self._task_level,
            step_count=self._step_count,
            workspace_dir=WORKSPACE_DIR,
            max_steps=self._max_steps,
            directory_contents=self._get_dir_contents(),
        )

    def reset(self, task_level: str = "easy", seed: int = 42, **kwargs) -> GrevObservation:
        """Wipe workspace and copy fresh task files."""
        self._task_level = task_level
        config = TASK_CONFIGS.get(task_level, TASK_CONFIGS["easy"])
        self._max_steps = config["max_steps"]
        self._step_count = 0
        self._done = False
        self._last_reward = 0.0
        self._cumulative_reward = 0.0

        # Violently wipe the workspace to prevent state-bleed
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)

        # Locate task source — try multiple paths for Docker vs local
        task_source = None
        candidates = [
            f"tasks/{task_level}",
            f"/app/env/tasks/{task_level}",
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "tasks", task_level),
        ]
        for candidate in candidates:
            if os.path.exists(candidate):
                task_source = candidate
                break

        if task_source:
            shutil.copytree(task_source, WORKSPACE_DIR)
        else:
            os.makedirs(WORKSPACE_DIR, exist_ok=True)

        return GrevObservation(
            done=False,
            reward=0.0,
            current_directory=WORKSPACE_DIR,
            directory_contents=self._get_dir_contents(),
            last_command_stdout=f"Environment reset to {task_level}.",
            last_command_stderr="",
            last_error=None,
        )

    def step(self, action: GrevAction) -> GrevObservation:
        """Execute the agent's command or file edit."""
        stdout = ""
        stderr = ""
        done = False
        reward = 0.0
        error: Optional[str] = None

        self._step_count += 1

        try:
            if action.action_type == "run_command":
                if not action.command:
                    error = "Missing command for run_command action."
                    stderr = error
                else:
                    result = subprocess.run(
                        action.command,
                        shell=True,
                        cwd=WORKSPACE_DIR,
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                    stdout = result.stdout or ""
                    stderr = result.stderr or ""

                    # If they ran pytest successfully, task is complete
                    if "pytest" in action.command and result.returncode == 0:
                        done = True
                        reward = 1.0

                    # Partial reward: parse pytest output even on failure
                    if "pytest" in action.command and result.returncode != 0:
                        reward = self._parse_pytest_reward(stdout)

            elif action.action_type == "edit_file":
                if not action.file_path:
                    error = "Missing file_path for edit_file action."
                    stderr = error
                elif action.new_content is None:
                    error = "Missing new_content for edit_file action."
                    stderr = error
                else:
                    target_path = self._resolve_workspace_path(action.file_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(action.new_content)
                    stdout = f"File {action.file_path} updated successfully."

                    # Run hidden evaluation after edit
                    eval_score = self._run_hidden_evaluation()
                    reward = eval_score
                    if eval_score == 1.0:
                        done = True
            else:
                error = f"Unknown action_type: {action.action_type}"
                stderr = error

        except subprocess.TimeoutExpired:
            error = "Command timed out after 15 seconds."
            stderr = error
        except Exception as e:
            error = str(e)
            stderr = error

        # Force done if max steps reached
        if self._step_count >= self._max_steps:
            done = True

        self._done = done
        self._last_reward = reward
        self._cumulative_reward += reward

        return GrevObservation(
            done=done,
            reward=reward,
            current_directory=WORKSPACE_DIR,
            directory_contents=self._get_dir_contents(),
            last_command_stdout=stdout,
            last_command_stderr=stderr,
            last_error=error,
        )

    def grade(self) -> Tuple[float, Dict]:
        """Run pytest and return (score, breakdown)."""
        try:
            result = subprocess.run(
                f"{sys.executable} -m pytest",
                shell=True,
                cwd=WORKSPACE_DIR,
                capture_output=True,
                text=True,
                timeout=10,
            )

            stdout = result.stdout or ""

            if result.returncode == 0:
                return 1.0, {"status": "all_tests_passed", "stdout": stdout}

            passed, failed = 0, 0
            passed_match = re.search(r"(\d+)\s+passed", stdout)
            failed_match = re.search(r"(\d+)\s+failed", stdout)

            if passed_match:
                passed = int(passed_match.group(1))
            if failed_match:
                failed = int(failed_match.group(1))

            total = passed + failed
            score = passed / total if total > 0 else 0.0

            return float(score), {
                "passed": passed,
                "failed": failed,
                "total": total,
                "stdout": stdout,
                "stderr": result.stderr or "",
            }
        except Exception as e:
            return 0.0, {"error": str(e)}

    def close(self):
        """Clean up."""
        pass

    # ── helpers ──────────────────────────────────────────────

    def _get_dir_contents(self) -> List[str]:
        if not os.path.exists(WORKSPACE_DIR):
            return []
        return os.listdir(WORKSPACE_DIR)

    def _resolve_workspace_path(self, file_path: str) -> str:
        clean_path = os.path.normpath(file_path).lstrip("/")
        if clean_path.startswith("tmp/grev_workspace"):
            clean_path = clean_path.replace("tmp/grev_workspace", "", 1).lstrip("/")
        return os.path.join(WORKSPACE_DIR, clean_path)

    def _parse_pytest_reward(self, stdout: str) -> float:
        passed, failed = 0, 0
        passed_match = re.search(r"(\d+)\s+passed", stdout)
        failed_match = re.search(r"(\d+)\s+failed", stdout)
        if passed_match:
            passed = int(passed_match.group(1))
        if failed_match:
            failed = int(failed_match.group(1))
        total = passed + failed
        return passed / total if total > 0 else 0.0

    def _run_hidden_evaluation(self) -> float:
        try:
            result = subprocess.run(
                f"{sys.executable} -m pytest",
                shell=True,
                cwd=WORKSPACE_DIR,
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                return 1.0
            return self._parse_pytest_reward(result.stdout or "")
        except Exception:
            return 0.0
