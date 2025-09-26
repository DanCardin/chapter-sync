from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import cast

import cappa
import pendulum
from bs4 import BeautifulSoup, Tag
from pendulum import now
from requests import Session

from chapter_sync.console import Console
from chapter_sync.request import (
    clean_emails,
    clean_namespaced_elements,
    get_soup,
    join_path,
    strip_colors,
)
from chapter_sync.schema import Chapter, Series


# XXX: og:title, article:published_time, article:modified_time, and og:site_name all seem decently standard
#      of wordpress based sites. These might make decent default values for `title`, `content_title_selector`,
#      and the chapter dates.
@dataclass
class Settings:
    url_base_value_selector: tuple[str, str] | None = None

    published_value_selector: tuple[str, str] = (
        'meta[property="article:published_time"]',
        "content",
    )

    content_selector: str = ""
    # If present, find something within `content` to use a chapter title; if not found, the link text to it will be used
    content_title_selector: str | None = None
    # If present, find a specific element in the `content` to be the chapter text
    content_text_selector: str | None = None
    # If present, it looks for chapters linked from `url`. If not, it assumes `url` points to a chapter.
    chapter_selector: str | None = None
    chapter_link_selector: str = "href"
    chapter_title_selector: str | None = None
    # If present, use to find a link to the next content page (only used if not using chapter_selector)
    next_selector: str | None = None
    # If present, use to filter out content that matches the selector
    filter_selector: str | None = None

    content_apply: list[Callable[[BeautifulSoup], None]] | None = None


def settings_handler(raw: dict | None):
    if raw is None:
        raise cappa.Exit("'custom'-type series require settings!", code=1)

    try:
        return Settings(**raw)
    except Exception as e:
        raise ValueError(f"Invalid settings: {e}")


def chapter_handler(
    requests: Session, series: Series, settings: Settings, console: Console
) -> Generator[Chapter, None, None]:
    if settings.chapter_selector:
        yield from find_by_chapter(requests, series, settings, console=console)
    elif settings.next_selector:
        yield from find_by_next(requests, series, settings, console=console)
    else:
        raise NotImplementedError()


def find_by_chapter(
    requests: Session, series: Series, settings: Settings, console: Console
) -> Generator[Chapter, None, None]:
    assert settings.chapter_selector

    url = series.url

    soup = get_soup(requests, url, console=console)

    url_base = get_url_base(soup, settings)

    existing_chapters = {c.url: c for c in series.chapters}

    existing_chapter = None
    for chapter_link in soup.select(settings.chapter_selector):
        partial_url = str(chapter_link.get(settings.chapter_link_selector))
        chapter_url = join_path(url_base, partial_url)

        chapter_title_node = chapter_link
        if settings.chapter_title_selector:
            chapter_title_node = chapter_link.select_one(
                settings.chapter_title_selector
            )

        assert chapter_title_node
        title = str(chapter_title_node.string).strip()

        if chapter_url in existing_chapters:
            existing_chapter = existing_chapters[chapter_url]
            continue

        for chapter in _collect_chapter(
            requests,
            series,
            settings,
            chapter_url,
            console=console,
            title=title,
            number=existing_chapter.number + 1 if existing_chapter else 1,
        ):
            yield chapter
            existing_chapter = chapter


def find_by_next(
    requests: Session, series: Series, settings: Settings, console: Console
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
                console=console,
                number=last_chapter.number + 1 if last_chapter else 1,
            ):
                yield chapter
                last_chapter = chapter

        existing_urls.add(next_url)

        soup = get_soup(requests, next_url, console=console)
        url_base = get_url_base(soup, settings)

        assert soup.head
        base = soup.head.base and soup.head.base.get("href") or False

        next_link = soup.select(settings.next_selector)
        if not next_link:
            break

        next_link_url = str(next_link[0].get("href"))
        if base:
            next_link_url = join_path(url_base, next_link_url)

        next_url = join_path(next_url, next_link_url)


def _collect_chapter(
    requests: Session,
    series: Series,
    settings: Settings,
    url: str,
    *,
    console: Console,
    title: str | None = None,
    number: int = 1,
):
    console.trace(f"Extracting chapter at '{url}'")
    soup = get_soup(requests, url, console=console)

    if not soup.select(settings.content_selector):
        return

    content_apply = [
        clean_namespaced_elements,
        clean_emails,
        strip_colors,
        *(settings.content_apply or []),
    ]
    for fn in content_apply:
        fn(soup)

    for content in soup.select(settings.content_selector):
        if settings.filter_selector:
            for filtered in content.select(settings.filter_selector):
                filtered.decompose()

        if settings.content_title_selector:
            title_element = content.select(settings.content_title_selector)
            if title_element:
                title = title_element[0].get_text().strip()
        assert title

        if settings.content_text_selector:
            content = content.select(settings.content_text_selector)[0]

        content.name = "div"

        time = now()
        yield Chapter(
            series_id=series.id,
            title=title,
            url=url,
            number=number,
            content=content.prettify(),
            published_at=get_published_at(soup, settings) or time,
            created_at=time,
        )


def get_url_base(soup: BeautifulSoup, settings: Settings) -> str | None:
    if settings.url_base_value_selector:
        selector, tag_name = settings.url_base_value_selector
        base_tag = soup.select_one(selector)
        if base_tag:
            assert isinstance(base_tag, Tag)
            return str(base_tag.get(tag_name))

    assert soup.head
    base = soup.head.base and soup.head.base.get("href")
    if base:
        return str(base)

    return None


def get_published_at(
    soup: BeautifulSoup, settings: Settings
) -> pendulum.DateTime | None:
    dt_string = None

    selector, tag_name = settings.published_value_selector
    published_tag = soup.select_one(selector)
    if published_tag:
        assert isinstance(published_tag, Tag)
        dt_string = str(published_tag.get(tag_name))

    if not dt_string:
        return None

    try:
        return cast(pendulum.DateTime, pendulum.parse(dt_string))
    except Exception:
        return None
