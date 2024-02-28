from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import cappa
from typing_extensions import Doc

from chapter_sync.handlers import HandlerTypes


@dataclass
class Series:
    """A collection of commands for managing series."""

    command: cappa.Subcommands[Add | Remove | Subscribe | Export | List | Set]


@cappa.command(invoke="chapter_sync.series.add")
@dataclass
class Add:
    """Add a new series to the database."""

    name: Annotated[str, Doc("The name of the series. Must be unique.")]
    url: Annotated[
        str, Doc("The root URL of the series, from which chapters are found.")
    ]

    author: Annotated[
        str | None,
        cappa.Arg(short=True, long=True),
        Doc("Optional 'author' metadata to attach to produced ebooks"),
    ] = None
    title: Annotated[
        str | None,
        cappa.Arg(long=True),
        Doc("Optional series title. If not supplied, defaults to the series 'name'."),
    ] = None
    cover_url: Annotated[
        str | None,
        cappa.Arg(short=True, long=True),
        Doc(
            "Optional url to cover art for the series. If not supplied, a page with the series 'title' will be generated."
        ),
    ] = None

    type: Annotated[
        HandlerTypes,
        cappa.Arg(short=True, long=True),
        Doc("One of the built-in types of series handlers. Defaults to 'custom'."),
    ] = "custom"
    settings: Annotated[
        str | None,
        cappa.Arg(short=True, long=True),
        Doc(
            "Configuration for the given 'type'. "
            "Depending on the 'type', this may or may not be required."
        ),
    ] = None
    file: Annotated[
        Path | None,
        cappa.Arg(short=True, long=True),
        Doc("Path to a configuration file, used in lieu of '--setting'."),
    ] = None


@cappa.command(invoke="chapter_sync.series.remove")
@dataclass
class Remove:
    """Remove an existing series from the database."""

    id: Annotated[
        int | None, cappa.Arg(long=True), Doc("The 'id' of the series to remove")
    ] = None
    name: Annotated[
        str | None, cappa.Arg(long=True), Doc("The 'name' of the series to remove")
    ] = None
    all: Annotated[
        bool,
        cappa.Arg(long=True),
        Doc("If no other options are supplied, --all can be used to remove all series"),
    ] = False


@cappa.command(invoke="chapter_sync.series.subscribe")
@dataclass
class Subscribe:
    """Add a subscriber to the given series."""

    series: Annotated[int, Doc("The 'id' of the series to subscribe to")]
    email: Annotated[
        str, cappa.Arg(short=True, long=True), Doc("The email to send the update to.")
    ]


@cappa.command(invoke="chapter_sync.series.export")
@dataclass
class Export:
    """Export the series as a standalone ebook."""

    series: Annotated[int, Doc("The 'id' of the series to export")]

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


@cappa.command(invoke="chapter_sync.series.list_series")
@dataclass
class List:
    """List all series in the database."""

    settings: Annotated[
        bool,
        cappa.Arg(long=True),
        Doc("Show the settings column"),
    ] = False


@cappa.command(invoke="chapter_sync.series.set_series")
@dataclass
class Set:
    """Change attributes about the chapter manually."""

    series: int

    settings: Annotated[
        str | None,
        cappa.Arg(long=True),
        Doc("Set the settings of the series to a new value."),
    ] = None
