import pytest
from cappa import Dep
from cappa.testing import CommandRunner
from sqlalchemy.orm import Session

from chapter_sync.cli.base import ChapterSync, database


def create_cli_fixture(*base_args: str):
    @pytest.fixture
    def fixture(db: Session) -> CommandRunner:
        def db_override():
            return db

        return CommandRunner(
            ChapterSync, base_args=list(base_args), deps={database: Dep(db_override)}
        )

    return fixture
