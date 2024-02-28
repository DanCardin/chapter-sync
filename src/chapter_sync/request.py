import re
import time
import urllib.parse
from typing import cast

import pendulum
from bs4 import BeautifulSoup, Tag
from requests import Session

from chapter_sync.console import Status

RE_NAMESPACED_ELEMENT = re.compile(r"[a-z]+:[a-z]+")


def requests_session():
    return Session()


def get_soup(
    session: Session,
    url,
    *,
    status: Status,
    method="html5lib",
    retry=3,
    retry_delay=10,
    timeout=30,
):
    page = session.get(url, timeout=timeout)
    if not page:
        if (
            page.status_code == 403
            and page.headers.get("Server", False) == "cloudflare"
            and "captcha-bypass" in page.text
        ):
            raise RuntimeError("Couldn't due to Cloudflare protection", url)

        if retry and retry > 0:
            real_delay = retry_delay
            if "Retry-After" in page.headers:
                real_delay = int(page.headers["Retry-After"])

            status.update(
                f"Load failed: waiting {real_delay} to retry ({page.status_code}: {page.url})",
            )
            time.sleep(real_delay)

            return get_soup(
                session,
                url,
                status=status,
                method=method,
                retry=retry - 1,
                retry_delay=retry_delay,
                timeout=timeout,
            )
        raise RuntimeError("Couldn't fetch", url)

    return BeautifulSoup(page.text, method)


def join_path(*segments):
    return urllib.parse.urljoin(*segments)


def clean_namespaced_elements(soup: BeautifulSoup):
    for namespaced in soup.find_all(RE_NAMESPACED_ELEMENT):
        # Namespaced elements are going to cause validation errors
        namespaced.decompose()


def clean_emails(soup: BeautifulSoup):
    # Cloudflare is used on many sites, and mangles things that look like email addresses
    # e.g. Point_Me_@_The_Sky becomes
    # <a href="/cdn-cgi/l/email-protection" class="__cf_email__" data-cfemail="85d5eaecebf1dac8e0dac5">[email&#160;protected]</a>_The_Sky
    for a in soup.find_all(
        "a", class_="__cf_email__", href="/cdn-cgi/l/email-protection"
    ):
        # See: https://usamaejaz.com/cloudflare-email-decoding/
        enc = bytes.fromhex(a["data-cfemail"])
        email = bytes([c ^ enc[0] for c in enc[1:]]).decode("utf8")
        a.insert_before(email)
        a.decompose()


def strip_colors(soup: BeautifulSoup):
    for tag in soup.find_all(style=re.compile(r"(?:color|background)\s*:")):
        tag["style"] = re.sub(r"(?:color|background)\s*:[^;]+;?", "", tag["style"])


def published_at(soup: BeautifulSoup) -> pendulum.DateTime | None:
    dt_string = None

    published_time = soup.find("meta", {"property": "article:published_time"})
    if published_time:
        assert isinstance(published_time, Tag)
        dt_string = str(published_time["content"])

    if not dt_string:
        return None

    try:
        return cast(pendulum.DateTime, pendulum.parse(dt_string))
    except Exception:
        return None
