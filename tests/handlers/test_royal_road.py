from textwrap import dedent

import pytest
from pendulum import datetime
from requests import Session
from responses import RequestsMock

from chapter_sync.console import Console
from chapter_sync.handlers.royal_road import Settings, chapter_handler
from chapter_sync.schema import Series


@pytest.fixture
def requests():
    from requests import Session

    return Session()


@pytest.fixture
def console():
    return Console()


def test_collect_chapter(requests: Session, console: Console, responses: RequestsMock):
    responses.add(responses.GET, "https://royalroad.com/series/", body=toc_content)
    responses.add(
        responses.GET, "https://royalroad.com/series/chapter1", body=chapter1_content
    )
    responses.add(
        responses.GET, "https://royalroad.com/series/chapter2", body=chapter2_content
    )

    series = Series(
        id=1,
        name="series",
        type="royal_road",
        url="https://royalroad.com/series/",
        title="RoyalRoadSeries",
        author="RoyalRoadSeries",
    )
    settings = Settings()
    with console.status("") as status:
        chapter = list(chapter_handler(requests, series, settings, status))

    responses.add(responses.GET, "https://royalroad.com/series/", body=toc_content_2)
    responses.add(
        responses.GET,
        "https://royalroad.com/series/chapter2-new-url",
        body=chapter2_content,
    )

    series.chapters = chapter

    with console.status("") as status:
        chapter = list(chapter_handler(requests, series, settings, status))

    all_chapters = series.chapters + chapter

    assert len(all_chapters) == 3

    chapter1 = all_chapters[0]
    assert chapter1.series_id == series.id
    assert chapter1.number == 1
    assert chapter1.title == "Chapter 1 TOC Title"
    assert chapter1.content == dedent(
        """<div class="chapter-inner chapter-content">
            <h3><span style="font-weight: 600">Chapter 1 Title</span></h3>
            <p class="somerandomgeneratedstuff">First paragraph</p>
            <p class="somerandomgeneratedstuff">Second paragraph</p>
            <p class="somerandomgeneratedstuff">Third paragraph</p>
          </div>"""
    )
    assert chapter1.url == "https://royalroad.com/series/chapter1"
    assert chapter1.published_at == datetime(2020, 1, 1)

    chapter2 = all_chapters[1]
    assert chapter2.series_id == series.id
    assert chapter2.number == 2
    assert chapter2.title == "Chapter 2 TOC Title"
    assert chapter2.content == dedent(
        """<div class="chapter-inner chapter-content">
            <h3><span style="font-weight: 600">Chapter 2 Title</span></h3>
            <p class="somerandomgeneratedstuff">Paragraph A</p>
            <p class="somerandomgeneratedstuff">Paragraph B</p>
            <p class="somerandomgeneratedstuff">Paragraph C</p>
          </div>"""
    )
    assert chapter2.url == "https://royalroad.com/series/chapter2"
    assert chapter2.published_at == datetime(2020, 1, 1)

    chapter3 = all_chapters[2]
    assert chapter3.series_id == series.id
    assert chapter3.number == 3
    assert chapter3.title == "Chapter 2 TOC Title"
    assert chapter3.content == dedent(
        """<div class="chapter-inner chapter-content">
            <h3><span style="font-weight: 600">Chapter 2 Title</span></h3>
            <p class="somerandomgeneratedstuff">Paragraph A</p>
            <p class="somerandomgeneratedstuff">Paragraph B</p>
            <p class="somerandomgeneratedstuff">Paragraph C</p>
          </div>"""
    )
    assert chapter3.url == "https://royalroad.com/series/chapter2-new-url"
    assert chapter3.published_at == datetime(2020, 1, 1)


toc_content = """
<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="utf-8"/>
    <title>Series - Table of Contents</title>
  </head>

  <body>
    <div class="portlet light">
      <div class="portlet-body">
      <table class="table no-border" id="chapters" data-chapters="2">
        <thead>
        <tr>
          <th data-priority="1">
            Chapter Name
          </th>
          <th class="text-right min-tablet-p" data-priority="2">
            Release Date
          </th>
        </tr>
        </thead>
        <tbody>
          <tr style="cursor: pointer" data-url="/series/chapter1" data-volume-id="null" class="chapter-row">
            <td>
              <a href="/series/chapter1">
              Chapter 1 TOC Title
              </a>
            </td>
            <td data-content="0" class="text-right">
              <a href="/series/chapter1" data-content="0">
                <time unixtime="1577836800" title="Thursday, February 15th, 2024 15:22" datetime="2024-02-15T15:22:07.0000000&#x2B;00:00" format="agoshort">1 month </time> ago
              </a>
            </td>
          </tr>
          <tr style="cursor: pointer" data-url="/series/chapter2" data-volume-id="null" class="chapter-row">
            <td>
              <a href="/series/chapter2">
              Chapter 2 TOC Title
              </a>
            </td>
            <td data-content="0" class="text-right">
              <a href="/series/chapter2" data-content="0">
                <time unixtime="1577836800" title="Thursday, February 15th, 2024 15:22" datetime="2024-02-15T15:22:07.0000000&#x2B;00:00" format="agoshort">1 month </time> ago
              </a>
            </td>
          </tr>
        </tbody>
      </table>
  </body>
</html>
"""

toc_content_2 = """
<!DOCTYPE html>
<html lang="en">

  <head>
    <meta charset="utf-8"/>
    <title>Series - Table of Contents</title>
  </head>

  <body>
    <div class="portlet light">
      <div class="portlet-body">
      <table class="table no-border" id="chapters" data-chapters="2">
        <thead>
        <tr>
          <th data-priority="1">
            Chapter Name
          </th>
          <th class="text-right min-tablet-p" data-priority="2">
            Release Date
          </th>
        </tr>
        </thead>
        <tbody>
          <tr style="cursor: pointer" data-url="/series/chapter1" data-volume-id="null" class="chapter-row">
            <td>
              <a href="/series/chapter1">
              Chapter 1 TOC Title
              </a>
            </td>
            <td data-content="0" class="text-right">
              <a href="/series/chapter1" data-content="0">
                <time unixtime="1577836800" title="Thursday, February 15th, 2024 15:22" datetime="2024-02-15T15:22:07.0000000&#x2B;00:00" format="agoshort">1 month </time> ago
              </a>
            </td>
          </tr>
          <tr style="cursor: pointer" data-url="/series/chapter2-new-url" data-volume-id="null" class="chapter-row">
            <td>
              <a href="/series/chapter2-new-url">
              Chapter 2 TOC Title
              </a>
            </td>
            <td data-content="0" class="text-right">
              <a href="/series/chapter2-new-url" data-content="0">
                <time unixtime="1577836800" title="Thursday, February 15th, 2024 15:22" datetime="2024-02-15T15:22:07.0000000&#x2B;00:00" format="agoshort">1 month </time> ago
              </a>
            </td>
          </tr>
        </tbody>
      </table>
  </body>
</html>
"""

chapter1_content = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
  </head>

  <body>
    <div>
      <div class="portlet light chapter font-size-22 width-100 font-family-default paragraph-spacing-30 indent-default">
        <div class="portlet-body">
          <div class="chapter-inner chapter-content">
            <h3><span style="font-weight: 600">Chapter 1 Title</span></h3>
            <p class="somerandomgeneratedstuff">First paragraph</p>
            <p class="somerandomgeneratedstuff">Second paragraph</p>
            <p class="somerandomgeneratedstuff">Third paragraph</p>
          </div>
        </div>
      </div>
      <div class="portlet light">
        <div class="portlet-body profile">
          <div class="row">
            <div class="col-md-10">
              <div class="row">
                <div class="col-md-8 profile-info">
                  <ul class="list-inline">
                    <li>
                      <i class="fa fa-calendar" title="Published"></i> <time unixtime="1577836800" datetime="2024-02-15T18:42:18.0000000Z" format="dddd, MMMM dnn, yyyy HH:mm" >Thursday, February 15th, 2024 18:42</time>
                    </li>
                  <ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
"""

chapter2_content = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8"/>
  </head>

  <body>
    <div>
      <div class="portlet light chapter font-size-22 width-100 font-family-default paragraph-spacing-30 indent-default">
        <div class="portlet-body">
          <div class="chapter-inner chapter-content">
            <h3><span style="font-weight: 600">Chapter 2 Title</span></h3>
            <p class="somerandomgeneratedstuff">Paragraph A</p>
            <p class="somerandomgeneratedstuff">Paragraph B</p>
            <p class="somerandomgeneratedstuff">Paragraph C</p>
          </div>
        </div>
      </div>
      <div class="portlet light">
        <div class="portlet-body profile">
          <div class="row">
            <div class="col-md-10">
              <div class="row">
                <div class="col-md-8 profile-info">
                  <ul class="list-inline">
                    <li>
                      <i class="fa fa-calendar" title="Published"></i> <time unixtime="1577836800" datetime="2024-02-15T18:42:18.0000000Z" format="dddd, MMMM dnn, yyyy HH:mm" >Thursday, February 15th, 2024 18:42</time>
                    </li>
                  <ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
"""
