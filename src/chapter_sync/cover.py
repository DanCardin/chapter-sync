from __future__ import annotations

import contextlib
import textwrap
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

import requests
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from chapter_sync.schema import Series


@dataclass
class CoverOptions:
    font_name: str = "Helvetica"
    font_size: int = 40
    width: int = 600
    height: int = 800
    wrap_at: int = 30
    bg_color: tuple = (120, 20, 20)
    text_color: tuple = (255, 255, 255)


def generate_cover_image(series: Series, options: CoverOptions = CoverOptions()):
    url = series.cover_url

    if url:
        with contextlib.suppress(Exception):
            return make_cover_from_url(url)

    return make_cover_image(series.title, series.author, options=options)


def make_cover_from_url(url: str) -> bytes:
    img = requests.Session().get(url)
    cover = BytesIO(img.content)

    imgformat = Image.open(cover).format
    cover.seek(0)

    if imgformat != "PNG":
        png_cover = BytesIO()
        Image.open(cover).save(png_cover, format="PNG")
        png_cover.name = "cover.png"
        png_cover.seek(0)
        cover = png_cover

    return cover.read()


def make_cover_image(
    title: str, author: str | None = None, options: CoverOptions = CoverOptions()
):
    title_font = select_font(options.font_name, size=options.font_size)
    author_font = select_font(options.font_name, size=options.font_size - 4)

    img = Image.new("RGBA", (options.width, options.height), options.bg_color)
    draw = ImageDraw.Draw(img)

    title = textwrap.fill(title, options.wrap_at)
    author = textwrap.fill(author or "", options.wrap_at)

    title_len = title_font.getlength(title)
    title_position = (options.width / 2 - title_len / 2, 100)
    draw.text(title_position, title, options.text_color, font=title_font)

    author_len = author_font.getlength(author)
    author_position = (options.width / 2 - author_len / 2, 200)
    draw.text(author_position, author, options.text_color, font=author_font)

    output = BytesIO()
    img.save(output, "PNG")
    output.name = "cover.png"

    output.seek(0)
    return output.read()


def select_font(preferred, *, size: int = 10):
    for font in (preferred, "Helvetica", "FreeSans", "Arial"):
        with contextlib.suppress(OSError):
            return ImageFont.truetype(font=font, size=size)

    return ImageFont.load_default(size=size)
