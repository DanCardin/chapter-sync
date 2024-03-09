import io
import zipfile

from cappa.testing import CommandRunner
from responses import RequestsMock
from sqlalchemy.orm import Session

from chapter_sync.schema import Chapter
from tests.cli import create_cli_fixture
from tests.email import StubEmailClient
from tests.factories import ModelFactory

cli = create_cli_fixture("sync")


def test_from_scratch(
    cli: CommandRunner, mf: ModelFactory, db: Session, responses: RequestsMock
):
    url = "http://example.com"
    toc_url = f"{url}/toc"
    chap1_url = "http://example.com/chap1"
    chap2_url = "http://example.com/chap2"

    mf.series(
        settings={"chapter_selector": "ul > li > a", "content_selector": "p"},
        url=toc_url,
    )

    responses.get(
        f"{url}/toc",
        body=f"""
        <ul>
            <li><a href="{chap1_url}">Chap 1</a></li>
            <li><a href="{chap2_url}">Chap 2</a></li>
        </ul>
        """,
    )
    responses.get(f"{chap1_url}", body="<p>one</p")
    responses.get(f"{chap2_url}", body="<p>two</p")

    cli.invoke()

    chapters = db.query(Chapter).all()
    assert len(chapters) == 2

    assert chapters[0].content == "<div>\n one\n</div>\n"
    assert chapters[1].content == "<div>\n two\n</div>\n"


def test_merge_with_existing_content(
    cli: CommandRunner, mf: ModelFactory, db: Session, responses: RequestsMock
):
    url = "http://example.com"
    toc_url = f"{url}/toc"
    chap1_url = "http://example.com/chap1"
    chap2_url = "http://example.com/chap2"
    chap3_url = "http://example.com/chap3"

    series = mf.series(
        settings={"chapter_selector": "ul > li > a", "content_selector": "p"},
        url=toc_url,
    )
    mf.chapter(
        series,
        number=1,
        title="Chapter 1",
        content="<p>This is some content!</p>",
        url=chap1_url,
    )
    mf.chapter(
        series,
        number=2,
        title="Chapter 2",
        content="<p>Ive got more to say.</p>",
        url=chap2_url,
    )

    responses.get(
        f"{url}/toc",
        body=f"""
        <ul>
            <li><a href="{chap1_url}">Chap 1</a></li>
            <li><a href="{chap2_url}">Chap 2</a></li>
            <li><a href="{chap3_url}">Chap 3</a></li>
        </ul>
        """,
    )
    responses.get(f"{chap3_url}", body="<p>This is new!</p")

    cli.invoke()

    chapters = db.query(Chapter).all()
    assert len(chapters) == 3

    new_chapter = chapters[2]
    assert new_chapter.content == "<div>\n This is new!\n</div>\n"
    assert new_chapter.ebook

    file = io.BytesIO(new_chapter.ebook)
    assert zipfile.is_zipfile(file)


def test_subscriber_send(
    cli: CommandRunner,
    mf: ModelFactory,
    responses: RequestsMock,
    email_client: StubEmailClient,
):
    url = "http://example.com"
    toc_url = f"{url}/toc"

    series = mf.series(
        settings={"chapter_selector": "ul > li > a"},
        url=toc_url,
    )
    mf.chapter(
        series,
        number=1,
        title="Chapter 1",
        content="<p>This is some content!</p>",
        sent_at=None,
    )
    subscriber = mf.subscriber()
    mf.series_subscriber(series, subscriber)

    responses.get(f"{url}/toc", body="""<ul></ul>""")

    cli.invoke()

    assert email_client.sent_emails == [
        {
            "attachment": b"foo",
            "body": None,
            "filename": "foo: Chapter 1.epub",
            "subject": "foo: Chapter 1.epub",
            "to": "foo@foo.com",
        }
    ]
