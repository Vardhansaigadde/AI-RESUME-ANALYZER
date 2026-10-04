"""Unit test for skills taxonomy building."""

import json
from pathlib import Path
import unittest

import pandas as pd

from scripts.build_skills_taxonomy import SKILL_SYNONYMS, build_skills_taxonomy


class TestSkillsTaxonomy(unittest.TestCase):
    def test_build_skills_taxonomy(self):
        tmp_csv = Path("scratch_test_fit.csv")
        tmp_json = Path("scratch_test_skills.json")

        df = pd.DataFrame(
            {
                "job_required_skills": ["['Python', 'SQL', 'Docker']"],
                "resume_skill_list": ["['Python', 'FastAPI']"],
                "ai_matched_skills": ["['Python']"],
            }
        )
        df.to_csv(tmp_csv, index=False)

        try:
            top_skills = build_skills_taxonomy(
                input_csv=tmp_csv,
                output_json=tmp_json,
                top_n=3,
                print_top=3,
            )
            self.assertEqual(len(top_skills), 3)
            self.assertEqual(top_skills[0], "python")

            with open(tmp_json, encoding="utf-8") as f:
                saved = json.load(f)
            self.assertEqual(saved, top_skills)
        finally:
            if tmp_csv.exists():
                tmp_csv.unlink()
            if tmp_json.exists():
                tmp_json.unlink()

    def test_synonym_canonicalization(self):
        tmp_csv = Path("scratch_test_synonyms.csv")
        tmp_json = Path("scratch_test_synonyms.json")

        df = pd.DataFrame(
            {
                "job_required_skills": ["['Microsoft Excel', 'Databases']"],
                "resume_skill_list": ["['MS Excel', 'Database Systems']"],
                "ai_matched_skills": ["['Excel', 'Database']"],
            }
        )
        df.to_csv(tmp_csv, index=False)

        try:
            top_skills = build_skills_taxonomy(
                input_csv=tmp_csv,
                output_json=tmp_json,
                top_n=2,
                print_top=2,
                synonym_map=SKILL_SYNONYMS,
            )
            self.assertEqual(top_skills, ["excel", "database"])
        finally:
            if tmp_csv.exists():
                tmp_csv.unlink()
            if tmp_json.exists():
                tmp_json.unlink()


if __name__ == "__main__":
    unittest.main()
