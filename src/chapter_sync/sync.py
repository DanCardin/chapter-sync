from __future__ import annotations

import time
from typing import Annotated

import cappa
import pendulum
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from chapter_sync.cli.base import Sync, Watch, console, database, email_client
from chapter_sync.console import Console
from chapter_sync.email import EmailClient
from chapter_sync.epub import Epub
from chapter_sync.handlers import get_chapter_handler, get_settings_handler
from chapter_sync.request import requests_session
from chapter_sync.schema import Chapter, Series


def watch(
    command: Watch,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
    email_client: Annotated[EmailClient, cappa.Dep(email_client)],
):
    try:
        with console.status("Syncing series") as status:
            while True:
                sync(command, database, console, email_client)

                status.update("Sleeping")
                time.sleep(command.interval)
    except KeyboardInterrupt:
        console.info("Stopping")
        return


def sync(
    command: Sync,
    database: Annotated[Session, cappa.Dep(database)],
    console: Annotated[Console, cappa.Dep(console)],
    email_client: Annotated[EmailClient, cappa.Dep(email_client)],
):
    query = select(Series).options(selectinload(Series.chapters))
    if command.series:
        query = query.where(Series.id.in_(command.series))

    series = database.scalars(query).all()

    console.info(f"Found {len(series)} series")

    for s in series:
        if command.update:
            update_series(database, s, console)
            console.info(f"Updated series: '{s.name}'")

        if command.save:
            save_series_ebooks(database, s, console)

        if command.send:
            send_series(command, database, s, email_client, console)


def update_series(database: Session, series: Series, console: Console):
    settings_handler = get_settings_handler(series.type, load=False)
    settings = settings_handler(series.settings)

    # Check for chapters without next_chapter_url (potentially incomplete chains)
    chapters_without_next = [c for c in series.chapters if not c.next_chapter_url]
    if chapters_without_next:
        console.info(f"Found {len(chapters_without_next)} chapters without next_chapter_url, re-syncing to update links")

    requests = requests_session()
    chapter_handler = get_chapter_handler(series.type)
    for chapter in chapter_handler(requests, series, settings, console):
        database.add(chapter)
        database.commit()
    
    # After sync, check for broken chains
    detect_broken_chains(series, console)


def detect_broken_chains(series: Series, console: Console):
    """Detect and report broken chapter chains."""
    if not series.chapters:
        return
    
    url_to_chapter = {c.url: c for c in series.chapters}
    
    # Find chapters that reference non-existent chapters
    broken_references = []
    for chapter in series.chapters:
        if chapter.previous_chapter_url and chapter.previous_chapter_url not in url_to_chapter:
            broken_references.append(f"Chapter '{chapter.title}' references missing previous chapter: {chapter.previous_chapter_url}")
        if chapter.next_chapter_url and chapter.next_chapter_url not in url_to_chapter:
            broken_references.append(f"Chapter '{chapter.title}' references missing next chapter: {chapter.next_chapter_url}")
    
    # Find orphaned chapters (not referenced by any other chapter)
    referenced_urls = set()
    for chapter in series.chapters:
        if chapter.previous_chapter_url:
            referenced_urls.add(chapter.previous_chapter_url)
        if chapter.next_chapter_url:
            referenced_urls.add(chapter.next_chapter_url)
    
    # Find chapters without previous that aren't the start of the chain
    first_chapters = [c for c in series.chapters if not c.previous_chapter_url]
    if len(first_chapters) > 1:
        console.warning(f"Found {len(first_chapters)} chapters without previous_chapter_url - may indicate multiple broken chains")
    
    # Find chapters without next that aren't the end of the chain  
    last_chapters = [c for c in series.chapters if not c.next_chapter_url]
    if len(last_chapters) > 1:
        console.warning(f"Found {len(last_chapters)} chapters without next_chapter_url - may indicate multiple broken chains or incomplete sync")
    
    if broken_references:
        console.warning("Broken chapter references detected:")
        for ref in broken_references:
            console.warning(f"  - {ref}")


def save_series_ebooks(database: Session, series: Series, console: Console):
    ordered_chapters = series.get_chapters_ordered()
    for chapter in ordered_chapters:
        console.info(f"Saving chapter: '{chapter.title}'")
        if chapter.ebook:
            continue

        # Get chapter position in the ordered list to pass correct chapter number
        chapter_position = ordered_chapters.index(chapter) + 1
        ebook = Epub.from_series(series, chapter, chapter_position=chapter_position).write_buffer()
        chapter.ebook = ebook.getbuffer()
        database.commit()


def send_series(
    command: Sync,
    database: Session,
    series: Series,
    email_client: EmailClient,
    console: Console,
):
    subscribers = series.email_subscribers
    ordered_chapters = series.get_chapters_ordered()
    unsent_chapters = [c for c in ordered_chapters if c.sent_at is None]

    if command.contiguous_chapters:
        # Build contiguous blocks based on chapter chain
        contiguous_blocks: list[list[Chapter]] = []
        current_block = []
        
        for chapter in unsent_chapters:
            if not current_block:
                current_block = [chapter]
            else:
                # Check if this chapter follows the previous one
                prev_chapter = current_block[-1]
                if prev_chapter.next_chapter_url == chapter.url:
                    current_block.append(chapter)
                else:
                    # Start new block
                    contiguous_blocks.append(current_block)
                    current_block = [chapter]
        
        if current_block:
            contiguous_blocks.append(current_block)
    else:
        contiguous_blocks = [[c] for c in unsent_chapters]

    for block in contiguous_blocks:
        if len(block) == 1 and block[0].ebook is not None:
            chapter = block[0]

            assert chapter.ebook is not None
            ebook = chapter.ebook

            title = chapter.filename()
        else:
            ebook = Epub.from_series(series, *block).write_buffer().read()
            if len(block) > 1:
                title = f"{series.name} - {block[0].title} to {block[-1].title}"
            else:
                title = f"{series.name} - {block[0].title}"

        titles = ", ".join([chapter.title for chapter in block])
        console.info(f"Sending chapters: {titles}")

        for subscriber in subscribers:
            email_client.send(
                subject=title,
                to=subscriber.email,
                filename=title,
                attachment=ebook,
            )

        for chapter in block:
            chapter.sent_at = pendulum.now("utc")

        database.commit()
        console.trace("Chapter(s) sent")
