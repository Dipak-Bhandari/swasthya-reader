"""Turn an uploaded file (image or PDF) into a list of (bytes, mime_type) images for Gemma 4."""
import pymupdf as fitz  # PyMuPDF

from .config import MAX_PDF_PAGES

IMAGE_MIMES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}


def _sniff(data: bytes, declared: str | None) -> str:
    if data[:4] == b"%PDF":
        return "application/pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return declared or "application/octet-stream"


def to_images(data: bytes, declared_mime: str | None = None) -> list[tuple[bytes, str]]:
    mime = _sniff(data, declared_mime)

    if mime in IMAGE_MIMES:
        return [(data, "image/jpeg" if mime == "image/jpg" else mime)]

    if mime == "application/pdf":
        doc = fitz.open(stream=data, filetype="pdf")
        images = []
        for i, page in enumerate(doc):
            if i >= MAX_PDF_PAGES:
                break
            pix = page.get_pixmap(dpi=150)
            images.append((pix.tobytes("jpeg", jpg_quality=85), "image/jpeg"))  # much smaller than PNG
        doc.close()
        if not images:
            raise ValueError("PDF has no pages")
        return images

    raise ValueError(f"Unsupported file type: {mime}")