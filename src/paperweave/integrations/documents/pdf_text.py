"""Local PDF text-layer extraction adapter. This adapter does not perform OCR."""
from dataclasses import dataclass
from io import BytesIO
from importlib.metadata import version

from pypdf import PdfReader


PROCESSOR = "pypdf-text-layer"
PROCESSOR_VERSION = version("pypdf")


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str
    error: str | None = None


def extract_pdf_pages(content: bytes) -> list[PageText]:
    reader = PdfReader(BytesIO(content), strict=False)
    if reader.is_encrypted:
        try:
            if reader.decrypt("") == 0:
                raise ValueError("Encrypted PDF requires a password")
        except Exception as exc:
            raise ValueError("Encrypted PDF cannot be opened without a password") from exc
    pages: list[PageText] = []
    for index, page in enumerate(reader.pages, start=1):
        try:
            pages.append(PageText(index, (page.extract_text() or "").strip()))
        except Exception as exc:
            pages.append(PageText(index, "", f"Page {index} text extraction failed: {type(exc).__name__}"))
    return pages
