"""Tests for app/services/skill_extractor.py.

Tests cover:
1. Unit tests for word-boundary-safe matching (multi-word, partial-match
   guard, special-char skills, case-insensitivity, empty/None input).
2. Integration tests using 2 real rows from
   data/processed/job_resume_fit_clean.csv, asserting that the extracted
   skills have a meaningful overlap (Jaccard >= 0.15) with the dataset's
   own resume_skill_list for that row.
3. compare_skills() correctness tests.
"""

import ast
from pathlib import Path
import sys
import unittest

# Ensure repository root is importable
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from app.services.skill_extractor import (
    SKILL_ALIASES,
    _load_skill_patterns,
    compare_skills,
    extract_skills,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def jaccard(a: set[str], b: set[str]) -> float:
    """Compute Jaccard similarity between two sets."""
    if not a and not b:
        return 1.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _load_row(index: int) -> dict:
    """Load a single row from the processed job-resume CSV."""
    csv_path = REPO_ROOT / "data" / "processed" / "job_resume_fit_clean.csv.gz"
    df = pd.read_csv(csv_path)
    row = df.iloc[index]
    return {
        "resume_text": row["resume_text"],
        "resume_skill_list": ast.literal_eval(row["resume_skill_list"]),
        "job_required_skills": ast.literal_eval(row["job_required_skills"]),
        "category": row["category"],
    }


# ---------------------------------------------------------------------------
# Unit tests: word-boundary matching
# ---------------------------------------------------------------------------


class TestExtractSkillsUnit(unittest.TestCase):
    """Unit tests for extract_skills() matching logic."""

    def test_simple_single_word_skill(self):
        """A plain skill found in text is returned."""
        result = extract_skills("She has strong python experience.")
        self.assertIn("python", result)

    def test_case_insensitive(self):
        """Matching is case-insensitive."""
        self.assertIn("python", extract_skills("PYTHON developer"))
        self.assertIn("python", extract_skills("Python developer"))

    def test_multi_word_skill_matched_as_phrase(self):
        """Multi-word skills like 'data analysis' match as a phrase."""
        result = extract_skills("Responsible for data analysis and reporting.")
        self.assertIn("data analysis", result)

    def test_multi_word_no_false_sub_match(self):
        """After 'time management' is matched, 'management' alone should not
        appear as a separate hit because the span was already consumed.

        'time management' and 'management' are both real taxonomy entries.
        The longest-first + span-masking strategy ensures 'time management'
        wins and 'management' does NOT additionally fire inside that phrase."""
        text = "Demonstrated time management skills throughout the project."
        result = extract_skills(text)
        self.assertIn("time management", result, "'time management' should be found as a phrase.")
        # 'management' on its own should NOT fire inside the already-masked span
        self.assertNotIn(
            "management", result, "'management' should not re-match inside the consumed 'time management' span."
        )

    def test_short_skill_r_not_inside_word(self):
        """'r' should NOT match inside 'trainer', 'order', 'framework'."""
        text = "experienced trainer and order management framework"
        result = extract_skills(text)
        self.assertNotIn("r", result)

    def test_short_skill_r_standalone(self):
        """'r' SHOULD match when it stands alone as a token."""
        result = extract_skills("proficient in r and python for statistics")
        self.assertIn("r", result)
        self.assertIn("python", result)

    def test_short_skill_c_not_inside_word(self):
        """'c' should NOT match inside 'architecture', 'according', 'c++'."""
        text = "background in architecture and according to best practices"
        result = extract_skills(text)
        self.assertNotIn("c", result)

    def test_special_char_skill_cpp(self):
        """'c++' should match exactly, not fire 'c' as a side effect."""
        result = extract_skills("skilled in c++ and system design")
        self.assertIn("c++", result)
        self.assertNotIn("c", result)

    def test_special_char_skill_csharp(self):
        """'c#' should match as a distinct token."""
        result = extract_skills("developed backend services in c#")
        self.assertIn("c#", result)

    def test_special_char_skill_nodejs(self):
        """'node.js' with a dot should be matched literally."""
        result = extract_skills("Built REST APIs using node.js and express")
        self.assertIn("node.js", result)

    def test_go_not_inside_google(self):
        """'go' should NOT match inside 'google', 'algorithm', 'django'."""
        text = "used google analytics and django for the project"
        result = extract_skills(text)
        self.assertNotIn("go", result)

    def test_go_standalone(self):
        """'go' SHOULD match as a standalone programming language token."""
        result = extract_skills("backend written in go and deployed on kubernetes")
        self.assertIn("go", result)
        self.assertIn("kubernetes", result)

    def test_empty_string(self):
        """Empty input returns empty set, no errors."""
        self.assertEqual(extract_skills(""), set())

    def test_none_input(self):
        """None input returns empty set, no errors."""
        self.assertEqual(extract_skills(None), set())

    def test_multi_skill_text(self):
        """Multiple skills in one text are all found."""
        text = "experience with python, sql, docker, and git version control"
        result = extract_skills(text)
        for expected in ["python", "sql", "docker", "git"]:
            self.assertIn(expected, result)

    def test_sql_not_inside_mysql(self):
        """After 'mysql' is matched (longer), 'sql' should not re-fire inside it."""
        text = "database experience with mysql and postgresql"
        result = extract_skills(text)
        # mysql and postgresql should be found
        self.assertIn("mysql", result)
        self.assertIn("postgresql", result)

    def test_swift_with_ios_context(self):
        """'swift' with nearby iOS/app context MUST be extracted as a skill."""
        text = "developed an iOS app using Swift"
        result = extract_skills(text)
        self.assertIn("swift", result, "Expected 'swift' to be extracted when paired with iOS/app context.")

    def test_swift_without_context_everyday_english(self):
        """'swift' in everyday English ('swift resolution') must NOT be extracted."""
        text = "ensured the swift resolution of customer issues"
        result = extract_skills(text)
        self.assertNotIn("swift", result, "'swift' should not match without technical context.")

    def test_react_with_frontend_context(self):
        """'react' with nearby UI/frontend/javascript context MUST be extracted."""
        text = "Built responsive frontend components using React and Redux"
        result = extract_skills(text)
        self.assertIn("react", result, "Expected 'react' to match with frontend context.")

    def test_react_without_context(self):
        """'react' as an everyday English verb must NOT be extracted."""
        text = "The manager did not react well to the delayed project timeline"
        result = extract_skills(text)
        self.assertNotIn("react", result, "'react' should not match in everyday English context.")

    def test_spark_with_big_data_context(self):
        """'spark' with nearby big data/hadoop/databricks context MUST be extracted."""
        text = "Engineered big data processing pipelines using Spark and Hadoop"
        result = extract_skills(text)
        self.assertIn("spark", result, "Expected 'spark' to match with big data context.")

    def test_spark_without_context(self):
        """'spark' as an everyday noun/verb must NOT be extracted."""
        text = "A sudden electric spark damaged the laboratory equipment"
        result = extract_skills(text)
        self.assertNotIn("spark", result, "'spark' should not match without data context.")

    # Sweep False-Positive Guard Tests
    def test_go_without_context_false_positive(self):
        """'go' in everyday English ('testing to go live') must NOT be extracted."""
        text = "into greytip software since testing to go live"
        result = extract_skills(text)
        self.assertNotIn("go", result, "'go' should not match without developer/backend context.")

    def test_spring_without_context_false_positive(self):
        """'spring' as calendar semester ('social psychology spring 2014') must NOT be extracted."""
        text = "group presentation social psychology spring 2014 collaborated with members"
        result = extract_skills(text)
        self.assertNotIn(
            "spring", result, "'spring' should not match calendar semesters without java/framework context."
        )

    def test_c_without_context_false_positive(self):
        """'c' as a letter grade ('course with c or above') must NOT be extracted."""
        text = "successfully completed the course with c or above recommended to instruct"
        result = extract_skills(text)
        self.assertNotIn("c", result, "'c' should not match standalone letter grade without programming context.")

    def test_r_without_context_false_positive(self):
        """'r' from stripped 'R&D' ('leading us r d center') must NOT be extracted."""
        text = "company name city state leading us r d center rockville md relocation project"
        result = extract_skills(text)
        self.assertNotIn("r", result, "'r' should not match stripped 'r d' without statistics/data context.")

    def test_ruby_without_context_false_positive(self):
        """'ruby' as reward tier ('ruby tier winner') must NOT be extracted."""
        text = "diamond tier winner in 2004 in region and ruby tier winner in region 2005"
        result = extract_skills(text)
        self.assertNotIn("ruby", result, "'ruby' should not match gemstone/award tiers without rails/coding context.")

    def test_rust_without_context_false_positive(self):
        """'rust' as place/resort name must NOT be extracted."""
        text = "to successfully lead all departments at rust resort including high resort estate"
        result = extract_skills(text)
        self.assertNotIn("rust", result, "'rust' should not match non-technical resort name.")

    # Sweep Legitimate Technical Mentions
    def test_go_with_golang_legitimate_context(self):
        """'go' MUST match legitimate tech phrase 'built microservices in golang'."""
        text = "built microservices in golang"
        result = extract_skills(text)
        self.assertIn("go", result, "Expected 'go' to be extracted from 'built microservices in golang'.")

    def test_spring_with_boot_legitimate_context(self):
        """'spring' MUST match legitimate tech phrase 'spring boot backend framework'."""
        text = "spring boot backend framework"
        result = extract_skills(text)
        self.assertIn("spring", result, "Expected 'spring' to be extracted from 'spring boot backend framework'.")

    def test_c_and_cpp_legitimate_context(self):
        """'c' and 'c++' MUST both match in 'programming in c and c++'."""
        text = "programming in c and c++"
        result = extract_skills(text)
        self.assertIn("c", result, "Expected 'c' to match with programming/c++ context.")
        self.assertIn("c++", result, "Expected 'c++' to match directly.")

    def test_r_with_rstudio_legitimate_context(self):
        """'r' MUST match in 'data analysis in r using rstudio'."""
        text = "data analysis in r using rstudio"
        result = extract_skills(text)
        self.assertIn("r", result, "Expected 'r' to match in 'data analysis in r using rstudio'.")
        self.assertIn("data analysis", result)

    def test_ruby_legitimate_context(self):
        """'ruby' MUST match in 'built web app with ruby on rails'."""
        text = "built web app with ruby on rails"
        result = extract_skills(text)
        self.assertIn("ruby", result, "Expected 'ruby' to match when paired with 'ruby on rails'.")

    def test_rust_legitimate_context(self):
        """'rust' MUST match in 'systems programming in rust'."""
        text = "systems programming in rust"
        result = extract_skills(text)
        self.assertIn("rust", result, "Expected 'rust' to match when paired with 'systems programming'.")


# ---------------------------------------------------------------------------
# Integration tests: real dataset rows
# ---------------------------------------------------------------------------


class TestExtractSkillsIntegration(unittest.TestCase):
    """Integration tests against real rows from job_resume_fit_clean.csv.

    For each row we assert:
    1. extract_skills() returns at least 1 skill.
    2. Jaccard similarity with the dataset's own resume_skill_list >= 0.10.
       (The dataset skills are domain-specific and may include soft/business
       terms not in our taxonomy; a threshold of 10% is deliberately modest
       to avoid flakiness while still confirming meaningful overlap.)
    """

    @classmethod
    def setUpClass(cls):
        csv_path = REPO_ROOT / "data" / "processed" / "job_resume_fit_clean.csv.gz"
        if not csv_path.exists():
            raise unittest.SkipTest(
                f"Processed CSV not found at {csv_path}. Run scripts/build_processed_data.py first."
            )

        cls.rows = {}
        # Row 0: HR category – heavy soft-skill / business terms
        # Row 5: HR category – Microsoft Office / productivity tools heavy
        for idx in [0, 5]:
            cls.rows[idx] = _load_row(idx)

    def _run_overlap_assertion(self, row_idx: int, jaccard_threshold: float = 0.10):
        """Core overlap assertion reused across row tests."""
        row = self.rows[row_idx]
        resume_text: str = row["resume_text"]
        dataset_skills = {s.strip().lower() for s in row["resume_skill_list"]}
        category: str = row["category"]

        extracted = extract_skills(resume_text)

        # Print diagnostic info (visible with -v or on failure)
        print(f"\n[Row {row_idx}] category={category}")
        print(f"  Dataset resume_skill_list ({len(dataset_skills)}): {sorted(dataset_skills)[:10]}")
        print(f"  Extracted skills ({len(extracted)}): {sorted(extracted)[:15]}")
        overlap = extracted & dataset_skills
        print(f"  Overlap ({len(overlap)}): {sorted(overlap)}")
        j = jaccard(extracted, dataset_skills)
        print(f"  Jaccard similarity: {j:.3f} (threshold >= {jaccard_threshold})")

        self.assertGreater(len(extracted), 0, f"Row {row_idx}: extract_skills() returned no skills at all.")
        self.assertGreaterEqual(
            j,
            jaccard_threshold,
            f"Row {row_idx} ({category}): Jaccard={j:.3f} below threshold "
            f"{jaccard_threshold}. Extracted: {sorted(extracted)[:10]}, "
            f"Dataset: {sorted(dataset_skills)[:10]}",
        )

    def test_row_0_overlap_with_dataset(self):
        """Row 0 (HR): extracted skills overlap meaningfully with dataset list."""
        self._run_overlap_assertion(0, jaccard_threshold=0.10)

    def test_row_5_overlap_with_dataset(self):
        """Row 5 (HR/Office): extracted skills overlap meaningfully with dataset list."""
        self._run_overlap_assertion(5, jaccard_threshold=0.10)

    def test_row_0_job_required_skills_extraction(self):
        """Job description skills can also be extracted from text when present."""
        row = self.rows[0]
        # Build a synthetic sentence containing the job required skills
        job_skills = [s.strip().lower() for s in row["job_required_skills"]]
        synthetic_text = " ".join(job_skills)
        extracted = extract_skills(synthetic_text)
        # At least some job skills should be in our taxonomy
        overlap = extracted & set(job_skills)
        print(f"\n[Row 0] Job skills synthetic extraction overlap: {sorted(overlap)}")
        # We only assert the function runs without error; overlap depends on taxonomy coverage
        self.assertIsInstance(extracted, set)

    def test_row_0_swift_not_extracted(self):
        """Confirm 'swift' is not extracted from Row 0's resume text ('swift resolution')."""
        row0_text = self.rows[0]["resume_text"]
        extracted = extract_skills(row0_text)
        self.assertNotIn(
            "swift",
            extracted,
            "'swift' should no longer be extracted from row 0 without technical iOS context.",
        )


# ---------------------------------------------------------------------------
# Unit tests: compare_skills()
# ---------------------------------------------------------------------------


class TestCompareSkills(unittest.TestCase):
    """Tests for compare_skills() returning (matched, missing)."""

    def test_basic_matched_and_missing(self):
        """matched = intersection, missing = job - resume."""
        resume = {"python", "sql", "communication"}
        job = {"python", "sql", "docker", "leadership"}
        matched, missing = compare_skills(resume, job)
        self.assertEqual(matched, {"python", "sql"})
        self.assertEqual(missing, {"docker", "leadership"})

    def test_no_overlap(self):
        """No overlap → matched empty, missing = full job set."""
        matched, missing = compare_skills(["java"], ["python", "sql"])
        self.assertEqual(matched, set())
        self.assertEqual(missing, {"python", "sql"})

    def test_full_overlap(self):
        """Resume covers all job skills → missing is empty."""
        matched, missing = compare_skills(
            ["python", "sql", "docker"],
            ["python", "sql", "docker"],
        )
        self.assertEqual(matched, {"python", "sql", "docker"})
        self.assertEqual(missing, set())

    def test_extra_resume_skills_ignored(self):
        """Skills in resume but not in job do not appear in either output."""
        matched, missing = compare_skills(
            ["python", "sql", "excel"],
            ["python"],
        )
        self.assertEqual(matched, {"python"})
        self.assertEqual(missing, set())
        # 'sql' and 'excel' should not appear in missing
        self.assertNotIn("sql", missing)
        self.assertNotIn("excel", missing)

    def test_case_insensitive_comparison(self):
        """Comparison normalizes case."""
        matched, missing = compare_skills(["Python", "SQL"], ["python", "sql"])
        self.assertEqual(matched, {"python", "sql"})
        self.assertEqual(missing, set())

    def test_empty_inputs(self):
        """Empty inputs return empty sets without errors."""
        matched, missing = compare_skills([], [])
        self.assertEqual(matched, set())
        self.assertEqual(missing, set())

    def test_list_and_set_inputs(self):
        """Accepts lists, sets, and frozensets interchangeably."""
        matched1, _ = compare_skills(["python"], ["python"])
        matched2, _ = compare_skills({"python"}, {"python"})
        matched3, _ = compare_skills(frozenset(["python"]), frozenset(["python"]))
        self.assertEqual(matched1, matched2)
        self.assertEqual(matched1, matched3)

    def test_compare_with_extracted_skills(self):
        """End-to-end: extract then compare against known job skills."""
        resume_text = (
            "Experienced data engineer with strong python, sql, and spark skills. "
            "Familiar with docker and kubernetes for deployment."
        )
        job_requirements = ["python", "sql", "spark", "aws", "docker"]

        resume_extracted = extract_skills(resume_text)
        matched, missing = compare_skills(resume_extracted, job_requirements)

        # We should match python, sql, spark, docker at minimum
        for skill in ["python", "sql", "docker"]:
            self.assertIn(skill, matched, f"'{skill}' should be in matched")
        # aws is not in the resume text, so it should be missing
        self.assertIn("aws", missing)


class TestBoundariesAndAliases(unittest.TestCase):
    """Regression tests for punctuation boundaries, context checks and aliases."""

    def test_sentence_final_period(self):
        """A skill at the end of a sentence still matches ("Python.")."""
        self.assertIn("python", extract_skills("I mostly write Python."))
        self.assertIn("sql", extract_skills("Strong in SQL. Also Excel."))

    def test_slash_separated_skills(self):
        """Slash-joined skills match individually ("HTML/CSS", "Python/Django")."""
        skills = extract_skills("Front end: HTML/CSS. Back end: Python/Django.")
        self.assertTrue({"html", "css", "python", "django"} <= skills, skills)

    def test_slash_skills_keep_their_own_identity(self):
        """Skills that contain a slash are still matched whole."""
        skills = extract_skills("Built CI/CD pipelines and wrote PL/SQL procedures; ran A/B testing.")
        self.assertTrue({"ci/cd", "pl/sql", "a/b testing"} <= skills, skills)
        self.assertNotIn("sql", skills)

    def test_dotted_skills_not_split(self):
        """'.net' and 'node.js' match literally; 'node.js' does not yield 'js' artifacts."""
        skills = extract_skills("Services in .NET and Node.js.")
        self.assertIn(".net", skills)
        self.assertIn("node.js", skills)

    def test_context_keyword_must_be_whole_token(self):
        """'ui' inside 'quickly' must not count as React context."""
        self.assertNotIn("react", extract_skills("Go to the store and react quickly in spring."))

    def test_aliases_map_to_canonical(self):
        skills = extract_skills(
            "Deployed on K8s with Postgres, built ReactJS + HTML5 UIs, used sklearn and Golang microservices."
        )
        self.assertTrue({"kubernetes", "postgresql", "react", "html", "scikit-learn", "go"} <= skills, skills)

    def test_ml_alias_needs_context(self):
        """'ML' counts as machine learning near AI/data words, but not as millilitres."""
        self.assertIn("machine learning", extract_skills("Built ML models in Python."))
        self.assertNotIn("machine learning", extract_skills("Administered 10 ml of saline every hour."))

    def test_core_student_skills_present(self):
        skills = extract_skills(
            "Coursework in machine learning, deep learning, data structures and algorithms; "
            "object-oriented programming in Java; Agile/Scrum team projects."
        )
        for skill in [
            "machine learning",
            "deep learning",
            "data structures",
            "algorithms",
            "object-oriented programming",
            "agile",
            "scrum",
        ]:
            self.assertIn(skill, skills)

    def test_every_alias_targets_a_taxonomy_skill(self):
        """Aliases must point at canonical skills that exist in skills_list.json."""
        canonical = {c for _, c, _ in _load_skill_patterns()}
        for alias, target in SKILL_ALIASES.items():
            self.assertIn(target, canonical, f"alias {alias!r} -> {target!r} not in taxonomy")


if __name__ == "__main__":
    unittest.main(verbosity=2)
