from typing import Annotated, cast

import cappa
from fastapi import Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.status import HTTP_302_FOUND

from chapter_sync import subscriber as subscriber_actions
from chapter_sync.console import Console
from chapter_sync.schema import EmailSubscriber, EmailSubscription, Series
from chapter_sync.web.dependencies import console, database, templates


def list_subscribers(
    request: Request,
    db: Annotated[Session, Depends(database)],
    templates: Annotated[Jinja2Templates, Depends(templates)],
):
    subscribers = db.query(EmailSubscriber).all()
    return templates.TemplateResponse(
        request=request,
        name="subscribers.html",
        context={
            "series": None,
            "chapter": None,
            "subscribers_list": subscribers,
        },
    )


def get_subscriber(
    request: Request,
    db: Annotated[Session, Depends(database)],
    templates: Annotated[Jinja2Templates, Depends(templates)],
    subscriber_id: int,
):
    subscriber = (
        db.query(EmailSubscriber)
        .where(EmailSubscriber.id == subscriber_id)
        .one_or_none()
    )
    subscribed_series = (
        db.query(Series)
        .join(EmailSubscription)
        .where(EmailSubscription.subscriber_id == subscriber_id)
        .all()
    )
    unsubscribed_series = (
        db.query(Series)
        .join(EmailSubscription, isouter=True)
        .where(EmailSubscription.subscriber_id.is_(None))
        .all()
    )
    return templates.TemplateResponse(
        request=request,
        name="subscriber.html",
        context={
            "subscriber": subscriber,
            "subscribed_series": subscribed_series,
            "unsubscribed_series": unsubscribed_series,
        },
    )


async def update_subscriber(
    request: Request,
    db: Annotated[Session, Depends(database)],
    subscriber_id: int,
):
    form_data = await request.form()
    email = str(form_data.get("email"))

    series = [int(cast(str, series_id)) for series_id in form_data.getlist("series")]

    command = subscriber_actions.Set(
        subscriber=subscriber_id, email=email, series=series
    )

    try:
        subscriber_actions.set_subscriber(command, db)
    except cappa.Exit:
        pass

    return RedirectResponse(
        url=request.url_for(
            "get_subscriber",
            subscriber_id=subscriber_id,
        ),
        status_code=HTTP_302_FOUND,
    )


async def add_subscriber(
    request: Request,
    db: Annotated[Session, Depends(database)],
    console: Annotated[Console, Depends(console)],
    email: Annotated[str | None, Form(...)] = None,
):
    command = subscriber_actions.Add(email=email)
    subscriber_actions.add(command, db, console)

    return RedirectResponse(
        url=request.url_for("list_subscribers"),
        status_code=HTTP_302_FOUND,
    )
