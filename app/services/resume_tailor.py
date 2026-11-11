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
from app.schemas.tailor import CatalogSkill, LikelySkill, ScorePair, TailorChange, TailorResponse
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
    _join,
    _kind_of,
    _lower_first,
    _sentence,
    _starts_with_verb,
)
from app.services.resume_sections import render_resume_text
from app.services.role_gap import target_roles
from app.services.score_integrity import implied_by
from app.services.skill_extractor import extract_skills
from app.services.skills_inventory import DOMAIN_GROUP, SOFT_GROUP, group_of

MAX_SUMMARY_SKILLS = 4
MAX_SUGGESTED = 10
MAX_NUMBER_NOTES = 3
MAX_NOTES = 7
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


_SHARED = re.compile(
    r"^(i\s+|we\s+)?(worked on|working on|helped|helping|assisted|assisting|"
    r"(?:was |were )?involved in)\s+(?:(?:to|in|with)\s+)?",
    re.I,
)
_RESPONSIBLE = re.compile(r"^(i\s+|we\s+)?(responsible for|in charge of)\s+", re.I)
_MADE = re.compile(r"^(i\s+|we\s+)?(made|created a project (?:on|for)|did)\s+", re.I)
_LEAVE = re.compile(r"^(i\s+|we\s+)?(was|were|participated in|took part in)\b", re.I)
# Words that show the student did it themselves, so "worked on" may become "Built"
_OWNED = re.compile(
    r"\b(independently|single[- ]handedly|solo|by myself|on my own|from scratch|end[- ]to[- ]end|my own)\b", re.I
)
BARE_VERBS = set(PAST_TENSE) | {
    "test", "code", "maintain", "prepare", "improve", "fix", "debug", "set", "run", "research", "document",
    "collect", "clean", "update", "integrate", "migrate", "review", "edit", "map", "support", "handle",
    "configure", "monitor", "optimize", "optimise", "refactor", "scrape", "visualize", "visualise", "model",
}  # fmt: skip
_IRREGULAR_PAST = {
    "set": "Set",
    "run": "Ran",
    "fix": "Fixed",
    "map": "Mapped",
    "debug": "Debugged",
    "scrape": "Scraped",
}


def _to_gerund(verb: str) -> str:
    """build -> building, write -> writing, plan -> planning."""
    v = verb.lower()
    if v.endswith("ie"):
        return v[:-2] + "ying"
    if v.endswith("e") and not v.endswith("ee"):
        return v[:-1] + "ing"
    if len(v) <= 4 and v[0] not in "aeiou" and re.search(r"[^aeiou][aeiou][^aeiouwxy]$", v):
        return v + v[-1] + "ing"
    return v + "ing"


def _to_past(verb: str) -> str:
    """build -> Built, test -> Tested, plan -> Planned."""
    v = verb.lower()
    if v in PAST_TENSE:
        return PAST_TENSE[v]
    if v in _IRREGULAR_PAST:
        return _IRREGULAR_PAST[v]
    if v.endswith("e"):
        return (v + "d").capitalize()
    if len(v) <= 4 and v[0] not in "aeiou" and re.search(r"[^aeiou][aeiou][^aeiouwxy]$", v):
        return (v + v[-1] + "ed").capitalize()
    return (v + "ed").capitalize()


def _gerund_to_past(word: str) -> str | None:
    """'managing' -> 'Managed', 'writing' -> 'Wrote', 'planning' -> 'Planned'."""
    low = word.lower()
    if not low.endswith("ing") or len(low) < 6:
        return None
    stem = low[:-3]
    for base in (stem, stem + "e", stem[:-1] if len(stem) > 2 and stem[-1] == stem[-2] else None):
        if base and (base in PAST_TENSE or base in BARE_VERBS):
            return _to_past(base)
    return (stem + "ed").capitalize()


def _as_action(phrase: str, context: str) -> str:
    """'build a site' / 'building a site' -> 'Built a site'; 'a site' -> 'Built a site' (by kind)."""
    head, _, tail = phrase.partition(" ")
    tail = f" {tail}" if tail else ""
    if head.lower() in BARE_VERBS:
        return _to_past(head) + tail
    if _gerund_to_past(head):
        return _gerund_to_past(head) + tail
    return f"{LEAD_VERBS[_kind_of(context)][0]} {_lower_first(phrase)}"


def _as_contribution(phrase: str) -> str:
    """'build a site' -> 'Contributed to building a site'; 'the testing' -> 'Contributed to the testing'."""
    head, _, tail = phrase.partition(" ")
    tail = f" {tail}" if tail else ""
    if head.lower() in BARE_VERBS:
        return f"Contributed to {_to_gerund(head)}{tail}"
    return f"Contributed to {_lower_first(phrase)}"


def improve_bullet(text: str, title: str = "") -> str:
    """A stronger, still honest version of a weak bullet, or the bullet unchanged when it's already fine.

    "Worked on" and "helped" only say the student took part, so they become "Contributed to ..."
    unless the bullet itself says they did it on their own. "Responsible for" says they owned it.
    """
    bullet = re.sub(r"^[\s•●▪◦*\-–]+", "", text or "").strip()
    if not bullet or _TECH_PREFIX.match(bullet) or _LEAVE.match(bullet):
        return text
    context = f"{title} {bullet}"

    if shared := _SHARED.match(bullet):
        phrase = bullet[shared.end() :].strip()
        if not phrase:
            return text
        team = (shared.group(1) or "").strip().lower() == "we" or shared.group(2).lower().startswith(("help", "assist"))
        if _OWNED.search(bullet) and not team:
            new = _as_action(phrase, context)
        else:
            new = _as_contribution(phrase)
    elif owned := _RESPONSIBLE.match(bullet):
        phrase = bullet[owned.end() :].strip()
        if not phrase:
            return text
        head = phrase.split(" ", 1)[0]
        if head.lower() in BARE_VERBS or _gerund_to_past(head):
            new = _as_action(phrase, context)
        else:
            new = f"Managed {_lower_first(phrase)}"
    elif made := _MADE.match(bullet):
        phrase = bullet[made.end() :].strip()
        if not phrase:
            return text
        verb = made.group(2).lower()
        new = f"Completed {_lower_first(phrase)}" if verb == "did" else f"Built {_lower_first(phrase)}"
    else:
        first, _, rest = bullet.partition(" ")
        rest = f" {rest}" if rest else ""
        if first.lower() in BARE_VERBS and first[:1].islower():
            new = _to_past(first) + rest
        elif _gerund_to_past(first) and not _starts_with_verb(first):
            new = _gerund_to_past(first) + rest
        else:
            new = bullet[:1].upper() + bullet[1:]
    new = _proper_names(_sentence(_format_numbers(new)))
    # Only a real improvement counts; capitalisation or a full stop alone keeps the original
    return new if _norm(new) != _norm(bullet) else text


def _proper_names(text: str) -> str:
    """Write one-word skills and known names properly inside a sentence (html -> HTML, python -> Python)."""
    for skill in extract_skills(clean_text(text)):
        named = skill in DISPLAY or any(skill in members for _, members in SKILL_GROUPS)
        if not named or (" " in skill and skill not in DISPLAY):
            continue  # "database", "machine learning" read fine in lower case; only names get capitals
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


def skill_catalog(names: list[str], target: _Target) -> list[CatalogSkill]:
    """Every candidate skill with its row, in display order (group order, most wanted first).

    The browser builds the skills section from this when the student keeps or undoes
    changes, so it matches what the server would build exactly.
    """
    rows: dict[str, list[str]] = {}
    for name in names:
        canonical = _canonical(name)
        keys = {name.lower(), canonical or ""}
        label = next((g for g, members in SKILL_GROUPS if keys & members), "Other")
        rows.setdefault(label, []).append(name)
    out: list[CatalogSkill] = []
    for label in [g for g, _ in SKILL_GROUPS] + ["Other"]:
        for name in sorted(rows.get(label, []), key=lambda n: -target.weight(_canonical(n))):
            out.append(CatalogSkill(name=name, group=label))
    return out


def grouped_rows(catalog: list[CatalogSkill], names: list[str]) -> list[str]:
    """'Languages: Python', 'SQL', 'Frameworks & Web: Flask', ... for the given names."""
    wanted = {n.lower() for n in names}
    out: list[str] = []
    last = None
    for item in catalog:
        if item.name.lower() not in wanted:
            continue
        out.append(f"{item.group}: {item.name}" if item.group != last else item.name)
        last = item.group
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


# ---------------------------------------------------------------------------- Indian resume habits
_PERSONAL = re.compile(
    r"\b(date of birth|d\.\s?o\.\s?b\.?|dob|father'?s name|mother'?s name|marital status|religion|caste|"
    r"passport (no|number)|gender)\b",
    re.I,
)
_DECLARATION = re.compile(r"\b(declaration|i hereby declare)\b", re.I)


def _habit_notes(text: str) -> list[str]:
    notes = []
    if _PERSONAL.search(text):
        notes.append(
            "Remove personal details like your photo, date of birth, father's name, marital status and religion: "
            "recruiters and ATS don't need them, and they can lead to bias."
        )
    if _DECLARATION.search(text):
        notes.append(
            "Remove the Declaration (“I hereby declare…”): ATS and recruiters skip it, and that space is better "
            "used for a project."
        )
    return notes


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
    Each change carries a ``patch`` so the browser can keep or undo it instantly, and the
    response's ``skill_catalog`` lets it rebuild the skills section the same way.
    ``score(resume) -> (match, ats)`` is injected so tests can run without the models.
    """
    skipped, accepted = set(skip or []), set(accept or [])
    changes: list[TailorChange] = []

    def change(
        cid: str, section: str, kind: str, title: str, before: str = "", after: str = "", patch: dict | None = None
    ) -> bool:
        suggestion = kind == "suggestion"
        applied = cid in accepted if suggestion else cid not in skipped
        changes.append(
            TailorChange(
                id=cid,
                section=section,
                kind=kind,
                title=title,
                before=before,
                after=after,
                applied=applied,
                patch=patch or {},
            )
        )
        return applied

    original_text = render_resume_text(resume)
    claimed = extract_skills(clean_text(original_text))
    target = _Target(job_text, target_role, claimed)

    # ---- skills: used-but-unlisted ones are added; likely-known and wanted ones are only offered
    typed = typed_skills(resume.skills)
    typed_canonical = {c for c in (_canonical(t) for t in typed) if c}
    from_entries = sorted((s for s in claimed - typed_canonical if _technical(s)), key=lambda s: (-target.weight(s), s))
    implied = implied_by(claimed)
    confirmed = [c.strip() for c in confirmed_skills or [] if c.strip()]
    confirmed_canonical = {c for c in (_canonical(n) for n in confirmed) if c} | {n.lower() for n in confirmed}

    used_names = [_display(s, original_text) for s in from_entries]
    likely = [
        LikelySkill(skill=_display(s), because=_display(implied[s], original_text))
        for s in target.wanted
        if s in implied and s not in claimed and s not in confirmed_canonical
    ]
    have_now = claimed | confirmed_canonical
    suggested = [_display(s) for s in target.wanted if s not in have_now and s not in implied and _technical(s)][
        :MAX_SUGGESTED
    ]

    names = list(typed)
    added: list[str] = []

    def add(new_names: list[str]) -> None:
        for name in new_names:
            if name.lower() not in {n.lower() for n in names}:
                names.append(name)
                added.append(name)

    if used_names and change(
        "skills-used",
        "Skills",
        "added",
        "Added skills you used in your projects or jobs",
        after=", ".join(used_names),
        patch={"add": used_names},
    ):
        add(used_names)
    if confirmed:
        if change(
            "skills-confirmed",
            "Skills",
            "added",
            "Added the skills you confirmed",
            after=", ".join(confirmed),
            patch={"add": confirmed},
        ):
            add(confirmed)

    candidates = list(dict.fromkeys([*typed, *used_names, *confirmed, *(x.skill for x in likely), *suggested]))
    catalog = skill_catalog(candidates, target)
    grouped = grouped_rows(catalog, names)
    if names and [s.lower() for s in grouped] != [s.lower() for s in resume.skills]:
        title = "Grouped your skills" + (", with the most wanted first" if target.wanted else "")
        skills = grouped if change("skills-group", "Skills", "reordered", title) else [*resume.skills, *added]
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
            patch={"order": ranked},
        ):
            order = ranked

    # ---- entries: weak bullets, Tech lines, dates
    date_patch = [
        {"section": section, "index": i, "date": fix_date(e.date)}
        for section in ("experience", "projects", "education")
        for i, e in enumerate(getattr(resume, section))
        if fix_date(e.date) != e.date
    ]
    fix_dates = bool(date_patch) and change(
        "dates", "Dates", "fixed", "Used one date format (Jun 2024 – Aug 2024)", patch={"entries": date_patch}
    )

    def fix_entries(section: str, label: str, entries: list[ResumeEntry], indexes: list[int]) -> list[ResumeEntry]:
        fixed = []
        for i in indexes:
            entry = entries[i]
            name = entry.title or label
            bullets = []
            for j, bullet in enumerate(entry.bullets):
                better = improve_bullet(bullet, entry.title)
                if better != bullet and change(
                    f"bullet:{section}:{i}:{j}",
                    label,
                    "rewrote",
                    f"Stronger bullet in “{name}”",
                    bullet,
                    better,
                    patch={"section": section, "index": i, "bullet": j, "text": better},
                ):
                    bullets.append(better)
                else:
                    bullets.append(bullet)
            update: dict = {"bullets": bullets}
            tech = tech_line(entry, target, names)
            if tech:
                line = f"Tech: {', '.join(tech)}"
                subtitle = f"{entry.subtitle} | {line}" if entry.subtitle.strip() else line
                if change(
                    f"tech:{section}:{i}",
                    label,
                    "added",
                    f"Added a Tech line to “{name}”",
                    after=line,
                    patch={"section": section, "index": i, "subtitle": subtitle},
                ):
                    update["subtitle"] = subtitle
            if fix_dates:
                update["date"] = fix_date(entry.date)
            fixed.append(entry.model_copy(update=update))
        return fixed

    experience = fix_entries("experience", "Experience", resume.experience, list(range(len(resume.experience))))
    projects = fix_entries("projects", "Projects", resume.projects, order)
    education = [e.model_copy(update={"date": fix_date(e.date)}) if fix_dates else e for e in resume.education]

    # ---- summary and headline (claims only skills the resume shows or the student confirmed)
    pool = [s for s in target.wanted if s in have_now and _technical(s)] or sorted(
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
            patch={"summary": ours},
        ):
            summary = ours
    elif _norm(ours) != _norm(resume.summary) and change(
        "summary",
        "Summary",
        "rewrote" if resume.summary.strip() else "new",
        f"Wrote a summary for {for_what}",
        resume.summary.strip(),
        ours,
        patch={"summary": ours},
    ):
        summary = ours

    headline = resume.headline
    if not headline.strip() and target.role:
        branch = re.split(r"\s+in\s+", resume.education[0].title, maxsplit=1)[-1].strip() if resume.education else ""
        _, graduated = _level(resume.education, date.today())
        who = f"{branch} {'Graduate' if graduated else 'Student'}" if branch else ""
        new_headline = f"{who} | Aspiring {target.role}" if who else f"Aspiring {target.role}"
        if change(
            "headline",
            "Header",
            "new",
            "Added a headline under your name",
            after=new_headline,
            patch={"headline": new_headline},
        ):
            headline = new_headline

    fixed = fixed.model_copy(update={"summary": summary, "headline": headline})

    # ---- what only the student can add or remove
    notes: list[str] = _habit_notes(original_text)
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

    template = "tech-compact" if _estimated_lines(fixed) > ONE_PAGE_LINES else "tech-classic"
    shown_after = have_now | {c for c in (_canonical(n) for n in added) if c}

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
        likely_skills=likely,
        suggested_skills=suggested,
        skill_catalog=catalog,
        notes=notes[:MAX_NOTES],
        before=scores(resume, claimed),
        after=scores(fixed, shown_after),
    )
