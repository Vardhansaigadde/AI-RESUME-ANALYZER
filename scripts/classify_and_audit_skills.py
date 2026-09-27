"""Audit and classify skills from taxonomy and inspect ranks 300-800.

1. Classifies the top 300 skills in app/data/skills_list.json into:
   - "technical" (programming languages, tools, frameworks, platforms, software)
   - "soft/business" (interpersonal, behavioral, generic business terms)
2. Prints category counts and the full list of technical skills found.
3. Analyzes skills ranked 300-800 by frequency from job_resume_fit_clean.csv
   and identifies critical technical skills excluded by the cutoff.
"""

from collections import Counter
import json
import logging
from pathlib import Path
import re
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.services.data_cleaning import safe_parse_skills
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("classify_skills")

# Known exact technical names, software, languages, and tools
EXACT_TECH_KEYWORDS = {
    # Office & productivity suites
    "excel", "microsoft excel", "powerpoint", "microsoft powerpoint",
    "word", "microsoft word", "outlook", "microsoft office",
    "microsoft office suite", "ms office", "microsoft project",
    # Programming & Web technologies
    "html", "css", "javascript", "python", "java", "c++", "c#", "c",
    "php", "sql", "mysql", "r", "ruby", "matlab",
    # Design, CAD & Creative tools
    "autocad", "cad", "adobe creative suite", "photoshop", "illustrator",
    "indesign", "figma", "sketch", "revit", "solidworks", "visio",
    # Enterprise & Cloud software
    "sap", "oracle", "salesforce", "crm (salesforce)", "quickbooks",
    "sharepoint", "google analytics", "hris", "erp", "crm",
    # Infrastructure, OS, Tech concepts
    "linux", "unix", "seo", "a/b testing", "cybersecurity", "video editing",
    "network architecture", "it infrastructure management",
    "server management", "infrastructure automation", "automation",
    "hardware", "programming",
}

# Regex pattern for technical suffixes indicating software, tools, platforms, or systems
TECH_PATTERN = re.compile(
    r"\b(software|platform|platforms|system|systems|database|databases|cloud|tools?|virtualization|technologies|technology)\b",
    re.IGNORECASE,
)

# Overrides for terms that contain technical keywords but are soft/business/domain-specific non-software
NON_TECH_OVERRIDES = {
    "safety program implementation",
    "training program development",
    "business process design",
    "assessment design",
    "building codes",
    "cooking techniques",
    "cpr/aed certification",
    "servsafe manager certification",
    "personal training certification",
    "technical report writing",
    "technical guidance",
    "troubleshooting techniques",
    "troubleshooting",
    "analytical thinking",
    "special populations knowledge",
    "standards-aligned curriculum",
}


def is_technical_skill(skill: str) -> bool:
    """Classify a skill string as technical or soft/business using heuristic rules."""
    s = skill.lower().strip()
    if s in NON_TECH_OVERRIDES:
        return False
    if s in EXACT_TECH_KEYWORDS:
        return True
    if TECH_PATTERN.search(s):
        return True
    return False


def main():
    skills_json_path = REPO_ROOT / "app" / "data" / "skills_list.json"
    clean_csv_path = REPO_ROOT / "data" / "processed" / "job_resume_fit_clean.csv"

    # -------------------------------------------------------------------------
    # 1. Classify the 300 exported skills
    # -------------------------------------------------------------------------
    with open(skills_json_path, "r", encoding="utf-8") as f:
        skills_300 = json.load(f)

    technical_skills = []
    soft_business_skills = []

    for skill in skills_300:
        if is_technical_skill(skill):
            technical_skills.append(skill)
        else:
            soft_business_skills.append(skill)

    print("=" * 70)
    print("PART 1: CLASSIFICATION OF TOP 300 EXPORTED SKILLS")
    print("=" * 70)
    print(f"Total Skills Evaluated : {len(skills_300)}")
    print(f"Technical Skills       : {len(technical_skills)} ({len(technical_skills)/len(skills_300)*100:.1f}%)")
    print(f"Soft / Business Skills : {len(soft_business_skills)} ({len(soft_business_skills)/len(skills_300)*100:.1f}%)")
    print("-" * 70)
    print(f"FULL LIST OF TECHNICAL SKILLS FOUND ({len(technical_skills)} total):")
    print("-" * 70)
    for idx, skill in enumerate(technical_skills, start=1):
        print(f" {idx:2d}. {skill}")

    # -------------------------------------------------------------------------
    # 2. Analyze skills ranked 300-800 by frequency
    # -------------------------------------------------------------------------
    df = pd.read_csv(clean_csv_path)
    skill_counter = Counter()

    for col in ["job_required_skills", "resume_skill_list", "ai_matched_skills"]:
        for raw_val in df[col]:
            parsed = safe_parse_skills(raw_val)
            if parsed:
                for s in parsed:
                    norm = s.strip().lower()
                    if norm:
                        skill_counter[norm] += 1

    all_sorted = skill_counter.most_common()
    skills_300_to_800 = all_sorted[300:800]

    excluded_tech = []
    for rank, (skill, count) in enumerate(skills_300_to_800, start=301):
        if is_technical_skill(skill):
            excluded_tech.append((rank, skill, count))

    print("\n" + "=" * 70)
    print("PART 2: EXCLUDED TECHNICAL SKILLS IN RANKS 300-800")
    print("=" * 70)
    print(f"Total skills examined in ranks 300-800 : {len(skills_300_to_800)}")
    print(f"Technical skills excluded by cutoff   : {len(excluded_tech)}")
    print("-" * 70)
    print(f"{'Rank':<6} {'Skill':<35} {'Frequency':>10}")
    print("-" * 70)
    for rank, skill, count in excluded_tech:
        print(f"{rank:<6} {skill:<35} {count:>10,}")
    print("=" * 70)


if __name__ == "__main__":
    main()
