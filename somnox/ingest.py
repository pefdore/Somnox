"""Import PDF : extraction de texte natif puis OCR en repli (Tesseract)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pymupdf

try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None
    Image = None

MIN_TEXT_CHARS = 200


def _extract_native(pdf_path: Path) -> str:
    parts: list[str] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            parts.append(page.get_text("text"))
    return "\n".join(parts)


def _extract_ocr(pdf_path: Path, lang: str = "fra") -> str:
    if pytesseract is None or shutil.which("tesseract") is None:
        return ""
    parts: list[str] = []
    with pymupdf.open(pdf_path) as doc:
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            parts.append(pytesseract.image_to_string(img, lang=lang))
    return "\n".join(parts)


def extract_text(pdf_path: str | Path) -> tuple[str, str]:
    """Retourne (texte, méthode). Essaie le texte natif, sinon OCR 300 dpi."""
    pdf_path = Path(pdf_path)
    text = _extract_native(pdf_path)
    if len(text.strip()) >= MIN_TEXT_CHARS:
        return text, "texte natif"
    ocr_text = _extract_ocr(pdf_path)
    if len(ocr_text.strip()) > len(text.strip()):
        return ocr_text, "OCR (Tesseract, 300 dpi)"
    return text, "texte natif partiel"
