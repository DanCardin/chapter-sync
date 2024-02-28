from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa
from typing_extensions import Doc


@dataclass
class Chapter:
    """A collection of commands for managing chapters."""

    command: cappa.Subcommands[Export | List | Send | Set]


@cappa.command(invoke="chapter_sync.chapter.export")
@dataclass
class Export:
    """Export an epub for a chapter."""

    series: int
    number: int

    output: Annotated[
        str | None,
        cappa.Arg(short=True, long=True),
        Doc("If not unspecified, it's calculated from the title/chapter"),
    ] = None

    no_save: Annotated[
        bool,
        cappa.Arg(long=True),
        Doc("Do not save the resultant epub to the chapter."),
    ] = False
    force: Annotated[
        bool,
        cappa.Arg(short=True, long=True),
        Doc("Do not save the resultant epub to the chapter."),
    ] = False


@cappa.command(invoke="chapter_sync.chapter.list_chapters")
@dataclass
class List:
    """List all chapters for the given series."""

    series: Annotated[int, Doc("The 'id' of the series to list chapters for.")]


@cappa.command(invoke="chapter_sync.chapter.send")
@dataclass
class Send:
    """Send the chapter to all subscribers."""

    series: Annotated[int, Doc("The 'id' of the series to list chapters for.")]
    number: Annotated[int, Doc("The 'number' of the chapter to send.")]


@cappa.command(invoke="chapter_sync.chapter.set_chapter")
@dataclass
class Set:
    """Change attributes about the chapter manually."""

    series: int
    number: int | None = None

    sent: Annotated[
        bool | None,
        cappa.Arg(long="--sent/--no-sent"),
        Doc("Set whether the chapter has been sent."),
    ] = None
    all: Annotated[
        bool,
        cappa.Arg(short=True, long=True),
        Doc("Whether to update all the chapters."),
    ] = False
