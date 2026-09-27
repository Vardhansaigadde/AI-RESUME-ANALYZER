"""Resume document text extraction service.

Supports extracting clean plain text from PDF documents (using pdfplumber)
and DOCX documents (using python-docx).
"""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import BinaryIO, Union

import docx
import pdfplumber

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}


def extract_text_from_pdf(source: Union[bytes, BinaryIO, Path, str]) -> str:
    """Extract all text content across pages from a PDF document.

    Args:
        source: File bytes, file-like binary stream, Path, or filepath string.

    Returns:
        Extracted plain text string joined across pages.

    Raises:
        ValueError: If PDF cannot be read or is corrupted.
    """
    try:
        stream = io.BytesIO(source) if isinstance(source, bytes) else source
        text_parts: list[str] = []
        with pdfplumber.open(stream) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())
        return "\n\n".join(text_parts).strip()
    except Exception as exc:
        logger.error("Failed to extract text from PDF: %s", exc)
        raise ValueError(f"Failed to extract text from PDF: {exc}") from exc


def extract_text_from_docx(source: Union[bytes, BinaryIO, Path, str]) -> str:
    """Extract all text content from paragraphs and tables in a DOCX document.

    Args:
        source: File bytes, file-like binary stream, Path, or filepath string.

    Returns:
        Extracted plain text string.

    Raises:
        ValueError: If DOCX cannot be read or is corrupted.
    """
    try:
        stream = io.BytesIO(source) if isinstance(source, bytes) else source
        doc = docx.Document(stream)
        text_parts: list[str] = []

        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                text_parts.append(text)

        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    text_parts.append(" | ".join(row_cells))

        return "\n\n".join(text_parts).strip()
    except Exception as exc:
        logger.error("Failed to extract text from DOCX: %s", exc)
        raise ValueError(f"Failed to extract text from DOCX: {exc}") from exc


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """Dispatch text extraction based on file extension.

    Args:
        file_content: Raw bytes of the document.
        filename: Name of the uploaded file (used to inspect extension).

    Returns:
        Extracted clean text string.

    Raises:
        ValueError: If file extension is unsupported or extraction fails.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_content)
    elif ext == ".docx":
        return extract_text_from_docx(file_content)
    else:
        raise ValueError(
            f"Unsupported file format '{ext}'. Only PDF (.pdf) and DOCX (.docx) files are supported."
        )
