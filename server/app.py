from openenv_core.env_server import create_app
from grev.env import gREVEnv

# 1. Initialize our custom environment
env = gREVEnv(task_level="easy")

# 2. Build the ASGI app (Meta simplified this in the latest update!)
app = create_app(env)
