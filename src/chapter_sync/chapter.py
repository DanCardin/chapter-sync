from __future__ import annotations

from pathlib import Path
from typing import Annotated

import cappa
import pendulum
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

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
    chapter = get_chapter_by_position(database, command.series, command.position)

    ebook = chapter.ebook
    if not ebook or command.force:
        # Get chapter position in ordered list
        ordered_chapters = chapter.series.get_chapters_ordered()
        try:
            chapter_position = ordered_chapters.index(chapter) + 1
        except ValueError:
            chapter_position = 1  # Fallback if chapter not found in ordered list
        
        epub = Epub.from_series(chapter.series, chapter, chapter_position=chapter_position).write_buffer()
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
            i + 1,  # Position in the ordered chain
            render_float(r.size_kb),
            render_datetime(r.sent_at),
            render_datetime(r.published_at),
            render_datetime(r.created_at),
        )
        for i, r in enumerate(result.get_chapters_ordered())
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
    chapter = get_chapter_by_position(database, command.series, command.position)
    ebook = chapter.ebook
    assert ebook

    for subscriber in chapter.series.email_subscribers:
        title = chapter.filename()
        email_client.send(
            subject=title,
            to=subscriber.email,
            filename=title,
            attachment=ebook,
        )


def set_chapter(
    command: Set,
    database: Annotated[Session, cappa.Dep(database)],
):
    if command.position is None and not command.all:
        raise cappa.Exit(
            "If no chapter position is supplied, the `--all` flag must be explicitly given",
            code=1,
        )

    if command.position is not None:
        chapter = get_chapter_by_position(database, command.series, command.position)
        chapters = [chapter]
    else:
        # Get all chapters for the series
        series = database.scalars(
            select(Series).options(selectinload(Series.chapters))
            .where(Series.id == command.series)
        ).one_or_none()
        if not series:
            raise cappa.Exit(f"No series found with id={command.series}", code=1)
        chapters = series.chapters

    now = pendulum.now()

    for chapter in chapters:
        if command.sent is not None:
            chapter.sent_at = now if command.sent else None
    database.commit()


def get_chapter_by_position(database: Session, series_id: int, position: int):
    series = database.scalars(
        select(Series)
        .options(selectinload(Series.chapters))
        .where(Series.id == series_id)
    ).one_or_none()
    
    if series is None:
        raise cappa.Exit(f"No series found with id={series_id}", code=1)
    
    ordered_chapters = series.get_chapters_ordered()
    
    if position < 1 or position > len(ordered_chapters):
        raise cappa.Exit(
            f"Chapter position {position} is out of range (1-{len(ordered_chapters)})",
            code=1,
        )
    
    return ordered_chapters[position - 1]
