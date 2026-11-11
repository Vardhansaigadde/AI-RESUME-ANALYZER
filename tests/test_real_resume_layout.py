"""A real student resume layout: links kept in place, Indian section names, and the student's own design.

Modelled on a real PDF (details made up): "GitHub | LinkedIn" labels in the header, link icons
after project and internship titles, a linked certificate bullet, dateless projects, wrapped
bullets, "Achievements & Awards" and "Certificates & Additional Information" sections, and
skills the student grouped themselves.
"""

import unittest

from app.services.parser import _place_pdf_links
from app.services.resume_sections import parse_resume
from app.services.resume_tailor import degree_of, tailor_resume
from app.services.rich_text import contact_link, link_label
from app.services.skill_extractor import extract_skills

GITHUB = "https://github.com/sample-dev"
LINKEDIN = "https://www.linkedin.com/in/sample-dev/"
DEMO = "https://quiz-app.example.com/"
POST = "https://www.linkedin.com/posts/sample-dev_internship-activity-7000000000000000000-abcd?utm_source=share"


class FakePage:
    """Just what _place_pdf_links reads from a pdfplumber page."""

    def __init__(self, words, hyperlinks):
        self._words, self.hyperlinks = words, hyperlinks

    def extract_words(self, x_tolerance=3):
        return self._words


def word(text, x0, top):
    return {"text": text, "x0": x0, "x1": x0 + 6 * len(text), "top": top, "bottom": top + 10}


class PdfLinkPlacementTests(unittest.TestCase):
    def test_links_go_back_where_they_sit(self):
        text = "Sample Dev\nGitHub | LinkedIn\nPROJECTS\nQuiz App – Online Quiz Platform\n• Built a quiz app.\nCERTIFICATES\n• Python – TechGig"
        words = [
            word("Sample", 40, 10), word("Dev", 90, 10),
            word("GitHub", 40, 30), word("|", 80, 30), word("LinkedIn", 90, 30),
            word("PROJECTS", 40, 50),
            word("Quiz", 40, 70), word("App", 70, 70), word("–", 95, 70), word("Online", 105, 70),
            word("Quiz", 145, 70), word("Platform", 175, 70),
            word("•", 40, 90), word("Built", 50, 90), word("a", 85, 90), word("quiz", 95, 90), word("app.", 125, 90),
            word("CERTIFICATES", 40, 110),
            word("•", 40, 130), word("Python", 50, 130), word("–", 90, 130), word("TechGig", 100, 130),
        ]  # fmt: skip
        links = [
            {"uri": GITHUB, "x0": 39, "x1": 77, "top": 30, "bottom": 40},  # on the word "GitHub"
            {"uri": LINKEDIN, "x0": 89, "x1": 139, "top": 30, "bottom": 40},  # on "LinkedIn"
            {"uri": DEMO, "x0": 230, "x1": 240, "top": 70, "bottom": 80},  # an icon after the title
            {"uri": POST, "x0": 150, "x1": 160, "top": 130, "bottom": 140},  # an icon after a bullet
            {"uri": "https://example.com/x", "x0": 39, "x1": 100, "top": 50, "bottom": 60},  # on a heading
        ]
        placed = _place_pdf_links(FakePage(words, links), text, 3.0).split("\n")
        self.assertEqual(placed[1], f"[GitHub]({GITHUB}) | [LinkedIn]({LINKEDIN})")
        self.assertEqual(placed[3], f"Quiz App – Online Quiz Platform [link]({DEMO})")
        self.assertEqual(placed[6], f"• [Python – TechGig]({POST})")
        self.assertEqual(placed[2], "PROJECTS")  # a heading is never turned into a link


RESUME = f"""Sample Dev
sample.dev@example.com | +91 98765 43210 | Eluru, Andhra Pradesh
[GitHub]({GITHUB}) | [LinkedIn]({LINKEDIN})
Summary
Aspiring AI & ML student with hands-on experience in machine learning, NLP and AI application development through internships and projects.
Skills
• Programming: Python, Java, SQL
• Generative AI & NLP: RAG, Prompt Engineering, LLMs
• Tools & Platforms: Scikit-Learn, Pandas, GitHub, VS Code
Projects
Quiz App – Online Quiz Platform [link]({DEMO})
• Developed a quiz platform using Python, FastAPI, React and Scikit-learn to score 1,200 answers a day, giving
students instant feedback.
Travel Planner – Multi-Agent AI
• Built a full-stack application using Python, React, and MongoDB for 300 users.
Education
Sample Institute of Technology, Andhra Pradesh 2027
B.Tech in Computer Science with Artificial Intelligence and Machine Learning
Internships
AI Intern – Sample Labs May 2025 – July 2025 [link]({POST})
• Developed a sentiment analysis project using NLP techniques.
Achievements & Awards
• Qualified the preliminary round of a national hackathon organised by a partner college – built a
multi-agent chatbot for idea refinement.
Certificates & Additional Information
• [Python – TechGig]({POST})
• Organised a college tech event with over 1,000 participants.
"""


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.resume = parse_resume(RESUME)

    def test_header_keeps_labelled_links_and_finds_the_location(self):
        r = self.resume
        self.assertEqual(r.links, [f"[GitHub]({GITHUB})", f"[LinkedIn]({LINKEDIN})"])
        self.assertEqual(r.location, "Eluru, Andhra Pradesh")
        self.assertEqual(r.headline, "")

    def test_projects_split_even_after_a_wrapped_bullet_and_keep_their_links(self):
        projects = self.resume.projects
        self.assertEqual(
            [p.title for p in projects], ["Quiz App – Online Quiz Platform", "Travel Planner – Multi-Agent AI"]
        )
        self.assertEqual(projects[0].link, DEMO)
        self.assertEqual(self.resume.experience[0].link, POST)
        self.assertEqual(self.resume.experience[0].date, "May 2025 – July 2025")

    def test_indian_section_names_and_wrapped_list_items(self):
        r = self.resume
        self.assertEqual(len(r.achievements), 1)
        self.assertIn("built a multi-agent chatbot", r.achievements[0])
        self.assertEqual([x.heading for x in r.additional], ["Certificates & Additional Information"])
        self.assertEqual(r.additional[0].items[0], f"[Python – TechGig]({POST})")

    def test_the_students_own_skill_groups_are_kept(self):
        self.assertEqual(
            self.resume.skills[:4],
            ["Programming: Python", "Java", "SQL", "Generative AI & NLP: RAG"],
        )


class FixedResumeRespectsTheDesignTests(unittest.TestCase):
    def setUp(self):
        self.result = tailor_resume(
            parse_resume(RESUME), job_text="ML Engineer\nRequirements: Python, PyTorch, SQL, FastAPI."
        )
        self.changes = {c.id: c for c in self.result.changes}

    def test_own_groups_and_header_are_kept(self):
        self.assertNotIn("skills-group", self.changes)
        self.assertEqual(self.changes["headline"].kind, "suggestion")
        self.assertFalse(self.changes["headline"].applied)
        self.assertEqual(self.result.resume.headline, "")

    def test_tech_lines_name_tools_only(self):
        tech = self.changes["tech:projects:0"].after
        self.assertIn("FastAPI", tech)
        self.assertIn("React", tech)
        self.assertNotIn("Machine Learning", tech)
        self.assertNotIn("tech:experience:0", self.changes)  # one topic (NLP) is not a Tech line

    def test_already_listed_skills_are_not_added_again(self):
        added = self.changes["skills-used"].after
        self.assertNotIn("RAG", added)
        self.assertIn("FastAPI", added)

    def test_the_degree_line_is_found_when_the_college_comes_first(self):
        self.assertTrue(degree_of(parse_resume(RESUME)).startswith("B.Tech in Computer Science"))


MESSY_WORD_EXPORT = """Sample Dev
https://www. .com/feed/update/urn:li:activity:7000000000000000001/ | https://www.linkedin.com/posts/sample-dev_x-activity-7000000000000000002-ab
sample.dev@example.com | +91 98765 43210 | https://github.com/sample-dev | https://quiz-app.example.com/
SUMMARY
Aspiring AI and ML student building practical projects with Python.
EXPERIENCE
AI Intern \u2013 Sample Labs\tMay 2025 \u2013 July 2025
\u2022 Developed a sentiment analysis project using NLP.
\u2022 Achievements & Awards
\u2022 Qualified the preliminary round of a national hackathon.
\u2022 Certificates & Additional Information
\u2022 Python \u2013 TechGig
"""


class MessyWordExportTests(unittest.TestCase):
    """A resume saved by an older tool: links as text in the header and headings saved as list items."""

    def setUp(self):
        self.resume = parse_resume(MESSY_WORD_EXPORT)

    def test_headings_saved_as_list_items_are_still_headings(self):
        self.assertEqual(self.resume.achievements, ["Qualified the preliminary round of a national hackathon."])
        self.assertEqual([x.heading for x in self.resume.additional], ["Certificates & Additional Information"])
        self.assertEqual(self.resume.experience[0].bullets, ["Developed a sentiment analysis project using NLP."])

    def test_header_keeps_only_real_profile_links(self):
        self.assertEqual(self.resume.links, ["https://github.com/sample-dev", "https://quiz-app.example.com/"])
        self.assertEqual(self.resume.headline, "")  # a line of addresses is never the headline

    def test_a_bulleted_skill_line_is_not_a_heading(self):
        resume = parse_resume("SKILLS\n\u2022 Tools: Git, Docker\n\u2022 Projects: 3 shipped\n")
        self.assertEqual(resume.skills[:2], ["Tools: Git", "Docker"])


class LinkDisplayTests(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(contact_link(f"[GitHub]({GITHUB})"), ("GitHub", GITHUB))
        self.assertEqual(link_label(DEMO), "quiz-app.example.com")
        self.assertEqual(link_label(POST), "LinkedIn post")

    def test_react_in_a_tech_stack_but_not_as_a_verb(self):
        self.assertIn("react", extract_skills("built with python, fastapi, react and mongodb"))
        self.assertNotIn("react", extract_skills("i react quickly to feedback"))


if __name__ == "__main__":
    unittest.main()
