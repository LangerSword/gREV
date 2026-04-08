import os
import json
import requests
from openai import OpenAI

# --- Configuration ---
# Fallback to localhost if ENV_URL is not set by the test runner
ENV_URL = os.getenv("ENV_URL", "http://localhost:7860")
HF_TOKEN = os.getenv("HF_TOKEN")

# Switched to Qwen2.5-72B-Instruct per the new spec
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct"

# Initialize OpenAI client pointing to HF Inference Endpoints
client = OpenAI(
    base_url="https://api-inference.huggingface.co/v1/",
    api_key=HF_TOKEN
)

def run_inference():
    tasks = ["easy", "medium", "hard"]
    max_steps = 10

    for task in tasks:
        print(f"[START] Task: {task}")

        # 1. Reset the environment via HTTP
        try:
            reset_res = requests.post(f"{ENV_URL}/reset", json={"task_id": task})
            reset_res.raise_for_status()
            obs = reset_res.json()
        except Exception as e:
            print(f"Failed to reset environment for task {task}: {e}")
            continue

        # 2. Step Loop
        for step in range(max_steps):
            print(f"[STEP] {step}")

            # Prepare the prompt with strict JSON requirements
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are an autonomous debugging agent operating in a headless environment. "
                        "You must output ONLY valid JSON in one of the following formats:\n"
                        "{\"action_type\": \"run_command\", \"command\": \"<your command>\"}\n"
                        "OR\n"
                        "{\"action_type\": \"edit_file\", \"file_path\": \"<path>\", \"new_content\": \"<content>\"}\n"
                        "Do not include markdown formatting, explanations, or any other text."
                    )
                },
                {
                    "role": "user",
                    "content": f"Current Observation: {json.dumps(obs)}"
                }
            ]

            # Call LLM
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=messages,
                    temperature=0.1
                )
                raw_action = response.choices[0].message.content.strip()

                # Resilient JSON parsing: Strip hallucinated markdown blocks
                if raw_action.startswith("```json"):
                    raw_action = raw_action[7:]
                if raw_action.startswith("```"):
                    raw_action = raw_action[3:]
                if raw_action.endswith("```"):
                    raw_action = raw_action[:-3]
                
                action_payload = json.loads(raw_action.strip())
            
            except json.JSONDecodeError:
                # Fallback action to prevent pipeline crashes on bad LLM output
                action_payload = {"action_type": "run_command", "command": "echo 'Invalid JSON returned by LLM. Retrying...'"}
            except Exception as e:
                print(f"Error during LLM inference: {e}")
                break

            # Execute action via HTTP POST /step
            try:
                step_res = requests.post(f"{ENV_URL}/step", json=action_payload)
                step_res.raise_for_status()
                obs = step_res.json()
            except Exception as e:
                print(f"Error calling /step endpoint: {e}")
                break

            # Break loop if environment signals the task is complete
            if obs.get("done"):
                break

        # 3. Grade the episode via HTTP
        try:
            grade_res = requests.post(f"{ENV_URL}/grade", json={"task_id": task})
            grade_res.raise_for_status()
            grade_data = grade_res.json()
            
            # Formatted exactly to spec
            print(f"[END] Task: {task} | Reward: {grade_data.get('total_reward')} | Success: {grade_data.get('success')}")
        except Exception as e:
            print(f"Error calling /grade endpoint for task {task}: {e}")

if __name__ == "__main__":
    run_inference()
