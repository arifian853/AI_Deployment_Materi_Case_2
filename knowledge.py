"""Extract plain text from one PDF to use as direct LLM context."""

from pathlib import Path

from pypdf import PdfReader


class KnowledgeError(Exception):
    """The knowledge PDF cannot be used for chat."""


def load_pdf(path: Path, max_chars: int) -> str:
    if not path.is_file():
        raise KnowledgeError(f"PDF belum ditemukan: {path}")

    try:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise KnowledgeError("PDF terenkripsi dan tidak dapat dibaca")
        pages = []
        total_chars = 0
        for number, page in enumerate(reader.pages, start=1):
            content = (page.extract_text() or "").strip()
            if not content:
                continue
            section = f"[Halaman {number}]\n{content}"
            total_chars += len(section)
            if total_chars > max_chars:
                raise KnowledgeError(
                    f"Teks PDF melebihi MAX_PDF_CHARS ({max_chars}); gunakan dokumen yang lebih ringkas"
                )
            pages.append(section)
    except KnowledgeError:
        raise
    except Exception as exc:
        raise KnowledgeError("PDF gagal dibaca atau bukan PDF yang valid") from exc

    if not pages:
        raise KnowledgeError("PDF tidak mengandung teks yang dapat diekstrak; PDF hasil scan perlu OCR")
    return "\n\n".join(pages)
