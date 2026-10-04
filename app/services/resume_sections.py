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
BULLET_RE = re.compile(r"^\s*(?:[•\-\*▪●◦‣–·■□➢➤►✓✔]|\d{1,2}[.)])\s+")

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
    ),
}
_HEADING_LOOKUP = {phrase: section for section, phrases in SECTION_HEADINGS.items() for phrase in phrases}
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
    norm = _normalize_heading(stripped.rstrip(":"))
    if norm in _HEADING_LOOKUP and len(norm.split()) <= 5:
        return _HEADING_LOOKUP[norm], stripped.rstrip(":").strip(), ""
    match = _HEADING_PREFIX_RE.match(stripped)
    if match:
        heading = match.group(1)
        return _HEADING_LOOKUP[_normalize_heading(heading)], heading.strip(), match.group(2).strip()
    return None


def _strip_bullet(line: str) -> str:
    text = BULLET_RE.sub("", line)
    text = re.sub(r"\s+([,.;:])", r"\1", re.sub(r"[\s ​]+", " ", text))
    return text.strip()


def _split_items(lines: list[str]) -> list[str]:
    """Split skill-style lines ("Languages: C, C++ | Python") into individual items."""
    items: list[str] = []
    seen: set[str] = set()
    for raw in lines:
        line = _strip_bullet(raw)
        if ":" in line and len(line.split(":", 1)[0].split()) <= 4:
            line = line.split(":", 1)[1]  # drop "Programming Languages:" style labels
        for part in re.split(r"[,;|•·▪/]|\s{3,}", line):
            if ":" in part and len(part.split(":", 1)[0].split()) <= 4:
                part = part.split(":", 1)[1]  # "Database: SQL" after a "|" separator
            item = re.sub(
                r"\s*\((?:proficient|familiar|basic|intermediate|advanced|expert)\)\s*", " ", part, flags=re.I
            )
            item = item.strip(" .-–\t")
            key = item.lower()
            if item and len(item.split()) <= 5 and key not in seen:
                seen.add(key)
                items.append(item)
    return items


def _parse_entries(lines: list[str]) -> list[ResumeEntry]:
    """Group a section's lines into entries of title, subtitle and bullets."""
    raw_lines = [raw for raw in lines if raw.strip()]
    entries: list[ResumeEntry] = []
    current: ResumeEntry | None = None
    for i, raw in enumerate(raw_lines):
        is_bullet = bool(BULLET_RE.match(raw))
        text = _strip_bullet(raw.strip())
        short = len(text.split()) <= 14 and len(text) <= 150
        has_bullets = current is not None and bool(current.bullets)

        if not is_bullet and has_bullets:
            last = current.bullets[-1]
            if text[:1].islower() or last.endswith(",") or not last.endswith((".", "!", "?", ")", "%")):
                # PDF extraction wraps a long bullet onto the next line
                if text[:1].islower() or last.endswith(","):
                    current.bullets[-1] = f"{last} {text}"
                    continue

        # A new entry's title has a date on its own line or the next one
        nearby = text + " " + (_strip_bullet(raw_lines[i + 1]) if i + 1 < len(raw_lines) else "")
        starts_entry = short and not is_bullet and bool(DATE_RE.search(nearby))

        if is_bullet:
            if current is None:
                current = ResumeEntry()
                entries.append(current)
            current.bullets.append(text)
        elif current is None:
            current = ResumeEntry(title=text) if short else ResumeEntry(bullets=[text])
            entries.append(current)
        elif has_bullets and starts_entry:
            current = ResumeEntry(title=text)
            entries.append(current)
        elif not has_bullets and not current.subtitle and short and current.title:
            current.subtitle = text
        else:
            current.bullets.append(text)
    return entries


def _paragraph(lines: list[str]) -> str:
    return " ".join(_strip_bullet(line) for line in lines if line.strip())


def parse_resume(text: str) -> StructuredResume:
    """Split extracted resume text into a StructuredResume (best effort)."""
    # Runs of 4+ spaces/tabs separate columns or headings in many PDF extractions
    # (and in flattened text), so treat them as line breaks.
    lines = [line.strip() for line in re.split(r"\n|[ \t\u00a0\u200b]{4,}", str(text or ""))]
    resume = StructuredResume()

    # Contact details can sit anywhere (header, footer, a sidebar)
    full = "\n".join(lines)
    email = EMAIL_RE.search(full)
    resume.email = email.group(0) if email else ""
    links: list[str] = []
    for match in URL_RE.finditer(full):
        url = match.group(0).rstrip(".)")
        if "@" not in url and url not in links:
            links.append(url)
    resume.links = links[:5]
    without_urls = URL_RE.sub(" ", EMAIL_RE.sub(" ", full))
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
        cleaned = line
        for bit in contact_bits:
            if bit:
                cleaned = cleaned.replace(bit, " ")
        cleaned = re.sub(r"(?:\s*[|•·,]\s*)+", " | ", cleaned).strip(" |")
        if not cleaned or EMAIL_RE.search(cleaned):
            continue
        if not resume.name and len(cleaned.split()) <= 5 and re.fullmatch(r"[A-Za-z .'-]+", cleaned):
            resume.name = cleaned.title() if cleaned.isupper() else cleaned
        elif resume.name and not resume.headline and len(cleaned.split()) <= 12:
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
            getattr(resume, section).extend(_strip_bullet(line) for line in body if line.strip())
        else:
            items = [_strip_bullet(line) for line in body if line.strip()]
            if items:
                resume.additional.append(ExtraSection(heading=title.title(), items=items))
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


def _render_entries(entries: list[ResumeEntry]) -> list[str]:
    out: list[str] = []
    for entry in entries:
        if entry.title:
            out.append(entry.title)
        if entry.subtitle:
            out.append(entry.subtitle)
        out.extend(f"• {bullet}" for bullet in entry.bullets if bullet.strip())
        out.append("")
    return out


def render_resume_text(resume: StructuredResume) -> str:
    """Render a StructuredResume as plain text with standard section headings."""
    lines: list[str] = []
    if resume.name:
        lines.append(resume.name)
    if resume.headline:
        lines.append(resume.headline)
    contact = " | ".join(x for x in [resume.email, resume.phone, resume.location, *resume.links] if x)
    if contact:
        lines.append(contact)
    lines.append("")

    def section(heading: str, body: list[str]) -> None:
        body = [line for line in body]
        if any(line.strip() for line in body):
            lines.extend([heading, *body, ""])

    section("SUMMARY", [resume.summary] if resume.summary.strip() else [])
    section("SKILLS", [", ".join(s for s in resume.skills if s.strip())] if resume.skills else [])
    section("EXPERIENCE", _render_entries(resume.experience))
    section("PROJECTS", _render_entries(resume.projects))
    section("EDUCATION", _render_entries(resume.education))
    section("CERTIFICATIONS", [f"• {c}" for c in resume.certifications if c.strip()])
    section("ACHIEVEMENTS", [f"• {a}" for a in resume.achievements if a.strip()])
    for extra in resume.additional:
        section(extra.heading.upper(), [f"• {item}" for item in extra.items if item.strip()])
    return "\n".join(lines).strip() + "\n"
