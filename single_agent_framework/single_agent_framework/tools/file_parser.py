"""
File Parser Tool — Extract text from PDF, DOCX, CSV, and Excel files.

Setup:
  pip install PyPDF2 python-docx openpyxl pandas
"""

import os
import logging
import csv
import io

logger = logging.getLogger(__name__)

DESCRIPTION = "Extract text content from PDF, DOCX, CSV, or Excel files."

PARAMETERS = {
    "file_path": {"type": "string", "description": "Path to the file"},
    "max_pages": {"type": "integer", "description": "Max pages to extract (PDF only)", "default": 10},
}


def run(file_path: str, max_pages: int = 10) -> dict:
    """Parse a file and return extracted text."""
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}"}

    ext = os.path.splitext(file_path)[1].lower()

    parsers = {
        ".pdf": _parse_pdf,
        ".docx": _parse_docx,
        ".csv": _parse_csv,
        ".xlsx": _parse_excel,
        ".xls": _parse_excel,
        ".txt": _parse_text,
    }

    parser = parsers.get(ext)
    if not parser:
        return {"error": f"Unsupported file type: {ext}. Supported: {list(parsers.keys())}"}

    try:
        return parser(file_path, max_pages=max_pages)
    except Exception as e:
        logger.error(f"File parsing failed: {e}")
        return {"error": str(e)}


def _parse_pdf(file_path: str, max_pages: int = 10) -> dict:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return {"error": "PyPDF2 not installed. Run: pip install PyPDF2"}

    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages[:max_pages]):
        text = page.extract_text() or ""
        pages.append({"page": i + 1, "text": text.strip()})

    return {"type": "pdf", "total_pages": len(reader.pages), "extracted_pages": len(pages), "pages": pages}


def _parse_docx(file_path: str, **kwargs) -> dict:
    try:
        import docx
    except ImportError:
        return {"error": "python-docx not installed. Run: pip install python-docx"}

    doc = docx.Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return {"type": "docx", "paragraphs": len(paragraphs), "text": "\n".join(paragraphs)}


def _parse_csv(file_path: str, **kwargs) -> dict:
    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return {"type": "csv", "row_count": len(rows), "columns": list(rows[0].keys()) if rows else [], "rows": rows[:50]}


def _parse_excel(file_path: str, **kwargs) -> dict:
    try:
        import pandas as pd
    except ImportError:
        return {"error": "pandas/openpyxl not installed. Run: pip install pandas openpyxl"}

    df = pd.read_excel(file_path, nrows=50)
    return {
        "type": "excel",
        "row_count": len(df),
        "columns": list(df.columns),
        "rows": df.to_dict(orient="records"),
    }


def _parse_text(file_path: str, **kwargs) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return {"type": "text", "char_count": len(content), "text": content[:5000]}
