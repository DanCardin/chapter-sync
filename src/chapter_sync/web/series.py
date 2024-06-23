import io
from typing import Annotated

import requests
from fastapi import Depends, Form, Request
from fastapi.responses import RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from chapter_sync import series as series_actions
from chapter_sync.cli.series import Export, Send
from chapter_sync.console import Console
from chapter_sync.email import EmailClient
from chapter_sync.handlers.base import HandlerTypes
from chapter_sync.schema import Chapter, Series
from chapter_sync.web.dependencies import console, database, email_client, templates


def find_series(db: Session, series_id: int) -> Series | None:
    return db.query(Series).where(Series.id == series_id).one_or_none()


def list_series(
    request: Request,
    db: Annotated[Session, Depends(database)],
    templates: Annotated[Jinja2Templates, Depends(templates)],
):
    series = db.query(Series).all()
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "series": None,
            "chapter": None,
            "series_list": series,
        },
    )


def get_series(
    request: Request,
    db: Annotated[Session, Depends(database)],
    series_id: int,
    templates: Annotated[Jinja2Templates, Depends(templates)],
):
    series = find_series(db, series_id)
    chapters = (
        db.query(Chapter)
        .where(Chapter.series_id == series_id)
        .order_by(Chapter.number.desc())
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="series.html",
        context={
            "series": series,
            "chapter_list": chapters,
        },
    )


async def add_series(
    request: Request,
    db: Annotated[Session, Depends(database)],
    console: Annotated[Console, Depends(console)],
    name: Annotated[str, Form(...)],
    url: Annotated[str, Form(...)],
    type: Annotated[HandlerTypes, Form(...)],
    auto: Annotated[bool, Form(...)],
    author: Annotated[str | None, Form(...)] = None,
    title: Annotated[str | None, Form(...)] = None,
    cover_url: Annotated[str | None, Form(...)] = None,
    settings: Annotated[str | None, Form(...)] = None,
):
    command = series_actions.Add(
        name=name,
        url=url,
        type=type,
        auto=auto,
        author=author or None,
        title=title or None,
        cover_url=cover_url or None,
        settings=settings or None,
    )
    series_actions.add(command, db, console, requests.Session())

    return RedirectResponse(
        url=request.url_for("list_series"),
        status_code=HTTP_302_FOUND,
    )


def export(
    request: Request,
    db: Annotated[Session, Depends(database)],
    console: Annotated[Console, Depends(console)],
    series_id: int,
):
    series = find_series(db, series_id)
    assert series

    export = Export(series_id, force=True)
    series_actions.export(export, db, console)

    return RedirectResponse(
        url=request.url_for(
            "get_series",
            series_id=series_id,
        ),
        status_code=HTTP_302_FOUND,
    )


def download(
    db: Annotated[Session, Depends(database)],
    series_id: int,
):
    series = find_series(db, series_id)

    assert series
    assert series.ebook
    return StreamingResponse(
        io.BytesIO(series.ebook),
        media_type="application/epub+zip",
        headers={"Content-Disposition": f'inline; filename="{series.filename()}"'},
    )


def send(
    request: Request,
    db: Annotated[Session, Depends(database)],
    email_client: Annotated[EmailClient, Depends(email_client)],
    series_id: int,
    chapter_id: int,
):
    series = find_series(db, series_id)

    assert series
    assert series.ebook

    send = Send(series_id)
    series_actions.send(send, db, email_client)

    return RedirectResponse(
        url=request.url_for(
            "get_chapter",
            series_id=series_id,
            chapter_id=chapter_id,
        ),
        status_code=HTTP_302_FOUND,
    )
