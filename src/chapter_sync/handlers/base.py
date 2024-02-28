import functools
import json
from collections.abc import Callable
from typing import Literal, TypeAlias

import cappa

HandlerTypes: TypeAlias = Literal["custom"]


def get_settings_handler(type: HandlerTypes, load: bool = True) -> Callable:
    from chapter_sync.handlers import custom

    settings_handlers: dict[HandlerTypes, Callable] = {
        "custom": custom.settings_handler,
    }

    handler = settings_handlers[type]
    if load:
        return _settings_loader(handler)
    return handler


def get_chapter_handler(type: HandlerTypes) -> Callable:
    from chapter_sync.handlers import custom

    chapter_handlers: dict[HandlerTypes, Callable] = {
        "custom": custom.chapter_handler,
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
