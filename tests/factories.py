from datetime import datetime
from typing import Literal

from sqlalchemy_model_factory import declarative

from chapter_sync.schema import Chapter, EmailSubscriber, EmailSubscription, Series


@declarative
class ModelFactory:
    def series(
        self,
        id: int | None = None,
        name: str = "foo",
        url: str = "http://example.com",
        type: Literal["custom"] = "custom",
        title: str | None = None,
        settings: dict | None = None,
    ):
        return Series(
            id=id,
            name=name,
            url=url,
            type=type,
            title=title or name,
            settings=settings,
        )

    def chapter(
        self,
        series: Series,
        *,
        id: int | None = None,
        number: int = 1,
        title: str = "title",
        url: str = "http://example.com",
        ebook: bytes = b"foo",
        content: str = "foo",
        sent_at: datetime | None = datetime(2020, 1, 1),
        published_at: datetime = datetime(2020, 1, 1),
        created_at: datetime = datetime(2020, 1, 1),
    ):
        return Chapter(
            series=series,
            id=id,
            number=number,
            title=title,
            url=url,
            ebook=ebook,
            content=content,
            sent_at=sent_at,
            published_at=published_at,
            created_at=created_at,
        )

    def email_subscriber(
        self,
        *,
        id: int | None = None,
        email: str = "foo@foo.com",
    ):
        return EmailSubscriber(id=id, email=email)

    def email_subscription(self, series: Series, subscriber: EmailSubscriber):
        return EmailSubscription(series_id=series.id, subscriber_id=subscriber.id)
