from datetime import datetime

import pytest
from cappa import Exit
from cappa.testing import CommandRunner

from tests.cli import create_cli_fixture
from tests.factories import ModelFactory

cli = create_cli_fixture("chapter", "list")


def test_no_options(cli: CommandRunner):
    with pytest.raises(Exit) as e:
        cli.invoke()

    assert e.value.code == 2
    assert e.value.message == "Option 'series' requires an argument"


def test_list(cli: CommandRunner, mf: ModelFactory, capsys):
    mf.series(id=1, title="My Series")

    cli.invoke("1")

    out = capsys.readouterr().out
    assert out == (
        """\
                         My Series                          
┏━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━┓
┃ Title ┃ Chapter ┃ Size (Kb) ┃ Sent ┃ Published ┃ Created ┃
┡━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━┩
└───────┴─────────┴───────────┴──────┴───────────┴─────────┘
"""
    )


def test_list_item(cli: CommandRunner, mf: ModelFactory, capsys):
    series = mf.series(id=1, title="My Series")
    mf.chapter(
        series=series,
        number=1,
        ebook=b"a" * 2048,
        created_at=datetime(2020, 1, 1),
        published_at=datetime(2020, 1, 2),
        sent_at=datetime(2020, 1, 3),
    )

    cli.invoke("1")

    out = capsys.readouterr().out
    assert out == (
        """\
                              My Series                               
┏━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Title ┃ Chapter ┃ Size (Kb) ┃ Sent       ┃ Published  ┃ Created    ┃
┡━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ title │ 1       │ 2.0       │ 2020-01-03 │ 2020-01-02 │ 2020-01-01 │
└───────┴─────────┴───────────┴────────────┴────────────┴────────────┘
"""
    )
