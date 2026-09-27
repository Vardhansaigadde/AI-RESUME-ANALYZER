"""Build skills taxonomy from processed job-resume dataset.

Aggregates skills from:
- job_required_skills
- resume_skill_list
- ai_matched_skills

Canonicalizes skill variants/synonyms BEFORE counting frequency, then
merges the data-derived top 300 with a curated list of essential technical
skills (app/data/curated_technical_skills.json), producing a union with no
duplicates. Saves the combined result to app/data/skills_list.json.
"""

from collections import Counter
import json
import logging
from pathlib import Path
import sys
from typing import Dict, List, Optional

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd
from app.services.data_cleaning import safe_parse_skills

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("build_skills_taxonomy")

# Manual canonical synonym mapping dict covering duplicates and variants.
# Applied BEFORE frequency counting so merged variants share one tally.
SKILL_SYNONYMS: Dict[str, str] = {
    # Databases & Data systems
    "databases": "database",
    "database systems": "database",
    # Microsoft & Office productivity tools
    "microsoft excel": "excel",
    "ms excel": "excel",
    "microsoft powerpoint": "powerpoint",
    "ms powerpoint": "powerpoint",
    "microsoft word": "word",
    "ms word": "word",
    "microsoft office suite": "microsoft office",
    "ms office": "microsoft office",
    "ms office suite": "microsoft office",
    "ms project": "microsoft project",
    "microsoft visio": "visio",
    "microsoft sharepoint": "sharepoint",
    "ms sharepoint": "sharepoint",
    # CRM & Salesforce
    "crm (salesforce)": "salesforce",
    "salesforce.com": "salesforce",
    "crm systems": "crm",
    # HRIS & ERP
    "hris systems": "hris",
    "erp systems": "erp",
    # Adobe & Design tools
    "adobe photoshop": "photoshop",
    "adobe illustrator": "illustrator",
    "adobe indesign": "indesign",
    # CAD / Engineering
    "computer-aided design (cad)": "cad",
    "computer aided design (cad)": "cad",
    # Financial / Accounting software
    "intuit quickbooks": "quickbooks",
    "quickbooks pro": "quickbooks",
    # Cloud
    "google cloud platform": "gcp",
    "google cloud": "gcp",
    "amazon web services": "aws",
    "microsoft azure": "azure",
    # Other common variants
    "node.js": "node.js",
    "nodejs": "node.js",
}


def load_curated_skills(curated_json: Path, synonym_map: Dict[str, str]) -> List[str]:
    """Load and canonicalize the curated technical skills list.

    Applies the same SKILL_SYNONYMS mapping to curated entries to resolve
    any overlap with data-derived canonical forms.

    Args:
        curated_json: Path to curated_technical_skills.json.
        synonym_map: Skill synonym mapping dict.

    Returns:
        List of canonicalized curated skill strings.
    """
    if not curated_json.exists():
        raise FileNotFoundError(f"Curated skills file not found: {curated_json}")

    with open(curated_json, "r", encoding="utf-8") as f:
        raw_curated = json.load(f)

    # Normalize and canonicalize using the same mapping
    canonicalized = []
    for skill in raw_curated:
        normalized = skill.strip().lower()
        canonical = synonym_map.get(normalized, normalized)
        if canonical:
            canonicalized.append(canonical)

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for s in canonicalized:
        if s not in seen:
            seen.add(s)
            deduped.append(s)

    logger.info(
        "Loaded curated skills: %d raw -> %d canonical (after synonym mapping and dedup).",
        len(raw_curated),
        len(deduped),
    )
    return deduped


def build_skills_taxonomy(
    input_csv: Path,
    output_json: Path,
    curated_json: Optional[Path] = None,
    top_n: int = 300,
    print_top: int = 50,
    synonym_map: Optional[Dict[str, str]] = None,
) -> List[str]:
    """Extract, canonicalize, merge with curated list, and compile skills.

    Process:
    1. Load processed dataset and count frequencies after synonym canonicalization.
    2. Take the top N data-derived skills by frequency.
    3. Load the curated technical skills list (if provided), canonicalize it.
    4. Merge: data-derived top N UNION curated list (no duplicates).
       Data-derived skills retain frequency ordering; curated additions appended after.
    5. Save combined result to output_json.

    Args:
        input_csv: Path to job_resume_fit_clean.csv.
        output_json: Path to save the final combined skills JSON array.
        curated_json: Optional path to curated_technical_skills.json.
        top_n: Number of top data-derived skills to include (default: 300).
        print_top: Number of top skills to display in frequency table (default: 50).
        synonym_map: Mapping of skill variants to canonical forms.

    Returns:
        Combined list of skills (data-derived top N union curated).
    """
    if synonym_map is None:
        synonym_map = SKILL_SYNONYMS

    logger.info("Loading processed dataset from: %s", input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Input file not found: {input_csv}")

    df = pd.read_csv(input_csv)
    logger.info("Loaded %d rows.", len(df))

    skill_cols = [
        "job_required_skills",
        "resume_skill_list",
        "ai_matched_skills",
    ]

    skill_counter: Counter = Counter()
    raw_unique_skills: set = set()
    total_tokens = 0

    for col in skill_cols:
        if col not in df.columns:
            logger.warning("Column '%s' not found in dataset, skipping.", col)
            continue

        for raw_val in df[col]:
            skills = safe_parse_skills(raw_val)
            if skills:
                for skill in skills:
                    normalized = skill.strip().lower()
                    if normalized:
                        raw_unique_skills.add(normalized)
                        # Canonicalize variant BEFORE counting frequency
                        canonical = synonym_map.get(normalized, normalized)
                        skill_counter[canonical] += 1
                        total_tokens += 1

    total_unique = len(skill_counter)
    logger.info(
        "Extracted %d total skill mentions (%d raw unique -> %d canonical unique).",
        total_tokens,
        len(raw_unique_skills),
        total_unique,
    )

    # Top N most frequent data-derived skills (frequency-ordered)
    top_n_tuples = skill_counter.most_common(top_n)
    top_n_skills = [skill for skill, _ in top_n_tuples]
    top_n_set = set(top_n_skills)

    # Print top print_top skills with counts
    print("\n" + "=" * 65)
    print(f"TOP {print_top} MOST FREQUENT CANONICAL SKILLS (out of {total_unique:,} unique)")
    print("=" * 65)
    print(f"{'Rank':<6} {'Skill':<35} {'Frequency':>12}")
    print("-" * 65)
    for rank, (skill, count) in enumerate(skill_counter.most_common(print_top), start=1):
        print(f"{rank:<6} {skill:<35} {count:>12,}")
    print("=" * 65 + "\n")

    # Load and merge curated skills
    curated_additions = []
    curated_skills_canonical = []
    if curated_json is not None:
        curated_skills_canonical = load_curated_skills(curated_json, synonym_map)
        # Only add skills NOT already in the data-derived top N
        for skill in curated_skills_canonical:
            if skill not in top_n_set:
                curated_additions.append(skill)

        logger.info(
            "Curated list: %d canonical skills. %d already in top %d, %d new additions.",
            len(curated_skills_canonical),
            len(curated_skills_canonical) - len(curated_additions),
            top_n,
            len(curated_additions),
        )

    # Final combined list: data-derived (frequency-ordered) + curated additions
    combined_skills = top_n_skills + curated_additions

    # Confirm all curated skills appear in the final output
    combined_set = set(combined_skills)
    missing_from_output = [s for s in curated_skills_canonical if s not in combined_set]

    # Save to JSON
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(combined_skills, f, indent=2, ensure_ascii=False)

    logger.info("Saved combined skills list to %s.", output_json)

    # Summary report
    print("=" * 65)
    print("MERGE SUMMARY")
    print("=" * 65)
    print(f"Data-derived top {top_n} skills    : {len(top_n_skills)}")
    print(f"Curated canonical skills total    : {len(curated_skills_canonical)}")
    print(f"  Already in top {top_n} (no-ops)  : {len(curated_skills_canonical) - len(curated_additions)}")
    print(f"  New curated additions           : {len(curated_additions)}")
    print(f"  {'-' * 40}")
    print(f"FINAL TOTAL SKILL COUNT           : {len(combined_skills)}")
    print("-" * 65)

    if missing_from_output:
        print(f"WARNING: {len(missing_from_output)} curated skills MISSING from output!")
        for s in missing_from_output:
            print(f"  MISSING: {s}")
    else:
        print(f"VERIFICATION PASSED: all {len(curated_skills_canonical)} curated skills")
        print(f"  are present in the final skills_list.json.")

    if curated_additions:
        print(f"\nNew technical skills added from curated list ({len(curated_additions)}):")
        for i, s in enumerate(curated_additions, 1):
            freq = skill_counter.get(s, 0)
            freq_note = f"(dataset freq: {freq})" if freq > 0 else "(not in dataset)"
            print(f"  {i:2d}. {s:<35} {freq_note}")
    print("=" * 65 + "\n")

    return combined_skills


def audit_excluded_tech_reentry(
    input_csv: Path,
    synonym_map: Dict[str, str],
    top_n: int = 300,
) -> None:
    """Check how many of the 59 previously excluded technical skills rank in top 300."""
    from scripts.classify_and_audit_skills import is_technical_skill

    df = pd.read_csv(input_csv)

    # Unmapped baseline to retrieve the exact excluded skills in ranks 300-800
    baseline_counter: Counter = Counter()
    for col in ["job_required_skills", "resume_skill_list", "ai_matched_skills"]:
        for raw_val in df[col]:
            parsed = safe_parse_skills(raw_val)
            if parsed:
                for s in parsed:
                    norm = s.strip().lower()
                    if norm:
                        baseline_counter[norm] += 1

    baseline_sorted = baseline_counter.most_common()
    baseline_300_800 = baseline_sorted[300:800]
    excluded_59 = [
        skill
        for rank, (skill, count) in enumerate(baseline_300_800, start=301)
        if is_technical_skill(skill)
    ]

    # Canonicalized counts
    canon_counter: Counter = Counter()
    for col in ["job_required_skills", "resume_skill_list", "ai_matched_skills"]:
        for raw_val in df[col]:
            parsed = safe_parse_skills(raw_val)
            if parsed:
                for s in parsed:
                    norm = s.strip().lower()
                    if norm:
                        canon = synonym_map.get(norm, norm)
                        canon_counter[canon] += 1

    top_300_tuples = canon_counter.most_common(top_n)
    rank_map = {skill: rank for rank, (skill, _) in enumerate(top_300_tuples, start=1)}

    reentered = []
    for orig_skill in excluded_59:
        canon_form = synonym_map.get(orig_skill, orig_skill)
        if canon_form in rank_map:
            reentered.append((orig_skill, canon_form, rank_map[canon_form], canon_counter[canon_form]))

    print("=" * 65)
    print("AUDIT: EXCLUDED TECHNICAL SKILLS NOW RANKING IN TOP 300")
    print("=" * 65)
    print(f"Total previously excluded technical skills : {len(excluded_59)}")
    print(f"Now ranking inside top {top_n}            : {len(reentered)}")
    print("-" * 65)
    print(f"{'New Rank':<10} {'Original Skill':<26} {'Canonical Form':<20} {'Frequency':>8}")
    print("-" * 65)
    for orig, canon, rank, cnt in sorted(reentered, key=lambda x: x[2]):
        print(f"{rank:<10} {orig:<26} {canon:<20} {cnt:>8,}")
    print("=" * 65 + "\n")


def main():
    input_path = REPO_ROOT / "data" / "processed" / "job_resume_fit_clean.csv"
    output_path = REPO_ROOT / "app" / "data" / "skills_list.json"
    curated_path = REPO_ROOT / "app" / "data" / "curated_technical_skills.json"

    build_skills_taxonomy(
        input_csv=input_path,
        output_json=output_path,
        curated_json=curated_path,
        top_n=300,
        print_top=50,
        synonym_map=SKILL_SYNONYMS,
    )

    audit_excluded_tech_reentry(
        input_csv=input_path,
        synonym_map=SKILL_SYNONYMS,
        top_n=300,
    )


if __name__ == "__main__":
    main()
