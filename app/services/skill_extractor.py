"""Skill extraction and comparison service.

Loads the skills taxonomy from app/data/skills_list.json and provides:
- extract_skills(text): Finds all known skills present in a text string
  using word-boundary-safe regex matching. Multi-word skills (e.g., "data
  analysis") are matched as complete phrases. Short ambiguous tokens like
  "r", "c", "go", "c#" use strict word-boundary rules to avoid partial
  matches inside words like "trainer" or "accord". Context-dependent skills
  (e.g., "swift", "react", "spark", "go", "spring", "c", "r", "ruby", "rust")
  require nearby domain-specific terms to avoid false positives from everyday
  English usage, grades, academic semesters, or proper names.
- compare_skills(resume_skills, job_skills): Given two skill sets, returns
  (matched, missing) sets indicating overlap and gaps.
"""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, FrozenSet, List, Set, Tuple

logger = logging.getLogger(__name__)

# Path to the combined data-derived + curated skills list
_SKILLS_JSON = Path(__file__).resolve().parent.parent / "data" / "skills_list.json"

# Ambiguous / polysemous skills that require nearby contextual keywords
# (within a window of ~5 words) to avoid false positives from everyday English,
# course grades, academic calendar semesters, or non-technical proper names.
CONTEXT_DEPENDENT_SKILLS: Dict[str, Tuple[str, ...]] = {
    "swift": (
        "ios",
        "apple",
        "xcode",
        "mobile development",
        "programming language",
        "mobile",
        "app",
        "apps",
        "swiftui",
        "cocoa",
    ),
    "react": (
        "javascript",
        "frontend",
        "front-end",
        "component",
        "redux",
        "ui",
        "react native",
        "js",
        "jsx",
        "web",
    ),
    "spark": (
        "hadoop",
        "databricks",
        "pyspark",
        "big data",
        "apache",
        "data engineering",
        "data engineer",
    ),
    "go": (
        "golang",
        "backend",
        "microservices",
        "docker",
        "kubernetes",
        "developer",
        "programming",
    ),
    "spring": (
        "java",
        "boot",
        "spring boot",
        "framework",
        "mvc",
        "backend",
        "microservices",
        "hibernate",
    ),
    "c": (
        "c++",
        "programming",
        "embedded",
        "algorithms",
        "linux",
        "assembly",
        "developer",
        "language",
    ),
    "r": (
        "python",
        "statistics",
        "data analysis",
        "modeling",
        "rstudio",
        "spss",
        "programming",
        "language",
    ),
    "ruby": (
        "rails",
        "ruby on rails",
        "programming",
        "gem",
        "developer",
        "backend",
    ),
    "rust": (
        "programming",
        "developer",
        "systems",
        "cargo",
        "memory",
        "backend",
    ),
}


def _has_required_context(
    text: str,
    match_start: int,
    match_end: int,
    context_keywords: Tuple[str, ...],
    window_words: int = 5,
) -> bool:
    """Check whether any required context keyword appears within window_words of the match.

    Args:
        text: Original unmasked text string.
        match_start: Starting character offset of the matched skill.
        match_end: Ending character offset of the matched skill.
        context_keywords: Tuple of keywords (any single match satisfies the guard).
        window_words: Number of words before and after the match to inspect (default: 5).

    Returns:
        True if at least one context keyword is present in the surrounding window, else False.
    """
    matched_token = text[match_start:match_end].lower()

    # If the candidate explicitly wrote 'golang' for the 'go' skill, it is unambiguous
    if matched_token == "golang":
        return True

    pre_tokens = re.findall(r"[a-z0-9\+\#\.\-]+", text[:match_start].lower())
    post_tokens = re.findall(r"[a-z0-9\+\#\.\-]+", text[match_end:].lower())

    nearby_pre = pre_tokens[-window_words:] if pre_tokens else []
    nearby_post = post_tokens[:window_words] if post_tokens else []

    window_tokens_set = set(nearby_pre + nearby_post)
    window_str = " ".join(nearby_pre + [matched_token] + nearby_post)

    for kw in context_keywords:
        kw_norm = kw.lower().strip()
        if " " in kw_norm:
            if kw_norm in window_str:
                return True
        else:
            if kw_norm in window_tokens_set or kw_norm in window_str:
                return True
    return False


def _build_skill_pattern(skill: str) -> re.Pattern:
    """Compile a word-boundary-safe regex pattern for a skill string.

    Strategy:
    - Escape the skill so special characters (e.g., "+", "#", ".") are
      treated literally.
    - For 'go', match either 'go' or 'golang' at word boundaries.
    - Use a *lookbehind* and *lookahead* that rejects adjacent alphanumeric
      characters and symbol chars that legitimately appear inside
      skill tokens ( + # . - / ' ). This lets "c++" match literally while
      "c" does NOT fire inside "accord" or "architect".
    - The pattern is case-insensitive.

    Args:
        skill: Lowercased skill string from the taxonomy.

    Returns:
        Compiled regex pattern.
    """
    _WORD_CHARS = r"a-z0-9\+\#\.\-/\'"

    if skill == "go":
        target = r"(?:go|golang)"
    else:
        target = re.escape(skill)

    pattern = (
        r"(?<![" + _WORD_CHARS + r"])"
        + target
        + r"(?![" + _WORD_CHARS + r"])"
    )
    return re.compile(pattern, re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_skill_patterns(
    skills_json: Path = _SKILLS_JSON,
) -> Tuple[Tuple[str, re.Pattern], ...]:
    """Load skills list and pre-compile regex patterns, cached after first load.

    Skills are sorted longest-first so multi-word phrases (e.g., "machine
    learning") are matched before their constituent tokens ("learning").

    Args:
        skills_json: Path to skills_list.json.

    Returns:
        Tuple of (skill_string, compiled_pattern) pairs, longest skill first.

    Raises:
        FileNotFoundError: If the skills JSON file does not exist.
    """
    if not skills_json.exists():
        raise FileNotFoundError(
            f"Skills list not found at: {skills_json}. "
            "Run scripts/build_skills_taxonomy.py to generate it."
        )

    with open(skills_json, "r", encoding="utf-8") as f:
        raw_skills: List[str] = json.load(f)

    # Normalize and deduplicate
    seen: set = set()
    skills: List[str] = []
    for s in raw_skills:
        norm = s.strip().lower()
        if norm and norm not in seen:
            seen.add(norm)
            skills.append(norm)

    # Sort: longest (by token count, then char count) first so multi-word
    # phrases match before their shorter substrings
    skills.sort(key=lambda s: (len(s.split()), len(s)), reverse=True)

    patterns = tuple(
        (skill, _build_skill_pattern(skill)) for skill in skills
    )
    logger.info(
        "Loaded and compiled %d skill patterns from %s.", len(patterns), skills_json
    )
    return patterns


def extract_skills(text: str) -> Set[str]:
    """Extract all known skills present in a text string.

    Matching is case-insensitive and word-boundary-safe:
    - Multi-word skills like "data analysis" are matched as complete phrases.
    - Single-character or short skills like "r", "c", "go" will NOT fire
      inside words (e.g., "trainer", "accord", "google" won't trigger "r",
      "c", "go" respectively).
    - Special-character skills like "c++", "c#", "node.js" are matched
      literally using escaped patterns ("c++" matches directly and does not
      require the "c" context guard).
    - Context-dependent skills (e.g., "swift", "react", "spark", "go",
      "spring", "c", "r", "ruby", "rust") require nearby domain terms
      within 5 words to confirm technical usage.

    Once a skill phrase is matched, the matched span is consumed (replaced
    with spaces in a working copy) so overlapping sub-matches are suppressed.

    Args:
        text: Raw or cleaned resume/job description text.

    Returns:
        Set of canonical skill strings found in the text.
    """
    if not text or not isinstance(text, str):
        return set()

    patterns = _load_skill_patterns()
    found: Set[str] = set()

    # Work on a lowercased mutable copy; mask consumed spans to prevent
    # sub-string re-matches (e.g., "time management" consuming "management")
    working = text.lower()

    for skill, pattern in patterns:
        if skill in CONTEXT_DEPENDENT_SKILLS:
            required_context = CONTEXT_DEPENDENT_SKILLS[skill]
            # Must find at least one match instance with valid surrounding context
            has_valid_match = False
            for match in pattern.finditer(working):
                if _has_required_context(
                    text,
                    match.start(),
                    match.end(),
                    required_context,
                    window_words=5,
                ):
                    has_valid_match = True
                    break

            if has_valid_match:
                found.add(skill)
                # Mask matched occurrences with spaces
                working = pattern.sub(lambda m: " " * len(m.group(0)), working)
        else:
            if pattern.search(working):
                found.add(skill)
                # Mask all occurrences of this skill in the working copy
                working = pattern.sub(lambda m: " " * len(m.group(0)), working)

    return found


def compare_skills(
    resume_skills: FrozenSet[str] | Set[str] | List[str],
    job_skills: FrozenSet[str] | Set[str] | List[str],
) -> Tuple[Set[str], Set[str]]:
    """Compare resume skills against job requirements.

    Args:
        resume_skills: Skills present in the candidate's resume.
        job_skills: Skills required by the job description.

    Returns:
        Tuple of (matched, missing):
            - matched: Skills in both resume and job.
            - missing: Job skills absent from the resume.
    """
    resume_set = {s.strip().lower() for s in resume_skills if s}
    job_set = {s.strip().lower() for s in job_skills if s}

    matched = resume_set & job_set
    missing = job_set - resume_set
    return matched, missing
