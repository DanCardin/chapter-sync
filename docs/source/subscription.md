## Subscription

While sync/watch commands will collect the chapter information, they wont
automatically produce a local ebook file. However, if you "subscribe" to a
series, new chapters will be automatically sent to subscribers.

````{note}
A new subscriber to an existing series, or a new series with no historical
record of chapters having been sent will initially want to sent one email per
unset chapter (which may be all of them!)

As such, during initial setup, you may want to
```bash
❯ chapter-sync sync --no-send
❯ chapter-sync chapter set <series-id> --sent --all
```

This will set all existing chapters as having been sent to all subscribers.
````

Note, a subscriber individually as they're detected to supported "subscribers".

### Email

This is probably most obviously meaningful since you can email epubs to
`<yourname>@kindle.com` to get them automatically on your kindle.

As such, `chapter-sync` can be set up to `watch` for chapters in the background
and automatically email the resultant new chapters to a kindle! (This was the
original motivation for the tool in the first place!)

This feature requires 3 environment variables to be set: `SMTP_HOST`,
`SMPT_USERNAME`, and `SMTP_PASSWORD`.

```{note}
You can set up Gmail to send emails using `SMTP_HOST=smtp.google.com` and
`SMTP_USERNAME=<your-email>`.

Using your actual password may or may not work depending on your account.
However you can set up an
["app password"](https://support.google.com/mail/answer/185833?hl=en) to
bypass those restrictions.
```
