import importlib.resources
import logging

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from chapter_sync.cli.base import ChapterSync, alembic_config, database_url
from chapter_sync.web.dependencies import database
from chapter_sync.web.routes import routes


def create_app(command: ChapterSync, routes=routes):
    logging.basicConfig(level="INFO")

    boostrap_db(command)

    app = FastAPI(command=command)

    static_dir = importlib.resources.files("chapter_sync.web.static")
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    for route in routes:
        app.add_api_route(
            path=route["path"],
            endpoint=route["endpoint"],
            methods=[route["method"]],
        )

    return app


def boostrap_db(command: ChapterSync):
    url = database_url(command)
    alembic = alembic_config(url)
    list(database(command, alembic))
