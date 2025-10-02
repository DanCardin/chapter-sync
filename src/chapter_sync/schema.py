from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pendulum import now
from sqlalchemy import (
    JSON,
    ColumnElement,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
    type_coerce,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.orm.collections import attribute_keyed_dict

from chapter_sync.handlers.base import HandlerTypes

convention = {
    "ix": "ix_%(column_0_N_label)s",
    "uq": "%(table_name)s_%(column_0_N_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_ckey",
    "fk": "%(table_name)s_%(column_0_N_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}

metadata = MetaData(naming_convention=convention)


class Base(DeclarativeBase):
    metadata = metadata


def utcnow() -> datetime:
    return now("UTC")


class Series(Base):
    __tablename__ = "series"

    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[HandlerTypes] = mapped_column(String, nullable=False)

    id: Mapped[int | None] = mapped_column(
        Integer, primary_key=True, default=None, nullable=False
    )
    title: Mapped[str] = mapped_column(String, nullable=False, default=None)
    author: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    cover_url: Mapped[str | None] = mapped_column(Text, nullable=True, default=None)

    settings: Mapped[dict] = mapped_column(
        JSON(none_as_null=True), nullable=True, default=None
    )

    last_built_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    ebook: Mapped[bytes | None] = mapped_column(LargeBinary, default=None)

    chapters: Mapped[list[Chapter]] = relationship(
        "Chapter",
        back_populates="series",
        order_by="Chapter.created_at",
    )
    email_subscribers: Mapped[list[EmailSubscriber]] = relationship(
        "EmailSubscriber",
        secondary="email_subscription",
        viewonly=True,
    )

    footnotes: ClassVar[list] = []

    def filename(self) -> str:
        return f"{self.title}.epub"

    def get_chapters_ordered(self) -> list[Chapter]:
        """Get chapters in correct order by following the chapter chain."""
        if not self.chapters:
            return []
        
        # Build URL to chapter mapping
        url_to_chapter = {c.url: c for c in self.chapters}
        
        # Find the first chapter (one with no previous chapter)
        first_chapter = None
        for chapter in self.chapters:
            if not chapter.previous_chapter_url:
                first_chapter = chapter
                break
        
        if not first_chapter:
            # Fallback to creation order if no clear chain
            return sorted(self.chapters, key=lambda c: c.created_at)
        
        # Follow the chain
        ordered = []
        current = first_chapter
        visited = set()
        
        while current and current.url not in visited:
            visited.add(current.url)
            ordered.append(current)
            
            # Find next chapter
            if current.next_chapter_url and current.next_chapter_url in url_to_chapter:
                current = url_to_chapter[current.next_chapter_url]
            else:
                break
                
        return ordered


class Chapter(Base):
    __tablename__ = "chapter"
    __table_args__ = (UniqueConstraint("series_id", "url"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("series.id"), nullable=False
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)

    previous_chapter_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_chapter_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    ebook: Mapped[bytes | None] = mapped_column(LargeBinary, default=None)

    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )

    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    @hybrid_property
    def size_kb(self) -> float:
        if self.ebook is None:
            return 0

        return len(self.ebook) / 1024

    @size_kb.inplace.expression
    @classmethod
    def _size_kb_expression(cls) -> ColumnElement[float]:
        return type_coerce(func.length(func.coalesce(cls.ebook, 0)) / 1024, Float)

    def filename(self) -> str:
        return f"{self.series.title}: {self.title}.epub"

    series: Mapped[Series] = relationship(
        "Series",
        back_populates="chapters",
        uselist=False,
    )


class EmailSubscriber(Base):
    __tablename__ = "email_subscriber"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )

    email_subscriptions: Mapped[list[EmailSubscription]] = relationship(
        overlaps="email_subcribers"
    )
    subscribed_series_by_id: Mapped[dict[int, Series]] = relationship(
        secondary="email_subscription",
        collection_class=attribute_keyed_dict("id"),
        overlaps="email_subscriptions",
    )


class EmailSubscription(Base):
    __tablename__ = "email_subscription"
    __table_args__ = (UniqueConstraint("series_id", "subscriber_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    series_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("series.id"), nullable=False
    )
    subscriber_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("email_subscriber.id"), nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
