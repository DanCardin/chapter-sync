# Series/Chapter

## Series

The "series" is the fundamental unit of operation in `chapter-sync`. A series
tells the tool the root information from which to collect chapters. It also
encodes different metadata about the series in question, which will end up baked
into the files the tool outputs.

```
Usage: chapter-sync series {add,remove,subscribe,export,list,set} [-h]

  A collection of commands for managing series.

  Subcommands
    add           Add a new series to the database.
    remove        Remove an existing series from the database.
    subscribe     Add a subscriber to the given series.
    export        Export the series as a standalone ebook.
    list          List all series in the database.
    set           Change attributes about the chapter manually.
```

Given an existing series, a user can [subscribe](./subscription.md) to updates
to the series.

## Chapter

Chapters are associated with a series, and represent each divisible unit of the
series. For books, this will generally actually correspond to a chapter, but may
not, depending on the content being pointed at.

When `sync` or `watch` detects a new chapter, it records the content, converts
the result into a standalone ebook, and then sends the resultant file to any
subscribers.
