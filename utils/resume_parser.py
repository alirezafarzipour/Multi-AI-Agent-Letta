"""
Resume parsing utilities.
Supports: PDF, TXT, plain string
"""

import os
import re
from pathlib import Path


def parse_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF given raw bytes."""
    try:
        import pdfplumber
        import io
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            return "\n".join(
                page.extract_text() or "" for page in pdf.pages
            ).strip()
    except ImportError:
        # Fallback: pypdf
        try:
            import pypdf
            import io
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            return "\n".join(
                page.extract_text() or "" for page in reader.pages
            ).strip()
        except Exception as e:
            return f"[PDF parse error: {e}]"
    except Exception as e:
        return f"[PDF parse error: {e}]"


def clean_resume_text(text: str) -> str:
    """Normalise whitespace and remove junk characters."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def resume_from_uploaded_file(uploaded_file) -> str:
    """
    Accept a Streamlit UploadedFile object and return clean resume text.
    Supports .pdf and .txt
    """
    name = uploaded_file.name.lower()
    raw  = uploaded_file.read()

    if name.endswith(".pdf"):
        text = parse_pdf(raw)
    else:
        text = raw.decode("utf-8", errors="replace")

    return clean_resume_text(text)


def resume_from_filepath(path: str) -> str:
    """Load resume from a local .txt or .pdf file path."""
    path = Path(path)
    if not path.exists():
        return f"[File not found: {path}]"

    if path.suffix.lower() == ".pdf":
        return clean_resume_text(parse_pdf(path.read_bytes()))
    else:
        return clean_resume_text(path.read_text(encoding="utf-8", errors="replace"))


def name_to_filepath(name: str, base_dir: str = "data/resumes") -> str:
    """Tony Stark  →  data/resumes/tony_stark.txt"""
    filename = name.lower().replace(" ", "_") + ".txt"
    return os.path.join(base_dir, filename)