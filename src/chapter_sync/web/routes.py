from collections.abc import Callable
from typing import Literal, TypedDict

from chapter_sync.web import chapter, series, subscriber


class Route(TypedDict):
    path: str
    endpoint: Callable
    method: Literal["POST", "GET", "DELETE", "PUT"]


routes: list[Route] = [
    {
        "method": "GET",
        "path": "/",
        "endpoint": series.list_series,
    },
    {
        "method": "GET",
        "path": "/subscriber",
        "endpoint": subscriber.list_subscribers,
    },
    {
        "method": "POST",
        "path": "/subscriber",
        "endpoint": subscriber.add_subscriber,
    },
    {
        "method": "GET",
        "path": "/subscriber/{subscriber_id}",
        "endpoint": subscriber.get_subscriber,
    },
    {
        "method": "POST",
        "path": "/subscriber/{subscriber_id}",
        "endpoint": subscriber.update_subscriber,
    },
    {
        "method": "POST",
        "path": "/series",
        "endpoint": series.add_series,
    },
    {
        "method": "GET",
        "path": "/series/{series_id}",
        "endpoint": series.get_series,
    },
    {
        "method": "GET",
        "path": "/series/{series_id}/chapter/{chapter_id}",
        "endpoint": chapter.get_chapter,
    },
    {
        "method": "POST",
        "path": "/series/{series_id}/chapter/{chapter_id}/export",
        "endpoint": chapter.export,
    },
    {
        "method": "GET",
        "path": "/series/{series_id}/chapter/{chapter_id}/ebook",
        "endpoint": chapter.download,
    },
    {
        "method": "POST",
        "path": "/series/{series_id}/chapter/{chapter_id}/ebook",
        "endpoint": chapter.send,
    },
]
