"""Unit tests for the role prediction service (app/services/role_predictor.py).

Verifies:
1. predict_roles() correctly vectorizes raw resume text and uses calibrated probabilities.
2. Top-N results are sorted in descending order of match_percent.
3. Match percentages are in range [0, 100].
4. Edge cases like empty or whitespace strings return empty lists gracefully.
5. Realistic resume texts predict their expected role categories.
"""

from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.data_cleaning import clean_text
from app.services.role_predictor import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_MIN_WORD_COUNT,
    clear_role_predictor_cache,
    is_low_confidence,
    predict_roles,
    predict_roles_with_confidence,
)


class TestRolePredictor(unittest.TestCase):
    """Tests for role predictor service functions."""

    def setUp(self):
        clear_role_predictor_cache()
        self.it_resume = (
            "Senior Information Technology Specialist and Systems Administrator with over 10 years "
            "of experience managing enterprise cloud infrastructure, corporate networks, and server environments. "
            "Expertise in designing, deploying, and maintaining highly available IT systems across AWS, Azure, "
            "and on-premises data centers. Skilled in network engineering, Cisco routing and switching, TCP/IP, "
            "firewall configuration, VPNs, DNS, DHCP, and active directory administration. "
            "Proficient in Linux RedHat, Ubuntu, CentOS, and Windows Server administration, system virtualization "
            "with VMware ESXi and Hyper-V, and storage area networks. "
            "Experienced in cybersecurity best practices, vulnerability assessments, penetration testing, endpoint "
            "protection, disaster recovery planning, and automated system backups. "
            "Proficient in database management with SQL Server, PostgreSQL, MySQL, and database performance tuning. "
            "Demonstrated success in infrastructure automation using Python, Bash scripting, PowerShell, Ansible, "
            "and Terraform. Led cross-functional teams in enterprise software migrations, cloud migrations, and ITIL "
            "service management protocols. Proven track record of ensuring 99.99% system uptime, optimizing server "
            "performance, resolving critical technical support escalations, and implementing comprehensive IT security policies."
        )
        self.accounting_resume = (
            "Certified Public Accountant senior accountant general ledger reconciliation "
            "audit balance sheet payroll financial reporting tax preparation"
        )
        self.hr_resume = (
            "Human resources manager talent acquisition recruiter onboarding benefits "
            "employee relations performance appraisal HR policies"
        )
        self.sparse_student_resume = (
            "ALEX SAMPLE\n"
            "Second-year B.Tech student specializing in Artificial Intelligence & Machine Learning "
            "with strong foundations in C/C++, Data Structures, and Algorithms. Active competitive "
            "programmer with 500+ coding problems solved across coding platforms. Experienced in "
            "building logic-driven applications and web-based systems. Interested in AI/ML, "
            "algorithms, and data-driven software development.\n"
            "EDUCATION: Bachelor of Technology - Computer Science (AI & ML), State University, 2024-2028\n"
            "TECHNICAL SKILLS: Programming Languages: C, C++ (Proficient), Python, Java (Familiar). "
            "Core CS: Data Structures & Algorithms, OOPS, Dynamic Programming, File Handling. "
            "Web Development: HTML, CSS, JavaScript. Database: SQL (Basic).\n"
            "TECHNICAL PROJECTS: Event Registration Portal (HTML, CSS, JavaScript), "
            "Java Mini Games Hub (Java, OOP).\n"
            "CERTIFICATIONS: Microsoft Excel, C++, HTML, JavaScript, React js, Python, Unix, DBMS."
        )

    def tearDown(self):
        clear_role_predictor_cache()

    def test_is_low_confidence(self):
        """is_low_confidence flags low top probability or short resumes."""
        thr, min_words = DEFAULT_CONFIDENCE_THRESHOLD, DEFAULT_MIN_WORD_COUNT
        long_enough = min_words + 50

        # High confidence: top >= threshold and long enough
        self.assertFalse(is_low_confidence([0.80, 0.10, 0.05, 0.05], word_count=long_enough))
        self.assertFalse(is_low_confidence([thr, 0.20, 0.15], word_count=long_enough))

        # Low confidence due to probability
        self.assertTrue(is_low_confidence([0.14, 0.12, 0.10, 0.08]))
        self.assertTrue(is_low_confidence([thr - 0.001, 0.10], word_count=long_enough))

        # Low confidence due to word count even with high raw probability
        self.assertTrue(is_low_confidence([0.80, 0.10, 0.05, 0.05], word_count=50))
        self.assertTrue(is_low_confidence([0.90, 0.05], word_count=min_words - 1))
        self.assertFalse(is_low_confidence([0.90, 0.05], word_count=min_words))

        # Explicit thresholds still work
        self.assertTrue(is_low_confidence([0.30, 0.20], threshold=0.35))

        # Empty / None / edge cases
        self.assertTrue(is_low_confidence([]))
        self.assertTrue(is_low_confidence(None))

    def test_senior_full_stack_software_engineer_deployment_resume(self):
        """26-word Senior Full Stack Software Engineer resume triggers the fallback
        and predicts INFORMATION-TECHNOLOGY with confidence='low'."""
        resume = (
            "Senior Full Stack Software Engineer with 6 years experience in Python, "
            "FastAPI, React, PostgreSQL, Docker, and AWS cloud infrastructure. "
            "Built microservices and machine learning recommendation engines."
        )
        roles, confidence = predict_roles_with_confidence(resume, top_n=3)
        self.assertEqual(confidence, "low")
        self.assertGreaterEqual(len(roles), 3)
        self.assertEqual(roles[0]["role"], "INFORMATION-TECHNOLOGY")
        self.assertGreater(roles[0]["match_percent"], roles[1]["match_percent"])

    def test_hybrid_fallback_on_sparse_student_resume(self):
        """Short student resume is low-confidence and lands on a technical category."""
        roles, confidence = predict_roles_with_confidence(self.sparse_student_resume, top_n=3)
        self.assertEqual(confidence, "low")
        self.assertIn(roles[0]["role"], ["INFORMATION-TECHNOLOGY", "ENGINEERING"])
        self.assertNotIn("AVIATION", [r["role"] for r in roles[:2]])

    def test_short_resume_uses_blend_not_pure_overlap(self):
        """A short resume with a non-trivial ML probability is blended 50/50 with skill overlap."""
        import joblib
        import numpy as np
        from app.services.role_predictor import (
            DEFAULT_CLASSIFIER_PATH,
            DEFAULT_VECTORIZER_PATH,
            VERY_LOW_CONFIDENCE,
        )

        test_resume = (
            "Junior Software Engineer with Python and SQL experience. "
            "Built simple database applications, REST API, Git, Docker, and Linux."
        )
        self.assertLess(len(test_resume.split()), DEFAULT_MIN_WORD_COUNT)

        clf = joblib.load(DEFAULT_CLASSIFIER_PATH)
        vec = joblib.load(DEFAULT_VECTORIZER_PATH)
        raw_proba = clf.predict_proba(vec.transform([clean_text(test_resume)]))[0]
        # Above the very-low cutoff, so the blend (not pure skill overlap) applies
        self.assertGreaterEqual(float(np.max(raw_proba)), VERY_LOW_CONFIDENCE)

        roles, confidence = predict_roles_with_confidence(test_resume, top_n=5)
        self.assertEqual(confidence, "low")
        self.assertEqual(roles[0]["role"], "INFORMATION-TECHNOLOGY")
        self.assertEqual(roles[1]["role"], "ENGINEERING")
        self.assertGreater(roles[0]["match_percent"], roles[1]["match_percent"])
        self.assertGreater(roles[1]["match_percent"], roles[2]["match_percent"])

    def test_predict_roles_with_confidence_high(self):
        """Confident resume returns confidence='high'."""
        roles, confidence = predict_roles_with_confidence(self.it_resume, top_n=3)
        self.assertEqual(confidence, "high")
        self.assertEqual(roles[0]["role"], "INFORMATION-TECHNOLOGY")

    def test_predict_roles_information_technology(self):
        """IT resume predicts INFORMATION-TECHNOLOGY at the top with high probability."""
        predictions = predict_roles(self.it_resume, top_n=3)
        self.assertEqual(len(predictions), 3)

        # Check keys and types
        for item in predictions:
            self.assertIn("role", item)
            self.assertIn("match_percent", item)
            self.assertIsInstance(item["role"], str)
            self.assertIsInstance(item["match_percent"], float)
            self.assertGreaterEqual(item["match_percent"], 0.0)
            self.assertLessEqual(item["match_percent"], 100.0)

        # Sorted descending
        probs = [item["match_percent"] for item in predictions]
        self.assertEqual(probs, sorted(probs, reverse=True))

        # Top predicted role should be INFORMATION-TECHNOLOGY
        top_role = predictions[0]["role"]
        self.assertEqual(top_role, "INFORMATION-TECHNOLOGY")
        self.assertGreater(predictions[0]["match_percent"], 50.0)

    def test_predict_roles_accounting(self):
        """Accounting resume predicts ACCOUNTANT at the top."""
        predictions = predict_roles(self.accounting_resume, top_n=3)
        self.assertEqual(len(predictions), 3)
        top_role = predictions[0]["role"]
        self.assertEqual(top_role, "ACCOUNTANT")
        self.assertGreater(predictions[0]["match_percent"], 50.0)

    def test_predict_roles_hr(self):
        """HR resume predicts HR at top with strong probability."""
        predictions = predict_roles(self.hr_resume, top_n=3)
        self.assertEqual(len(predictions), 3)
        top_role = predictions[0]["role"]
        self.assertEqual(top_role, "HR")
        self.assertGreater(predictions[0]["match_percent"], 40.0)

    def test_predict_roles_top_n(self):
        """top_n parameter controls length of returned list."""
        for n in [1, 2, 5]:
            predictions = predict_roles(self.it_resume, top_n=n)
            self.assertEqual(len(predictions), n)

    def test_service_matches_raw_model(self):
        """Confirm the same top category and roughly the same probability is returned
        through the actual service function as the raw model."""
        import joblib
        import numpy as np
        from app.services.role_predictor import (
            DEFAULT_CLASSIFIER_PATH,
            DEFAULT_VECTORIZER_PATH,
        )

        clf = joblib.load(DEFAULT_CLASSIFIER_PATH)
        vec = joblib.load(DEFAULT_VECTORIZER_PATH)
        raw_proba = clf.predict_proba(vec.transform([clean_text(self.it_resume)]))[0]
        top_idx = int(np.argmax(raw_proba))
        raw_top_category = str(clf.classes_[top_idx])
        raw_top_prob_percent = float(raw_proba[top_idx]) * 100

        service_predictions = predict_roles(self.it_resume, top_n=3)
        self.assertGreater(len(service_predictions), 0)
        self.assertEqual(service_predictions[0]["role"], raw_top_category)
        self.assertAlmostEqual(
            service_predictions[0]["match_percent"],
            raw_top_prob_percent,
            delta=0.5,
        )

    def test_synthetic_short_resumes_across_professions(self):
        """Synthetic short resumes (20-40 words) across clear professions are low-confidence
        (shorter than DEFAULT_MIN_WORD_COUNT) and return the right category."""
        benchmarks = [
            (
                "Frontend Web Developer experienced in building responsive modern web applications with TypeScript, React, Next.js, Redux, HTML5, CSS3, Tailwind CSS, and RESTful API integration.",
                "INFORMATION-TECHNOLOGY",
                ["INFORMATION-TECHNOLOGY", "ENGINEERING"],
            ),
            (
                "Python Backend Software Engineer with 5 years experience designing scalable microservices, PostgreSQL databases, Redis caching, Celery background workers, and high throughput asynchronous APIs.",
                "INFORMATION-TECHNOLOGY",
                ["INFORMATION-TECHNOLOGY", "ENGINEERING"],
            ),
            (
                "Certified Public Accountant (CPA) with 7 years experience handling corporate tax filings, general ledger reconciliation, GAAP compliance, financial statement audits, and QuickBooks reporting systems.",
                "ACCOUNTANT",
                ["ACCOUNTANT", "FINANCE"],
            ),
            (
                "Registered Nurse (RN) with 6 years experience in hospital emergency department, triage protocols, vital signs monitoring, intravenous medication administration, and compassionate patient clinical care.",
                "HEALTHCARE",
                ["HEALTHCARE"],
            ),
            (
                "High School Mathematics Teacher with 8 years experience teaching algebra, geometry, calculus, designing secondary curriculum, assessing student progress, and maintaining effective classroom management.",
                "TEACHER",
                ["TEACHER"],
            ),
            (
                "Executive Chef leading high-volume culinary operations, seasonal menu engineering, food cost control, kitchen sanitation compliance standards, and fine dining classical French culinary techniques.",
                "CHEF",
                ["CHEF"],
            ),
        ]

        for text, expected, acceptable in benchmarks:
            wc = len(text.split())
            self.assertGreaterEqual(wc, 20)
            self.assertLessEqual(wc, 40)
            roles, confidence = predict_roles_with_confidence(text, top_n=3)
            self.assertEqual(confidence, "low", f"Expected 'low' confidence for short resume ({wc} words): {text}")
            self.assertGreaterEqual(len(roles), 1)
            top_role = roles[0]["role"]
            self.assertIn(
                top_role,
                acceptable,
                f"Expected one of {acceptable} for resume, got '{top_role}'. Text: {text}",
            )

    def test_206_word_bedside_nurse_regression(self):
        """206-word bedside nurse resume (a documented failure of the original model).

        The first model predicted ADVOCATE at ~48.7% with confidence='high', because the
        dataset's ADVOCATE category contains many patient-advocate resumes. Retraining with
        sublinear TF plus consistent text cleaning moved it to HEALTHCARE, but ADVOCATE stays
        a close second, so this pins the ranking rather than claiming the overlap is solved.
        """
        text = (
            "Staff Registered Nurse (RN) with 6 years of intensive bedside clinical nursing experience in a busy hospital "
            "emergency department and step-down medical care unit. Responsible for direct bedside patient care, routine vital signs "
            "monitoring, pulse oximetry, blood pressure checks, and continuous cardiac telemetry monitoring for high-acuity patients. "
            "Administer prescribed medications safely via oral, subcutaneous, intramuscular, and intravenous (IV) routes, including "
            "titrating cardiac infusions, antibiotic drips, and pain management medications according to physician orders and clinical protocols. "
            "Perform frequent clinical assessments to monitor patient condition changes, recognizing vital sign instability, and reporting critical "
            "diagnostic laboratory values to attending physicians and hospital medical staff. Carry out essential nursing procedures including "
            "inserting peripheral intravenous catheters, phlebotomy blood draws, Foley catheter insertion, nasogastric tube placement, and sterile "
            "wound dressing changes. Maintain comprehensive and accurate clinical nursing documentation in electronic medical records, logging medication "
            "administration records, patient vitals, intake and output, and treatment progress notes. Actively communicate with patient families "
            "regarding daily nursing care plans, diagnostic test schedules, and hospital discharge instructions. Function as charge nurse when assigned, "
            "organizing staff shift assignments, coordinating emergency room bed placement, maintaining patient safety and infection control standards, "
            "collaborating with attending physicians during morning rounds, and mentoring newly graduated staff nurses and clinical nursing students."
        )
        wc = len(text.split())
        self.assertEqual(wc, 206)

        roles, confidence = predict_roles_with_confidence(text, top_n=3)
        self.assertEqual(confidence, "high")
        self.assertEqual(roles[0]["role"], "HEALTHCARE")
        self.assertEqual(roles[1]["role"], "ADVOCATE")

    def test_all_synthetic_short_resumes_top1(self):
        """Every hand-written short resume in scripts/synthetic_resumes.py gets the right top-1 role."""
        from scripts.synthetic_resumes import SYNTHETIC_SHORT_RESUMES

        for item in SYNTHETIC_SHORT_RESUMES:
            roles, _ = predict_roles_with_confidence(item["text"], top_n=3)
            self.assertEqual(roles[0]["role"], item["true_role"], item["name"])

    def test_predict_roles_empty_string(self):
        """Empty or whitespace-only inputs return empty list."""
        self.assertEqual(predict_roles(""), [])
        self.assertEqual(predict_roles("   "), [])
        self.assertEqual(predict_roles(None), [])


if __name__ == "__main__":
    unittest.main()

