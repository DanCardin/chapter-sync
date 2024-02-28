import pytest
from cappa import Exit
from cappa.testing import CommandRunner
from sqlalchemy.orm import Session

from chapter_sync.schema import Series
from tests.cli import create_cli_fixture
from tests.factories import ModelFactory

cli = create_cli_fixture("series", "remove")


def test_no_options(cli: CommandRunner):
    with pytest.raises(Exit) as e:
        cli.invoke()

    assert e.value.code == 1
    assert e.value.message == "Please provide an id or a name"


def test_by_id_bad(cli: CommandRunner, mf: ModelFactory):
    mf.series(id=2)

    with pytest.raises(Exit) as e:
        cli.invoke("--id=1")

    assert e.value.code == 1
    assert e.value.message == "id=1, name=None matched no records"


def test_by_id(cli: CommandRunner, db: Session, mf: ModelFactory):
    mf.series(id=2)

    cli.invoke("--id=2")

    result = db.query(Series).one_or_none()
    assert result is None


def test_by_name_bad(cli: CommandRunner, db: Session, mf: ModelFactory):
    mf.series(name="foo")

    with pytest.raises(Exit) as e:
        cli.invoke("--name=asdf")

    assert e.value.code == 1
    assert e.value.message == "id=None, name=asdf matched no records"


def test_by_name(cli: CommandRunner, db: Session, mf: ModelFactory):
    mf.series(name="foo")

    cli.invoke("--name=foo")

    result = db.query(Series).one_or_none()
    assert result is None
