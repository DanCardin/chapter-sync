from __future__ import annotations

import logging
import textwrap
from dataclasses import asdict, dataclass, fields
from io import BytesIO
from typing import TYPE_CHECKING, Any

import requests
from PIL import Image, ImageDraw, ImageFont

if TYPE_CHECKING:
    from chapter_sync.schema import Series


@dataclass
class Cover:
    fontname: str | None = None
    fontsize: int | None = None
    width: int | None = None
    height: int | None = None
    wrapat: int | None = None
    bgcolor: tuple | None = None
    textcolor: tuple | None = None
    cover_url: str | None = None

    @classmethod
    def from_options(cls, options: dict[str, Any] | None = None):
        if options is None:
            return cls()

        return cls(
            **{
                field.name: options[field.name]
                for field in fields(cls)
                if field.name in options
            }
        )

    @classmethod
    def default(cls):
        return cls()

    def generate_image(self, series: Series):
        if self.cover_url:
            return make_cover_from_url(self.cover_url, series.title, series.author)

        if series.cover_url:
            return make_cover_from_url(series.cover_url, series.title, series.author)

        data = {k: v for k, v in asdict(self).items() if v is not None}
        return make_cover_image(series.title, series.author, **data)


logger = logging.getLogger(__name__)


def make_cover_image(
    title,
    author,
    width=600,
    height=800,
    fontname="Helvetica",
    fontsize=40,
    bgcolor=(120, 20, 20),
    textcolor=(255, 255, 255),
    wrap_at=30,
):
    img = Image.new("RGBA", (width, height), bgcolor)
    draw = ImageDraw.Draw(img)

    title = textwrap.fill(title, wrap_at)
    author = textwrap.fill(author or "", wrap_at)

    font = _safe_font(fontname, size=fontsize)
    title_size = draw.textsize(title, font=font)
    draw_text_outlined(
        draw, ((width - title_size[0]) / 2, 100), title, textcolor, font=font
    )
    # draw.text(((width - title_size[0]) / 2, 100), title, textcolor, font=font)

    font = _safe_font(fontname, size=fontsize - 2)
    author_size = draw.textsize(author, font=font)
    draw_text_outlined(
        draw,
        ((width - author_size[0]) / 2, 100 + title_size[1] + 70),
        author,
        textcolor,
        font=font,
    )

    output = BytesIO()
    img.save(output, "PNG")
    output.name = "cover.png"
    # writing left the cursor at the end of the file, so reset it
    output.seek(0)
    return output.read()


def make_cover_from_url(url, title, author):
    try:
        logger.info("Downloading cover from " + url)
        img = requests.Session().get(url)
        cover = BytesIO(img.content)

        imgformat = Image.open(cover).format
        # The `Image.open` read a few bytes from the stream to work out the
        # format, so reset it:
        cover.seek(0)

        if imgformat != "PNG":
            cover = _convert_to_png(cover)
    except Exception as e:
        logger.info("Encountered an error downloading cover: " + str(e))
        cover = make_cover_image(title, author)

    return cover.read()


def _convert_to_png(image_bytestream):
    png_image = BytesIO()
    Image.open(image_bytestream).save(png_image, format="PNG")
    png_image.name = "cover.png"
    png_image.seek(0)

    return png_image


def _safe_font(preferred, *args, **kwargs):
    for font in (preferred, "Helvetica", "FreeSans", "Arial"):
        try:
            return ImageFont.truetype(*args, font=font, **kwargs)
        except OSError:
            pass

    # This is pretty terrible, but it'll work regardless of what fonts the
    # system has. Worst issue: can't set the size.
    return ImageFont.load_default()


def draw_text_outlined(draw, xy, text, fill=None, font=None, anchor=None):
    x, y = xy

    # Outline
    draw.text((x - 1, y), text=text, fill=(0, 0, 0), font=font, anchor=anchor)
    draw.text((x + 1, y), text=text, fill=(0, 0, 0), font=font, anchor=anchor)
    draw.text((x, y - 1), text=text, fill=(0, 0, 0), font=font, anchor=anchor)
    draw.text((x, y + 1), text=text, fill=(0, 0, 0), font=font, anchor=anchor)

    # Fill
    draw.text(xy, text=text, fill=fill, font=font, anchor=anchor)
