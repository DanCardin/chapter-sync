from __future__ import annotations

from pathlib import Path
from typing import Annotated

import cappa
import pendulum
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from chapter_sync.cli.base import console, database, email_client
from chapter_sync.cli.chapter import Export, List, Send, Set
from chapter_sync.console import Console, escape, render_datetime, render_float
from chapter_sync.email import EmailClient
from chapter_sync.epub import Epub
from chapter_sync.schema import Chapter, Series


def export(
    command: Export,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    chapter = get_chapter(database, command.series, command.number)

    ebook = chapter.ebook
    if not ebook or command.force:
        epub = Epub.from_series(chapter.series, chapter).write_buffer()
        ebook = epub.getbuffer()

        if not command.no_save:
            chapter.ebook = ebook
            database.commit()

    file = command.output
    if file is None:
        file = chapter.filename()

    Path(file).write_bytes(ebook)
    console.info(f"Exported '{file}'")


def list_chapters(
    command: List,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
):
    result = database.scalar(
        select(Series)
        .options(joinedload(Series.chapters).defer(Chapter.ebook))
        .where(Series.id == command.series)
    )
    if not result:
        console.info("No chapters found")
        return

    table_result = [
        (
            f"[link={escape(r.url)}]{r.title}[/link]",
            r.number,
            render_float(r.size_kb),
            render_datetime(r.sent_at),
            render_datetime(r.published_at),
            render_datetime(r.created_at),
        )
        for r in result.chapters
    ]
    console.table(
        result.title,
        ["Title", "Chapter", "Size (Kb)", "Sent", "Published", "Created"],
        table_result,
    )


def send(
    command: Send,
    database: Annotated[Session, cappa.Dep(database)],
    email_client: Annotated[EmailClient, cappa.Dep(email_client)],
):
    chapter = get_chapter(database, command.series, command.number)

    for subscriber in chapter.series.email_subscribers:
        title = chapter.filename()
        email_client.send(
            subject=title,
            to=subscriber.email,
            filename=title,
            attachment=chapter.ebook,
        )


def set_chapter(
    command: Set,
    database: Annotated[Session, cappa.Dep(database)],
):
    if command.number is None and not command.all:
        raise cappa.Exit(
            "If no chapter number is supplied, the `--all` flag must be explictly given",
            code=1,
        )

    query = (
        select(Chapter)
        .options(joinedload(Chapter.series))
        .where(
            Chapter.series_id == command.series,
        )
    )
    if command.number is not None:
        query = query.where(Chapter.number == command.number)

    chapters = database.scalars(query).all()

    now = pendulum.now()

    for chapter in chapters:
        if command.sent is not None:
            chapter.sent_at = now if command.sent else None
    database.commit()


def get_chapter(database: Session, series: int, number: int | None = None):
    chapter = database.scalars(
        select(Chapter)
        .options(joinedload(Chapter.series))
        .where(
            Chapter.series_id == series,
            Chapter.number == number,
        )
    ).one_or_none()
    if chapter is None:
        raise cappa.Exit(
            f"No chapter found with series={series}, number={number}",
            code=1,
        )

    return chapter
