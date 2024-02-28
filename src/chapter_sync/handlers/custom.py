from collections.abc import Generator
from dataclasses import dataclass

import cappa
from pendulum import now
from requests import Session

from chapter_sync.console import Status
from chapter_sync.request import (
    clean_emails,
    clean_namespaced_elements,
    get_soup,
    join_path,
    published_at,
    strip_colors,
)
from chapter_sync.schema import Chapter, Series


# XXX: og:title, article:published_time, article:modified_time, and og:site_name all seem decently standard
#      of wordpress based sites. These might make decent default values for `title`, `content_title_selector`,
#      and the chapter dates.
@dataclass
class Settings:
    content_selector: str = ""
    # If present, find something within `content` to use a chapter title; if not found, the link text to it will be used
    content_title_selector: str | None = None
    # If present, find a specific element in the `content` to be the chapter text
    content_text_selector: str | None = None
    # If present, it looks for chapters linked from `url`. If not, it assumes `url` points to a chapter.
    chapter_selector: str | None = None
    # If present, use to find a link to the next content page (only used if not using chapter_selector)
    next_selector: str | None = None
    # If present, use to filter out content that matches the selector
    filter_selector: str | None = None


def settings_handler(raw: dict | None):
    if raw is None:
        raise cappa.Exit("'custom'-type series require settings!", code=1)

    try:
        return Settings(**raw)
    except Exception as e:
        raise ValueError(f"Invalid settings: {e}")


def chapter_handler(
    requests: Session, series: Series, settings: Settings, status: Status
) -> Generator[Chapter, None, None]:
    if settings.chapter_selector:
        yield from find_by_chapter(requests, series, settings, status=status)
    elif settings.next_selector:
        yield from find_by_next(requests, series, settings, status=status)
    else:
        raise NotImplementedError()


def find_by_chapter(
    requests: Session, series: Series, settings: Settings, status: Status
) -> Generator[Chapter, None, None]:
    assert settings.chapter_selector

    url = series.url

    soup = get_soup(requests, url, status=status)

    assert soup.head
    base = soup.head.base and soup.head.base.get("href") or False

    existing_chapters = {c.url: c for c in series.chapters}

    existing_chapter = None
    for chapter_link in soup.select(settings.chapter_selector):
        chapter_url = str(chapter_link.get("href"))

        if chapter_url in existing_chapters:
            existing_chapter = existing_chapters[chapter_url]
            continue

        if base:
            chapter_url = join_path(base, chapter_url)

        for chapter in _collect_chapter(
            requests,
            series,
            settings,
            chapter_url,
            status=status,
            title=chapter_link.string,
            number=existing_chapter.number + 1 if existing_chapter else 1,
        ):
            yield chapter
            existing_chapter = chapter


def find_by_next(
    requests: Session, series: Series, settings: Settings, status: Status
) -> Generator[Chapter, None, None]:
    assert settings.next_selector

    last_chapter = None
    if series.chapters:
        last_chapter = series.chapters[-1]

    next_url = last_chapter.url if last_chapter else series.url

    existing_urls = {c.url for c in series.chapters}

    while next_url:
        if next_url not in existing_urls:
            for chapter in _collect_chapter(
                requests,
                series,
                settings,
                next_url,
                status=status,
                number=last_chapter.number + 1 if last_chapter else 1,
            ):
                yield chapter
                last_chapter = chapter

        existing_urls.add(next_url)

        soup = get_soup(requests, next_url, status=status)

        assert soup.head
        base = soup.head.base and soup.head.base.get("href") or False

        next_link = soup.select(settings.next_selector)
        if not next_link:
            break

        next_link_url = str(next_link[0].get("href"))
        if base:
            next_link_url = join_path(series.url, base, next_link_url)

        next_url = join_path(next_url, next_link_url)


def _collect_chapter(
    requests: Session,
    series: Series,
    settings: Settings,
    url: str,
    *,
    status: Status,
    title: str | None = None,
    number: int = 1,
):
    status.update(f"Extracting chapter at '{url}'")
    soup = get_soup(requests, url, status=status)

    if not soup.select(settings.content_selector):
        return

    clean_namespaced_elements(soup)

    for content in soup.select(settings.content_selector):
        if settings.filter_selector:
            for filtered in content.select(settings.filter_selector):
                filtered.decompose()

        if settings.content_title_selector:
            title_element = content.select(settings.content_title_selector)
            if title_element:
                title = title_element[0].get_text().strip()

        if settings.content_text_selector:
            content = content.select(settings.content_text_selector)[0]

        content.name = "div"

        clean_emails(soup)
        strip_colors(soup)

        assert title
        time = now()
        yield Chapter(
            series_id=series.id,
            title=title,
            url=url,
            number=number,
            content=content.prettify(),
            published_at=published_at(soup) or time,
            created_at=time,
        )


def default_chapter(series: Series, chapter_num: int):
    return f"{series.title}: Chapter {chapter_num}"
