from collections.abc import Iterable

from alembic import context
from alembic.operations import MigrationScript
from alembic.runtime.migration import MigrationContext
from sqlalchemy import engine_from_config, pool

from chapter_sync.schema import metadata


def process_revision_directives(
    context: MigrationContext,
    revision: str | Iterable[str | None] | Iterable[str],
    directives: list[MigrationScript],
):
    revision_context = context.opts["revision_context"]
    opts = revision_context.command_args
    if opts.get("message") and opts.get("autogenerate", False):
        script = directives[0]
        assert script.upgrade_ops is not None
        if script.upgrade_ops.is_empty():
            directives[:] = []


def run_migrations_online() -> None:
    config = context.config

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=metadata,
            compare_types=True,
            render_as_batch=True,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if __name__ == "env_py":
    run_migrations_online()
