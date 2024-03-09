from dataclasses import dataclass, field

from chapter_sync.email import EmailClient


@dataclass
class StubEmailClient(EmailClient):
    sent_emails: list = field(default_factory=list)

    def send(
        self,
        *,
        subject: str,
        to: str,
        attachment: bytes,
        filename: str,
        body: str | None = None,
    ):
        self.sent_emails.append(
            {
                "subject": subject,
                "to": to,
                "attachment": attachment,
                "filename": filename,
                "body": body,
            }
        )
