from openenv_core.env_server import create_app
from grev.env import gREVEnv
from grev.models import Action, Observation

# 1. Initialize our custom environment
env = gREVEnv(task_level="easy")

# 2. Build the ASGI app using Meta's core server builder
app = create_app(
    env=env,
    action_type=Action,
    observation_type=Observation,
)
