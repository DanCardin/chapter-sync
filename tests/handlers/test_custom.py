from textwrap import dedent

import pytest
from pendulum import datetime
from requests import Session
from responses import RequestsMock

from chapter_sync.console import Console
from chapter_sync.handlers.custom import Settings, chapter_handler
from chapter_sync.schema import Series


@pytest.fixture
def requests():
    from requests import Session

    return Session()


@pytest.fixture
def console():
    return Console()


def test_collect_chapter(requests: Session, console: Console, responses: RequestsMock):
    responses.add(responses.GET, "http://basic.com/", body=chapter1_content)
    responses.add(responses.GET, "http://basic.com/chapter2", body=chapter2_content)

    series = Series(
        id=1,
        name="series",
        type="custom",
        url="http://basic.com/",
        title="Basic",
        author="Basic",
    )
    settings = Settings(
        content_selector="#main",
        content_title_selector="h1.title",
        content_text_selector=".entry-content",
        filter_selector=".skipme",
        next_selector='a[rel="next"]:not([href*="prologue"])',
    )
    chapter = list(chapter_handler(requests, series, settings, console))

    assert len(chapter) == 2

    chapter1 = chapter[0]
    assert chapter1.series_id == series.id
    assert chapter1.number == 1
    assert chapter1.title == "Chapter 1"
    assert chapter1.content == dedent(
        """\
                  <div class="entry-content">
                   <p>
                    <span>
                     Example
                    </span>
                    <br/>
                   </p>
                   <p>
                   </p>
                  </div>
                  """
    )
    assert chapter1.url == "http://basic.com/"
    assert chapter1.published_at == datetime(2020, 1, 1)
    assert chapter1.created_at == datetime(2020, 1, 1)

    chapter2 = chapter[1]
    assert chapter2.series_id == series.id
    assert chapter2.number == 2
    assert chapter2.title == "Chapter 2"
    assert chapter2.content == dedent(
        """\
                    <div class="entry-content">
                     <p>
                      <span>
                       Example 2
                      </span>
                     </p>
                     <p>
                     </p>
                    </div>
                    """
    )
    assert chapter2.url == "http://basic.com/chapter2"
    assert chapter2.published_at == datetime(2020, 1, 1)
    assert chapter2.created_at == datetime(2020, 1, 1)


chapter1_content = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta property="og:type" content="article" />
    <meta property="og:title" content="Chapter 1" />
    <meta property="article:published_time" content="2020-01-01T00:00:00+00:00" />
    <meta property="article:modified_time" content="2020-01-02T00:00:00+00:00" />
    <meta property="og:site_name" content="Example" />
  </head>

  <body>
    <div class="site-content">
      <div id="primary" class="content-area">
        <main id="main" class="site-main" role="main">
          <article class="content">
            <header class="entry-header">
              <h1 class="title">Chapter 1</h1>
            </header>

            <div class="entry-content">
              <p>
                <span>Example</span><br />
                <div class="skipme">
                  <span>I get skipped</span>
                </div>
              </p>
            </div>
            <span>Some content afterwards</span>
          </article>
          <nav class="navigation post-navigation" role="navigation">
            <div class="nav-links">
              <a href="http://basic.com/chapter2" rel="next">Chapter 2</a>
            </div>
          </nav>
        </main>
      </div>
    </div>
  </body>
</html>
"""

chapter2_content = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta property="og:type" content="article" />
    <meta property="og:title" content="Chapter 2" />
    <meta property="article:published_time" content="2020-01-01T00:00:00+00:00" />
    <meta property="article:modified_time" content="2020-01-02T00:00:00+00:00" />
  </head>

  <body>
    <article id="main">
      <div class="content">
        <h1 class="title">Chapter 2</h1>
        <div class="entry-content">
          <p>
            <span>Example 2</span>
            <div class="skipme">
              <span>I get skipped</span>
            </div>
          </p>
        </div>
      </div>
    </article>
  </body>
</html>
"""
