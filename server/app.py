"""FastAPI application for gREV — OpenEnv environment for autonomous code repair."""

from __future__ import annotations
import os

try:
    from openenv.core.env_server.http_server import create_app
except ImportError:
    try:
        from openenv_core.env_server.http_server import create_app
    except ImportError:
        create_app = None

try:
    from grev.models import GrevAction, GrevObservation
    from grev.env import gREVEnv
except ImportError:
    from models import GrevAction, GrevObservation
    from grev.env import gREVEnv


# Build the OpenEnv app if the framework is available, otherwise a plain FastAPI app
if create_app is not None:
    app = create_app(
        gREVEnv,
        GrevAction,
        GrevObservation,
        env_name="grev",
        max_concurrent_envs=1,
    )
else:
    from fastapi import FastAPI
    app = FastAPI(title="gREV")

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Mount static assets
_static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(_static_dir, "index.html")
    try:
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="<h1>gREV</h1><p>Landing page not found.</p>", status_code=200)


@app.get("/health")
async def explicit_health():
    return JSONResponse(content={"status": "ok", "tasks": ["easy", "medium", "medium_hard", "hard", "very_hard"]})


def main(host: str = "0.0.0.0", port: int = 7860):
    """Run the server locally."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
