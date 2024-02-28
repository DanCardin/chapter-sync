from __future__ import annotations

import datetime
import html
import importlib.resources
import os.path
import unicodedata
import uuid
import zipfile
from dataclasses import dataclass, field
from io import BytesIO
from typing import Any, BinaryIO

import xmltodict

from chapter_sync.cover import Cover
from chapter_sync.schema import Chapter, Series

templates = importlib.resources.files("chapter_sync.templates")


default_chapter_template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="../Styles/base.css" />
</head>
<body>
<h1>{title}</h1>
{text}
</body>
</html>
"""

default_footnotes_template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="Styles/base.css" />
</head>
<body>
<h1>{title}</h1>
{text}
</body>
</html>
"""

default_frontmatter_template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Front Matter</title>
    <link rel="stylesheet" type="text/css" href="Styles/base.css" />
</head>
<body>
<div class="cover title">
    <h1>{title}<br />By {author}</h1>
    <dl>
        <dt>Source</dt>
        <dd>{unique_id}</dd>
        <dt>Started</dt>
        <dd>{started}</dd>
        <dt>Updated</dt>
        <dd>{updated}</dd>
        <dt>Downloaded on</dt>
        <dd>{now:%Y-%m-%d}</dd>
    </dl>
</div>
</body>
</html>
"""

default_cover_template = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>Cover</title>
    <link rel="stylesheet" type="text/css" href="Styles/base.css" />
</head>
<body>
<div class="cover">
<svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
    width="100%" height="100%" viewBox="0 0 573 800" preserveAspectRatio="xMidYMid meet">
<image width="600" height="800" xlink:href="images/cover.png" />
</svg>
</div>
</body>
</html>
"""


@dataclass
class EpubFile:
    id: str
    path: str
    contents: str | bytes
    title: str | None = None
    filetype: str = "application/xhtml+xml"


@dataclass
class Epub:
    """Produces an `epub` from the component parts of a "book".

    An Epub file is a zip file with a specific structure.
    """

    title: str
    author: str
    cover: EpubFile
    cover_image: EpubFile
    frontmatter: EpubFile
    chapters: list[EpubFile]
    footnotes: EpubFile
    style: EpubFile

    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    frontmatter_template: str = default_frontmatter_template
    cover_template: str = default_cover_template
    chapter_template: str = default_chapter_template
    footnotes_template: str = default_footnotes_template

    mimetype_filename = "mimetype"
    container_xml_filename = "META-INF/container.xml"
    toc_ncx_filename = "OEBPS/toc.ncx"
    content_opf_filename = "OEBPS/Content.opf"

    @classmethod
    def from_series(
        cls,
        series: Series,
        *chapters: Chapter,
        cover_options: dict[str, Any] | None = None,
    ) -> Epub:
        cover = Cover.from_options(cover_options)
        return cls(
            title=series.title,
            author=series.author or "Unkown",
            id=str(series.id),
            cover=EpubFile(
                id="cover_html",
                title="Cover",
                path="cover.html",
                contents=cls.cover_template,
            ),
            cover_image=EpubFile(
                id="cover_image",
                path="images/cover.png",
                contents=cover.generate_image(series),
                filetype="image/png",
            ),
            footnotes=EpubFile(
                id="footnotes",
                title="Footnotes",
                path="footnotes.html",
                contents=cls.footnotes_template.format(
                    title="Footnotes",
                    text="\n\n".join(series.footnotes),
                ),
            ),
            frontmatter=EpubFile(
                id="frontmatter",
                title="Front Matter",
                path="frontmatter.html",
                contents=cls.frontmatter_template.format(
                    now=datetime.datetime.now(),
                    unique_id=series.id,
                    started=series.created_at,
                    updated=series.last_built_at,
                    title=series.title,
                    author=series.author,
                ),
            ),
            style=EpubFile(
                id="style",
                path="Styles/base.css",
                contents=templates.joinpath("base.css").read_text(),
                filetype="text/css",
            ),
            chapters=[
                EpubFile(
                    id=f"chapter_{chapter.number}",
                    title=chapter.title,
                    path=f"chapter/{chapter.number}.html",
                    contents=cls.chapter_template.format(
                        title=normalize(chapter.title, escape_html=True),
                        text=normalize(chapter.content),
                    ),
                )
                for chapter in chapters
            ],
        )

    def write_buffer(self):
        buffer = BytesIO()
        self.write(buffer)
        buffer.seek(0)
        return buffer

    def write(
        self,
        output_file: str | BinaryIO | None = None,
        *,
        load_from: str | None = None,
        output_dir: str | None = None,
        compress: bool = True,
    ):
        if output_file is None:
            output_file = self.title + ".epub"

        if isinstance(output_file, str) and output_dir:
            output_file = os.path.join(output_dir, output_file)

        from_zf = None
        if load_from:
            from_zf = zipfile.ZipFile(
                load_from,
                "r",
                compression=compress and zipfile.ZIP_DEFLATED or zipfile.ZIP_STORED,
            )

        to_zf = zipfile.ZipFile(
            output_file,
            "w",
            compression=compress and zipfile.ZIP_DEFLATED or zipfile.ZIP_STORED,
        )

        self.write_mimetype(to_zf, from_zf=from_zf)
        self.write_container(to_zf, from_zf=from_zf)
        self.write_toc_ncx(to_zf, self.id, self.title, self.author, from_zf=from_zf)
        self.write_content_opf(to_zf, self.id, self.title, self.author, from_zf=from_zf)

        content_files = [
            self.cover,
            self.cover_image,
            self.frontmatter,
            self.footnotes,
            self.style,
            *self.chapters,
        ]
        for file in content_files:
            to_zf.writestr("OEBPS/" + file.path, file.contents)

        self.replicate_other_files(to_zf, from_zf)

        return to_zf.filename

    def write_mimetype(
        self, zf: zipfile.ZipFile, *, from_zf: zipfile.ZipFile | None = None
    ):
        """Write the mimetype file.

        The first file must be named "mimetype", and shouldn't be compressed.
        """
        write_content(
            zf,
            self.mimetype_filename,
            content="application/epub+zip",
            compress_type=zipfile.ZIP_STORED,
            from_zf=from_zf,
        )

    def write_container(
        self, zf: zipfile.ZipFile, *, from_zf: zipfile.ZipFile | None = None
    ):
        """We need an index file, that lists all other HTML files.

        This index file itself is referenced in the META_INF/container.xml file.
        """
        container_xml = {
            "container": {
                "@version": "1.0",
                "@xmlns": "urn:oasis:names:tc:opendocument:xmlns:container",
                "rootfiles": {
                    "rootfile": {
                        "@full-path": self.content_opf_filename,
                        "@media-type": "application/oebps-package+xml",
                    }
                },
            }
        }
        write_content(
            zf,
            self.container_xml_filename,
            content=container_xml,
            compress_type=zipfile.ZIP_STORED,
            from_zf=from_zf,
        )

    def write_toc_ncx(
        self,
        zf: zipfile.ZipFile,
        id: str,
        title: str,
        author: str,
        *,
        from_zf: zipfile.ZipFile | None = None,
    ):
        toc_ncx = {
            "ncx": {
                "@xmlns": "http://www.daisy.org/z3986/2005/ncx/",
                "@version": "2005-1",
                "@xml:lang": "en-US",
                "head": {
                    "meta": {
                        "@name": "dtb:uid",
                        "@content": id,
                    },
                },
                "docTitle": {"text": title},
                "docAuthor": {"text": author},
                "navMap": {
                    "navPoint": [
                        {
                            "@class": "h1",
                            "@id": file.id,
                            "navLabel": {"text": file.title},
                            "content": {"@src": file.path},
                        }
                        for file in [
                            self.cover,
                            self.frontmatter,
                            *self.chapters,
                            self.footnotes,
                        ]
                    ]
                },
            }
        }
        write_content(
            zf,
            self.toc_ncx_filename,
            content=toc_ncx,
            from_zf=from_zf,
        )

    def write_content_opf(
        self,
        zf: zipfile.ZipFile,
        id: str,
        title: str,
        author: str,
        from_zf: zipfile.ZipFile | None = None,
    ):
        chapters = [
            {
                "@id": file.id,
                "@href": file.path,
                "@media-type": "application/xhtml+xml",
            }
            for file in self.chapters
        ]
        spine_items = [{"@idref": file.id} for file in self.chapters]

        content_opf = {
            "package": {
                "@version": "2.0",
                "@xmlns": "http://www.idpf.org/2007/opf",
                "@unique-identifier": "book_identifier",
                "metadata": {
                    "@xmlns:dc": "http://purl.org/dc/elements/1.1/",
                    "@xmlns:opf": "http://www.idpf.org/2007/opf",
                    "dc:identifier": {
                        "@id": "book_identifier",
                        "#text": id,
                    },
                    "dc:title": title,
                    "dc:language": "en",
                    "dc:creator": {"@opf:role": "aut", "#text": author},
                    "meta": [
                        {"@name": "generator", "@content": "chapter-sync"},
                        {"@name": "cover", "@content": "cover_image"},
                    ],
                },
                "manifest": {
                    "item": [
                        {
                            "@id": "cover_html",
                            "@href": "cover.html",
                            "@media-type": "application/xhtml+xml",
                        },
                        {
                            "@id": "cover_image",
                            "@href": "images/cover.png",
                            "@media-type": "image/png",
                        },
                        *chapters,
                        {
                            "@id": "footnotes",
                            "@href": "footnotes.html",
                            "@media-type": "application/xhtml+xml",
                        },
                        {
                            "@id": "frontmatter",
                            "@href": "frontmatter.html",
                            "@media-type": "application/xhtml+xml",
                        },
                        {
                            "@id": "style",
                            "@href": "Styles/base.css",
                            "@media-type": "text/css",
                        },
                        {
                            "@id": "ncx",
                            "@href": "toc.ncx",
                            "@media-type": "application/x-dtbncx+xml",
                        },
                    ]
                },
                "spine": {
                    "@toc": "ncx",
                    "itemref": [
                        {"@idref": "cover_html", "@linear": "no"},
                        {"@idref": "frontmatter", "@linear": "no"},
                        *spine_items,
                        {"@idref": "footnotes", "@linear": "no"},
                    ],
                },
                "guide": {
                    "reference": {
                        "@type": "cover",
                        "@title": "Cover",
                        "@href": "cover.html",
                    }
                },
            }
        }
        write_content(
            zf,
            self.content_opf_filename,
            content=content_opf,
            from_zf=from_zf,
        )

    def replicate_other_files(
        self, zf: zipfile.ZipFile, from_zf: zipfile.ZipFile | None = None
    ):
        """Add files from the `from_zf` to the destination oneself.

        Updating an existing zipfile in-place isn't supported. So we need to copy
        over any other files.
        """
        if from_zf is None:
            return

        files = set(zf.namelist())
        from_files = set(from_zf.namelist())
        missing_files = from_files - files
        for missing_file in missing_files:
            zf.writestr(missing_file, from_zf.read(missing_file))


def write_content(
    zf: zipfile.ZipFile,
    filename: str,
    *,
    content: str | dict,
    compress_type=None,
    from_zf: zipfile.ZipFile | None = None,
    full_document: bool = True,
):
    # existing_content_str = None
    # if from_zf:
    #     existing_content_str = from_zf.read(filename)

    if isinstance(content, str):
        zf.writestr(filename, content, compress_type=compress_type)

    elif isinstance(content, dict):
        # existing_content = xmltodict.parse(existing_content_str)

        content_str = xmltodict.unparse(
            content, pretty=True, indent="  ", full_document=full_document
        )

        zf.writestr(filename, content_str, compress_type=compress_type)


def normalize(value: str, escape_html: bool = False):
    result = unicodedata.normalize("NFKC", value)
    if escape_html:
        result = html.escape(result)
    return result
