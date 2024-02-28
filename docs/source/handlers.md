# Handlers

Every [series](.series.md) has a "type" which corresponds to the set of
supported site "handler"s. A handler corresponds to the set of sites it would
know how to ingest, for example a theoretical 'royal-road' handler.

Supported handlers:

- [custom](#Custom)

```{note}
I am personally most likely to funnel effort into sites on which content I
personally read exists, and/or sites I will be able to access/test support for
directly, although would be happy to support any reasonable set of site specific
handlers.
```

If not otherwise specified through the `series add --type=<handler>` flag, it
will attempt to infer the handler from the website's hostname, and otherwise
fall back to "custom".

## Custom

A series which doesn't exist on a generalizable site (such as RoyalRoad) is
considered "custom". In such cases, CSS selectors are used to tell
`chapter-sync` what content on the page ought to be collected.

Such selectors are not bundled into the tool. Instead
[see the wiki](https://github.com/DanCardin/chapter-sync/wiki/%22Custom%22-Settings),
for a list of known-good settings for series. (And feel free to submit new
ones!)

## royal-road

TBD
