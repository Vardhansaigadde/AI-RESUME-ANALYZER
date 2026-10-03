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
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

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


# Unambiguous surface forms that should count as a canonical taxonomy skill.
# Matched with the same boundary rules as the skills themselves; an alias is
# only used if its canonical target exists in skills_list.json.
SKILL_ALIASES: Dict[str, str] = {
    # Languages & runtimes
    "golang": "go",
    "cpp": "c++",
    "c plus plus": "c++",
    "c sharp": "c#",
    "dotnet": ".net",
    "asp.net": ".net",
    "es6": "javascript",
    "ecmascript": "javascript",
    "html5": "html",
    "css3": "css",
    "nodejs": "node.js",
    "node js": "node.js",
    "reactjs": "react",
    "react.js": "react",
    "react js": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "angularjs": "angular",
    "angular.js": "angular",
    "spring boot": "spring",
    # Data & ML
    "ml": "machine learning",
    "ai/ml": "machine learning",
    "aiml": "machine learning",
    "nlp": "natural language processing",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "tensorflow 2": "tensorflow",
    "keras": "deep learning",
    "power-bi": "power bi",
    "powerbi": "power bi",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "ms word": "word",
    "microsoft word": "word",
    "ms powerpoint": "powerpoint",
    "microsoft powerpoint": "powerpoint",
    "ms office": "microsoft office",
    "dsa": "data structures",
    "oop": "object-oriented programming",
    "oops": "object-oriented programming",
    "object oriented programming": "object-oriented programming",
    # Databases
    "postgres": "postgresql",
    "mongo db": "mongodb",
    "mssql": "sql server",
    "ms sql": "sql server",
    "ms sql server": "sql server",
    "microsoft sql server": "sql server",
    # Cloud & DevOps
    "amazon web services": "aws",
    "google cloud platform": "gcp",
    "microsoft azure": "azure",
    "k8s": "kubernetes",
    "ci cd": "ci/cd",
    "ci/cd pipelines": "ci/cd",
    "continuous integration": "ci/cd",
    "github actions": "ci/cd",
    "restful api": "rest api",
    "restful apis": "rest api",
    "rest apis": "rest api",
    "restful services": "rest api",
    "rest services": "rest api",
    "restful web services": "rest api",
    # Business tools
    "salesforce.com": "salesforce",
    "intuit quickbooks": "quickbooks",
    "adobe photoshop": "photoshop",
    "adobe illustrator": "illustrator",
    "adobe indesign": "indesign",
    "emr": "electronic medical record systems",
    "ehr": "electronic medical record systems",
    "a/p": "accounts payable",
    "a/r": "accounts receivable",
    "intravenous": "iv therapy",
    "registered nurse": "nursing",
    "rn": "nursing",
}

# Aliases that are also common non-technical abbreviations and therefore need
# nearby technical context (e.g. "ml" is also millilitres in nursing resumes).
ALIAS_CONTEXT: Dict[str, Tuple[str, ...]] = {
    "ml": (
        "ai",
        "machine",
        "artificial",
        "data",
        "python",
        "model",
        "models",
        "engineer",
        "engineering",
        "nlp",
        "deep",
        "scikit-learn",
        "tensorflow",
        "pytorch",
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
            # Multi-word keyword: must appear as a whole phrase in the window
            if re.search(r"(?<![a-z0-9])" + re.escape(kw_norm) + r"(?![a-z0-9])", window_str):
                return True
        elif kw_norm in window_tokens_set:
            # Single-word keyword: whole-token match only ("ui" must not match "quickly")
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
      skill tokens ( + # - ' and a token-continuing "." ). This lets "c++" match literally while
      "c" does NOT fire inside "accord" or "architect".
    - The pattern is case-insensitive.

    Args:
        skill: Lowercased skill string from the taxonomy.

    Returns:
        Compiled regex pattern.
    """
    # Characters that, when adjacent, mean the match is part of a larger token
    # (e.g. "c" inside "c++" or "accord"). "/" is deliberately NOT included so
    # "HTML/CSS" and "Python/Django" match both skills, and a trailing "." only
    # blocks a match when it continues a token (".net", "node.js"), so
    # sentence-final "Python." still matches.
    _WORD_CHARS = r"a-z0-9\+\#\-'"

    target = re.escape(skill)

    pattern = (
        r"(?<![" + _WORD_CHARS + r"])(?<![a-z0-9]\.)"
        + target
        + r"(?![" + _WORD_CHARS + r"])(?!\.[a-z0-9])"
    )
    return re.compile(pattern, re.IGNORECASE)


@lru_cache(maxsize=1)
def _load_skill_patterns(
    skills_json: Path = _SKILLS_JSON,
) -> Tuple[Tuple[str, str, re.Pattern], ...]:
    """Load skills list plus aliases and pre-compile regex patterns (cached).

    Every taxonomy skill matches itself; every entry in SKILL_ALIASES whose
    canonical target exists in the taxonomy is added as an extra surface form.
    Surface forms are sorted longest-first so multi-word phrases (e.g.,
    "machine learning") are matched before their constituent tokens
    ("learning").

    Args:
        skills_json: Path to skills_list.json.

    Returns:
        Tuple of (surface_form, canonical_skill, compiled_pattern), longest first.

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
    surface_to_canonical: Dict[str, str] = {}
    for s in raw_skills:
        norm = s.strip().lower()
        if norm and norm not in surface_to_canonical:
            surface_to_canonical[norm] = norm

    for alias, canonical in SKILL_ALIASES.items():
        alias_norm = alias.strip().lower()
        if canonical not in surface_to_canonical:
            logger.warning("Skill alias '%s' targets unknown skill '%s'; skipped.", alias, canonical)
            continue
        surface_to_canonical.setdefault(alias_norm, canonical)

    # Sort: longest (by token count, then char count) first so multi-word
    # phrases match before their shorter substrings
    surfaces = sorted(
        surface_to_canonical, key=lambda s: (len(s.split()), len(s)), reverse=True
    )

    patterns = tuple(
        (surface, surface_to_canonical[surface], _build_skill_pattern(surface))
        for surface in surfaces
    )
    logger.info(
        "Loaded and compiled %d skill patterns (%d skills + aliases) from %s.",
        len(patterns),
        len(set(surface_to_canonical.values())),
        skills_json,
    )
    return patterns


def _context_keywords_for(surface: str, canonical: str) -> Optional[Tuple[str, ...]]:
    """Return the context keywords a surface form needs, or None if unambiguous."""
    if surface in ALIAS_CONTEXT:
        return ALIAS_CONTEXT[surface]
    if surface == canonical and canonical in CONTEXT_DEPENDENT_SKILLS:
        return CONTEXT_DEPENDENT_SKILLS[canonical]
    return None


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
    - Aliases (SKILL_ALIASES, e.g. "k8s", "reactjs", "postgres") are reported
      under their canonical skill name.

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

    # Context is checked against the unmasked lowercased text; matching runs on
    # a mutable copy where consumed spans are masked to prevent sub-string
    # re-matches (e.g., "time management" consuming "management").
    lowered = text.lower()
    working = lowered

    for surface, canonical, pattern in patterns:
        required_context = _context_keywords_for(surface, canonical)
        if required_context is not None:
            matched = any(
                _has_required_context(
                    lowered,
                    match.start(),
                    match.end(),
                    required_context,
                    window_words=5,
                )
                for match in pattern.finditer(working)
            )
        else:
            matched = pattern.search(working) is not None

        if matched:
            found.add(canonical)
            # Mask all occurrences of this surface form in the working copy
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
