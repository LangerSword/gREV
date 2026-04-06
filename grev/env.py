import os
import re
import shutil
import subprocess
from typing import Any

from .models import Action, Observation, Reward

WORKSPACE_DIR = "/tmp/grev_workspace"


class gREVEnv:
    def __init__(self, task_level: str):
        if task_level not in {"easy", "medium", "hard"}:
            raise ValueError("task_level must be one of: easy, medium, hard")
        self.task_level = task_level
        self._last_stdout = ""
        self._last_stderr = ""

    def reset(self) -> Observation:
        shutil.rmtree(WORKSPACE_DIR, ignore_errors=True)
        shutil.copytree(f"tasks/{self.task_level}", WORKSPACE_DIR)

        self._last_stdout = ""
        self._last_stderr = ""
        return self.state()

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict[str, Any]]:
        done = False
        score = 0.0
        stdout = ""
        stderr = ""

        if action.action_type == "edit_file":
            if not action.file_path:
                stderr = "Missing file_path for edit_file action."
            elif action.new_content is None:
                stderr = "Missing new_content for edit_file action."
            else:
                try:
                    target_path = self._resolve_workspace_path(action.file_path)
                    parent_dir = os.path.dirname(target_path)
                    if parent_dir:
                        os.makedirs(parent_dir, exist_ok=True)
                    with open(target_path, "w", encoding="utf-8") as file_handle:
                        file_handle.write(action.new_content)
                    stdout = "File updated successfully."
                except Exception as exc:
                    stderr = str(exc)

        elif action.action_type == "run_command":
            if not action.command:
                stderr = "Missing command for run_command action."
            else:
                try:
                    result = subprocess.run(
                        action.command,
                        shell=True,
                        cwd=WORKSPACE_DIR,
                        capture_output=True,
                        text=True,
                        timeout=15,
                    )
                except subprocess.TimeoutExpired as exc:
                    stdout = exc.stdout or ""
                    timeout_msg = "Command timed out after 15 seconds."
                    stderr = f"{(exc.stderr or '').strip()}\n{timeout_msg}".strip()
                    self._last_stdout = stdout
                    self._last_stderr = stderr
                    observation = self.state()
                    return observation, Reward.model_construct(score=-0.5), False, {}

                stdout = result.stdout or ""
                stderr = result.stderr or ""

                if action.command.strip().startswith("pytest"):
                    if result.returncode == 0:
                        score = 1.0
                        done = True
                    else:
                        passed_match = re.search(r"(\d+)\s+passed", stdout)
                        failed_match = re.search(r"(\d+)\s+failed", stdout)
                        if passed_match and failed_match:
                            passed = int(passed_match.group(1))
                            failed = int(failed_match.group(1))
                            total = passed + failed
                            score = passed / total if total > 0 else 0.1
                        else:
                            score = 0.1
                        done = False
        else:
            stderr = f"Unsupported action_type: {action.action_type}"

        self._last_stdout = stdout
        self._last_stderr = stderr
        observation = self.state()
        return observation, Reward(score=score), done, {}

    def state(self) -> Observation:
        if os.path.isdir(WORKSPACE_DIR):
            directory_contents = sorted(os.listdir(WORKSPACE_DIR))
        else:
            directory_contents = []
        return Observation(
            current_directory=WORKSPACE_DIR,
            directory_contents=directory_contents,
            last_command_stdout=self._last_stdout,
            last_command_stderr=self._last_stderr,
        )

    def _resolve_workspace_path(self, file_path: str) -> str:
        candidate = os.path.abspath(os.path.join(WORKSPACE_DIR, file_path))
        workspace_abs = os.path.abspath(WORKSPACE_DIR)
        if os.path.commonpath([workspace_abs, candidate]) != workspace_abs:
            raise ValueError("file_path must stay within the workspace")
        return candidate


gREV = gREVEnv
