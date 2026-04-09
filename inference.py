"""
gREV Inference Script
=====================
Mandatory env vars:
    API_BASE_URL   LLM endpoint  (default: Groq)
    MODEL_NAME     Model to use   (default: llama-3.3-70b-versatile)
    GROQ_API_KEY   Groq key  OR
    HF_TOKEN       HF token as fallback
    ENV_URL        gREV server   (default: http://localhost:7860)

STDOUT format (validated by the hackathon runner):
    [START] task=<task> env=<benchmark> model=<model>
    [STEP]  step=<n> action=<json_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...>
"""

import os
import json
import re
import sys
import time
import textwrap
import requests
from typing import List, Optional
from openai import OpenAI

# ── Configuration ────────────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.groq.com/openai/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "llama-3.3-70b-versatile")
API_KEY      = (
    os.getenv("GROQ_API_KEY")
    or os.getenv("HF_TOKEN")
    or os.getenv("API_KEY")
)
ENV_URL      = os.getenv("ENV_URL", "http://localhost:7860")
BENCHMARK    = "gREV"
MAX_STEPS    = 10

# Strip markdown link syntax if ENV_URL was accidentally set as "[text](url)"
_link_match = re.search(r'\((https?://[^)]+)\)', ENV_URL)
if _link_match:
    ENV_URL = _link_match.group(1)

SYSTEM_PROMPT = textwrap.dedent("""
    You are a Senior Python Engineer diagnosing a broken repository.
    The repo has a bug that is making pytest fail. Your job is to fix it.

    Strategy — follow this order strictly:
    1. On your first action, ALWAYS run: pytest --tb=short -q
    2. Read the traceback carefully. Identify the file and line number.
    3. Use cat <filename> to read the broken file in full.
    4. Write the corrected file using edit_file. Overwrite the whole file.
    5. Run pytest again to confirm all tests pass.

    RULES:
    - Respond with ONLY valid JSON. No explanation, no markdown fences.
    - For run_command: {"action_type": "run_command", "command": "<shell command>"}
    - For edit_file:   {"action_type": "edit_file", "file_path": "<path>", "new_content": "<full file content>"}
    - In new_content, use \\n for newlines. Escape all backslashes and quotes properly.
    - Never leave new_content empty. Always write the complete corrected file.
    - Do not use triple backticks or any text outside the JSON object.
""").strip()

# ── Logging (exact format the validator expects) ──────────────────────────────
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    print(
        f"[STEP] step={step} action={json.dumps(action)} "
        f"reward={reward:.2f} done={str(done).lower()} "
        f"error={error if error else 'null'}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )

# ── HTTP helpers (sync requests — no asyncio complexity) ──────────────────────
def wait_for_health(timeout: int = 60) -> bool:
    """Poll /health until the server responds or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(f"{ENV_URL}/health", timeout=3)
            if r.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False

def reset_env(task_id: str) -> dict:
    r = requests.post(
        f"{ENV_URL}/reset",
        json={"task_id": task_id, "seed": 42},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    # Handle both {observation: {...}} and flat observation shapes
    return data.get("observation", data)

def step_env(action: dict) -> dict:
    r = requests.post(f"{ENV_URL}/step", json=action, timeout=30)
    r.raise_for_status()
    return r.json()

def grade_env() -> dict:
    r = requests.post(f"{ENV_URL}/grade", timeout=30)
    r.raise_for_status()
    return r.json()

# ── Action parsing (robust — handles markdown fences and trailing text) ────────
def parse_action(raw: str) -> Optional[dict]:
    """Extract the first valid JSON object from the LLM response."""
    # Strip markdown code fences if present
    clean = re.sub(r"```(?:json)?", "", raw).strip()

    # Try direct parse first
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # Find the first { ... } block
    match = re.search(r'\{.*\}', clean, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None

# ── LLM call ──────────────────────────────────────────────────────────────────
def get_llm_action(client: OpenAI, messages: List[dict]) -> Optional[dict]:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
        )
        raw = response.choices[0].message.content or ""
        return parse_action(raw), raw
    except Exception as exc:
        return None, str(exc)

# ── Single task runner ─────────────────────────────────────────────────────────
def run_task(client: OpenAI, task: str) -> None:
    log_start(task=task, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        # ── Reset ────────────────────────────────────────────────────────────
        obs = reset_env(task)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for step in range(1, MAX_STEPS + 1):
            steps_taken = step

            # Build user message from current observation
            user_content = (
                f"Step {step}/{MAX_STEPS}\n"
                f"Directory: {obs.get('current_directory', '?')}\n"
                f"Files: {obs.get('directory_contents', [])}\n"
                f"STDOUT:\n{obs.get('last_command_stdout', '')}\n"
                f"STDERR:\n{obs.get('last_command_stderr', '')}\n"
                f"Done: {obs.get('done', False)}\n\n"
                f"What is your next action? Respond with JSON only."
            )
            messages.append({"role": "user", "content": user_content})

            # ── Get action from LLM ───────────────────────────────────────
            action_dict, raw_response = get_llm_action(client, messages)

            if action_dict is None:
                # LLM failed or gave unparseable output — fall back to pytest
                action_dict = {"action_type": "run_command", "command": "pytest --tb=short -q"}
                raw_response = json.dumps(action_dict)

            # Add assistant response to history
            messages.append({"role": "assistant", "content": raw_response})

            # ── Step the environment ──────────────────────────────────────
            try:
                step_result = step_env(action_dict)
            except requests.exceptions.RequestException as e:
                log_step(step=step, action=json.dumps(action_dict),
                         reward=0.0, done=True, error=str(e))
                rewards.append(0.0)
                break

            obs = step_result.get("observation", step_result)
            reward_obj = step_result.get("reward", {})
            reward = float(
                reward_obj.get("total", reward_obj)
                if isinstance(reward_obj, dict)
                else reward_obj
            )
            done = step_result.get("done", obs.get("done", False))
            error = step_result.get("info", {}).get("error") if isinstance(step_result.get("info"), dict) else None

            rewards.append(reward)
            log_step(
                step=step,
                action=json.dumps(action_dict),
                reward=reward,
                done=done,
                error=error,
            )

            if done:
                break

        # ── Grade ─────────────────────────────────────────────────────────
        try:
            grade_result = grade_env()
            score = float(grade_result.get("total_reward", 0.0))
        except Exception:
            # Fallback: derive score from rewards if /grade fails
            score = max(rewards) if rewards else 0.0

        score = min(max(score, 0.0), 1.0)
        success = score >= 0.7

    except Exception as exc:
        # Catch-all — always emit [END] no matter what
        print(f"[DEBUG] Task {task} crashed: {exc}", flush=True)
        score = 0.0
        success = False

    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)


# ── Entry point ───────────────────────────────────────────────────────────────
def main() -> None:
    # Validate API key
    if not API_KEY:
        print("[DEBUG] No API key found. Set GROQ_API_KEY, HF_TOKEN, or API_KEY.", flush=True)
        # Still emit END lines so the validator doesn't hang
        for task in ["easy", "medium", "hard"]:
            log_start(task=task, env=BENCHMARK, model=MODEL_NAME)
            log_end(success=False, steps=0, score=0.0, rewards=[])
        sys.exit(0)

    # Wait for the environment server to be healthy
    print(f"[DEBUG] Waiting for environment at {ENV_URL} ...", flush=True)
    if not wait_for_health(timeout=60):
        print(f"[DEBUG] Environment not reachable at {ENV_URL} after 60s.", flush=True)
        for task in ["easy", "medium", "hard"]:
            log_start(task=task, env=BENCHMARK, model=MODEL_NAME)
            log_end(success=False, steps=0, score=0.0, rewards=[])
        sys.exit(0)

    print(f"[DEBUG] Environment healthy. Starting tasks.", flush=True)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)

    for task in ["easy", "medium", "hard"]:
        run_task(client, task)


if __name__ == "__main__":
    main()

