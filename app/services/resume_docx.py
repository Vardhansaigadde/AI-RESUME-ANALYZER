"""Render a StructuredResume as an ATS-friendly Word document.

The template avoids everything ATS commonly misread: one column, no tables,
text boxes, images, headers or footers; standard section headings; contact
details as plain text in the body; real Word bullet lists; a standard font.
"""

from __future__ import annotations

import io

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

from app.schemas.resume import ResumeEntry, StructuredResume

FONT = "Calibri"
INK = RGBColor(0x1F, 0x23, 0x28)
MUTED = RGBColor(0x55, 0x5B, 0x63)


def _set_base_style(document: Document) -> None:
    style = document.styles["Normal"]
    style.font.name = FONT
    style.font.size = Pt(10.5)
    style.font.color.rgb = INK
    style.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    style.paragraph_format.space_after = Pt(2)
    for section in document.sections:
        section.top_margin = section.bottom_margin = Pt(48)
        section.left_margin = section.right_margin = Pt(54)


def _bottom_border(paragraph) -> None:
    p_pr = paragraph._p.get_or_add_pPr()
    borders = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for key, value in {"w:val": "single", "w:sz": "6", "w:space": "1", "w:color": "B8BEC6"}.items():
        bottom.set(qn(key), value)
    borders.append(bottom)
    p_pr.append(borders)


def _heading(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    paragraph.paragraph_format.space_before = Pt(10)
    paragraph.paragraph_format.space_after = Pt(4)
    run = paragraph.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(11)
    _bottom_border(paragraph)


def _bullet(document: Document, text: str) -> None:
    paragraph = document.add_paragraph(text.strip(), style="List Bullet")
    paragraph.paragraph_format.space_after = Pt(1)


def _entries(document: Document, heading: str, entries: list[ResumeEntry]) -> None:
    entries = [e for e in entries if e.title.strip() or e.subtitle.strip() or any(b.strip() for b in e.bullets)]
    if not entries:
        return
    _heading(document, heading)
    for entry in entries:
        if entry.title.strip():
            title = document.add_paragraph()
            title.paragraph_format.space_before = Pt(4)
            title.paragraph_format.space_after = Pt(0)
            title.add_run(entry.title.strip()).bold = True
        if entry.subtitle.strip():
            subtitle = document.add_paragraph()
            run = subtitle.add_run(entry.subtitle.strip())
            run.italic = True
            run.font.color.rgb = MUTED
        for bullet in entry.bullets:
            if bullet.strip():
                _bullet(document, bullet)


def build_resume_docx(resume: StructuredResume) -> bytes:
    """Return the resume as .docx bytes."""
    document = Document()
    _set_base_style(document)

    if resume.name.strip():
        name = document.add_paragraph()
        name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = name.add_run(resume.name.strip())
        run.bold = True
        run.font.size = Pt(18)
    if resume.headline.strip():
        headline = document.add_paragraph()
        headline.alignment = WD_ALIGN_PARAGRAPH.CENTER
        headline.add_run(resume.headline.strip()).font.color.rgb = MUTED
    contact = " | ".join(x.strip() for x in [resume.email, resume.phone, resume.location, *resume.links] if x.strip())
    if contact:
        line = document.add_paragraph()
        line.alignment = WD_ALIGN_PARAGRAPH.CENTER
        line.add_run(contact).font.size = Pt(9.5)

    if resume.summary.strip():
        _heading(document, "Summary")
        document.add_paragraph(resume.summary.strip())
    skills = [s.strip() for s in resume.skills if s.strip()]
    if skills:
        _heading(document, "Skills")
        document.add_paragraph(", ".join(skills))
    _entries(document, "Experience", resume.experience)
    _entries(document, "Projects", resume.projects)
    _entries(document, "Education", resume.education)
    for heading, items in [("Certifications", resume.certifications), ("Achievements", resume.achievements)]:
        items = [i for i in items if i.strip()]
        if items:
            _heading(document, heading)
            for item in items:
                _bullet(document, item)
    for extra in resume.additional:
        items = [i for i in extra.items if i.strip()]
        if extra.heading.strip() and items:
            _heading(document, extra.heading)
            for item in items:
                _bullet(document, item)

    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()
