"""Rule-based ATS-friendliness check.

Applicant tracking systems differ, but they fail on the same things: text they
cannot extract (scans, images, odd fonts), layouts they read in the wrong
order (tables, text boxes, multiple columns), contact details hidden in page
headers, missing standard section headings, and missing keywords from the job
posting. This module checks for those problems and combines them into a
0-100 estimate. It is a transparent heuristic, not the output of a real ATS.

Scoring: each check has a weight; pass = full weight, warn = half, fail = 0,
skip = excluded (for example layout checks on edited text, which is exported
through an ATS-friendly template).
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from app.schemas.resume import AtsCheck, AtsReport, StructuredResume
from app.services.data_cleaning import clean_text
from app.services.parser import LayoutInfo
from app.services.resume_sections import BULLET_RE, EMAIL_RE, section_order

ACTION_VERBS = frozenset(
    """
    accelerated achieved administered analyzed architected assembled assessed audited automated balanced
    boosted built calculated championed coached collaborated completed conducted configured consolidated
    constructed consulted contributed coordinated created cut debugged decreased defined delivered deployed
    designed developed devised diagnosed directed drafted drove earned eliminated enabled engineered enhanced
    established evaluated executed expanded facilitated forecasted formulated founded generated grew guided
    handled headed identified implemented improved increased initiated innovated installed instructed
    integrated introduced investigated launched led maintained managed maximized mentored migrated minimized
    modeled modernized monitored negotiated optimized orchestrated organized oversaw participated performed
    pioneered planned prepared presented prioritized processed produced programmed proposed prototyped
    published raised redesigned reduced refactored resolved restructured revamped reviewed saved scaled
    secured simplified solved spearheaded standardized streamlined strengthened supervised supported surpassed
    taught tested trained transformed troubleshot upgraded utilized validated wrote
    """.split()
)

PHONE_HINT_RE = re.compile(r"(?:\+?\d[\d\s().-]{8,}\d)")
LINK_RE = re.compile(r"linkedin\.com|github\.com|gitlab\.com|behance\.net|portfolio|https?://", re.I)
NUMBER_RE = re.compile(r"\d")
UNUSUAL_CHAR_RE = re.compile(r"[☀-➿\U0001f300-\U0001faff-]")

WEIGHTS = {
    "readable_text": 3,
    "no_tables": 2,
    "single_column": 2,
    "no_images": 1,
    "no_text_boxes": 2,
    "contact_in_body": 2,
    "page_count": 1,
    "email": 3,
    "phone": 2,
    "profile_link": 1,
    "standard_sections": 3,
    "length": 2,
    "bullets": 2,
    "quantified": 2,
    "action_verbs": 1,
    "special_characters": 1,
    "keywords": 3,
    # Student / fresher mode
    "education_first": 1,
    "projects": 3,
    "internship": 2,
    "grades": 1,
    "github": 1,
    "one_page": 2,
}
GRADE_RE = re.compile(
    r"\b(?:c?gpa|sgpa|cpi|percentage|grade)\b|\b\d{1,2}(?:\.\d{1,2})?\s*%|\b\d\.\d{1,2}\s*/\s*(?:10|4)\b", re.I
)
INTERNSHIP_RE = re.compile(r"\b(?:intern(?:ship)?|trainee|training|apprentice(?:ship)?|virtual experience)\b", re.I)
STATUS_VALUE = {"pass": 1.0, "warn": 0.5, "fail": 0.0}


@dataclass
class _Check:
    id: str
    category: str
    title: str
    status: str
    detail: str
    tip: str = ""


def _bullets(text: str, resume: StructuredResume) -> list[str]:
    from_text = [BULLET_RE.sub("", line).strip() for line in text.splitlines() if BULLET_RE.match(line)]
    from_entries = [b for group in (resume.experience, resume.projects) for e in group for b in e.bullets]
    return from_entries if len(from_entries) >= len(from_text) else from_text


def check_ats(
    text: str,
    resume: StructuredResume,
    layout: LayoutInfo | None = None,
    job_skill_overlap: float | None = None,
    missing_skills: list[str] | None = None,
    student_mode: bool = False,
) -> AtsReport:
    """Run all checks and return the ATS report.

    Args:
        text: Resume text with line breaks (as extracted, or rendered from edits).
        resume: The same resume split into sections (app.services.resume_sections).
        layout: Layout facts of the uploaded file; None for edited text, which is
            exported through an ATS-friendly template, so layout checks are skipped.
        job_skill_overlap: Share of the job's skills found in the resume (0-1), if a
            job description was given.
        missing_skills: Job skills not found in the resume, for the keyword tip.
        student_mode: Add the student / fresher checklist (projects, internships,
            grades, education first, one page).
    """
    checks: list[_Check] = []
    add = checks.append
    words = len(clean_text(text).split())  # same count as the match-score warning
    edited = layout is None

    # Format and layout
    if edited:
        # Edited or pasted text is exported through resume_docx's template, which
        # is built to pass these checks. Counting them as passes (instead of
        # dropping them) keeps the score comparable with the uploaded file's.
        template = "The downloadable .docx uses a single-column template with no tables, images or text boxes."
        for cid, title in [
            ("readable_text", "Text can be read"),
            ("no_tables", "No tables"),
            ("single_column", "Single-column layout"),
            ("no_images", "No images or icons"),
            ("no_text_boxes", "No text boxes"),
            ("contact_in_body", "Contact details in the main text"),
        ]:
            add(_Check(cid, "format", title, "pass", template))
        pages = max(1, round(words / 500))
        if pages > 2:
            add(
                _Check(
                    "page_count",
                    "format",
                    "Length in pages",
                    "warn",
                    f"About {pages} pages when exported.",
                    "Aim for 1 page (students) or 2 pages at most.",
                )
            )
        else:
            add(_Check("page_count", "format", "Length in pages", "pass", f"About {pages} page(s) when exported."))
    else:
        if layout.unreadable_ratio > 0.02:
            add(
                _Check(
                    "readable_text",
                    "format",
                    "Text can be read",
                    "fail",
                    "Parts of the text came out as garbled characters, which usually means an embedded font "
                    "the parser can't map.",
                    "Re-export the PDF from Word or Google Docs with standard fonts, or upload a DOCX.",
                )
            )
        else:
            add(_Check("readable_text", "format", "Text can be read", "pass", "All text was extracted cleanly."))

        if layout.tables:
            add(
                _Check(
                    "no_tables",
                    "format",
                    "No tables",
                    "warn",
                    f"Found {layout.tables} table(s). Many ATS read tables cell by cell and scramble the order.",
                    "Replace tables with plain lines (e.g. 'Python, SQL, Docker' instead of a skills grid).",
                )
            )
        else:
            add(_Check("no_tables", "format", "No tables", "pass", "No tables found."))

        if layout.multi_column:
            add(
                _Check(
                    "single_column",
                    "format",
                    "Single-column layout",
                    "warn",
                    "The page looks like it has two columns. ATS often read straight across both columns, "
                    "mixing sections together.",
                    "Use a single-column layout; put the sidebar content into normal sections.",
                )
            )
        else:
            add(_Check("single_column", "format", "Single-column layout", "pass", "Text flows in a single column."))

        if layout.images:
            add(
                _Check(
                    "no_images",
                    "format",
                    "No images or icons",
                    "warn",
                    f"Found {layout.images} image(s). Text inside images, logos or icon fonts is invisible to an ATS.",
                    "Keep photos and icons out, and write contact details as plain text.",
                )
            )
        else:
            add(_Check("no_images", "format", "No images or icons", "pass", "No images found."))

        if layout.text_boxes:
            add(
                _Check(
                    "no_text_boxes",
                    "format",
                    "No text boxes",
                    "fail",
                    f"Found {layout.text_boxes} text box(es). Text boxes are often skipped entirely by ATS.",
                    "Move the text out of the text boxes into the normal page body.",
                )
            )
        else:
            add(_Check("no_text_boxes", "format", "No text boxes", "pass", "No text boxes found."))

        hf = layout.header_footer_text
        if hf and (EMAIL_RE.search(hf) or PHONE_HINT_RE.search(hf)):
            add(
                _Check(
                    "contact_in_body",
                    "format",
                    "Contact details in the main text",
                    "warn",
                    "Your email or phone number is in the page header/footer, which some ATS ignore.",
                    "Put your contact details in the first lines of the page body.",
                )
            )
        else:
            add(
                _Check(
                    "contact_in_body",
                    "format",
                    "Contact details in the main text",
                    "pass",
                    "Contact details are in the page body.",
                )
            )

        if layout.pages and layout.pages > 2:
            add(
                _Check(
                    "page_count",
                    "format",
                    "Length in pages",
                    "warn",
                    f"The resume is {layout.pages} pages.",
                    "Aim for 1 page (students) or 2 pages at most.",
                )
            )
        else:
            detail = f"{layout.pages} page(s)." if layout.pages else "Page count looks fine."
            add(_Check("page_count", "format", "Length in pages", "pass", detail))

    # Contact details
    if resume.email or EMAIL_RE.search(text):
        add(_Check("email", "content", "Email address", "pass", "Email address found."))
    else:
        add(
            _Check(
                "email",
                "content",
                "Email address",
                "fail",
                "No email address found.",
                "Add a professional email address at the top.",
            )
        )
    if resume.phone or PHONE_HINT_RE.search(text):
        add(_Check("phone", "content", "Phone number", "pass", "Phone number found."))
    else:
        add(
            _Check(
                "phone",
                "content",
                "Phone number",
                "warn",
                "No phone number found.",
                "Add a phone number recruiters can call.",
            )
        )
    if resume.links or LINK_RE.search(text):
        add(_Check("profile_link", "content", "LinkedIn / portfolio link", "pass", "Profile link found."))
    else:
        add(
            _Check(
                "profile_link",
                "content",
                "LinkedIn / portfolio link",
                "warn",
                "No LinkedIn, GitHub or portfolio link.",
                "Add your LinkedIn (and GitHub or portfolio for technical roles).",
            )
        )

    # Standard sections
    missing_sections = []
    if not (resume.experience or resume.projects):
        missing_sections.append("Experience or Projects")
    if not resume.education:
        missing_sections.append("Education")
    if not resume.skills:
        missing_sections.append("Skills")
    if not missing_sections:
        add(
            _Check(
                "standard_sections",
                "content",
                "Standard section headings",
                "pass",
                "Found Experience/Projects, Education and Skills sections.",
            )
        )
    else:
        status = "fail" if len(missing_sections) >= 2 else "warn"
        add(
            _Check(
                "standard_sections",
                "content",
                "Standard section headings",
                status,
                "Couldn't find: " + ", ".join(missing_sections) + ".",
                "Use plain headings such as 'Experience', 'Projects', 'Education' and 'Skills' so the ATS "
                "files your details correctly.",
            )
        )

    # Length
    if 250 <= words <= 1000:
        add(_Check("length", "content", "Resume length", "pass", f"{words} words."))
    elif 150 <= words < 250 or 1000 < words <= 1400:
        tip = "Add detail to projects and experience." if words < 250 else "Trim older or less relevant points."
        add(_Check("length", "content", "Resume length", "warn", f"{words} words; 250–1,000 is typical.", tip))
    else:
        tip = (
            "Describe your projects, experience and skills in more detail."
            if words < 150
            else "Cut it down to the most relevant 1–2 pages."
        )
        add(_Check("length", "content", "Resume length", "fail", f"{words} words; 250–1,000 is typical.", tip))

    # Bullets, numbers, verbs
    bullets = _bullets(text, resume)
    if len(bullets) >= 4:
        add(_Check("bullets", "content", "Bullet points", "pass", f"{len(bullets)} bullet points."))
    else:
        add(
            _Check(
                "bullets",
                "content",
                "Bullet points",
                "warn" if bullets else "fail",
                f"{len(bullets)} bullet point(s) found.",
                "Describe each role or project with 2–5 short bullet points.",
            )
        )

    quantified = sum(bool(NUMBER_RE.search(b)) for b in bullets)
    if quantified >= 3:
        add(
            _Check(
                "quantified", "content", "Measurable results", "pass", f"{quantified} bullet points include numbers."
            )
        )
    else:
        add(
            _Check(
                "quantified",
                "content",
                "Measurable results",
                "warn" if quantified else "fail",
                f"{quantified} bullet point(s) include numbers.",
                "Show impact with numbers: users, %, time saved, team size, accuracy.",
            )
        )

    if bullets:
        verb_share = sum(
            (b.split()[0].lower().strip(",.") if b.split() else "") in ACTION_VERBS for b in bullets
        ) / len(bullets)
        if verb_share >= 0.5:
            add(
                _Check(
                    "action_verbs",
                    "content",
                    "Starts with action verbs",
                    "pass",
                    f"{verb_share:.0%} of bullet points start with an action verb.",
                )
            )
        else:
            add(
                _Check(
                    "action_verbs",
                    "content",
                    "Starts with action verbs",
                    "warn",
                    f"Only {verb_share:.0%} of bullet points start with an action verb.",
                    "Start bullets with verbs like Built, Led, Improved, Automated, Designed.",
                )
            )
    else:
        add(_Check("action_verbs", "content", "Starts with action verbs", "skip", "No bullet points to check."))

    unusual = len(UNUSUAL_CHAR_RE.findall(text))
    if unusual:
        add(
            _Check(
                "special_characters",
                "content",
                "Plain characters",
                "warn",
                f"{unusual} emoji or icon character(s) found; ATS may drop or garble them.",
                "Replace icons and emoji with plain text labels.",
            )
        )
    else:
        add(_Check("special_characters", "content", "Plain characters", "pass", "No emoji or icon characters."))

    # Keywords
    if job_skill_overlap is None:
        add(_Check("keywords", "keywords", "Job keywords", "skip", "Add a job description to check keywords."))
    else:
        pct = job_skill_overlap
        missing = ", ".join((missing_skills or [])[:5])
        tip = f"Add the skills you genuinely have from the posting: {missing}." if missing else ""
        if pct >= 0.6:
            add(
                _Check(
                    "keywords",
                    "keywords",
                    "Job keywords",
                    "pass",
                    f"Your resume mentions {pct:.0%} of the job's skills.",
                    tip,
                )
            )
        elif pct >= 0.3:
            add(
                _Check(
                    "keywords",
                    "keywords",
                    "Job keywords",
                    "warn",
                    f"Your resume mentions {pct:.0%} of the job's skills.",
                    tip,
                )
            )
        else:
            add(
                _Check(
                    "keywords",
                    "keywords",
                    "Job keywords",
                    "fail",
                    f"Your resume mentions only {pct:.0%} of the job's skills.",
                    tip,
                )
            )

    if student_mode:
        checks.extend(_student_checks(text, resume, words))

    scored = [c for c in checks if c.status != "skip"]
    total = sum(WEIGHTS[c.id] for c in scored)
    score = round(100 * sum(WEIGHTS[c.id] * STATUS_VALUE[c.status] for c in scored) / total, 1) if total else 0.0
    verdict = "ATS-friendly" if score >= 80 else "Needs a few fixes" if score >= 60 else "Needs work"
    return AtsReport(score=score, verdict=verdict, checks=[AtsCheck(**c.__dict__) for c in checks])


def _student_checks(text: str, resume: StructuredResume, words: int) -> list[_Check]:
    """Checklist for students and freshers, whose resumes are judged differently."""
    out: list[_Check] = []

    order = section_order(text)
    if "education" in order and ("experience" not in order or order.index("education") < order.index("experience")):
        out.append(
            _Check("education_first", "student", "Education near the top", "pass", "Education comes before experience.")
        )
    elif "education" in order:
        out.append(
            _Check(
                "education_first",
                "student",
                "Education near the top",
                "warn",
                "Education comes after experience.",
                "As a student, put Education right after your summary; it's your strongest credential.",
            )
        )
    else:
        out.append(
            _Check(
                "education_first",
                "student",
                "Education near the top",
                "fail",
                "No Education section found.",
                "Add your degree, college, years and CGPA.",
            )
        )

    projects = len(resume.projects)
    if projects >= 2:
        out.append(_Check("projects", "student", "Projects", "pass", f"{projects} projects listed."))
    else:
        out.append(
            _Check(
                "projects",
                "student",
                "Projects",
                "warn" if projects == 1 else "fail",
                f"{projects} project(s) listed.",
                "List 2–4 projects with the tech you used and a measurable result; they replace work experience.",
            )
        )

    if resume.experience or INTERNSHIP_RE.search(text):
        out.append(
            _Check(
                "internship",
                "student",
                "Internship or training",
                "pass",
                "Internship, training or work experience found.",
            )
        )
    else:
        out.append(
            _Check(
                "internship",
                "student",
                "Internship or training",
                "warn",
                "No internship, training or work experience found.",
                "Add internships, virtual internships, freelance work, hackathons or a leadership role in a club.",
            )
        )

    # Percentages elsewhere ("cut costs by 40%") are not grades: only look in Education
    education_text = " ".join(f"{e.title} {e.subtitle} {' '.join(e.bullets)}" for e in resume.education)
    if GRADE_RE.search(education_text) or re.search(r"\b(?:c?gpa|sgpa|cpi)\b", text, re.I):
        out.append(_Check("grades", "student", "Grades", "pass", "CGPA / percentage found."))
    else:
        out.append(
            _Check(
                "grades",
                "student",
                "Grades",
                "warn",
                "No CGPA, GPA or percentage found.",
                "Add your CGPA if it's good (around 7/10 or 3/4 and above), plus relevant coursework.",
            )
        )

    links = " ".join(resume.links) + " " + text
    if re.search(r"github\.com|gitlab\.com|portfolio|behance\.net|kaggle\.com", links, re.I):
        out.append(_Check("github", "student", "GitHub / portfolio", "pass", "GitHub or portfolio link found."))
    else:
        out.append(
            _Check(
                "github",
                "student",
                "GitHub / portfolio",
                "warn",
                "No GitHub or portfolio link.",
                "Link your GitHub (or Kaggle/Behance) so recruiters can see your projects.",
            )
        )

    if words <= 650:
        out.append(_Check("one_page", "student", "Fits on one page", "pass", f"{words} words, about one page."))
    else:
        out.append(
            _Check(
                "one_page",
                "student",
                "Fits on one page",
                "warn" if words <= 900 else "fail",
                f"{words} words, more than one page.",
                "Freshers should keep it to one page: cut older school details and weaker points.",
            )
        )
    return out
