from __future__ import annotations

from typing import Annotated

import cappa
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from chapter_sync.cli.base import console, database
from chapter_sync.cli.subscriber import Add, Remove, Set
from chapter_sync.console import Console
from chapter_sync.schema import EmailSubscriber, EmailSubscription


def add(
    command: Add,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    if command.email:
        conflicts = database.scalars(
            select(EmailSubscriber).where(EmailSubscriber.email == command.email)
        ).all()
        if conflicts:
            raise cappa.Exit(
                f"Subscriber already exists with email='{command.email}'",
                code=1,
            )

        subscriber = EmailSubscriber(email=command.email)
        database.add(subscriber)
        database.commit()

        console.info(f'Added subscriber "{command.email}" (email: "{command.email}")')


def remove(
    command: Remove,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    if not any([command.id, command.email, command.all]):
        raise cappa.Exit("Please provide an id or a name", code=1)

    query = delete(EmailSubscriber)
    if command.id:
        query = query.where(EmailSubscriber.id == command.id)
    if command.email:
        query = query.where(EmailSubscriber.email == command.email)

    result = database.execute(query)
    if result.rowcount == 0:
        raise cappa.Exit(
            f"id={command.id}, name={command.email} matched no records", code=1
        )

    database.commit()

    console.info(f"Removed from {result.rowcount} subscriber(s)")


def list_subscribers(
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    result = database.scalars(select(EmailSubscriber)).all()
    if not result:
        console.info("No subscribers found")
        return

    columns = ["ID", "Email"]
    table_result = [(r.id, r.email) for r in result]

    console.table(
        "Subscriber",
        columns,
        table_result,
    )


def set_subscriber(
    command: Set,
    database: Annotated[Session, cappa.Dep(database)],
):
    query = select(EmailSubscriber).where(
        EmailSubscriber.id == command.subscriber,
    )
    subscriber = database.scalars(query).one_or_none()
    if subscriber is None:
        raise cappa.Exit(f"No subscriber with id={command.subscriber}", code=1)

    if command.email:
        subscriber.email = command.email

    if command.series is not None:
        declared_series = set(command.series)
        existing_series = set(subscriber.subscribed_series_by_id)
        extra_series = existing_series - declared_series
        new_series = declared_series - existing_series
        for series in extra_series:
            subscriber.subscribed_series_by_id.pop(series)

        for series in new_series:
            subscriber.email_subscriptions.append(EmailSubscription(series_id=series))

    database.commit()
