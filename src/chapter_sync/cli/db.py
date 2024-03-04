from __future__ import annotations

from dataclasses import dataclass

import cappa


@dataclass
class Db:
    """A collection of commands for managing the database."""

    command: cappa.Subcommands[Upgrade | Check | Revision]


@cappa.command(invoke="chapter_sync.db.upgrade")
@dataclass
class Upgrade:
    """Upgrade the database from a prior revision."""


@cappa.command(invoke="chapter_sync.db.check")
@dataclass
class Check:
    """Check whether the database requires an upgrade."""


@cappa.command(invoke="chapter_sync.db.revision", hidden=True)
@dataclass
class Revision:
    """Check whether the database requires an upgrade."""

    message: str
