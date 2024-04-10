import importlib.resources
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from chapter_sync.cli.base import alembic_config, database_url
from chapter_sync.web.dependencies import chapter_sync, database
from chapter_sync.web.routes import routes


def create_app(routes=routes):
    logging.basicConfig(level="INFO")

    boostrap_db()

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


def boostrap_db():
    app = chapter_sync()
    url = database_url(app)
    alembic = alembic_config(url)
    list(database(app, alembic))
