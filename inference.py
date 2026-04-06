import os
import json
from openai import OpenAI
from grev.env import gREVEnv

# MANDATORY HACKATHON VARIABLES
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Meta-Llama-3-70B-Instruct")

MAX_STEPS = 8

SYSTEM_PROMPT = """
You are an expert Python developer fixing broken repositories.
You must use the provided JSON schema to take actions. 
You can either 'run_command' (like 'pytest' or 'cat file.py') or 'edit_file' (to fix bugs).
Your ultimate goal is to make all tests pass.
Respond strictly in JSON format:
{"action_type": "run_command", "command": "pytest"}
OR
{"action_type": "edit_file", "file_path": "main.py", "new_content": "def main():\\n    pass"}
"""

def main():
    if not API_KEY:
        print("CRITICAL: HF_TOKEN or API_KEY environment variable is missing.")
        return

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    tasks = ["easy", "medium", "hard"]

    for task in tasks:
        print(f"\n{'='*40}\nStarting gREV Task: {task.upper()}\n{'='*40}")
        env = gREVEnv(task_level=task)
        observation, info = env.reset() # OpenEnv standard returns obs, info
        
        history = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        for step in range(1, MAX_STEPS + 1):
            print(f"\n--- Step {step} ---")
            
            user_msg = (
                f"Current Directory: {observation.current_directory}\n"
                f"Files: {observation.directory_contents}\n"
                f"STDOUT: {observation.last_command_stdout}\n"
                f"STDERR: {observation.last_command_stderr}\n"
                "What is your next action? Respond in JSON."
            )
            history.append({"role": "user", "content": user_msg})
            
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=history,
                    response_format={"type": "json_object"},
                    temperature=0.2
                )
                action_json = response.choices[0].message.content
                print(f"Agent Action: {action_json}")
                history.append({"role": "assistant", "content": action_json})
                
                action_dict = json.loads(action_json)
                observation, reward, done, truncated, info = env.step(action_dict)
                
                print(f"Reward: {reward} | Done: {done}")
                
                if done:
                    print(f"Task {task} finished successfully!")
                    break
            except Exception as e:
                print(f"Agent failed or generated invalid JSON: {e}")
                break
        env.close()

if __name__ == "__main__":
    main()
