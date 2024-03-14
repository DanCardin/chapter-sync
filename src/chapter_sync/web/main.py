import importlib.resources
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from chapter_sync.web.routes import routes


def create_app(routes=routes):
    logging.basicConfig(level="INFO")

    app = FastAPI()

    static_dir = importlib.resources.files("chapter_sync.web.static")
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    for route in routes:
        app.add_api_route(
            path=route["path"],
            endpoint=route["endpoint"],
            methods=[route["method"]],
        )

    return app
