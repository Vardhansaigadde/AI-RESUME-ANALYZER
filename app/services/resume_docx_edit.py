"""Apply "Generate a fixed resume" changes inside the student's own Word file.

Only the text changes: fonts, sizes, colours, spacing, columns and layout stay
as the student designed them. Each change is matched to the paragraph that
holds the original text (in the body, tables and text boxes), and the new text
reuses that paragraph's formatting. New lines (a Tech line, a summary that
didn't exist) are copies of a nearby paragraph, so they look like the rest.

Layout-level changes (regrouping skills, reordering projects, a new headline)
are left out on purpose: they would change the student's design.
"""

from __future__ import annotations

from copy import deepcopy
from io import BytesIO
import re

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

from app.schemas.resume import StructuredResume
from app.schemas.tailor import TailorResponse
from app.services.resume_sections import BULLET_GLYPHS, _match_heading
from app.services.resume_tailor import fix_date, typed_skills

LAYOUT_CHANGES = {"skills-group", "projects-order", "headline"}
_GLYPHS = re.compile(rf"^[\s{re.escape(BULLET_GLYPHS)}\-*–]+")


def _norm(text: str) -> str:
    text = _GLYPHS.sub("", text or "")
    return re.sub(r"[\s.]+$", "", re.sub(r"\s+", " ", text).strip()).lower()


class _Doc:
    def __init__(self, data: bytes):
        self.doc = Document(BytesIO(data))

    def paragraphs(self) -> list[Paragraph]:
        """Every paragraph, including those in tables and text boxes, in reading order."""
        body = self.doc.element.body
        return [Paragraph(p, self.doc._body) for p in body.iter(qn("w:p"))]

    def find(self, text: str, prefix: bool = False) -> Paragraph | None:
        want = _norm(text)
        if not want:
            return None
        for par in self.paragraphs():
            have = _norm(par.text)
            if have == want or (prefix and have.startswith(want)):
                return par
        return None

    def save(self) -> bytes:
        out = BytesIO()
        self.doc.save(out)
        return out.getvalue()


def _runs(par: Paragraph) -> list:
    """Text runs, including those inside hyperlinks."""
    return [r for r in par._p.iter(qn("w:r")) if r.find(qn("w:t")) is not None]


def _set_text(par: Paragraph, text: str) -> None:
    """Replace the paragraph's text, keeping the formatting of its first text run (and any bullet glyph run)."""
    runs = _runs(par)
    keep = next(
        (r for r in runs if "".join(t.text or "" for t in r.iter(qn("w:t"))).strip(BULLET_GLYPHS + " \t")), None
    )
    if keep is None:
        par.add_run(text)
        return
    texts = list(keep.iter(qn("w:t")))
    glyph = _GLYPHS.match("".join(t.text or "" for t in texts))
    if glyph and glyph.group(0).strip():
        text = glyph.group(0) + text  # "• " typed in the same run as the text
    texts[0].text = text
    texts[0].set(qn("xml:space"), "preserve")
    for extra in texts[1:]:
        extra.getparent().remove(extra)
    after = False
    for run in runs:
        if run is keep:
            after = True
            continue
        if after:
            run.getparent().remove(run)


def _append_text(par: Paragraph, text: str) -> None:
    runs = _runs(par)
    if not runs:
        par.add_run(text)
        return
    new = deepcopy(runs[-1])
    for extra in list(new.iter(qn("w:t")))[1:]:
        extra.getparent().remove(extra)
    t = new.find(qn("w:t"))
    t.text = text
    t.set(qn("xml:space"), "preserve")
    runs[-1].addnext(new)


def _copy_near(anchor: Paragraph, text: str, before: bool = False, plain: bool = False) -> Paragraph:
    """A new paragraph styled like ``anchor``, placed right after (or before) it."""
    new_p = deepcopy(anchor._p)
    if before:
        anchor._p.addprevious(new_p)
    else:
        anchor._p.addnext(new_p)
    par = Paragraph(new_p, anchor._parent)
    if plain:
        ppr = new_p.find(qn("w:pPr"))
        if ppr is not None and ppr.find(qn("w:numPr")) is not None:
            ppr.remove(ppr.find(qn("w:numPr")))
    _set_text(par, text)
    if plain:
        for run in _runs(par):
            rpr = run.find(qn("w:rPr"))
            if rpr is not None:
                for tag in ("w:b", "w:bCs"):
                    for el in rpr.findall(qn(tag)):
                        rpr.remove(el)
    return par


def _section_paragraphs(doc: _Doc, section: str) -> tuple[Paragraph | None, list[Paragraph]]:
    """The heading of a section ('skills', 'summary', ...) and the paragraphs under it."""
    heading, body = None, []
    for par in doc.paragraphs():
        found = _match_heading(par.text)
        if heading is None:
            if found and found[0] == section:
                heading = par
            continue
        if found:
            break
        if par.text.strip():
            body.append(par)
    return heading, body


def apply_to_docx(data: bytes, original: StructuredResume, fixed: TailorResponse) -> tuple[bytes, dict[str, list[str]]]:
    """The student's Word file with the applied changes, and which changes were applied, missed or left to layout."""
    doc = _Doc(data)
    report: dict[str, list[str]] = {"applied": [], "missed": [], "layout": []}

    def done(cid: str, ok: bool) -> None:
        report["applied" if ok else "missed"].append(cid)

    skill_ids = []
    # Tech lines first: they find their place by the original bullet text, before bullets change
    ordered = sorted(fixed.changes, key=lambda c: not c.id.startswith("tech:"))
    for change in ordered:
        if not change.applied:
            continue
        cid = change.id
        if cid in LAYOUT_CHANGES:
            report["layout"].append(cid)
        elif cid.startswith("bullet:"):
            _, section, i, j = cid.split(":")
            par = doc.find(getattr(original, section)[int(i)].bullets[int(j)])
            if par is not None:
                _set_text(par, change.after)
            done(cid, par is not None)
        elif cid.startswith("tech:"):
            _, section, i = cid.split(":")
            entry = getattr(original, section)[int(i)]
            if entry.subtitle.strip() and (par := doc.find(entry.subtitle)) is not None:
                _append_text(par, f" | {change.after}")
                done(cid, True)
            elif entry.bullets and (par := doc.find(entry.bullets[0])) is not None:
                _copy_near(par, change.after, before=True)
                done(cid, True)
            elif (par := doc.find(entry.title, prefix=True)) is not None:
                _copy_near(par, change.after, plain=True)
                done(cid, True)
            else:
                done(cid, False)
        elif cid == "summary":
            done(cid, _apply_summary(doc, original.summary, fixed.resume.summary))
        elif cid.startswith("skills-"):
            skill_ids.append(cid)
        elif cid == "dates":
            done(cid, _apply_dates(doc, original))

    if skill_ids:
        new = [
            n
            for n in typed_skills(fixed.resume.skills)
            if n.lower() not in {t.lower() for t in typed_skills(original.skills)}
        ]
        _, body = _section_paragraphs(doc, "skills")
        ok = bool(new) and bool(body)
        if ok:
            _append_text(body[-1], ", " + ", ".join(new))
        for cid in skill_ids:
            done(cid, ok)

    return doc.save(), report


def _apply_summary(doc: _Doc, old: str, new: str) -> bool:
    if old.strip():
        whole = _norm(old)
        parts = [p for p in doc.paragraphs() if len(_norm(p.text)) >= 15 and _norm(p.text) in whole]
        if not parts:
            return False
        _set_text(parts[0], new)
        for extra in parts[1:]:
            extra._p.getparent().remove(extra._p)
        return True
    # No summary yet: add a heading and paragraph above the first section, styled like the resume's own
    pars = doc.paragraphs()
    first = next((i for i, p in enumerate(pars) if _match_heading(p.text)), None)
    if first is None:
        return False
    heading = pars[first]
    body = next((p for p in pars[first + 1 :] if p.text.strip() and not _match_heading(p.text)), None)
    new_heading = deepcopy(heading._p)
    heading._p.addprevious(new_heading)
    _set_text(Paragraph(new_heading, heading._parent), "SUMMARY" if heading.text.strip().isupper() else "Summary")
    new_body = deepcopy((body or heading)._p)
    heading._p.addprevious(new_body)
    ppr = new_body.find(qn("w:pPr"))
    if ppr is not None and ppr.find(qn("w:numPr")) is not None:
        ppr.remove(ppr.find(qn("w:numPr")))  # a paragraph, not a bullet
    _set_text(Paragraph(new_body, heading._parent), new)
    return True


def _apply_dates(doc: _Doc, original: StructuredResume) -> bool:
    entries = [*original.experience, *original.projects, *original.education]
    changed = [(e.date, fix_date(e.date)) for e in entries if e.date and fix_date(e.date) != e.date]
    hits = 0
    for old, new in changed:
        for par in doc.paragraphs():
            replaced = False
            for run in _runs(par):
                for t in run.iter(qn("w:t")):
                    if t.text and old in t.text:
                        t.text = t.text.replace(old, new)
                        replaced = True
            if replaced:
                hits += 1
                break
    return hits > 0
