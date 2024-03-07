from __future__ import annotations

from typing import Annotated

import cappa
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from chapter_sync.cli.base import console, database
from chapter_sync.cli.subscriber import Add, Remove, Set
from chapter_sync.console import Console
from chapter_sync.schema import Subscriber


def add(
    command: Add,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    conflicts = database.scalars(
        select(Subscriber).where(Subscriber.name == command.name)
    ).all()
    if conflicts:
        raise cappa.Exit(
            f"Subscriber already exists with name='{command.name}'",
            code=1,
        )

    subscriber = Subscriber(name=command.name, email=command.email)
    database.add(subscriber)
    database.commit()

    console.info(f'Added subscriber "{command.name}" (email: "{command.email}")')


def remove(
    command: Remove,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    if not any([command.id, command.name, command.all]):
        raise cappa.Exit("Please provide an id or a name", code=1)

    query = delete(Subscriber)
    if command.id:
        query = query.where(Subscriber.id == command.id)
    if command.name:
        query = query.where(Subscriber.name == command.name)

    result = database.execute(query)
    if result.rowcount == 0:
        raise cappa.Exit(
            f"id={command.id}, name={command.name} matched no records", code=1
        )

    database.commit()

    console.info(f"Removed from {result.rowcount} subscriber(s)")


def list_subscribers(
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    result = database.scalars(select(Subscriber)).all()
    if not result:
        console.info("No subscribers found")
        return

    columns = ["ID", "Name", "Email"]
    table_result = [(r.id, r.name, r.email) for r in result]

    console.table(
        "Subscriber",
        columns,
        table_result,
    )


def set_subscriber(
    command: Set,
    database: Annotated[Session, cappa.Dep(database)],
):
    if not any([command.email]):
        raise cappa.Exit("If no fields selected to set", code=1)

    query = select(Subscriber).where(
        Subscriber.id == command.subscriber,
    )
    subscriber = database.scalars(query).one_or_none()
    if subscriber is None:
        raise cappa.Exit(f"No subscriber with id={command.subscriber}", code=1)

    if command.email:
        subscriber.email = command.email

    database.commit()
