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

from app.services.role_predictor import (
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
            "GADDE VARDHAN SAI\n"
            "Second-year B.Tech student specializing in Artificial Intelligence & Machine Learning "
            "with strong foundations in C/C++, Data Structures, and Algorithms. Active competitive "
            "programmer with 500+ coding problems solved across coding platforms. Experienced in "
            "building logic-driven applications and web-based systems. Interested in AI/ML, "
            "algorithms, and data-driven software development.\n"
            "EDUCATION: Bachelor of Technology - Computer Science (AI & ML), Aditya University, 2024-2028\n"
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
        """is_low_confidence correctly identifies high vs low probability predictions and word count triggers."""
        # High confidence (top >= 0.35, word_count >= 150)
        self.assertFalse(is_low_confidence([0.80, 0.10, 0.05, 0.05], word_count=200))
        self.assertFalse(is_low_confidence([0.35, 0.20, 0.15], word_count=200))

        # Low confidence due to probability (top < 0.35)
        self.assertTrue(is_low_confidence([0.14, 0.12, 0.10, 0.08]))
        self.assertTrue(is_low_confidence([0.249, 0.10]))
        self.assertTrue(is_low_confidence([0.349, 0.20, 0.15]))

        # Low confidence due to word count (< 150 words) even with high raw probability
        self.assertTrue(is_low_confidence([0.80, 0.10, 0.05, 0.05], word_count=50))
        self.assertTrue(is_low_confidence([0.90, 0.05], word_count=149))

        # Empty / None / edge cases
        self.assertTrue(is_low_confidence([]))
        self.assertTrue(is_low_confidence(None))

    def test_senior_full_stack_software_engineer_deployment_resume(self):
        """26-word Senior Full Stack Software Engineer resume triggers fallback
        and correctly predicts INFORMATION-TECHNOLOGY (not AVIATION) with confidence='low'."""
        resume = (
            "Senior Full Stack Software Engineer with 6 years experience in Python, "
            "FastAPI, React, PostgreSQL, Docker, and AWS cloud infrastructure. "
            "Built microservices and machine learning recommendation engines."
        )
        roles, confidence = predict_roles_with_confidence(resume, top_n=3)
        self.assertEqual(confidence, "low")
        self.assertGreaterEqual(len(roles), 3)
        self.assertEqual(roles[0]["role"], "INFORMATION-TECHNOLOGY")
        self.assertNotEqual(roles[0]["role"], "AVIATION")
        self.assertEqual(roles[0]["match_percent"], 42.5)

    def test_hybrid_fallback_on_sparse_student_resume(self):
        """Sparse student resume triggers hybrid fallback, changing top role from raw ML AVIATION
        to sensible tech roles (INFORMATION-TECHNOLOGY or ENGINEERING) with confidence='low'."""
        import joblib
        import numpy as np
        from app.services.role_predictor import (
            DEFAULT_CLASSIFIER_PATH,
            DEFAULT_VECTORIZER_PATH,
        )

        # 1. Confirm raw ML classifier alone produces low confidence and spurious AVIATION
        clf = joblib.load(DEFAULT_CLASSIFIER_PATH)
        vec = joblib.load(DEFAULT_VECTORIZER_PATH)
        raw_proba = clf.predict_proba(vec.transform([self.sparse_student_resume]))[0]
        raw_top_idx = int(np.argmax(raw_proba))
        raw_top_category = str(clf.classes_[raw_top_idx])
        raw_top_prob = float(raw_proba[raw_top_idx])

        self.assertTrue(is_low_confidence(raw_proba, threshold=0.35))
        self.assertLess(raw_top_prob, 0.35)
        self.assertEqual(raw_top_category, "AVIATION")

        # 2. Confirm service with hybrid fallback engages and produces sensible tech roles
        roles, confidence = predict_roles_with_confidence(self.sparse_student_resume, top_n=3)
        self.assertEqual(confidence, "low")
        self.assertGreater(len(roles), 0)

        # Top role should now be INFORMATION-TECHNOLOGY (or ENGINEERING), not AVIATION
        top_role = roles[0]["role"]
        self.assertIn(top_role, ["INFORMATION-TECHNOLOGY", "ENGINEERING"])
        self.assertNotEqual(top_role, "AVIATION")

        # Second role should also be a relevant technical category
        second_role = roles[1]["role"]
        self.assertIn(second_role, ["INFORMATION-TECHNOLOGY", "ENGINEERING", "DESIGNER"])

    def test_50_50_blend_in_15_to_25_percent_range(self):
        """Test case specifically in the 15-25% ML confidence range to confirm 50/50 blend."""
        import joblib
        import numpy as np
        from app.services.role_predictor import (
            DEFAULT_CLASSIFIER_PATH,
            DEFAULT_VECTORIZER_PATH,
        )

        test_resume = (
            "Junior Software Engineer with Python and SQL experience. "
            "Built simple database applications, REST API, Git, Docker, and Linux."
        )

        # 1. Verify raw ML lands in [0.15, 0.25)
        clf = joblib.load(DEFAULT_CLASSIFIER_PATH)
        vec = joblib.load(DEFAULT_VECTORIZER_PATH)
        raw_proba = clf.predict_proba(vec.transform([test_resume]))[0]
        top_prob = float(np.max(raw_proba))
        self.assertGreaterEqual(top_prob, 0.15)
        self.assertLess(top_prob, 0.25)

        # 2. Run service prediction
        roles, confidence = predict_roles_with_confidence(test_resume, top_n=5)
        self.assertEqual(confidence, "low")
        self.assertGreaterEqual(len(roles), 3)

        # Check rankings: IT is #1 due to strong skill overlap (python, sql, database, rest api, docker, git),
        # ENGINEERING is #2, and probabilities are distinct (no tie bug)
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
        raw_proba = clf.predict_proba(vec.transform([self.it_resume]))[0]
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
        """Synthetic short resumes (20-40 words) across clear professions (software engineer,
        accountant, nurse, teacher, chef) engage fallback and return accurate categories with confidence='low'."""
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

    def test_206_word_bedside_nurse_inherent_limitation_regression(self):
        """Pin the 206-word realistic bedside nurse resume to its documented behavior.

        This serves as a regression anchor for the known limitation documented in README.md:
        on full-length resumes (>= 150 words) with high raw model probability (>= 35%),
        both safety filters are bypassed, predicting ADVOCATE with confidence='high' (~48.7%).
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
        self.assertEqual(roles[0]["role"], "ADVOCATE")
        self.assertAlmostEqual(roles[0]["match_percent"], 48.7, delta=1.0)
        self.assertEqual(roles[1]["role"], "HEALTHCARE")
        self.assertAlmostEqual(roles[1]["match_percent"], 18.2, delta=1.0)

    def test_predict_roles_empty_string(self):
        """Empty or whitespace-only inputs return empty list."""
        self.assertEqual(predict_roles(""), [])
        self.assertEqual(predict_roles("   "), [])
        self.assertEqual(predict_roles(None), [])


if __name__ == "__main__":
    unittest.main()

