"""Generate a fixed resume: job, role and general modes, undo, kept summaries, and in-place Word edits."""

import io
import json
import unittest

from docx import Document
from docx.shared import Pt, RGBColor
from fastapi.testclient import TestClient

from app.main import app
from app.services.resume_sections import parse_resume
from app.services.resume_tailor import fix_date, good_summary, improve_bullet, tailor_resume

client = TestClient(app)

LINES = [
    ("Ravi Kumar", True),
    ("ravi@example.com | 98765 43210", False),
    ("EDUCATION", True),
    ("B.Tech in Computer Science and Engineering", True),
    ("Aditya University · CGPA 8.1/10", False),
    ("2022-2026", False),
    ("PROJECTS", True),
    ("Weather App", True),
    ("• worked on a weather app using html css and javascript", False),
    ("• responsible for fetching data from an api", False),
    ("Churn Predictor", True),
    ("• Trained machine learning models on 10000 customer records with 91% accuracy", False),
    ("EXPERIENCE", True),
    ("Intern, Acme Labs", True),
    ("May 2025 to Jul 2025", False),
    ("• helped build internal dashboards in python and flask", False),
    ("SKILLS", True),
    ("Python, Machine Learning, Git, Communication", False),
]
TEXT = "\n".join(text for text, _ in LINES)
JOB = """Backend Developer (Fresher)
Requirements: Python, FastAPI or Flask, SQL, pandas, REST APIs, Docker, Git.
Nice to have: AWS. You will build and maintain APIs with the product team."""
RESUME = parse_resume(TEXT)


def ids(response):
    return {c.id for c in response.changes if c.applied}


class BulletTests(unittest.TestCase):
    def test_taking_part_is_never_upgraded_to_building(self):
        self.assertEqual(
            improve_bullet("worked on a weather app using html"), "Contributed to a weather app using HTML."
        )
        self.assertEqual(
            improve_bullet("helped build internal dashboards in python"),
            "Contributed to building internal dashboards in Python.",
        )
        self.assertEqual(improve_bullet("we worked on a chatbot"), "Contributed to a chatbot.")
        self.assertEqual(improve_bullet("assisted with documentation"), "Contributed to documentation.")
        self.assertEqual(improve_bullet("was part of the web team"), "was part of the web team")

    def test_own_work_gets_an_action_verb(self):
        self.assertEqual(
            improve_bullet("worked on the college app independently from scratch"),
            "Built the college app independently from scratch.",
        )
        self.assertEqual(improve_bullet("responsible for fetching data"), "Fetched data.")
        self.assertEqual(improve_bullet("responsible for the database"), "Managed the database.")
        self.assertEqual(improve_bullet("managing the data cleaning steps"), "Managed the data cleaning steps.")
        self.assertEqual(improve_bullet("made a portfolio website"), "Built a portfolio website.")

    def test_strong_bullets_stay_exactly_as_written(self):
        bullet = "Built a REST API in Flask used by 1,200 students"
        self.assertEqual(improve_bullet(bullet), bullet)

    def test_dates(self):
        self.assertEqual(fix_date("May 2025 to Jul 2025"), "May 2025 – Jul 2025")
        self.assertEqual(fix_date("2022-2026"), "2022 – 2026")
        self.assertEqual(fix_date("Jan 2026 - present"), "Jan 2026 – Present")


class TailorTests(unittest.TestCase):
    def test_job_mode_fixes_and_never_invents(self):
        result = tailor_resume(RESUME, job_text=JOB)
        self.assertEqual(result.mode, "job")
        self.assertEqual(result.role, "Backend Developer")
        self.assertTrue({"skills-used", "summary", "dates", "tech:projects:0"} <= ids(result))
        skills = " ".join(result.resume.skills).lower()
        # Likely known from Machine Learning and asked for by the job: offered, never added on its own
        self.assertEqual([(s.skill, s.because) for s in result.likely_skills], [("pandas", "Machine Learning")])
        self.assertNotIn("pandas", skills)
        for missing in ("Docker", "SQL", "AWS"):  # wanted but not shown: only suggested
            self.assertIn(missing, result.suggested_skills)
            self.assertNotIn(missing.lower(), skills)
        self.assertNotIn("pandas", result.resume.summary.lower())  # the summary claims only proven skills
        self.assertEqual(result.resume.projects[0].subtitle, "Tech: CSS, HTML, JavaScript")

    def test_undo_and_confirmed_skills(self):
        result = tailor_resume(RESUME, job_text=JOB, skip=["bullet:projects:0:0"], confirmed_skills=["SQL", "pandas"])
        self.assertEqual(result.resume.projects[0].bullets[0], RESUME.projects[0].bullets[0])
        skills = " ".join(result.resume.skills).lower()
        self.assertIn("pandas", skills)
        self.assertIn("sql", skills)
        self.assertNotIn("SQL", result.suggested_skills)
        self.assertEqual(result.likely_skills, [])

    def test_a_good_summary_is_kept_and_ours_is_only_offered(self):
        summary = (
            "Backend-focused computer science student who builds Python and Flask services, cleans data with SQL, "
            "and has shipped two projects used by real users at my college."
        )
        self.assertTrue(good_summary(summary))
        self.assertFalse(good_summary("Hardworking student seeking a challenging opportunity to utilise my skills."))
        resume = RESUME.model_copy(update={"summary": summary})
        kept = tailor_resume(resume, job_text=JOB)
        change = next(c for c in kept.changes if c.id == "summary")
        self.assertEqual((change.kind, change.applied, kept.resume.summary), ("suggestion", False, summary))
        taken = tailor_resume(resume, job_text=JOB, accept=["summary"])
        self.assertIn("Backend Developer", taken.resume.summary)

    def test_role_mode_counts_the_roles_core_skills(self):
        result = tailor_resume(RESUME, target_role="Data Analyst")
        self.assertEqual((result.mode, result.role), ("role", "Data Analyst"))
        self.assertEqual(result.before.role_total, result.after.role_total)
        self.assertGreaterEqual(result.after.role_have, result.before.role_have)
        self.assertIn("SQL", result.suggested_skills)

    def test_general_mode_adds_nothing_role_specific(self):
        result = tailor_resume(RESUME)
        self.assertEqual(result.mode, "general")
        self.assertEqual(result.likely_skills, [])
        self.assertNotIn("projects-order", ids(result))
        self.assertEqual(result.suggested_skills, [])
        self.assertTrue(any("job description" in note for note in result.notes))


class IndianResumeHabitTests(unittest.TestCase):
    def test_personal_details_and_declaration_get_notes(self):
        text = (
            TEXT
            + "\nPERSONAL DETAILS\nDate of Birth: 01-01-2004\nFather's Name: R. Kumar\nDECLARATION\nI hereby declare that the above is true.\n"
        )
        notes = " ".join(tailor_resume(parse_resume(text), job_text=JOB).notes)
        self.assertIn("date of birth, father's name", notes)
        self.assertIn("Declaration", notes)

    def test_no_notes_when_they_are_absent(self):
        notes = " ".join(tailor_resume(RESUME, job_text=JOB).notes)
        self.assertNotIn("Declaration", notes)
        self.assertNotIn("father", notes)


class EndpointTests(unittest.TestCase):
    def test_scores_before_and_after(self):
        response = client.post("/api/resume/tailor", json={"resume": RESUME.model_dump(), "job_description": JOB})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertGreater(body["after"]["match"], body["before"]["match"])
        self.assertIsNotNone(body["after"]["ats"])

    def test_own_word_file_is_edited_in_place(self):
        doc = Document()
        for text, bold in LINES:
            run = doc.add_paragraph().add_run(text)
            run.font.name, run.font.size, run.bold = "Garamond", Pt(11), bold
            run.font.color.rgb = RGBColor(0x1F, 0x3A, 0x5F)
        buffer = io.BytesIO()
        doc.save(buffer)
        response = client.post(
            "/api/resume/tailor/docx",
            files={"file": ("ravi.docx", buffer.getvalue(), "application/octet-stream")},
            data={"payload": json.dumps({"resume": RESUME.model_dump(), "job_description": JOB})},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["x-fitlens-missed"], "0")
        out = Document(io.BytesIO(response.content))
        texts = [p.text for p in out.paragraphs]
        self.assertIn("• Contributed to a weather app using HTML CSS and JavaScript.", texts)
        self.assertEqual(response.headers["x-fitlens-pages"], "1,1")
        self.assertIn("SUMMARY", texts)
        self.assertIn("2022 – 2026", texts)
        self.assertTrue(texts[texts.index("May 2025 – Jul 2025") + 1].endswith("Tech: Flask, Python"))
        fonts = {(r.font.name, r.font.size.pt) for p in out.paragraphs for r in p.runs}
        self.assertEqual(fonts, {("Garamond", 11.0)})

    def test_pdf_is_refused_for_in_place_edits(self):
        response = client.post(
            "/api/resume/tailor/docx",
            files={"file": ("ravi.pdf", b"%PDF-1.4 x", "application/pdf")},
            data={"payload": json.dumps({"resume": RESUME.model_dump()})},
        )
        self.assertEqual(response.status_code, 400)


class ParserTests(unittest.TestCase):
    def test_project_titles_without_dates_start_new_entries(self):
        text = "PROJECTS\nWeather App\n• worked on a weather app\nChurn Predictor\n• Trained models\n"
        self.assertEqual([p.title for p in parse_resume(text).projects], ["Weather App", "Churn Predictor"])

    def test_personal_details_and_declaration_never_leak_into_skills(self):
        text = TEXT + "\nPERSONAL DETAILS\nDate of Birth: 01-01-2004\nDECLARATION\nI hereby declare it is true.\n"
        resume = parse_resume(text)
        self.assertEqual(resume.skills, ["Python", "Machine Learning", "Git", "Communication"])
        self.assertEqual([x.heading for x in resume.additional], ["Personal Details", "Declaration"])

    def test_a_bullet_wrapped_mid_phrase_stays_one_bullet(self):
        text = "PROJECTS\nWeather App\n• Built an app with the forecast for\nHyderabad and Vijayawada\n• Deployed it\n"
        projects = parse_resume(text).projects
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0].bullets[0], "Built an app with the forecast for Hyderabad and Vijayawada")


if __name__ == "__main__":
    unittest.main()
