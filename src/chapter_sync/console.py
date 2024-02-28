from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from rich import console
from rich.markup import escape
from rich.status import Status
from rich.table import Table
from rich.theme import Theme

__all__ = [
    "Console",
    "Status",
    "escape",
]


class Console(console.Console):
    theme = Theme(
        {"trace": "white", "info": "blue", "warn": "yellow", "error": "bold red"}
    )

    def __init__(self, verbosity=0, force_terminal: bool | None = None):
        super().__init__(
            theme=self.theme,
            log_time=True,
            log_path=False,
            force_terminal=force_terminal,
        )
        self.verbosity = verbosity

    def trace(self, message):
        if self.verbosity >= 1:
            return self.log(message, style="trace")
        return None

    def info(self, message):
        return self.log(message, style="info")

    def warn(self, message):
        return self.log(message, style="warn")

    def error(self, message):
        return self.log(message, style="error")

    def table(self, title: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]):
        table = Table(title=title)

        for column in columns:
            table.add_column(column)

        for row in rows:
            table.add_row(*(str(c) for c in row))
        self.print(table)


def render_datetime(d: datetime | None, include_minutes=False) -> str:
    if d is None:
        return "N/A"

    format = "%Y-%m-%d"
    if include_minutes:
        format += " %H:%M"

    return d.strftime(format)


def render_float(f: float | None, length=1) -> str:
    if f is None:
        return "N/A"

    quantizor = Decimal(".1") / (10 ** (length - 1))
    result = Decimal(f).quantize(quantizor)
    return str(result)
