from collections.abc import Callable
from typing import Literal, TypedDict

from typing_extensions import NotRequired

from chapter_sync.web import chapter, series


class Route(TypedDict):
    path: str
    endpoint: Callable
    method: NotRequired[Literal["POST", "GET", "DELETE", "PUT"]]
    tags: list[str]


routes: list[Route] = [
    {
        "path": "/",
        "endpoint": series.list_series,
        "method": "GET",
        "tags": [],
    },
    {
        "path": "/series/{series_id}",
        "endpoint": series.get_series,
        "method": "GET",
        "tags": [],
    },
    {
        "path": "/series/{series_id}/chapter/{chapter_id}",
        "endpoint": chapter.get_chapter,
        "method": "GET",
        "tags": [],
    },
    {
        "path": "/series/{series_id}/chapter/{chapter_id}/export",
        "endpoint": chapter.export,
        "method": "POST",
        "tags": [],
    },
    {
        "path": "/series/{series_id}/chapter/{chapter_id}/ebook",
        "endpoint": chapter.download,
        "method": "GET",
        "tags": [],
    },
]
