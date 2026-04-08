import os
import shutil
import subprocess
import re
import sys
from grev.models import Action, Observation

WORKSPACE_DIR = "/tmp/grev_workspace"

class gREVEnv:
    def __init__(self, task_level="easy", **kwargs):
        self.task_level = task_level
        
    def reset(self, task_id=None, **kwargs):
        """Wipes the workspace and copies the fresh task files."""
        # If the client asked for a specific task, update it!
        if task_id:
            self.task_level = task_id
            
        # Violently wipe the workspace to prevent state-bleed
        if os.path.exists(WORKSPACE_DIR):
            shutil.rmtree(WORKSPACE_DIR)
            
        # Copy the correct broken task into the workspace
        task_source = f"tasks/{self.task_level}"
        if os.path.exists(task_source):
            shutil.copytree(task_source, WORKSPACE_DIR)
        else:
            # Failsafe just in case the tasks directory is missing
            os.makedirs(WORKSPACE_DIR, exist_ok=True)

        return Observation(
            done=False,
            current_directory=WORKSPACE_DIR,
            directory_contents=self._get_dir_contents(),
            last_command_stdout=f"Environment reset to {self.task_level}.",
            last_command_stderr=""
        )

    async def reset_async(self, **kwargs):
        return self.reset(**kwargs)

    def _get_dir_contents(self):
        """Helper to safely return the directory contents for the Observation model."""
        if not os.path.exists(WORKSPACE_DIR):
            return []
        return os.listdir(WORKSPACE_DIR)

    def _resolve_workspace_path(self, file_path):
        """Ensures file paths don't escape the sandbox."""
        clean_path = os.path.normpath(file_path).lstrip('/')
        # Strip duplicate /tmp/grev_workspace if the AI hallucinated the absolute path
        if clean_path.startswith("tmp/grev_workspace"):
            clean_path = clean_path.replace("tmp/grev_workspace", "", 1).lstrip('/')
        return os.path.join(WORKSPACE_DIR, clean_path)

    def _run_hidden_evaluation(self) -> float:
        """Silent background evaluation for intermediate step rewards."""
        try:
            result = subprocess.run(
                f"{sys.executable} -m pytest", 
                shell=True, 
                cwd=WORKSPACE_DIR, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if result.returncode == 0:
                return 1.0
                
            stdout = result.stdout or ""
            passed, failed = 0, 0
            
            passed_match = re.search(r"(\d+)\s+passed", stdout)
            failed_match = re.search(r"(\d+)\s+failed", stdout)
            
            if passed_match: passed = int(passed_match.group(1))
            if failed_match: failed = int(failed_match.group(1))
                
            total = passed + failed
            return passed / total if total > 0 else 0.0
        except Exception:
            return 0.0

    def step(self, action: Action):
        """Executes the agent's command or file edit."""
        stdout = ""
        stderr = ""
        done = False

        try:
            if action.action_type == "run_command":
                # Sandbox safety: timeout=15
                result = subprocess.run(
                    action.command,
                    shell=True,
                    cwd=WORKSPACE_DIR,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                stdout = result.stdout or ""
                stderr = result.stderr or ""
                
                # If they explicitly ran pytest and it succeeded, flag task complete
                if "pytest" in action.command and result.returncode == 0:
                    done = True

            elif action.action_type == "edit_file":
                if not action.file_path:
                    stderr = "Missing file_path for edit_file action."
                else:
                    target_path = self._resolve_workspace_path(action.file_path)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    with open(target_path, "w", encoding="utf-8") as f:
                        f.write(action.new_content)
                    stdout = f"File {action.file_path} updated successfully."
                    
                    # INTERMEDIATE GRADING: Check if this file edit fixed the repo!
                    score = self._run_hidden_evaluation()
                    if score == 1.0:
                        done = True

        except subprocess.TimeoutExpired:
            stderr = "Command timed out after 15 seconds."
        except Exception as e:
            stderr = str(e)

        return Observation(
            done=done,
            current_directory=WORKSPACE_DIR,
            directory_contents=self._get_dir_contents(),
            last_command_stdout=stdout,
            last_command_stderr=stderr
        )

    async def step_async(self, action: Action):
        return self.step(action)

    def grade(self):
        """
        OpenEnv Framework Grader: This is automatically called by the wrapper's /grade endpoint.
        Returns a tuple of (reward: float, breakdown: dict).
        """
        try:
            result = subprocess.run(
                f"{sys.executable} -m pytest", 
                shell=True, 
                cwd=WORKSPACE_DIR, 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            stdout = result.stdout or ""
            
            # Perfect Score
            if result.returncode == 0:
                return 1.0, {"status": "all_tests_passed", "stdout": stdout}
                
            # Partial Score
            passed, failed = 0, 0
            passed_match = re.search(r"(\d+)\s+passed", stdout)
            failed_match = re.search(r"(\d+)\s+failed", stdout)
            
            if passed_match: passed = int(passed_match.group(1))
            if failed_match: failed = int(failed_match.group(1))
                
            total = passed + failed
            score = passed / total if total > 0 else 0.0
            
            return float(score), {
                "passed": passed, 
                "failed": failed, 
                "total": total,
                "stdout": stdout,
                "stderr": result.stderr or ""
            }
        except Exception as e:
            return 0.0, {"error": str(e)}

    async def grade_async(self):
        return self.grade()

    def evaluate(self):
        """Alias to satisfy OpenEnv's internal evaluator checker"""
        return self.grade()

    async def evaluate_async(self):
        return self.grade()
        
    def close(self):
        pass
