"""PDF inspection helpers used by the QA / verification step."""
from __future__ import annotations

from pathlib import Path
from typing import List

from pypdf import PdfReader


def count_pages(path: Path) -> int:
    return len(PdfReader(str(path)).pages)


def blank_pages(path: Path, min_chars: int = 60) -> List[int]:
    """1-based page numbers whose extracted text is shorter than ``min_chars``."""
    reader = PdfReader(str(path))
    return [i for i, page in enumerate(reader.pages, start=1)
            if len((page.extract_text() or "").strip()) < min_chars]
