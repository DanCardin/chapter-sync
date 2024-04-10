from __future__ import annotations

import functools
import json
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Literal, TypeAlias

import cappa

from chapter_sync.schema import Chapter


@dataclass
class ChapterInvalidation:
    number: int


HandlerTypes: TypeAlias = Literal["custom", "royal-road"]
ChapterHandlerResult: TypeAlias = Generator[Chapter | ChapterInvalidation, None, None]


def detect(url: str) -> HandlerTypes:
    from chapter_sync.handlers import royal_road

    settings_handlers: dict[HandlerTypes, Callable] = {
        "royal-road": royal_road.detect,
    }

    for name, fn in settings_handlers.items():
        if fn(url):
            return name

    return "custom"


def get_infer_handler(type: HandlerTypes) -> Callable | None:
    from chapter_sync.handlers import royal_road

    settings_handlers: dict[HandlerTypes, Callable] = {
        "royal-road": royal_road.infer,
    }

    handler = settings_handlers.get(type)
    if not handler:
        return None

    return handler


def get_settings_handler(type: HandlerTypes, load: bool = True) -> Callable:
    from chapter_sync.handlers import custom, royal_road

    settings_handlers: dict[HandlerTypes, Callable] = {
        "custom": custom.settings_handler,
        "royal-road": royal_road.settings_handler,
    }

    handler = settings_handlers[type]
    if load:
        return _settings_loader(handler)
    return handler


def get_chapter_handler(type: HandlerTypes) -> Callable:
    from chapter_sync.handlers import custom, royal_road

    chapter_handlers: dict[HandlerTypes, Callable] = {
        "custom": custom.chapter_handler,
        "royal-road": royal_road.chapter_handler,
    }
    return chapter_handlers[type]


def _settings_loader(handler):
    @functools.wraps(handler)
    def wrapper(content: str | None):
        if content is None:
            data = None
        else:
            try:
                data = json.loads(content)
            except json.JSONDecodeError as e:
                raise cappa.Exit(f"Invalid settings format: {e}", code=1)

        return handler(data)

    return wrapper
