import importlib.resources
from collections.abc import Generator
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from typing import Annotated

import pendulum
from dataclass_settings import Env, load_settings
from fastapi import Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from chapter_sync.cli import base
from chapter_sync.console import Console
from chapter_sync.email import EmailClient


@dataclass(frozen=True)
class Config:
    timezone: Annotated[str, Env("TIMEZONE")] = "UTC"


@cache
def config():
    return load_settings(Config)


def chapter_sync():
    return base.ChapterSync(None)


def database(
    chapter_sync: Annotated[base.ChapterSync, Depends(chapter_sync)],
) -> Generator[Session, None, None]:
    url = base.database_url(chapter_sync)
    yield from base.database(url)


def console(
    chapter_sync: Annotated[base.ChapterSync, Depends(chapter_sync)],
) -> Generator[base.Console, None, None]:
    yield from base.console(chapter_sync)


def email_client(console: Annotated[Console, Depends(console)]) -> EmailClient:
    return base.email_client(console)


@cache
def templates(config: Annotated[Config, Depends(config)]):
    template_dir = importlib.resources.files("chapter_sync.web").joinpath("templates")

    templates = Jinja2Templates(directory=str(template_dir))

    def relative_datetime(dt: datetime | None) -> str:
        if dt is None:
            return "N/A"

        then = pendulum.instance(dt, tz=config.timezone)
        now = pendulum.now(tz=config.timezone)
        diff = now - then
        return pendulum.format_diff(diff, is_now=True)

    def format_datetime(dt: datetime | None) -> str:
        if dt is None:
            return "N/A"

        return pendulum.instance(dt, tz=config.timezone).to_day_datetime_string()

    templates.env.filters["relative_datetime"] = relative_datetime
    templates.env.filters["format_datetime"] = format_datetime

    return templates
