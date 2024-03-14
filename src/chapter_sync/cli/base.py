from __future__ import annotations

import importlib.resources
import sys
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
from chapter_sync.cli.subscriber import Subscriber
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
    alembic_config: Annotated[Config | None, cappa.Dep(alembic_config)] = None,
) -> Generator[Session, None, None]:
    from chapter_sync.db import bootstrap

    engine = create_engine(database_url)

    if alembic_config:
        with engine.connect() as conn:
            bootstrap(conn, alembic_config)

    with Session(bind=engine) as session:
        yield session


def console(command: ChapterSync):
    console = Console(command.verbose, force_terminal=command.tty)
    try:
        yield console
    except KeyboardInterrupt:
        console.show_cursor()
        raise cappa.Exit("Exiting...")


def email_client(console: Annotated[Console, cappa.Dep(console)]) -> EmailClient:
    return EmailClient.from_env(console)


@dataclass
class ChapterSync:
    """A tool for managing ongoing series and subscribing to updates to them.

    Once a series has been added, the `sync` or `watch` commands can be used
    to keep the series up-to-date, and emit those updates to supported subscribers.
    """

    commands: cappa.Subcommands[
        Subscriber | Series | Sync | Watch | Chapter | Db | Web | None
    ]

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
    update: Annotated[
        bool,
        cappa.Arg(long="--update/--no-update"),
        Doc("Whether to check the series for new content updates (Default True)"),
    ] = True
    save: Annotated[
        bool,
        cappa.Arg(long="--save/--no-save"),
        Doc(
            "Whether to save the resultant epub to the chapter database (Default True)"
        ),
    ] = True
    send: Annotated[
        bool,
        cappa.Arg(long="--send/--no-send"),
        Doc("Whether send updates to subscribers (Default True)"),
    ] = True

    contiguous_chapters: Annotated[
        bool,
        cappa.Arg(long="--contiguous-chapters/--no-contiguous-chapters"),
        Doc(
            "Whether to combine unsent contiguous chapters into a single epub when sending (Default True)"
        ),
    ] = True


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


@dataclass
class Web:
    host: Annotated[str, cappa.Arg(short=True, long=True)] = "127.0.0.1"
    port: Annotated[int, cappa.Arg(short=True, long=True)] = 8000

    def __call__(self):
        import uvicorn

        from chapter_sync.web.main import create_app

        uvicorn.run(create_app(), host=self.host, port=self.port)


def run():
    try:
        cappa.invoke(ChapterSync, deps=[load_dotenv])
    except KeyboardInterrupt:
        sys.stderr.write("Exiting...\n")
