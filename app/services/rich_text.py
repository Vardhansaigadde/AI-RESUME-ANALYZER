"""Links and skill groups inside resume text.

Users can turn any text into a link with Markdown-style ``[text](url)``, give an
entry a link (code, demo, certificate), and group skills by starting an item
with a label (``Languages: Python`` then ``Java`` ...). The browser preview
(frontend/src/lib/richText.js) follows the same rules.
"""

from __future__ import annotations

import re

INLINE_LINK_RE = re.compile(r"\[([^\]\n]{1,200})\]\(([^)\s]{1,500})\)")
SKILL_LABEL_RE = re.compile(r"^([^:,]{1,40}):\s*(.*)$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_SCHEME_RE = re.compile(r"^[a-z][a-z0-9+.-]*:", re.IGNORECASE)


def safe_url(value: str) -> str | None:
    """A clickable URL for a link the user typed, or None if it should stay plain text.

    Bare domains get https://, e-mail addresses become mailto:. Any other
    scheme (javascript:, data:, file: ...) is refused.
    """
    url = (value or "").strip()
    if not url or any(c.isspace() for c in url):
        return None
    if EMAIL_RE.match(url):
        return f"mailto:{url}"
    lower = url.lower()
    if lower.startswith(("http://", "https://", "mailto:", "tel:")):
        return url
    if _SCHEME_RE.match(url) and not re.match(r"^[^:/]+:\d", url):
        return None
    if "." in url.split("/")[0]:
        return f"https://{url}"
    return None


def short_url(value: str) -> str:
    """A URL as it reads best on a resume: no scheme, no www, no trailing slash."""
    return re.sub(r"^(?:https?://)?(?:www\.)?", "", (value or "").strip(), flags=re.IGNORECASE).rstrip("/")


def link_label(value: str) -> str:
    """How an entry's link reads next to its title (same rules as linkLabel in lib/richText.js)."""
    short = short_url(value)
    if len(short) <= 32:
        return short
    host = short.split("/")[0].lower()
    if host.endswith("linkedin.com"):
        return "LinkedIn post" if re.search(r"/(posts|feed)/", short) else "LinkedIn"
    if host.endswith("github.com"):
        return "GitHub"
    if "drive.google" in host or "docs.google" in host:
        return "Google Drive"
    if host.endswith("youtube.com") or host == "youtu.be":
        return "Video"
    return f"{host}"


def contact_link(value: str) -> tuple[str, str | None]:
    """A header link as (text, url): "[GitHub](https://github.com/you)" reads "GitHub"; an address reads as typed."""
    raw = (value or "").strip()
    labelled = re.fullmatch(INLINE_LINK_RE, raw)
    if labelled:
        return labelled.group(1), safe_url(labelled.group(2))
    return raw, safe_url(raw)


def split_links(text: str) -> list[tuple[str, str | None]]:
    """Split text into (piece, url) parts; url is None for plain pieces and unsafe links."""
    parts: list[tuple[str, str | None]] = []
    last = 0
    for match in INLINE_LINK_RE.finditer(text or ""):
        if match.start() > last:
            parts.append((text[last : match.start()], None))
        label, url = match.group(1), safe_url(match.group(2))
        parts.append((label, url) if url else (match.group(0), None))
        last = match.end()
    if last < len(text or ""):
        parts.append((text[last:], None))
    return parts


def plain_links(text: str) -> str:
    """``[text](url)`` as ``text (url)``, so ATS-style analysis sees the address."""
    return INLINE_LINK_RE.sub(lambda m: f"{m.group(1)} ({short_url(m.group(2))})", text or "")


def group_skills(items: list[str]) -> list[tuple[str, list[str]]]:
    """Group skills by label items: ['Languages: Python', 'Java', 'Tools: Git'] ->
    [('Languages', ['Python', 'Java']), ('Tools', ['Git'])]. Unlabelled items come
    first with an empty label."""
    groups: list[tuple[str, list[str]]] = []
    for raw in items:
        item = (raw or "").strip()
        if not item:
            continue
        match = SKILL_LABEL_RE.match(item)
        if match:
            groups.append((match.group(1).strip(), [match.group(2).strip()] if match.group(2).strip() else []))
        elif groups:
            groups[-1][1].append(item)
        else:
            groups.append(("", [item]))
    return groups
