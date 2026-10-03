"""Pipeline script to generate cleaned, processed datasets.

Loads:
- data/raw/Resume.csv
- data/raw/job_resume_fit.csv

Applies cleaning and parsing:
- Cleans unstructured text (lowercasing, HTML tag stripping, whitespace normalization,
  preserving alphanumeric characters and technical symbols like +, #, ., -, /).
- Safely parses stringified skill lists with ast.literal_eval.
- Logs and drops any malformed rows.

Saves:
- data/processed/resume_clean.csv
- data/processed/job_resume_fit_clean.csv
"""

import logging
from pathlib import Path
import sys

# Ensure repository root is on sys.path for direct script execution
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pandas as pd

from app.services.data_cleaning import (
    clean_job_fit_dataframe,
    clean_resume_dataframe,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("build_processed_data")


def main():
    raw_dir = REPO_ROOT / "data" / "raw"
    processed_dir = REPO_ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    resume_raw_path = raw_dir / "Resume.csv.gz"
    job_fit_raw_path = raw_dir / "job_resume_fit.csv.gz"

    resume_clean_path = processed_dir / "resume_clean.csv.gz"
    job_fit_clean_path = processed_dir / "job_resume_fit_clean.csv.gz"

    logger.info("==================================================")
    logger.info("Starting Processed Data Pipeline")
    logger.info("Raw Directory: %s", raw_dir)
    logger.info("Processed Directory: %s", processed_dir)
    logger.info("==================================================")

    # -------------------------------------------------------------------------
    # 1. Process Resume.csv
    # -------------------------------------------------------------------------
    if not resume_raw_path.exists():
        logger.error("Resume.csv not found at: %s", resume_raw_path)
        sys.exit(1)

    logger.info("Loading %s...", resume_raw_path.name)
    df_resume_raw = pd.read_csv(resume_raw_path)
    logger.info("Loaded %d rows from %s", len(df_resume_raw), resume_raw_path.name)

    logger.info("Cleaning Resume text (ignoring Resume_html)...")
    df_resume_clean = clean_resume_dataframe(
        df_resume_raw,
        text_col="Resume_str",
        drop_html=True,
    )
    logger.info(
        "Saving cleaned resumes (%d rows) to %s...",
        len(df_resume_clean),
        resume_clean_path.name,
    )
    df_resume_clean.to_csv(resume_clean_path, index=False)
    logger.info("Saved %s successfully.", resume_clean_path.name)

    # -------------------------------------------------------------------------
    # 2. Process job_resume_fit.csv
    # -------------------------------------------------------------------------
    if not job_fit_raw_path.exists():
        logger.error("job_resume_fit.csv not found at: %s", job_fit_raw_path)
        sys.exit(1)

    logger.info("Loading %s...", job_fit_raw_path.name)
    df_job_fit_raw = pd.read_csv(job_fit_raw_path)
    raw_fit_count = len(df_job_fit_raw)
    logger.info("Loaded %d rows from %s", raw_fit_count, job_fit_raw_path.name)

    logger.info("Cleaning job/resume text and safely parsing skill lists...")
    df_job_fit_clean, dropped_rows = clean_job_fit_dataframe(
        df_job_fit_raw,
        text_cols=["resume_text", "job_text"],
        skill_cols=[
            "job_required_skills",
            "resume_skill_list",
            "ai_matched_skills",
        ],
    )

    logger.info(
        "Saving cleaned job-fit records (%d rows) to %s...",
        len(df_job_fit_clean),
        job_fit_clean_path.name,
    )
    df_job_fit_clean.to_csv(job_fit_clean_path, index=False)
    logger.info("Saved %s successfully.", job_fit_clean_path.name)

    # -------------------------------------------------------------------------
    # Summary Report
    # -------------------------------------------------------------------------
    logger.info("==================================================")
    logger.info("Processing Summary:")
    logger.info("  Resume.csv: %d rows processed -> %d rows saved", len(df_resume_raw), len(df_resume_clean))
    logger.info("  job_resume_fit.csv: %d rows processed -> %d rows saved", raw_fit_count, len(df_job_fit_clean))
    logger.info("  Rows dropped due to parsing errors: %d", dropped_rows)
    logger.info("Pipeline completed successfully!")
    logger.info("==================================================")


if __name__ == "__main__":
    main()
