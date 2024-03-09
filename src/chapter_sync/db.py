from __future__ import annotations

from typing import Annotated

import alembic.command
import cappa
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.runtime.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from alembic.util import AutogenerateDiffsDetected
from sqlalchemy import Connection

from chapter_sync.cli.base import alembic_config, console
from chapter_sync.cli.db import Revision
from chapter_sync.console import Console, confirm


def bootstrap(conn: Connection, alembic_config: Config):
    script = ScriptDirectory.from_config(alembic_config)
    env_context = EnvironmentContext(alembic_config, script)
    migration_context = MigrationContext.configure(conn)

    head = env_context.get_head_revision()
    revision = migration_context.get_current_revision()

    if not revision:
        alembic.command.upgrade(alembic_config, "head")
        return

    if head == revision:
        return

    if confirm("Database version is out of date, would you like to upgrade?"):
        alembic.command.upgrade(alembic_config, "head")
        return

    raise cappa.Exit("Database must be upgraded! Run `chapter-sync db upgrade`")


def upgrade(
    alembic_config: Annotated[Config, cappa.Dep(alembic_config)],
    console: Annotated[Console, cappa.Dep(console)],
):
    alembic.command.upgrade(alembic_config, "head")
    console.info("Success")


def check(
    alembic_config: Annotated[Config, cappa.Dep(alembic_config)],
):
    try:
        alembic.command.check(alembic_config)
    except AutogenerateDiffsDetected:
        raise cappa.Exit("New upgrade operations detected", code=1)


def revision(
    command: Revision,
    alembic_config: Annotated[Config, cappa.Dep(alembic_config)],
    console: Annotated[Console, cappa.Dep(console)],
):
    alembic.command.revision(alembic_config, command.message, autogenerate=True)