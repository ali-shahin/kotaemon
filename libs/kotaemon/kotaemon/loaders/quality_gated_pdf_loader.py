import logging
import re
from pathlib import Path
from typing import List, Optional

from decouple import config

from kotaemon.base import Document, Param

from .base import BaseReader
from .docling_loader import DoclingReader
from .pdf_loader import PDFThumbnailReader

logger = logging.getLogger(__name__)

# Placeholder that pypdf/docling emit for glyphs without a Unicode mapping,
# e.g. "GLYPH<EOT>" — a symptom of a PDF whose fonts lack a valid ToUnicode CMap.
_GLYPH_RE = re.compile(r"GLYPH<[^>]*>")
# Control characters, excluding tab / newline / carriage-return.
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def undecodable_ratio(text: str) -> float:
    """Fraction of the text that is undecodable.

    Counts characters belonging to ``GLYPH<...>`` placeholders, the Unicode
    replacement character, and control characters, over the total length. A high
    ratio means the extracted text layer is unusable and OCR is needed.
    """
    if not text:
        return 0.0

    bad = sum(len(m.group()) for m in _GLYPH_RE.finditer(text))
    bad += text.count("�")
    bad += len(_CONTROL_RE.findall(text))

    return bad / len(text)


class QualityGatedPDFReader(BaseReader):
    """Fast PDF text extraction with an OCR fallback for broken text layers.

    Extracts with :class:`PDFThumbnailReader` (pypdf, no OCR). If the extracted
    text is largely undecodable — e.g. an Arabic PDF whose fonts lack a
    ``ToUnicode`` CMap, producing ``GLYPH<...>`` placeholders — it re-extracts
    with :class:`DoclingReader` OCR (configured for ``ocr_lang``). Clean PDFs keep
    the fast path, so this does not regress well-formed documents.
    """

    bad_ratio_threshold: float = Param(
        config("PDF_OCR_FALLBACK_THRESHOLD", default=0.15, cast=float),
        help=(
            "If the undecodable-character ratio of the fast text extraction "
            "exceeds this, fall back to OCR."
        ),
    )
    ocr_lang: list[str] = Param(
        ["ar", "en"],
        help="OCR languages (EasyOCR codes) for the fallback reader.",
    )

    _primary = None
    _fallback = None

    @property
    def primary(self) -> PDFThumbnailReader:
        if self._primary is None:
            self._primary = PDFThumbnailReader()
        return self._primary

    @property
    def fallback(self) -> DoclingReader:
        if self._fallback is None:
            self._fallback = DoclingReader(ocr_lang=self.ocr_lang)
        return self._fallback

    def run(
        self, file_path: str | Path, extra_info: Optional[dict] = None, **kwargs
    ) -> List[Document]:
        return self.load_data(file_path, extra_info=extra_info, **kwargs)

    def load_data(
        self, file_path: str | Path, extra_info: Optional[dict] = None, **kwargs
    ) -> List[Document]:
        docs = self.primary.load_data(Path(file_path), extra_info=extra_info, **kwargs)

        text = "\n".join(
            doc.text
            for doc in docs
            if doc.metadata.get("type") != "thumbnail" and doc.text
        )
        ratio = undecodable_ratio(text)

        if ratio > self.bad_ratio_threshold:
            logger.warning(
                "PDF text layer looks broken (undecodable ratio %.2f > %.2f); "
                "falling back to OCR for %s",
                ratio,
                self.bad_ratio_threshold,
                file_path,
            )
            return self.fallback.load_data(file_path, extra_info=extra_info, **kwargs)

        logger.info(
            "PDF text layer OK (undecodable ratio %.2f); using fast reader for %s",
            ratio,
            file_path,
        )
        return docs
