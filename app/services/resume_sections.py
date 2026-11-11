"""Split resume text into editable sections and render sections back to text.

parse_resume() works on the text extracted from a PDF/DOCX (line breaks
preserved). It recognises common section headings ("Work Experience",
"TECHNICAL SKILLS:", "Education" ...), pulls contact details from anywhere in
the text, and groups each experience/project/education section into entries
(a title line, an optional subtitle line, and bullet points). Free-form
resumes vary a lot, so the result is a starting point for the user to edit,
not a guaranteed-correct parse.

render_resume_text() turns a StructuredResume back into plain text with
standard headings; it is what the edited resume is analyzed as.
"""

from __future__ import annotations

import re

from app.schemas.resume import ExtraSection, ResumeEntry, StructuredResume
from app.services.rich_text import INLINE_LINK_RE, plain_links, short_url

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?<![\w/])(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{2,5}\)?[\s.-]?){2,4}\d{2,5}(?![\w/])")
URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?(?:linkedin\.com|github\.com|gitlab\.com|behance\.net|dribbble\.com)/[^\s,;|]+"
    r"|https?://[^\s,;|]+",
    re.IGNORECASE,
)
DATE_RE = re.compile(
    r"\b(?:19|20)\d{2}\b|(?:\bto\b|[-–—])\s*(?:present|current|now|date|ongoing)\b"
    r"|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{2,4}\b|\b\d{1,2}/\d{2,4}\b",
    re.IGNORECASE,
)
# A date or date range at the end of an entry's title or subtitle ("... | Jun 2024 - Present")
_DATE_TOKEN = (
    r"(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+)?(?:19|20)\d{2}"
    r"|present|current|now|ongoing|today"
)
TRAILING_DATE_RE = re.compile(
    rf"^(?P<rest>.*?)(?:\s*[|,·•(]\s*|\s+[-–—]\s+|\s+|^)"
    rf"(?P<date>(?:{_DATE_TOKEN})(?:\s*(?:-|–|—|to)\s*(?:{_DATE_TOKEN}))?)\)?\s*$",
    re.IGNORECASE,
)
# Bullet glyphs. PDFs often drop the space after the glyph ("•Built ..."), and
# Word's Symbol/Wingdings bullets arrive as private-use characters (U+F0B7 etc.).
BULLET_GLYPHS = "•▪●◦‣·■□➢➤►✓✔❖◆◇▸▹▶➔➜→⇒★⁃∙⦁"
BULLET_RE = re.compile(rf"^\s*(?:[{BULLET_GLYPHS}]\s*|[-*–—]\s+|\d{{1,2}}[.)]\s+)")
LINK_LABEL_RE = re.compile(
    r"\b(?:github|linkedin|leetcode|hackerrank|codechef|codeforces|kaggle|portfolio|website|e-?mail|phone|mobile)\b"
    r"\s*:?",
    re.IGNORECASE,
)
LONE_BULLET_RE = re.compile(rf"^\s*[{BULLET_GLYPHS}\-*–]\s*$")

# Canonical section -> heading phrases (lower case, without trailing colon)
SECTION_HEADINGS: dict[str, tuple[str, ...]] = {
    "summary": (
        "summary",
        "professional summary",
        "profile",
        "professional profile",
        "objective",
        "career objective",
        "about me",
        "career overview",
        "executive summary",
    ),
    "experience": (
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "employment",
        "internships",
        "internship",
        "internship experience",
        "relevant experience",
    ),
    "education": (
        "education",
        "academic background",
        "education and training",
        "academic qualifications",
        "qualifications",
        "academics",
    ),
    "skills": (
        "skills",
        "technical skills",
        "core competencies",
        "key skills",
        "skill highlights",
        "highlights",
        "technologies",
        "tools and technologies",
        "skills and abilities",
        "areas of expertise",
        "competencies",
    ),
    "projects": (
        "projects",
        "academic projects",
        "personal projects",
        "technical projects",
        "key projects",
        "project experience",
    ),
    "certifications": (
        "certifications",
        "certificates",
        "licenses and certifications",
        "licenses & certifications",
        "courses",
        "certifications and courses",
    ),
    "achievements": (
        "achievements",
        "awards",
        "honors",
        "honors and awards",
        "accomplishments",
        "awards and achievements",
    ),
    "additional": (
        "languages",
        "interests",
        "hobbies",
        "volunteer",
        "volunteering",
        "volunteer experience",
        "activities",
        "extracurricular activities",
        "publications",
        "references",
        "additional information",
        "leadership",
        "positions of responsibility",
        # Common on Indian resumes; kept as their own sections so they never leak into skills
        "personal details",
        "personal information",
        "personal profile",
        "personal data",
        "personal info",
        "declaration",
        "languages known",
        "strengths",
        "coding and problem solving",
        "coding profiles",
        "competitive programming",
        "online profiles",
        "coding platforms",
        "research interests",
        "areas of interest",
        "technical interests",
        "fields of interest",
        "hobbies and interests",
        "extra curricular activities",
    ),
}
_HEADING_LOOKUP = {phrase: section for section, phrases in SECTION_HEADINGS.items() for phrase in phrases}
_HEADING_WORDS = {word for phrase in _HEADING_LOOKUP for word in phrase.split()} | {"and", "other", "my"}
_HEADING_PREFIX_RE = re.compile(
    r"^\s*(" + "|".join(sorted(map(re.escape, _HEADING_LOOKUP), key=len, reverse=True)) + r")\s*[:\-–]\s*(.*)$",
    re.IGNORECASE,
)


def _normalize_heading(line: str) -> str:
    text = re.sub(r"[^a-z& ]", " ", line.lower().replace("&", " and "))
    return re.sub(r"\s+", " ", text).strip()


def _match_heading(line: str) -> tuple[str, str, str] | None:
    """Return (section, heading text, inline content) if the line starts a section."""
    stripped = line.strip()
    if not stripped or len(stripped) > 60:
        return None
    if BULLET_RE.match(stripped):
        # Word files sometimes format a heading as a list item: accept it only as a whole heading
        found = _match_heading(BULLET_RE.sub("", stripped))
        return found if found and not found[2] else None
    norm = _normalize_heading(stripped.rstrip(":"))
    if norm in _HEADING_LOOKUP and len(norm.split()) <= 5:
        return _HEADING_LOOKUP[norm], stripped.rstrip(":").strip(), ""
    words = norm.split()
    if 2 <= len(words) <= 6 and not re.search(r"\d", stripped) and set(words) <= _HEADING_WORDS:
        # Made only of heading words: the section of the first known heading phrase in it
        for size in (3, 2, 1):
            for start in range(len(words) - size + 1):
                phrase = " ".join(words[start : start + size])
                if phrase in _HEADING_LOOKUP:
                    return _HEADING_LOOKUP[phrase], stripped.rstrip(":").strip(), ""
    match = _HEADING_PREFIX_RE.match(stripped)
    if match:
        heading = match.group(1)
        return _HEADING_LOOKUP[_normalize_heading(heading)], heading.strip(), match.group(2).strip()
    return None


def _strip_bullet(line: str) -> str:
    text = BULLET_RE.sub("", line)
    text = re.sub(r"\s+([,.;:])", r"\1", re.sub(r"[\s ​]+", " ", text))
    return text.strip()


def _list_items(lines: list[str]) -> list[str]:
    """One item per bullet; in a bulleted list, a line without a bullet continues the one above."""
    raw = [line for line in lines if line.strip()]
    bulleted = sum(bool(BULLET_RE.match(line)) for line in raw) >= max(1, len(raw) // 3)
    items: list[str] = []
    for line in raw:
        text = _strip_bullet(line)
        if items and bulleted and not BULLET_RE.match(line):
            items[-1] = f"{items[-1]} {text}"
        else:
            items.append(text)
    return items


def _split_items(lines: list[str]) -> list[str]:
    """Split skill-style lines ("Languages: C, C++ | Python") into individual items."""
    items: list[str] = []
    seen: set[str] = set()
    for raw in lines:
        line = _strip_bullet(raw)
        links = INLINE_LINK_RE.findall(line)
        if links:
            # A line of profile links ("CodeChef: [vardhan_2423](https://...)") is kept whole
            if line not in seen:
                seen.add(line)
                items.append(line)
            continue
        label = ""
        if ":" in line and len(line.split(":", 1)[0].split()) <= 4:
            label, line = (x.strip() for x in line.split(":", 1))  # "Programming Languages: ..." starts a group
        for part in re.split(r"[,;|•·▪/]|\s{3,}", line):
            if ":" in part and len(part.split(":", 1)[0].split()) <= 4:
                label, part = (x.strip() for x in part.split(":", 1))  # "Database: SQL" after a "|" separator
            item = re.sub(
                r"\s*\((?:proficient|familiar|basic|intermediate|advanced|expert)\)\s*", " ", part, flags=re.I
            )
            item = item.strip(" .-–\t")
            key = item.lower()
            if item and len(item.split()) <= 5 and key not in seen:
                seen.add(key)
                items.append(f"{label}: {item}" if label else item)
                label = ""  # only the group's first item carries the label
    return items


# A bullet that ends mid-phrase ("... the forecast for") continues on the next line
_CONTINUES = re.compile(r"\b(for|and|or|of|in|to|with|the|a|an|on|at|by|from|using|via|into|across|over)$", re.I)


# A real address has a dot in its site name ("https://www" alone is a broken fragment)
_REAL_HOST = re.compile(r"^(?:https?://)?(?:www\.)?[a-z0-9-]+(?:\.[a-z0-9-]+)+", re.IGNORECASE)
_POST_LINK = re.compile(r"linkedin\.com/(?:posts|feed|pulse)/", re.IGNORECASE)
_ENTRY_LINK = re.compile(r"\s*\[link\]\(([^)\s]+)\)")


def _titled(text: str) -> ResumeEntry:
    """A new entry from its title line; a "[link](url)" on it (an icon link in the PDF) is the entry's link."""
    found = _ENTRY_LINK.search(text)
    if not found:
        return ResumeEntry(title=text)
    return ResumeEntry(title=_ENTRY_LINK.sub("", text).strip(), link=found.group(1))


_SMALL_WORDS = {"a", "an", "the", "and", "or", "of", "for", "in", "on", "to", "with", "&", "-", "–", "|"}


def _looks_like_title(text: str) -> bool:
    """A short name in Title Case ("Java Mini Games Hub"), not a sentence or a "Label:" line."""
    words = text.split()
    if not 2 <= len(words) <= 8 or text.rstrip().endswith((".", "!", "?", ",", ":", ";")) or ":" in text:
        return False
    content = [w for w in words if w.lower() not in _SMALL_WORDS]
    capital = [w for w in content if w[:1].isupper() or w[:1].isdigit()]
    return bool(content) and len(capital) / len(content) >= 0.75


def _parse_entries(lines: list[str]) -> list[ResumeEntry]:
    """Group a section's lines into entries of title, subtitle and bullets."""
    raw_lines = [raw for raw in lines if raw.strip()]
    entries: list[ResumeEntry] = []
    current: ResumeEntry | None = None
    for i, raw in enumerate(raw_lines):
        is_bullet = bool(BULLET_RE.match(raw))
        text = _strip_bullet(raw.strip())
        visible = _ENTRY_LINK.sub("", text)
        short = len(visible.split()) <= 14 and len(visible) <= 150
        has_bullets = current is not None and bool(current.bullets)

        if not is_bullet and has_bullets:
            last = current.bullets[-1]
            if text[:1].islower() or last.endswith(",") or not last.endswith((".", "!", "?", ")", "%")):
                # PDF extraction wraps a long bullet onto the next line
                if text[:1].islower() or last.endswith(",") or _CONTINUES.search(last):
                    current.bullets[-1] = f"{last} {text}"
                    continue

        # A new entry's title has a date on its own line or the next one
        nearby = text + " " + (_strip_bullet(raw_lines[i + 1]) if i + 1 < len(raw_lines) else "")
        starts_entry = short and not is_bullet and bool(DATE_RE.search(nearby))
        # ...or, in a bulleted section, a short capitalised line between bullet groups is the
        # next entry's title even without a date ("Churn Predictor" after a project's bullets)
        if not starts_entry and has_bullets and short and not is_bullet and i > 0:
            ahead = raw_lines[i + 1 : i + 3]
            last_bullet = current.bullets[-1] if current is not None and current.bullets else ""
            starts_entry = (
                (bool(BULLET_RE.match(raw_lines[i - 1])) or last_bullet.rstrip().endswith((".", "!", "?", ")", "%")))
                and text[:1].isupper()
                and not text.endswith((".", "!", "?", ","))
                and bool(ahead)
                and (
                    bool(BULLET_RE.match(ahead[0]))
                    or (len(ahead) == 2 and not BULLET_RE.match(ahead[0]) and bool(BULLET_RE.match(ahead[1])))
                )
            ) or (bool(ahead) and _looks_like_title(visible))

        if is_bullet:
            if current is None:
                current = ResumeEntry()
                entries.append(current)
            current.bullets.append(text)
        elif current is None:
            current = _titled(text) if short or _ENTRY_LINK.search(text) else ResumeEntry(bullets=[text])
            entries.append(current)
        elif has_bullets and starts_entry:
            current = _titled(text)
            entries.append(current)
        elif not has_bullets and not current.subtitle and short and current.title:
            current.subtitle = text
        else:
            current.bullets.append(text)
    return entries


def _paragraph(lines: list[str]) -> str:
    return " ".join(_strip_bullet(line) for line in lines if line.strip())


def _join_lone_bullets(lines: list[str]) -> list[str]:
    """Some PDFs put the bullet glyph on its own line; attach it to the next text line."""
    joined: list[str] = []
    pending = False
    for line in lines:
        if LONE_BULLET_RE.match(line):
            pending = True
            continue
        if pending and line:
            joined.append(f"• {line}")
            pending = False
        else:
            joined.append(line)
    return joined


def parse_resume(text: str) -> StructuredResume:
    """Split extracted resume text into a StructuredResume (best effort)."""
    # Runs of 4+ spaces/tabs separate columns or headings in many PDF extractions
    # (and in flattened text), so treat them as line breaks.
    lines = _join_lone_bullets([line.strip() for line in re.split(r"\n|[ \t\u00a0\u200b]{4,}", str(text or ""))])
    resume = StructuredResume()

    # Contact details can sit anywhere (header, footer, a sidebar)
    full = "\n".join(lines)
    email = EMAIL_RE.search(full)
    resume.email = email.group(0) if email else ""
    links: list[str] = []
    # Labelled links in the header ("[GitHub](https://github.com/...)") keep their label
    first_heading = next((i for i, line in enumerate(lines) if _match_heading(line)), len(lines))
    for line in lines[:first_heading]:
        for match in INLINE_LINK_RE.finditer(line):
            if match.group(1).lower() != "link" and "@" not in match.group(2):
                links.append(match.group(0))
    # Visible addresses anywhere, except those already inside a [text](url) link
    for match in URL_RE.finditer(INLINE_LINK_RE.sub(" ", full)):
        url = match.group(0).rstrip(".)")
        if "@" not in url and url not in links and not _POST_LINK.search(url) and _REAL_HOST.search(url):
            links.append(url)
    resume.links = links[:5]
    without_urls = URL_RE.sub(" ", EMAIL_RE.sub(" ", INLINE_LINK_RE.sub(" ", full)))
    for match in PHONE_RE.finditer(without_urls):
        candidate = match.group(0).strip()
        digits = re.sub(r"\D", "", candidate)
        looks_like_dates = re.search(r"(19|20)\d{2}\s*[-–]\s*(19|20)\d{2}", candidate)
        if 10 <= len(digits) <= 13 and candidate.count("(") == candidate.count(")") and not looks_like_dates:
            resume.phone = candidate
            break

    # Split into the header block and sections
    sections: list[tuple[str, str, list[str]]] = []
    header: list[str] = []
    for line in lines:
        heading = _match_heading(line)
        if heading:
            section, title, inline = heading
            sections.append((section, title, [inline] if inline else []))
        elif sections:
            sections[-1][2].append(line)
        elif line.strip():
            header.append(line.strip())

    # Name and headline: first header lines that are not contact details
    contact_bits = {resume.email, resume.phone, *resume.links}
    for line in header[:4]:
        contact_line = any(bit and bit in line for bit in (resume.email, resume.phone))
        cleaned = line
        for bit in contact_bits:
            if bit:
                cleaned = cleaned.replace(bit, " ")
        # Link labels whose URL sits behind the word ("GitHub | LinkedIn")
        cleaned = INLINE_LINK_RE.sub(" ", cleaned)
        cleaned = LINK_LABEL_RE.sub(" ", cleaned)
        cleaned = re.sub(r"(?:\s*[|•·,]\s*)+", " | ", cleaned).strip(" |")
        if not cleaned or EMAIL_RE.search(cleaned):
            continue
        if contact_line:
            place = cleaned.replace(" | ", ", ")
            if not resume.location and len(place.split()) <= 6 and re.fullmatch(r"[A-Za-z .,'-]+", place):
                resume.location = place
            continue
        if not resume.name and len(cleaned.split()) <= 5 and re.fullmatch(r"[A-Za-z .'-]+", cleaned):
            resume.name = cleaned  # exactly as the student wrote it ("GADDE JASWITHA" stays in capitals)
        elif (
            resume.name
            and not resume.headline
            and len(cleaned.split()) <= 12
            and len(cleaned) >= 4
            and not re.search(r"https?:|www\.|\.com\b|/", line, re.IGNORECASE)
        ):
            resume.headline = cleaned
    if not sections and len(header) > 2:
        # No recognisable headings: keep everything after the name as the summary
        resume.summary = _paragraph(header[1:])

    for section, title, body in sections:
        if section == "summary":
            resume.summary = (resume.summary + " " + _paragraph(body)).strip()
        elif section == "skills":
            resume.skills.extend(s for s in _split_items(body) if s not in resume.skills)
        elif section in ("experience", "projects", "education"):
            getattr(resume, section).extend(_parse_entries(body))
        elif section in ("certifications", "achievements"):
            getattr(resume, section).extend(_list_items(body))
        else:
            items = _list_items(body)
            if items:
                resume.additional.append(ExtraSection(heading=title.title(), items=items))
    for entries in (resume.experience, resume.projects, resume.education):
        _move_dates(entries)
    return _within_limits(resume)


def _within_limits(resume: StructuredResume) -> StructuredResume:
    """Trim parsed values to the schema limits (appends bypass validation).

    Re-validating also guarantees the API never fails to serialize a parse.
    """
    data = resume.model_dump()
    fields = StructuredResume.model_fields
    for key in ("name", "headline", "email", "phone", "location", "summary"):
        limit = next(m.max_length for m in fields[key].metadata if hasattr(m, "max_length"))
        data[key] = data[key][:limit]
    for key in (
        "links",
        "skills",
        "experience",
        "projects",
        "education",
        "certifications",
        "achievements",
        "additional",
    ):
        limit = next(m.max_length for m in fields[key].metadata if hasattr(m, "max_length"))
        data[key] = data[key][:limit]
    for key in ("experience", "projects", "education"):
        for entry in data[key]:
            entry["title"] = entry["title"][:300]
            entry["subtitle"] = entry["subtitle"][:300]
            entry["bullets"] = entry["bullets"][:60]
    for extra in data["additional"]:
        extra["heading"] = extra["heading"][:100]
        extra["items"] = extra["items"][:60]
    return StructuredResume.model_validate(data)


def section_order(text: str) -> list[str]:
    """Canonical sections in the order their headings appear in the text."""
    order: list[str] = []
    for line in re.split(r"\n|[ \t\u00a0\u200b]{4,}", str(text or "")):
        heading = _match_heading(line)
        if heading and heading[0] not in order:
            order.append(heading[0])
    return order


STUDENT_RE = re.compile(
    r"\b(?:student|fresher|undergraduate|pursuing|final[- ]year|(?:second|third|fourth|2nd|3rd|4th)[- ]year|"
    r"expected (?:graduation|20\d{2})|class of 20\d{2}|b\.?\s?tech|b\.?\s?e\.?|b\.?\s?sc|bca|mca|internship)\b",
    re.IGNORECASE,
)


def looks_like_student(text: str, resume: StructuredResume, current_year: int) -> bool:
    """Heuristic: student wording, or an education end year that hasn't passed yet."""
    if STUDENT_RE.search(text or ""):
        return True
    for entry in resume.education:
        years = [int(y) for y in re.findall(r"\b(20\d{2})\b", f"{entry.title} {entry.subtitle}")]
        if years and max(years) >= current_year:
            return True
    return False


def split_trailing_date(text: str) -> tuple[str, str]:
    """("Software Intern, Acme | Jun 2024 - Aug 2024") -> ("Software Intern, Acme", "Jun 2024 - Aug 2024").

    Only dates that include a year count, so "Present" alone or a version number stay put.
    """
    match = TRAILING_DATE_RE.match(text.strip())
    if not match or not re.search(r"(?:19|20)\d{2}", match["date"]):
        return text, ""
    return match["rest"].strip(" |,·•-–—("), match["date"].strip()


# "2024 – 2028 | CGPA: 9.02": a date range, a separator, then more
_LEADING_DATE = re.compile(r"^\s*(.{4,30}?)\s*[|·•,]\s*(\S.*)$")


def _move_dates(entries: list[ResumeEntry]) -> None:
    """Give each entry a separate date when its subtitle or title ends with one."""
    for entry in entries:
        if entry.date:
            continue
        for field in ("subtitle", "title"):
            rest, date = split_trailing_date(getattr(entry, field))
            if date:
                setattr(entry, field, rest)
                entry.date = date
                break
        else:
            # A line that is only a date ("2022 – 2026") under the entry is its date, not a bullet;
            # "2024 – 2028 | CGPA: 9.02" gives its date and keeps the rest
            for i, bullet in enumerate(entry.bullets):
                if _is_date_only(bullet):
                    entry.date = bullet.strip()
                    del entry.bullets[i]
                    break
                lead = _LEADING_DATE.match(bullet)
                if lead and _is_date_only(lead.group(1)):
                    entry.date = lead.group(1).strip()
                    entry.bullets[i] = lead.group(2).strip()
                    break


def _is_date_only(line: str) -> bool:
    text = line.strip()
    if not text or len(text) > 40 or not DATE_RE.search(text):
        return False
    rest = re.sub(
        r"\b(?:to|till|until|present|current|now|ongoing|expected)\b", " ", DATE_RE.sub(" ", text), flags=re.I
    )
    return not re.sub(r"[\s\-–—/.,()']", "", rest)


def _render_entries(entries: list[ResumeEntry]) -> list[str]:
    out: list[str] = []
    for entry in entries:
        if entry.title or entry.date:
            out.append(" | ".join(x for x in (entry.title, entry.date) if x))
        if entry.subtitle:
            out.append(plain_links(entry.subtitle))
        if entry.link.strip():
            out.append(short_url(entry.link))
        out.extend(f"• {plain_links(bullet)}" for bullet in entry.bullets if bullet.strip())
        out.append("")
    return out


def render_resume_text(resume: StructuredResume) -> str:
    """Render a StructuredResume as plain text with standard section headings."""
    lines: list[str] = []
    if resume.name:
        lines.append(resume.name)
    if resume.headline:
        lines.append(resume.headline)
    contact = " | ".join(plain_links(x) for x in [resume.email, resume.phone, resume.location, *resume.links] if x)
    if contact:
        lines.append(contact)
    lines.append("")

    def section(heading: str, body: list[str]) -> None:
        body = [line for line in body]
        if any(line.strip() for line in body):
            lines.extend([heading, *body, ""])

    section("SUMMARY", [plain_links(resume.summary)] if resume.summary.strip() else [])
    section("SKILLS", [", ".join(s for s in resume.skills if s.strip())] if resume.skills else [])
    section("EXPERIENCE", _render_entries(resume.experience))
    section("PROJECTS", _render_entries(resume.projects))
    section("EDUCATION", _render_entries(resume.education))
    section("CERTIFICATIONS", [f"• {plain_links(c)}" for c in resume.certifications if c.strip()])
    section("ACHIEVEMENTS", [f"• {plain_links(a)}" for a in resume.achievements if a.strip()])
    for extra in resume.additional:
        section(extra.heading.upper(), [f"• {plain_links(item)}" for item in extra.items if item.strip()])
    return "\n".join(lines).strip() + "\n"
