import re
from collections.abc import Generator
from dataclasses import dataclass

import pendulum
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


@dataclass
class Settings:
    ...


def detect(url: str) -> bool:
    return bool(re.match(r"^(https?://(?:www\.)?royalroad\.com/fiction/\d+)/?.*", url))


def infer(requests: Session, url: str, settings: Settings) -> tuple[str, str, str]:
    soup = get_soup(requests, url)

    title_h1 = soup.find("h1")
    title = title_h1.string.strip()  # type: ignore
    author = str(soup.find("meta", property="books:author").get("content").strip())  # type: ignore
    cover_url = str(soup.find("img", class_="thumbnail")["src"])  # type: ignore
    return (title, author, cover_url)


def settings_handler(raw: dict | None):
    if raw is None:
        return Settings()

    try:
        return Settings(**raw)
    except Exception as e:
        raise ValueError(f"Invalid settings: {e}")


def chapter_handler(
    requests: Session, series: Series, settings: Settings, console: Console
) -> Generator[Chapter, None, None]:
    # TODO: It's likely most kinds of sites can be handled in terms of the "custom" handler
    #       based on TOC. The main drawback would be things like login requirements, or
    #       the below extra cleaning bits. A system of callbacks for cleaning could be the most
    #       straghtforward way. And login could be handled by the requests session input.
    url = series.url

    soup = get_soup(requests, url, console=console)

    existing_chapters = {c.url: c for c in series.chapters}
    existing_chapter_number = -1
    if len(series.chapters) > 0:
        existing_chapter_number = series.chapters[-1].number

    chapter_elements = soup.select("#chapters tbody tr[data-url]")
    for number, chapter in enumerate(chapter_elements, start=1):
        chapter_url = join_path(series.url, str(chapter.get("data-url")))

        if chapter_url in existing_chapters:
            continue

        new_chapter_number = number
        if existing_chapter_number > 0:
            new_chapter_number = existing_chapter_number + 1

        title = chapter.find("a", href=True).string.strip()  # type: ignore
        yield _collect_chapter(
            requests,
            series,
            chapter_url,
            console=console,
            title=title,
            number=new_chapter_number,
        )
        existing_chapter_number = new_chapter_number


def _collect_chapter(
    requests: Session,
    series: Series,
    url: str,
    *,
    console: Console,
    title: str | None = None,
    number: int = 1,
):
    console.trace(f"Extracting chapter at '{url}'")
    soup = get_soup(requests, url, console=console)

    clean_namespaced_elements(soup)
    clean_emails(soup)
    strip_colors(soup)
    strip_spoilers(soup)

    content = soup.find("div", class_="chapter-content")
    strip_display_none_content(soup, content)

    published_at = pendulum.from_timestamp(
        int(soup.find(class_="profile-info").find("time").get("unixtime"))  # type: ignore
    )

    return Chapter(
        series_id=series.id,
        title=title,
        url=url,
        number=number,
        content=str(content),
        published_at=published_at,
    )


def strip_display_none_content(soup, content):
    # Royalroad has started inserting "this was stolen" notices into its
    # HTML, and hiding them with CSS. Currently the CSS is very easy to
    # find, so do so and filter them out.
    for style in soup.find_all("style"):
        match = re.match(r"\s*\.(\w+)\s*{[^}]*display:\s*none;[^}]*}", style.string)
        if not match:
            continue

        css_class = match.group(1)
        for warning in content.find_all(class_=css_class):
            warning.decompose()


def strip_spoilers(soup):
    for spoiler in soup.find_all(class_=("spoiler-new")):
        spoiler.decompose()
