import os
import smtplib
from dataclasses import dataclass, field
from email.message import EmailMessage

from typing_extensions import Self

from chapter_sync.console import Console


@dataclass
class EmailClient:
    console: Console = field(default_factory=Console)

    host: str | None = None
    username: str | None = None
    password: str | None = None

    @classmethod
    def from_env(cls, console: Console, environ=os.environ) -> Self:
        host = environ.get("SMTP_HOST")
        username = environ.get("SMTP_USERNAME")
        password = environ.get("SMTP_PASSWORD")
        return cls(console, host, username, password)

    def send(
        self,
        *,
        subject: str,
        to: str,
        attachment: bytes,
        filename: str,
        body: str | None = None,
    ):
        if not (self.host and self.username and self.password):
            self.console.warn(
                "Not all of `SMTP_HOST`, `SMTP_USERNAME`, and `SMTP_PASSWORD` "
                "environment variables are set"
            )
            return

        msg = EmailMessage()

        msg["Subject"] = subject
        msg["From"] = self.username
        msg["To"] = to

        if body:
            msg.set_content(body)

        msg.add_attachment(
            attachment,
            maintype="application",
            subtype="epub+zip",
            filename=filename,
        )

        with smtplib.SMTP_SSL(self.host) as s:
            s.login(self.username, self.password)
            s.send_message(msg)
