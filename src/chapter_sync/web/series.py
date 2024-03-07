from typing import Annotated

from fastapi import Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from chapter_sync.schema import Chapter, Series
from chapter_sync.web.dependencies import database, templates


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
    series = db.query(Series).where(Series.id == series_id).one_or_none()
    chapters = (
        db.query(Chapter)
        .where(Chapter.series_id == series_id)
        .order_by(Chapter.number)
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
