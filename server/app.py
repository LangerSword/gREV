import uvicorn
from openenv_core.env_server import create_app
from grev.env import gREVEnv
from grev.models import Action, Observation

# 1. Create a factory blueprint
def env_factory():
    return gREVEnv(task_level="easy")

# 2. Build the ASGI app
app = create_app(
    env=env_factory,
    action_cls=Action,
    observation_cls=Observation,
)

# 3. Add the main execution block required by the validator
def main():
    # Run the server on the hackathon-compliant port
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()
