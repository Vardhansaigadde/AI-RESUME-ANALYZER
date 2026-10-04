"""Data cleaning and preprocessing service module.

Provides reusable functions to:
1. Clean raw resume and job description text (lowercasing, HTML artifact removal,
   whitespace normalization, while preserving alphanumeric characters and
   domain-specific technical punctuation like '+', '#', '.', '-', '/').
2. Safely parse stringified list columns from CSVs into real Python lists using
   ast.literal_eval, with robust error logging and handling for malformed rows.
"""

import ast
import html
import logging
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def clean_text(text: Any) -> str:
    """Clean raw resume or job description text.

    Transformations applied:
    - Decodes HTML entities (e.g. &nbsp;, &amp;)
    - Strips HTML tags (<...>)
    - Converts text to lowercase
    - Preserves alphanumeric characters and essential tech punctuation (+, #, ., -, /)
    - Replaces repeated dashes ('----') and ellipses ('...') with spaces
    - Normalizes multi-whitespace/newlines to a single space and strips edges.

    Args:
        text: Raw text string (or stringifiable object).

    Returns:
        Cleaned, normalized string.
    """
    if text is None or pd.isna(text):
        return ""

    if not isinstance(text, str):
        text = str(text)

    # 1. Decode HTML entities (e.g., &nbsp;, &lt;, &gt;)
    text = html.unescape(text)

    # 2. Strip HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # 3. Lowercase
    text = text.lower()

    # 4. Keep alphanumeric characters, spaces, and basic technical punctuation (+ # . - /)
    # This preserves terms like 'c++', 'c#', '.net', 'node.js', 'ci/cd', '15+ years'
    text = re.sub(r"[^a-z0-9\s+#./-]", " ", text)

    # 5. Clean up divider repeats (e.g. '------' or '.....')
    text = re.sub(r"[-]{2,}", " ", text)
    text = re.sub(r"\.{2,}", " ", text)

    # 6. Normalize excess whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def strip_leading_title(text: Any, max_tokens: int = 12) -> str:
    """Remove a resume's leading ALL-CAPS headline (e.g. "SALES ASSOCIATE Summary ...").

    Most resumes in data/raw/Resume.csv open with an upper-case job title that
    often repeats the category label verbatim ("CONSULTANT", "SALES"), which
    lets a classifier read the answer instead of the content. Real user resumes
    usually open with a name instead, so evaluation uses this to measure
    accuracy without that shortcut. Operates on raw (not lower-cased) text.

    Args:
        text: Raw resume text with original casing.
        max_tokens: Maximum number of leading tokens to drop.

    Returns:
        The text with the leading run of tokens that contain no lowercase
        letters removed (whitespace normalized).
    """
    if text is None or (not isinstance(text, str) and pd.isna(text)):
        return ""
    tokens = str(text).split()
    i = 0
    while i < len(tokens) and i < max_tokens and not re.search(r"[a-z]", tokens[i]):
        i += 1
    return " ".join(tokens[i:])


def safe_parse_skills(val: Any) -> list[str] | None:
    """Safely parse a stringified list of skills using ast.literal_eval.

    Reuses the validated logic from notebooks/01_explore_data.ipynb.
    If parsing fails due to ValueError, SyntaxError, or if the parsed object
    is not a list, logs a warning and returns None (allowing malformed rows
    to be identified and handled without crashing).

    Args:
        val: String representation of a list (e.g. "['python', 'sql']") or existing list.

    Returns:
        Parsed list of strings if successful, or None if malformed.
    """
    if val is None or pd.isna(val):
        return None

    if isinstance(val, list):
        return [str(item).strip() for item in val]

    if isinstance(val, str):
        trimmed = val.strip()
        if not trimmed:
            return []
        try:
            parsed = ast.literal_eval(trimmed)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed]
            logger.warning(
                "Parsed skill value is not a list (type: %s): %s",
                type(parsed).__name__,
                val[:100],
            )
            return None
        except (ValueError, SyntaxError) as err:
            logger.warning(
                "Malformed skill list string encountered: %s | Error: %s",
                val[:100],
                err,
            )
            return None

    logger.warning("Unexpected data type for skill value: %s (%s)", type(val), val)
    return None


def clean_resume_dataframe(
    df: pd.DataFrame,
    text_col: str = "Resume_str",
    drop_html: bool = True,
) -> pd.DataFrame:
    """Clean the raw Resume.csv DataFrame.

    - Cleans the raw resume text column.
    - Optionally drops the 'Resume_html' column.

    Args:
        df: Raw Resume DataFrame.
        text_col: Column name containing raw text (default: 'Resume_str').
        drop_html: Whether to drop 'Resume_html' column (default: True).

    Returns:
        Processed DataFrame with cleaned text.
    """
    cleaned_df = df.copy()

    if drop_html and "Resume_html" in cleaned_df.columns:
        cleaned_df = cleaned_df.drop(columns=["Resume_html"])

    if text_col in cleaned_df.columns:
        cleaned_df[text_col] = cleaned_df[text_col].apply(clean_text)

    return cleaned_df


def clean_job_fit_dataframe(
    df: pd.DataFrame,
    text_cols: list[str] | None = None,
    skill_cols: list[str] | None = None,
) -> tuple[pd.DataFrame, int]:
    """Clean the raw job_resume_fit.csv DataFrame.

    - Cleans resume_text and job_text columns.
    - Parses stringified list skill columns into Python lists using safe_parse_skills.
    - Drops and logs rows with malformed skill lists.

    Args:
        df: Raw job_resume_fit DataFrame.
        text_cols: List of text columns to clean (default: ['resume_text', 'job_text']).
        skill_cols: List of skill list columns to parse (default:
            ['job_required_skills', 'resume_skill_list', 'ai_matched_skills']).

    Returns:
        Tuple of (cleaned_df, num_dropped_rows).
    """
    if text_cols is None:
        text_cols = ["resume_text", "job_text"]
    if skill_cols is None:
        skill_cols = [
            "job_required_skills",
            "resume_skill_list",
            "ai_matched_skills",
        ]

    cleaned_df = df.copy()

    # Clean text columns
    for col in text_cols:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].apply(clean_text)

    # Safely parse skill list columns
    malformed_mask = pd.Series(False, index=cleaned_df.index)
    for col in skill_cols:
        if col in cleaned_df.columns:
            parsed_series = cleaned_df[col].apply(safe_parse_skills)
            # Mark rows where parsing failed
            col_malformed = parsed_series.isna()
            if col_malformed.any():
                logger.warning(
                    "Column '%s' had %d malformed rows.",
                    col,
                    col_malformed.sum(),
                )
            malformed_mask = malformed_mask | col_malformed
            cleaned_df[col] = parsed_series

    num_dropped = int(malformed_mask.sum())
    if num_dropped > 0:
        logger.warning(
            "Dropping %d rows due to malformed skill list parsing errors.",
            num_dropped,
        )
        cleaned_df = cleaned_df.loc[~malformed_mask].copy()

    return cleaned_df, num_dropped
