from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import cappa
from typing_extensions import Doc


@dataclass
class Subscriber:
    """A collection of commands for managing subscribers."""

    command: cappa.Subcommands[Add | Remove | List | Set]


@cappa.command(invoke="chapter_sync.subscriber.add")
@dataclass
class Add:
    """Add a new subscriber to the database."""

    email: Annotated[
        str | None,
        cappa.Arg(long=True),
        Doc(
            "Optional subscriber email. This enables the sending of emails on subscriptions."
        ),
    ] = None


@cappa.command(invoke="chapter_sync.subscriber.remove")
@dataclass
class Remove:
    """Remove an existing subscriber from the database."""

    id: Annotated[
        int | None, cappa.Arg(long=True), Doc("The 'id' of the subscriber to remove")
    ] = None
    email: Annotated[
        str | None, cappa.Arg(long=True), Doc("The 'email' of the subscriber to remove")
    ] = None
    all: Annotated[
        bool,
        cappa.Arg(long=True),
        Doc(
            "If no other options are supplied, --all can be used to remove all subscribers"
        ),
    ] = False


@cappa.command(invoke="chapter_sync.subscriber.list_subscribers")
@dataclass
class List:
    """List all subscriber in the database."""


@cappa.command(invoke="chapter_sync.subscriber.set_subscribers")
@dataclass
class Set:
    """Change attributes about the chapter manually."""

    subscriber: int

    email: Annotated[
        str | None,
        cappa.Arg(long=True),
        Doc("Set the email of the subscriber to a new value."),
    ] = None

    series: Annotated[
        list[int] | None,
        cappa.Arg(long=True),
        Doc("The set of series to be subscribed to."),
    ] = None
