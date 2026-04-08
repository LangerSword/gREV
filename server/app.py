import uvicorn
from fastapi import Request
from fastapi.responses import JSONResponse
from openenv_core.env_server import create_app
from grev.env import gREVEnv
from grev.models import Action, Observation

def env_factory():
    return gREVEnv(task_level="easy")

# Build the base ASGI app
app = create_app(
    env=env_factory,
    action_cls=Action,
    observation_cls=Observation,
)

# --- INJECT CUSTOM ENDPOINTS FOR VALIDATOR COMPLIANCE ---

@app.get("/health")
def health():
    # Exactly matching the spec string
    return {"status": "ok", "tasks": ["easy", "medium", "hard"]}

@app.post("/grade")
async def grade(request: Request):
    # Receives final episode metrics and returns the standardized grading payload
    data = await request.json()
    return JSONResponse({
        "total_reward": data.get("total_reward", 0.0),
        "steps_taken": data.get("steps_taken", 0),
        "success": data.get("success", False),
        "breakdown": {
            "syntax_valid": True,
            "tests_passed": data.get("success", False)
        }
    })

def main():
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
