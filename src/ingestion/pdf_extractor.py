from pathlib import Path
from typing import List
import pypdf


def extract_text_from_pdf(pdf_path: Path, normalize_whitespace: bool = True) -> str:
    """
    Extract text from a PDF file page by page.
    If normalize_whitespace is True, collapses redundant line breaks and spaces between words.
    """
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    reader = pypdf.PdfReader(str(pdf_path))
    pages_text: List[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
    
    raw = "\n".join(pages_text)
    if normalize_whitespace:
        # Collapse whitespace to clean readable text while preserving sentence breaks
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        return " ".join(lines)
    return raw
