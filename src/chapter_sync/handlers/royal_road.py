import re
from collections.abc import Generator
from dataclasses import dataclass

from requests import Session

from chapter_sync.console import Console
from chapter_sync.handlers import custom
from chapter_sync.request import get_soup
from chapter_sync.schema import Chapter, Series


@dataclass
class Settings:
    volume_id: str | None = None


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
    chapter_selector = "#chapters tbody tr[data-url]"
    if settings.volume_id:
        chapter_selector += f'[data-volume-id="{settings.volume_id}"]'

    custom_settings = custom.Settings(
        chapter_selector=chapter_selector,
        chapter_link_selector="data-url",
        chapter_title_selector="td a",
        content_selector="div.chapter-content",
        content_apply=[strip_spoilers, strip_display_none_content],
        published_value_selector=("i.fa.fa-calendar + time", "datetime"),
        url_base_value_selector=('meta[property="og:url"]', "content"),
    )

    yield from custom.find_by_chapter(requests, series, custom_settings, console)


def strip_display_none_content(soup):
    # Royalroad has started inserting "this was stolen" notices into its
    # HTML, and hiding them with CSS. Currently the CSS is very easy to
    # find, so do so and filter them out.
    for style in soup.find_all("style"):
        match = re.match(r"\s*\.(\w+)\s*{[^}]*display:\s*none;[^}]*}", style.string)
        if not match:
            continue

        css_class = match.group(1)
        for warning in soup.find_all(class_=css_class):
            warning.decompose()


def strip_spoilers(soup):
    for spoiler in soup.find_all(class_=("spoiler-new")):
        spoiler.decompose()
