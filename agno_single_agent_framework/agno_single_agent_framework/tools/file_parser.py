"""
File Parser Toolkit — Extract text from files using Agno framework.

Supports: PDF, DOCX, CSV, Excel, TXT

Setup:
  pip install PyPDF2 python-docx openpyxl pandas
"""

import os
import csv
import logging
from agno.tools import Toolkit

logger = logging.getLogger(__name__)


class FileParserToolkit(Toolkit):
    """Toolkit for extracting text content from various file types."""

    def __init__(self):
        super().__init__(name="file_parser")
        self.register(self.parse_file)
        self.register(self.parse_pdf)
        self.register(self.parse_csv)

    def parse_file(self, file_path: str, max_pages: int = 10) -> dict:
        """
        Parse any supported file and extract its text content.

        Supported file types: PDF, DOCX, CSV, XLSX, XLS, TXT

        Args:
            file_path: Absolute or relative path to the file to parse
            max_pages: Maximum number of pages to extract for PDF files (default 10)

        Returns:
            A dictionary with file type, content, and metadata
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}

        ext = os.path.splitext(file_path)[1].lower()

        parsers = {
            ".pdf": self._parse_pdf,
            ".docx": self._parse_docx,
            ".csv": self._parse_csv,
            ".xlsx": self._parse_excel,
            ".xls": self._parse_excel,
            ".txt": self._parse_text,
        }

        parser = parsers.get(ext)
        if not parser:
            return {"error": f"Unsupported file type: {ext}. Supported: {list(parsers.keys())}"}

        try:
            return parser(file_path, max_pages=max_pages)
        except Exception as e:
            logger.error(f"File parsing failed for {file_path}: {e}")
            return {"error": str(e)}

    def parse_pdf(self, file_path: str, max_pages: int = 10) -> dict:
        """
        Extract text content from a PDF file.

        Args:
            file_path: Path to the PDF file
            max_pages: Maximum number of pages to extract (default 10)

        Returns:
            A dictionary with total pages, extracted pages, and page-by-page text
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        return self._parse_pdf(file_path, max_pages=max_pages)

    def parse_csv(self, file_path: str, max_rows: int = 50) -> dict:
        """
        Parse a CSV file and return its data as structured rows.

        Args:
            file_path: Path to the CSV file
            max_rows: Maximum number of rows to return (default 50)

        Returns:
            A dictionary with row count, column names, and rows data
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        try:
            with open(file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            return {
                "type": "csv",
                "row_count": len(rows),
                "columns": list(rows[0].keys()) if rows else [],
                "rows": rows[:max_rows],
            }
        except Exception as e:
            return {"error": str(e)}

    def _parse_pdf(self, file_path: str, max_pages: int = 10, **kwargs) -> dict:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            return {"error": "PyPDF2 not installed. Run: pip install PyPDF2"}

        reader = PdfReader(file_path)
        pages = []
        for i, page in enumerate(reader.pages[:max_pages]):
            text = page.extract_text() or ""
            pages.append({"page": i + 1, "text": text.strip()})

        return {
            "type": "pdf",
            "total_pages": len(reader.pages),
            "extracted_pages": len(pages),
            "pages": pages,
        }

    def _parse_docx(self, file_path: str, **kwargs) -> dict:
        try:
            import docx
        except ImportError:
            return {"error": "python-docx not installed. Run: pip install python-docx"}

        doc = docx.Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return {"type": "docx", "paragraphs": len(paragraphs), "text": "\n".join(paragraphs)}

    def _parse_csv(self, file_path: str, **kwargs) -> dict:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        return {
            "type": "csv",
            "row_count": len(rows),
            "columns": list(rows[0].keys()) if rows else [],
            "rows": rows[:50],
        }

    def _parse_excel(self, file_path: str, **kwargs) -> dict:
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

    def _parse_text(self, file_path: str, **kwargs) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"type": "text", "char_count": len(content), "text": content[:5000]}


# Backward compatibility
DESCRIPTION = "Extract text content from PDF, DOCX, CSV, or Excel files."
PARAMETERS = {
    "file_path": {"type": "string", "description": "Path to the file"},
    "max_pages": {"type": "integer", "description": "Max pages to extract (PDF only)", "default": 10},
}


def run(file_path: str, max_pages: int = 10) -> dict:
    """Parse a file and return extracted text (legacy interface)."""
    toolkit = FileParserToolkit()
    return toolkit.parse_file(file_path, max_pages)
