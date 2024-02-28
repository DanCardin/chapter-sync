# Sync/watch

## Watch

The `watch` command simply executes the `sync` command periodically. This is
most useful when run on a machine that's always on and can passively detect new
chapters quickly after they're published.

## Sync

When `sync` or `watch` detects a new chapter, it records the content, converts
the result into a standalone ebook, and then sends the resultant file to any
subscribers.
