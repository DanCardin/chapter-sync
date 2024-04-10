import re
from dataclasses import dataclass

from requests import Session

from chapter_sync.console import Status
from chapter_sync.handlers import custom
from chapter_sync.handlers.base import ChapterHandlerResult
from chapter_sync.request import (
    get_soup,
)
from chapter_sync.schema import Series


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
    requests: Session, series: Series, _: Settings, status: Status
) -> ChapterHandlerResult:
    settings = custom.Settings(
        chapter_selector="#chapters tbody tr td:first-child a",
        content_selector="chapter-content",
        filter_selector="spoiler-new",
        published_at_selector="profile-into time[datetime]",
    )
    yield from custom.chapter_handler(requests, series, settings, status)
