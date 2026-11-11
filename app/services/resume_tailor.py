"""Generate a fixed resume: the student's own resume with the report's issues fixed.

Three modes:
- job: tailored to a pasted job description;
- role: no job, but a target role (its core skills stand in for the job's);
- general: neither, so only role-free fixes are made.

Rule-based like the resume generator (no AI service; nothing leaves the server),
and it never invents anything:

- Skills: skills used in projects or jobs but missing from the skills section
  are added; skills the student very likely knows (Machine Learning -> pandas)
  are added when the job or role needs them; rows are grouped, wanted skills
  first. Wanted skills the resume doesn't show are only *suggested*.
- Projects: the ones that match come first, and each gets a "Tech: ..." line
  from the skills it already mentions.
- Bullets: only weak ones change ("worked on", "responsible for" -> action
  verbs; numbers formatted). Strong bullets stay exactly as written.
- Summary: a good existing summary is kept and ours is offered as a
  suggestion; a missing or thin one is replaced.
- Dates use one format.

Every change has an id. The student can undo any change (``skip``) or take a
suggestion (``accept``), and the resume is rebuilt with only what they kept.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
import re

from app.schemas.resume import ResumeEntry, StructuredResume
from app.schemas.tailor import ScorePair, TailorChange, TailorResponse
from app.services.data_cleaning import clean_text
from app.services.job_decoder import decode_job
from app.services.resume_generator import (
    LEAD_VERBS,
    ONE_PAGE_LINES,
    PAST_TENSE,
    SKILL_GROUPS,
    _canonical,
    _estimated_lines,
    _format_numbers,
    _helped,
    _join,
    _kind_of,
    _lower_first,
    _sentence,
    _starts_with_verb,
    _strip_weak_start,
)
from app.services.resume_sections import render_resume_text
from app.services.role_gap import target_roles
from app.services.score_integrity import implied_by
from app.services.skill_extractor import extract_skills
from app.services.skills_inventory import DOMAIN_GROUP, SOFT_GROUP, group_of

MAX_SUMMARY_SKILLS = 4
MAX_SUGGESTED = 10
MAX_NUMBER_NOTES = 3
GOOD_SUMMARY_WORDS = 20

# How common skills are written (the extractor works in lower case)
DISPLAY = {
    "javascript": "JavaScript",
    "typescript": "TypeScript",
    "node.js": "Node.js",
    "next.js": "Next.js",
    "github": "GitHub",
    "gitlab": "GitLab",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
    "sqlite": "SQLite",
    "numpy": "NumPy",
    "pandas": "pandas",
    "scikit-learn": "scikit-learn",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow",
    "fastapi": "FastAPI",
    "rest api": "REST API",
    "power bi": "Power BI",
    "ci/cd": "CI/CD",
    "opencv": "OpenCV",
    "langchain": "LangChain",
    "llms": "LLMs",
    "iot": "IoT",
    "c++": "C++",
    "c#": "C#",
    ".net": ".NET",
    "graphql": "GraphQL",
    "wordpress": "WordPress",
    "solidworks": "SolidWorks",
    "autocad": "AutoCAD",
    "matlab": "MATLAB",
    "xgboost": "XGBoost",
    "mlops": "MLOps",
    "ui/ux design": "UI/UX Design",
    "hugging face": "Hugging Face",
    "vs code": "VS Code",
    "tailwind css": "Tailwind CSS",
    "react native": "React Native",
    "dbms": "DBMS",
    "vlsi": "VLSI",
    "plc": "PLC",
    "gst": "GST",
    "catia": "CATIA",
    "ansys": "ANSYS",
    "etabs": "ETABS",
    "staad pro": "STAAD Pro",
}
_SHORT_WORDS = {"git", "java", "go", "rust", "dart", "ruby", "vue", "excel", "figma", "jira", "linux", "react"}

_TECH_PREFIX = re.compile(r"^\s*(tech(nologies|nology| stack)?|tools?|stack|built with|skills)\s*[:\-–]", re.I)
_DATE_PART = r"(?:[A-Za-z]{3,9}\.?\s+)?(?:19|20)\d{2}|present|current|now|ongoing"
_DATE_RANGE = re.compile(rf"^\s*({_DATE_PART})\s*(?:-|–|—|to|till|until)\s*({_DATE_PART})\s*$", re.I)
_HAS_NUMBER = re.compile(r"\d")
_LABEL = re.compile(r"^\s*([A-Za-z &/+.-]{2,40}):\s*(.*)$")
_SPLIT = re.compile(r"\s*[,|•;]\s*")
_WEAK = re.compile(
    r"^(i\s+|we\s+)?(worked on|working on|helped|helping|assisted|involved in|responsible for|"
    r"participated in|did|made|was|were|created a project)\b",
    re.I,
)
_GENERIC_SUMMARY = re.compile(
    r"\b(hard[- ]?working|seeking (a|an) (challenging|opportunit)|to (work|grow) in a (reputed|dynamic)|"
    r"utili[sz]e my skills|esteemed organi[sz]ation)\b",
    re.I,
)


# ---------------------------------------------------------------------------- text helpers
def _norm(text: str) -> str:
    return re.sub(r"[\s.]+$", "", re.sub(r"\s+", " ", (text or "").strip())).lower()


def _display(skill: str, *sources: str) -> str:
    """How a skill should read: the student's own spelling unless it's all lower case."""
    for source in sources:
        found = re.search(rf"(?<![\w.+#]){re.escape(skill)}(?![\w+#])", source or "", re.I)
        if found and not found.group(0).islower():
            return found.group(0)
    if skill in DISPLAY:
        return DISPLAY[skill]
    if len(skill) <= 4 and " " not in skill and skill not in _SHORT_WORDS:
        return skill.upper()
    return " ".join(w[:1].upper() + w[1:] for w in skill.split(" "))


def _gerund_to_past(word: str) -> str | None:
    """'managing' -> 'Managed', 'writing' -> 'Wrote', 'planning' -> 'Planned'."""
    low = word.lower()
    if not low.endswith("ing") or len(low) < 6:
        return None
    stem = low[:-3]
    for base in (stem, stem + "e"):
        if base in PAST_TENSE:
            return PAST_TENSE[base]
    return (stem + "ed").capitalize()


def improve_bullet(text: str, title: str = "") -> str:
    """A stronger version of a weak bullet, or the bullet unchanged when it's already fine."""
    bullet = re.sub(r"^[\s•●▪◦*\-–]+", "", text or "").strip()
    if not bullet or _TECH_PREFIX.match(bullet):
        return text
    context = f"{title} {bullet}"
    first = bullet.split(" ", 1)[0]
    rest = bullet[len(first) :].strip()

    if _WEAK.match(bullet):
        stripped = _strip_weak_start(bullet)
        head = stripped.split(" ", 1)[0] if stripped else ""
        tail = stripped[len(head) :]
        if not stripped:
            return text
        if _helped(bullet):
            lead = "Collaborated to" if head.lower() in PAST_TENSE else "Contributed to"
            new = f"{lead} {_lower_first(stripped)}"
        elif _starts_with_verb(stripped):
            new = stripped[:1].upper() + stripped[1:]
        elif head.lower() in PAST_TENSE:
            new = PAST_TENSE[head.lower()] + tail
        elif _gerund_to_past(head):
            new = _gerund_to_past(head) + tail
        else:
            new = f"{LEAD_VERBS[_kind_of(context)][0]} {_lower_first(stripped)}"
    elif first.lower() in PAST_TENSE and first[:1].islower():
        new = PAST_TENSE[first.lower()] + (f" {rest}" if rest else "")
    elif _gerund_to_past(first) and not _starts_with_verb(first):
        new = _gerund_to_past(first) + (f" {rest}" if rest else "")
    else:
        new = bullet[:1].upper() + bullet[1:]
    new = _proper_names(_sentence(_format_numbers(new)))
    # Only a real improvement counts; capitalisation or a full stop alone keeps the original
    return new if _norm(new) != _norm(bullet) else text


def _proper_names(text: str) -> str:
    """Write one-word skills and known names properly inside a sentence (html -> HTML, python -> Python)."""
    for skill in extract_skills(clean_text(text)):
        if " " in skill and skill not in DISPLAY:
            continue  # "machine learning" reads fine in lower case
        proper = _display(skill)
        text = re.sub(
            rf"(?<![\w.+#/]){re.escape(skill)}(?![\w+#])",
            lambda m, proper=proper: proper if m.group(0).islower() else m.group(0),
            text,
        )
    return text


def fix_date(value: str) -> str:
    match = _DATE_RANGE.match(value or "")
    if not match:
        return value or ""
    start, end = (part.strip() for part in match.groups())
    end = "Present" if end.lower() in {"present", "current", "now", "ongoing"} else end
    return f"{start} – {end}"


def _level(education: list[ResumeEntry], today: date) -> tuple[str, bool]:
    years = [int(y) for e in education for y in re.findall(r"(?:19|20)\d{2}", f"{e.date} {e.subtitle}")]
    if not years:
        return "", False
    left = max(years) - today.year - (0 if today.month < 7 else 1)
    if left < 0:
        return "Recent", True
    return {0: "Final-year", 1: "Third-year", 2: "Second-year"}.get(left, "First-year"), False


def typed_skills(skills: list[str]) -> list[str]:
    """Skill names from the skills section, without row labels ("Languages: Python, SQL")."""
    names: list[str] = []
    for item in skills:
        label = _LABEL.match(item)
        body = label.group(2) if label else item
        for name in _SPLIT.split(body):
            name = name.strip(" .")
            if name and name.lower() not in {n.lower() for n in names}:
                names.append(name)
    return names


def _technical(skill: str) -> bool:
    return group_of(skill) not in {SOFT_GROUP, DOMAIN_GROUP}


def _job_role(job_text: str) -> str:
    """The role from the posting's first line ("Backend Developer (Fresher)" -> "Backend Developer")."""
    for line in (job_text or "").splitlines():
        line = line.strip(" \t-•*#")
        if not line:
            continue
        if ":" in line or len(line.split()) > 7:
            return ""
        line = re.sub(r"\(.*?\)|\[.*?\]", "", line)
        line = re.split(r"\s+[-–|@]\s+|,", line)[0].strip()
        return line if 1 <= len(line.split()) <= 5 else ""
    return ""


def good_summary(text: str) -> bool:
    """Worth keeping: long enough, names real skills or a field, and isn't boilerplate."""
    words = (text or "").split()
    if len(words) < GOOD_SUMMARY_WORDS or _GENERIC_SUMMARY.search(text):
        return False
    return any(_technical(s) for s in extract_skills(clean_text(text)))


# ---------------------------------------------------------------------------- what the resume aims at
class _Target:
    def __init__(self, job_text: str, role: str, claimed: set[str]):
        self.must: list[str] = []
        self.nice: list[str] = []
        if job_text.strip():
            self.mode = "job"
            insights = decode_job(job_text, claimed)
            self.must = insights.must_have
            self.nice = [*insights.nice_to_have, *insights.also_mentioned]
            self.role = _job_role(job_text)
        elif role in target_roles():
            self.mode = "role"
            self.must = list(target_roles()[role])
            self.role = role
        else:
            self.mode = "general"
            self.role = ""
        self.wanted = list(dict.fromkeys([*self.must, *self.nice]))

    def weight(self, skill: str | None) -> int:
        if not skill:
            return 0
        return 3 if skill in self.must else 2 if skill in self.nice else 0


def _entry_skills(entry: ResumeEntry) -> set[str]:
    return extract_skills(clean_text(" ".join([entry.title, entry.subtitle, *entry.bullets])))


def tech_line(entry: ResumeEntry, target: _Target, names: list[str]) -> list[str]:
    """Skills for a 'Tech: ...' line, from what the entry already mentions (none invented)."""
    if _TECH_PREFIX.match(entry.subtitle) or any(_TECH_PREFIX.match(b) for b in entry.bullets):
        return []
    if extract_skills(clean_text(entry.subtitle)):
        return []  # the subtitle already is a tech list ("Python, Flask, MySQL")
    used = sorted((s for s in _entry_skills(entry) if _technical(s)), key=lambda s: (-target.weight(s), s))
    source = " ".join([entry.title, *entry.bullets])
    return [_display(s, source, ", ".join(names)) for s in used[:6]]


def _skill_rows(names: list[str], target: _Target) -> list[str]:
    rows: dict[str, list[str]] = {}
    for name in names:
        canonical = _canonical(name)
        keys = {name.lower(), canonical or ""}
        label = next((g for g, members in SKILL_GROUPS if keys & members), "Other")
        rows.setdefault(label, []).append(name)
    out: list[str] = []
    for label in [g for g, _ in SKILL_GROUPS] + ["Other"]:
        if label not in rows:
            continue
        ordered = sorted(rows[label], key=lambda n: -target.weight(_canonical(n)))
        out.append(f"{label}: {ordered[0]}")
        out.extend(ordered[1:])
    return out


def _summary(resume: StructuredResume, target: _Target, top: list[str]) -> str:
    level, graduated = _level(resume.education, date.today())
    degree = resume.education[0].title.strip() if resume.education else ""
    person = re.sub(r"\s+", " ", f"{level} {degree} {'graduate' if graduated else 'student'}").strip()
    person = person[:1].upper() + person[1:]
    parts = [f"{person}{f' targeting {target.role} roles' if target.role else ''}."]
    built = []
    if resume.projects:
        built.append(f"{len(resume.projects)} project{'s' if len(resume.projects) > 1 else ''}")
    if resume.experience:
        built.append(f"{len(resume.experience)} internship{'s' if len(resume.experience) > 1 else ''}")
    if top:
        parts.append(f"Hands-on with {_join(top)}{f' through {_join(built)}' if built else ''}.")
    elif built:
        parts.append(f"Hands-on experience from {_join(built)}.")
    return " ".join(parts)


# ---------------------------------------------------------------------------- entry point
def tailor_resume(
    resume: StructuredResume,
    job_text: str = "",
    target_role: str = "",
    confirmed_skills: list[str] | None = None,
    skip: list[str] | None = None,
    accept: list[str] | None = None,
    score: Callable[[StructuredResume], tuple[float | None, float | None]] | None = None,
) -> TailorResponse:
    """The fixed resume, every change (with whether it is applied) and the scores before and after.

    ``skip`` lists change ids the student undid; ``accept`` lists suggestions they took.
    ``score(resume) -> (match, ats)`` is injected so tests can run without the models.
    """
    skipped, accepted = set(skip or []), set(accept or [])
    changes: list[TailorChange] = []

    def change(cid: str, section: str, kind: str, title: str, before: str = "", after: str = "") -> bool:
        suggestion = kind == "suggestion"
        applied = cid in accepted if suggestion else cid not in skipped
        changes.append(
            TailorChange(id=cid, section=section, kind=kind, title=title, before=before, after=after, applied=applied)
        )
        return applied

    original_text = render_resume_text(resume)
    claimed = extract_skills(clean_text(original_text))
    target = _Target(job_text, target_role, claimed)

    # ---- skills
    typed = typed_skills(resume.skills)
    typed_canonical = {c for c in (_canonical(t) for t in typed) if c}
    from_entries = sorted((s for s in claimed - typed_canonical if _technical(s)), key=lambda s: (-target.weight(s), s))
    implied = implied_by(claimed)
    likely = [s for s in target.wanted if s in implied and s not in claimed]
    confirmed = [c.strip() for c in confirmed_skills or [] if c.strip()]

    names = list(typed)
    added: list[str] = []

    def add(new_names: list[str]) -> None:
        for name in new_names:
            if name.lower() not in {n.lower() for n in names}:
                names.append(name)
                added.append(name)

    used_names = [_display(s, original_text) for s in from_entries]
    if used_names and change(
        "skills-used", "Skills", "added", "Added skills you used in your projects or jobs", after=", ".join(used_names)
    ):
        add(used_names)
    if likely:
        detail = ", ".join(f"{_display(s)} (you know {_display(implied[s], original_text)})" for s in likely)
        if change("skills-likely", "Skills", "added", "Added skills you very likely know", after=detail):
            add([_display(s) for s in likely])
    if confirmed:
        change("skills-confirmed", "Skills", "added", "Added the skills you confirmed", after=", ".join(confirmed))
        add(confirmed)

    grouped = _skill_rows(names, target)
    if names and [s.lower() for s in grouped] != [s.lower() for s in resume.skills]:
        title = "Grouped your skills" + (", with the most wanted first" if target.wanted else "")
        if change("skills-group", "Skills", "reordered", title):
            skills = grouped
        else:
            skills = [*resume.skills, *added]
    else:
        skills = [*resume.skills, *added]

    # ---- projects: best match first (only when there is something to match)
    order = list(range(len(resume.projects)))
    if target.wanted:
        ranked = sorted(order, key=lambda i: -sum(target.weight(s) for s in _entry_skills(resume.projects[i])))
        if ranked != order and change(
            "projects-order",
            "Projects",
            "reordered",
            "Put the projects that match best first",
            after=" → ".join(resume.projects[i].title for i in ranked if resume.projects[i].title),
        ):
            order = ranked

    # ---- entries: weak bullets, Tech lines, dates
    date_fixes = [e for e in [*resume.experience, *resume.projects, *resume.education] if fix_date(e.date) != e.date]
    fix_dates = bool(date_fixes) and change("dates", "Dates", "fixed", "Used one date format (Jun 2024 – Aug 2024)")

    def fix_entries(section: str, label: str, entries: list[ResumeEntry], indexes: list[int]) -> list[ResumeEntry]:
        fixed = []
        for i in indexes:
            entry = entries[i]
            name = entry.title or label
            bullets = []
            for j, bullet in enumerate(entry.bullets):
                better = improve_bullet(bullet, entry.title)
                if better != bullet and change(
                    f"bullet:{section}:{i}:{j}", label, "rewrote", f"Stronger bullet in “{name}”", bullet, better
                ):
                    bullets.append(better)
                else:
                    bullets.append(bullet)
            update: dict = {"bullets": bullets}
            tech = tech_line(entry, target, names)
            if tech and change(
                f"tech:{section}:{i}",
                label,
                "added",
                f"Added a Tech line to “{name}”",
                after=f"Tech: {', '.join(tech)}",
            ):
                line = f"Tech: {', '.join(tech)}"
                update["subtitle"] = f"{entry.subtitle} | {line}" if entry.subtitle.strip() else line
            if fix_dates:
                update["date"] = fix_date(entry.date)
            fixed.append(entry.model_copy(update=update))
        return fixed

    experience = fix_entries("experience", "Experience", resume.experience, list(range(len(resume.experience))))
    projects = fix_entries("projects", "Projects", resume.projects, order)
    education = [e.model_copy(update={"date": fix_date(e.date)}) if fix_dates else e for e in resume.education]

    # ---- summary and headline
    claimed_after = claimed | {c for c in (_canonical(n) for n in confirmed) if c}
    pool = [s for s in target.wanted if s in claimed_after and _technical(s)] or sorted(
        (s for s in claimed if _technical(s)), key=lambda s: s not in typed_canonical
    )
    top = [_display(s, original_text, ", ".join(names)) for s in pool][:MAX_SUMMARY_SKILLS]
    fixed = resume.model_copy(
        update={"skills": skills, "projects": projects, "experience": experience, "education": education}
    )
    ours = _summary(fixed, target, top)
    for_what = f"the {target.role} role" if target.role else "your resume"
    summary = resume.summary
    if good_summary(resume.summary):
        if change(
            "summary",
            "Summary",
            "suggestion",
            f"Your summary is good, so we kept it. Here's one written for {for_what} if you prefer",
            resume.summary.strip(),
            ours,
        ):
            summary = ours
    elif _norm(ours) != _norm(resume.summary) and change(
        "summary",
        "Summary",
        "rewrote" if resume.summary.strip() else "new",
        f"Wrote a summary for {for_what}",
        resume.summary.strip(),
        ours,
    ):
        summary = ours

    headline = resume.headline
    if not headline.strip() and target.role:
        branch = re.split(r"\s+in\s+", resume.education[0].title, maxsplit=1)[-1].strip() if resume.education else ""
        _, graduated = _level(resume.education, date.today())
        who = f"{branch} {'Graduate' if graduated else 'Student'}" if branch else ""
        new_headline = f"{who} | Aspiring {target.role}" if who else f"Aspiring {target.role}"
        if change("headline", "Header", "new", "Added a headline under your name", after=new_headline):
            headline = new_headline

    fixed = fixed.model_copy(update={"summary": summary, "headline": headline})

    # ---- what only the student can add
    notes: list[str] = []
    if not resume.email.strip() or not resume.phone.strip():
        notes.append("Add your email and phone number at the top: recruiters need a way to reach you.")
    if not any(re.search(r"linkedin|github", link, re.I) for link in resume.links):
        notes.append("Add your LinkedIn and GitHub links: recruiters check them.")
    without_numbers = [
        e.title
        for e in [*resume.experience, *resume.projects]
        if e.title and not any(_HAS_NUMBER.search(b) for b in e.bullets)
    ]
    for title in without_numbers[:MAX_NUMBER_NOTES]:
        notes.append(f"Add a number to “{title}” (users, accuracy, time saved). We never invent one.")
    if not resume.projects and not resume.experience:
        notes.append("Add at least one project: it's what recruiters look at first in a student resume.")
    if target.mode == "general":
        notes.append("Paste a job description or pick a target role to tailor the skills and projects too.")

    have = claimed_after | {c for c in (_canonical(n) for n in added) if c}
    suggested = [_display(s) for s in target.wanted if s not in have and s not in implied and _technical(s)][
        :MAX_SUGGESTED
    ]

    template = "tech-compact" if _estimated_lines(fixed) > ONE_PAGE_LINES else "tech-classic"

    def scores(version: StructuredResume, skills_shown: set[str]) -> ScorePair:
        match, ats = score(version) if score else (None, None)
        role_have = len([s for s in target.must if s in skills_shown]) if target.mode == "role" else None
        role_total = len(target.must) if target.mode == "role" else None
        return ScorePair(match=match, ats=ats, role_have=role_have, role_total=role_total)

    return TailorResponse(
        mode=target.mode,
        role=target.role,
        resume=fixed,
        template=template,
        changes=changes,
        suggested_skills=suggested,
        notes=notes[:6],
        before=scores(resume, claimed),
        after=scores(fixed, have),
    )
