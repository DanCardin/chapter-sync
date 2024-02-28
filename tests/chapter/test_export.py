from datetime import datetime
from unittest.mock import patch

import pytest
from cappa import Exit
from cappa.testing import CommandRunner

from tests.cli import create_cli_fixture
from tests.factories import ModelFactory

cli = create_cli_fixture("chapter", "export")


@pytest.mark.parametrize("arg, issue", (((), "series"), (("1",), "number")))
def test_no_options(cli: CommandRunner, arg: tuple[str, ...], issue: str):
    with pytest.raises(Exit) as e:
        cli.invoke(*arg)

    assert e.value.code == 2
    assert e.value.message == f"Option '{issue}' requires an argument"


def test_export(cli: CommandRunner, mf: ModelFactory, capsys):
    series = mf.series(id=1, title="My Series")
    mf.chapter(
        series=series,
        number=1,
        ebook=b"abcdef",
        created_at=datetime(2020, 1, 1),
        published_at=datetime(2020, 1, 2),
        sent_at=datetime(2020, 1, 3),
    )

    with patch("pathlib.Path.write_bytes") as write_bytes:
        cli.invoke("1", "1")

    assert write_bytes.call_count == 1
    assert write_bytes.call_args[0][0] == b"abcdef"
