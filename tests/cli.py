import pytest
from cappa import Dep
from cappa.testing import CommandRunner
from sqlalchemy.orm import Session

from chapter_sync.cli.base import ChapterSync, database
from chapter_sync.cli.base import email_client as email_client_dep
from chapter_sync.email import EmailClient


def create_cli_fixture(*base_args: str):
    @pytest.fixture
    def fixture(db: Session, email_client: EmailClient) -> CommandRunner:
        def db_override():
            return db

        def email_override():
            return email_client

        return CommandRunner(
            ChapterSync,
            base_args=list(base_args),
            deps={database: Dep(db_override), email_client_dep: Dep(email_override)},
        )

    return fixture
