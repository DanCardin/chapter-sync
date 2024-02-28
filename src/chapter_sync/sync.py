from __future__ import annotations

import time
from typing import Annotated

import cappa
import pendulum
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from chapter_sync.cli.base import Sync, Watch, console, database, email_client
from chapter_sync.console import Console, Status
from chapter_sync.email import EmailClient
from chapter_sync.epub import Epub
from chapter_sync.handlers import get_chapter_handler, get_settings_handler
from chapter_sync.request import requests_session
from chapter_sync.schema import Series


def watch(
    command: Watch,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
    email_client: Annotated[EmailClient, cappa.Dep(email_client)],
):
    try:
        with console.status("Syncing series") as status:
            while True:
                sync(command, database, console, email_client, status)
                time.sleep(command.interval)
                status.update("Sleeping")
    except KeyboardInterrupt:
        console.info("Stopping")
        return


def sync(
    command: Sync,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
    email_client: Annotated[EmailClient, cappa.Dep(email_client)],
    status: Status | None = None,
):
    requires_status = status is None
    if status is None:
        status = console.status("Syncing series")
        status.start()

    query = select(Series).options(selectinload(Series.chapters))
    series = database.scalars(query).all()

    status.update(f"Found {len(series)} series")

    for s in series:
        if not command.no_update:
            update_series(database, s, status)
            status.update(f"Updated series: '{s.name}'")

        if not command.no_send:
            send_series(command, database, s, email_client, status)

    status.update("Done")

    if requires_status:
        status.stop()


def update_series(database: Session, series: Series, status: Status):
    settings_handler = get_settings_handler(series.type, load=False)
    settings = settings_handler(series.settings)

    requests = requests_session()
    chapter_handler = get_chapter_handler(series.type)
    for chapter in chapter_handler(requests, series, settings, status):
        database.add(chapter)
        database.commit()


def send_series(
    command: Sync,
    database: Session,
    series: Series,
    email_client: EmailClient,
    status: Status,
):
    for chapter in series.chapters:
        status.update(f"Saving chapter: '{chapter.title}'")
        epub = Epub.from_series(series, chapter).write_buffer()
        if not command.no_save:
            chapter.ebook = epub.getbuffer()
            database.commit()

        if chapter.sent_at is not None:
            continue

        status.update(f"Sending chapter: '{chapter.title}'")
        for subscriber in series.email_subscribers:
            title = chapter.filename()
            email_client.send(
                subject=title,
                to=subscriber.email,
                filename=title,
                attachment=epub.read(),
            )

        chapter.sent_at = pendulum.now()
        database.commit()
        status.update("Chapter sent")
