# Chapter-sync

[![Actions Status](https://github.com/DanCardin/chapter-sync/actions/workflows/test.yml/badge.svg)](https://github.com/dancardin/chapter-sync/actions)
[![codecov](https://codecov.io/gh/DanCardin/chapter-sync/graph/badge.svg?token=e8T6QN2tTz)](https://codecov.io/gh/DanCardin/chapter-sync)
[![Documentation Status](https://readthedocs.org/projects/chapter-sync/badge/?version=latest)](https://chapter-sync.readthedocs.io/en/latest/?badge=latest)
[![Docker](https://img.shields.io/docker/v/dancardin/chapter-sync?label=Docker&style=flat)](https://hub.docker.com/r/dancardin/chapter-sync)

- [Full documentation here](https://chapter-sync.readthedocs.io/en/latest/).
- [Installation/Usage](https://chapter-sync.readthedocs.io/en/latest/installation.html).

A tool for recording serialized web content, in partial web-serial type novels,
or other serialized content for which you want to be sent updates as they're
published.

The other tools in the space (at least that I'm aware of: Leech, FanFicFare) are
mostly designed around manual one-off usage of the tool to capture the current
state of a story/series and turn it into an ebook.

`chapter-sync`, by contrast, records everything it captures to a sqlite database
and will only collect new/missing chapters. It also bakes in (through supported
subscription methods) the ability to send new chapters to "subscribers" who have
not yet received it.

## Quickstart

```bash
❯ chapter-sync series add some-book 'https://some-book.com/table-of-contents/' --title 'Some Book' --settings '{"content_selector": "#main .entry-content", "chapter_selector": "#main .entry-content > ul > li > a"}'
Added series "some-book" at "https://some-book.com/table-of-contents/"

❯ chapter-sync series list
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID ┃ Name                       ┃ URL                                  ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ some-book                  │ https://some-book.com/table-of-cont… │
└────┴────────────────────────────┴──────────────────────────────────────┘

❯ chapter-sync sync
...
Done

❯ chapter-sync chapter list 1
                               Some Book
┏━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Title      ┃ Chapter ┃ Size (Kb) ┃ Sent       ┃ Published  ┃ Created    ┃
┡━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ Chapter 1  │ 1       │ 37.3      │ 2024-03-02 │ 2023-07-28 │ 2024-03-02 │
│ Chapter 2  │ 2       │ 37.1      │ 2024-03-02 │ 2023-08-04 │ 2024-03-02 │
│ Chapter 3  │ 3       │ 36.9      │ 2024-03-02 │ 2023-08-11 │ 2024-03-02 │
│ Chapter 4  │ 4       │ 36.9      │ 2024-03-02 │ 2023-08-18 │ 2024-03-02 │
└────────────┴─────────┴───────────┴────────────┴────────────┴────────────┘

❯ chapter-sync chapter export 1 4
❯ ls
Some Book: Chapter 4.epub

❯ chapter-sync series export 1
❯ ls
Some Book.epub
```

## Web

The tool also ships with a web service which can be used to view and manage
subscriptions.

![Web Example](docs/web.png)

## Inspiration

**this** tool started off as an attempt at a refactor/PR to
[Leech](https://github.com/kemayo/leech) to enable it to more granularly record
updates to books as they changed.

However, `chapter-sync` is designed from the ground up to be able to
individually record/send chapters as they are published, which ultimately means
the to tools ultimately end up being almost entirely different.

I **had** been using InstaPaper to send updates of series to my kindle, until
they made that a paid feature. Additionally the drawback there, was that the
file they'd send would contain all chapters in the whole series, in reverse.
