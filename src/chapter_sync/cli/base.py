from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Annotated

import cappa
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from typing_extensions import Doc

from chapter_sync.cli.chapter import Chapter
from chapter_sync.cli.series import Series
from chapter_sync.console import Console
from chapter_sync.email import EmailClient


def database(chapter_sync: ChapterSync) -> Generator[Session, None, None]:
    from chapter_sync.schema import Base

    engine = create_engine(f"sqlite:///{chapter_sync.database_name}")

    Base.metadata.create_all(bind=engine)

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

    commands: cappa.Subcommands[Series | Sync | Watch | Chapter]

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
