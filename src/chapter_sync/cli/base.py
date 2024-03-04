from __future__ import annotations

import importlib.resources
from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

import cappa
from alembic.config import Config
from dotenv import load_dotenv
from requests import Session as RequestsSession
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing_extensions import Doc

from chapter_sync.cli.chapter import Chapter
from chapter_sync.cli.db import Db
from chapter_sync.cli.series import Series
from chapter_sync.console import Console
from chapter_sync.email import EmailClient
from chapter_sync.request import requests_session


def database_url(chapter_sync: ChapterSync) -> str:
    return f"sqlite:///{chapter_sync.database_name}"


def requests() -> RequestsSession:
    return requests_session()


def alembic_config(database_url: Annotated[str, cappa.Dep(database_url)]) -> Config:
    migrations = importlib.resources.files("chapter_sync.migrations")
    alembic_ini = migrations.joinpath("alembic.ini")
    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    alembic_cfg.set_main_option("script_location", str(migrations))
    return alembic_cfg


def database(
    database_url: Annotated[str, cappa.Dep(database_url)],
    alembic_config: Annotated[Config, cappa.Dep(alembic_config)],
) -> Generator[Session, None, None]:
    from chapter_sync.db import bootstrap

    engine = create_engine(database_url)
    with engine.connect() as conn:
        bootstrap(conn, alembic_config)

    with Session(bind=engine) as session:
        yield session


def console(command: ChapterSync):
    return Console(command.verbose, force_terminal=command.tty)


def email_client(console: Annotated[Console, cappa.Dep(console)]) -> EmailClient:
    return EmailClient.from_env(console)


@dataclass
class ChapterSync:
    """A tool for managing ongoing series and subscribing to updates to them.

    Once a series has been added, the `sync` or `watch` commands can be used
    to keep the series up-to-date, and emit those updates to supported subscribers.
    """

    commands: cappa.Subcommands[Series | Sync | Watch | Chapter | Db]

    database_name: Annotated[
        str,
        cappa.Arg(short=True, long=True),
        Doc("The name of the database file. Defaults to 'chapter_sync.sqlite'."),
    ] = "chapter_sync.sqlite"
    verbose: Annotated[
        int,
        cappa.Arg(short=True, long=True, action=cappa.ArgAction.count),
        Doc("Increase verbosity."),
    ] = 0
    tty: Annotated[bool | None, cappa.Arg(long="--tty/--no-tty", hidden=True)] = None


@cappa.command(invoke="chapter_sync.sync.sync")
@dataclass
class Sync:
    """Sync updates to all series."""

    series: Annotated[
        list[int] | None,
        cappa.Arg(long=True),
        Doc("Only sync the supplied set of series ids."),
    ] = None
    no_update: Annotated[
        bool,
        cappa.Arg(long=True),
        Doc("Do not update the set of known content."),
    ] = False
    no_save: Annotated[
        bool,
        cappa.Arg(long=True),
        Doc("Do not save the resultant epub to the chapter."),
    ] = False
    no_send: Annotated[
        bool,
        cappa.Arg(long=True),
        Doc("Do not send updates to subscribers."),
    ] = False


@cappa.command(invoke="chapter_sync.sync.watch")
@dataclass
class Watch(Sync):
    """Periodically sync updates to all series."""

    interval: Annotated[
        int,
        cappa.Arg(short=True, long=True),
        Doc("The duration (in seconds) to wait between each sync. Defaults to 3600."),
    ] = 3600
    iterations: Annotated[
        int,
        cappa.Arg(short="n", long=True),
        Doc(
            "The number of times to perform a sync. Defaults to 0, which will sync until stopped."
        ),
    ] = 0


def run():
    cappa.invoke(ChapterSync, deps=[load_dotenv])
