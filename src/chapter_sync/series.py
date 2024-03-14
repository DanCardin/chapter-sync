from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any

import cappa
from requests import Session as RequestsSession
from sqlalchemy import delete, or_, select
from sqlalchemy.orm import Session, selectinload

from chapter_sync.cli.base import console, database, requests
from chapter_sync.cli.series import Add, Export, List, Remove, Set, Subscribe
from chapter_sync.console import Console
from chapter_sync.epub import Epub
from chapter_sync.handlers import detect, get_infer_handler, get_settings_handler
from chapter_sync.schema import EmailSubscription, Series


def add(
    command: Add,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
    requests: Annotated[RequestsSession, cappa.Dep(requests)],
):
    conflicts = database.scalars(
        select(Series).where(Series.name == command.name)
    ).all()
    if conflicts:
        raise cappa.Exit(
            f"Series already exists with name='{command.name}' or url='{command.url}'",
            code=1,
        )

    series_type = detect(command.url) if command.type is None else command.type

    raw_settings = None
    if command.settings:
        raw_settings = command.settings
    elif command.file:
        raw_settings = command.file.read_text()

    settings_handler = get_settings_handler(series_type)
    settings = settings_handler(raw_settings)

    title = command.title
    author = command.author
    cover_url = command.cover_url
    if command.auto:
        infer_handler = get_infer_handler(series_type)
        if infer_handler:
            _title, _author, _cover_url = infer_handler(requests, command.url, settings)

            if title is None:
                title = _title
            if author is None:
                author = _author
            if cover_url is None:
                cover_url = _cover_url

    series = Series(
        name=command.name,
        url=command.url,
        cover_url=cover_url,
        title=title or command.name,
        author=author,
        type=series_type,
        settings=asdict(settings),
    )
    database.add(series)
    database.commit()

    console.info(f'Added series "{command.name}" at "{command.url}"')


def remove(
    command: Remove,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    if not any([command.id, command.name, command.all]):
        raise cappa.Exit("Please provide an id or a name", code=1)

    query = delete(Series)
    if command.id:
        query = query.where(Series.id == command.id)
    if command.name:
        query = query.where(Series.name == command.name)

    result = database.execute(query)
    if result.rowcount == 0:
        raise cappa.Exit(
            f"id={command.id}, name={command.name} matched no records", code=1
        )

    database.commit()

    console.info(f"Removed from {result.rowcount} series(s)")


def list_series(
    command: List,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    result = database.scalars(select(Series)).all()
    if not result:
        console.info("No series found")
        return

    if command.settings:
        columns = ["ID", "Name", "URL", "Settings"]
        table_result: list[tuple[Any, ...]] = [
            (r.id, r.name, r.url, json.dumps(r.settings)) for r in result
        ]
    else:
        columns = ["ID", "Name", "URL"]
        table_result = [(r.id, r.name, r.url) for r in result]

    console.table(
        "Series",
        columns,
        table_result,
    )


def subscribe(
    command: Subscribe,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    conflicts = database.scalars(
        select(EmailSubscription).where(
            or_(
                EmailSubscription.subscriber_id == command.subscriber,
                EmailSubscription.series_id == command.series,
            )
        )
    ).all()
    if conflicts:
        raise cappa.Exit(
            f"Subscriber already exists with email='{command.subscriber}' and series='{command.series}'",
            code=1,
        )

    sub = EmailSubscription(
        subscriber_id=command.subscriber,
        series_id=command.series,
    )
    database.add(sub)
    database.commit()

    console.info(f'Subscribed to "{command.series}" with "{command.subscriber}"')


def export(
    command: Export,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    series = get_series(database, command.series)

    ebook = series.ebook
    if not ebook or command.force:
        epub = Epub.from_series(series, *series.chapters).write_buffer()
        ebook = epub.getbuffer()

        if not command.no_save:
            series.ebook = ebook
            database.commit()

    file = command.output
    if file is None:
        file = series.filename()

    Path(file).write_bytes(ebook)
    console.info(f"Exported '{file}'")


def set_series(
    command: Set,
    database: Annotated[Session, cappa.Dep(database)],
):
    if not any([command.settings]):
        raise cappa.Exit("If no fields selected to set", code=1)

    query = select(Series).where(
        Series.id == command.series,
    )
    series = database.scalars(query).one_or_none()
    if series is None:
        raise cappa.Exit(f"No series with id={command.series}", code=1)

    if command.settings:
        settings_handler = get_settings_handler(series.type)
        settings = settings_handler(command.settings)
        series.settings = asdict(settings)

    database.commit()


def get_series(database: Session, series: int):
    sub = database.scalars(
        select(Series)
        .options(selectinload(Series.chapters))
        .where(
            Series.id == series,
        )
    ).one_or_none()

    if sub is None:
        raise cappa.Exit(
            f"No series found with id={series}",
            code=1,
        )

    return sub
