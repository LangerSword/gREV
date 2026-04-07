from openenv_core.env_server import create_app
from grev.env import gREVEnv
from grev.models import Action, Observation

# 1. Initialize our custom environment
env = gREVEnv(task_level="easy")

# 2. Build the ASGI app using Meta's newly renamed parameters
app = create_app(
    env=env,
    action_cls=Action,
    observation_cls=Observation,
)
