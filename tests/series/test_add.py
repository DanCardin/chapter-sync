from dataclasses import asdict

import pytest
from cappa import Exit
from cappa.testing import CommandRunner
from sqlalchemy.orm import Session

from chapter_sync.handlers.custom import Settings
from chapter_sync.schema import Series
from tests.cli import create_cli_fixture

cli = create_cli_fixture("series", "add")
default_settings = ("--settings", '{"chapter_selector": ""}')


def test_custom_missing_settings(cli: CommandRunner):
    with pytest.raises(Exit) as e:
        cli.invoke("foo", "http://example.com")

    assert e.value.code == 1
    assert e.value.message == "'custom'-type series require settings!"


def test_custom(cli: CommandRunner, db: Session):
    cli.invoke("foo", "http://example.com", *default_settings)
    series = db.query(Series).one()
    assert series.name == "foo"
    assert series.url == "http://example.com"
    assert series.settings == asdict(Settings(chapter_selector=""))


def test_duplicate(cli: CommandRunner, db: Session):
    cli.invoke("foo", "http://example.com", *default_settings)

    with pytest.raises(Exit) as e:
        cli.invoke("foo", "http://example.com", *default_settings)

    assert e.value.code == 1
    assert (
        e.value.message
        == "Series already exists with name='foo' or url='http://example.com'"
    )

    series = db.query(Series).one()
    assert series


def test_extra_fields(cli: CommandRunner, db: Session):
    cli.invoke(
        "foo",
        "http://example.com",
        "--author=me",
        "--title=Title",
        "--cover-url=http://image",
        *default_settings,
    )
    series = db.query(Series).one()
    assert series.title == "Title"
    assert series.author == "me"
    assert series.cover_url == "http://image"
