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
from chapter_sync.schema import ChapterSendEvent, Series


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
    if command.series:
        query = query.where(Series.id.in_(command.series))

    series = database.scalars(query).all()

    status.update(f"Found {len(series)} series")

    for s in series:
        if command.update:
            update_series(database, s, status)
            status.update(f"Updated series: '{s.name}'")

        if command.send:
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
        if command.save and chapter.ebook is None:
            ebook = Epub.from_series(series, chapter).write_buffer()
            chapter.ebook = ebook.getbuffer()
            database.commit()

        if chapter.sent_at is not None:
            continue

        status.update(f"Sending chapter: '{chapter.title}'")
        for series_subscribers in series.series_subscribers:
            if series_subscribers.send_event:
                continue

            if chapter.ebook is None:
                ebook = Epub.from_series(series, chapter).write_buffer().read()
            else:
                ebook = chapter.ebook

            database.add(
                ChapterSendEvent(
                    chapter_id=chapter.id, series_subscriber_id=series_subscribers.id
                )
            )

            title = chapter.filename()
            email_client.send(
                subject=title,
                to=series_subscribers.subscriber.email,
                filename=title,
                attachment=ebook,
            )

        chapter.sent_at = pendulum.now("utc")
        database.commit()
        status.update("Chapter sent")
