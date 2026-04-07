from openenv_core.env_server import create_app
from grev.env import gREVEnv
from grev.models import Action, Observation

# 1. Create a factory blueprint instead of a global instance
def env_factory():
    return gREVEnv(task_level="easy")

# 2. Pass the factory function to their server builder
app = create_app(
    env=env_factory,
    action_cls=Action,
    observation_cls=Observation,
)
