"""Metadata extractors for various document formats."""

from pathlib import Path

from metaextract.core.models import ExtractionResult, FileType
from metaextract.extractors.base import MetadataExtractor
from metaextract.extractors.docx import DOCXExtractor
from metaextract.extractors.legacy_office import LegacyOfficeExtractor
from metaextract.extractors.openoffice import OpenOfficeExtractor
from metaextract.extractors.pdf import PDFExtractor
from metaextract.extractors.pptx import PPTXExtractor
from metaextract.extractors.xlsx import XLSXExtractor

# Registry mapping file types to extractors
EXTRACTOR_REGISTRY: dict[FileType, type[MetadataExtractor]] = {
    FileType.PDF: PDFExtractor,
    FileType.DOC: LegacyOfficeExtractor,
    FileType.XLS: LegacyOfficeExtractor,
    FileType.PPT: LegacyOfficeExtractor,
    FileType.DOCX: DOCXExtractor,
    FileType.XLSX: XLSXExtractor,
    FileType.PPTX: PPTXExtractor,
    FileType.ODS: OpenOfficeExtractor,
    FileType.ODP: OpenOfficeExtractor,
    FileType.ODT: OpenOfficeExtractor,
}


def get_extractor(file_path: Path) -> MetadataExtractor | None:
    """Get the appropriate extractor for a file.

    Args:
        file_path: Path to the file to extract metadata from.

    Returns:
        Appropriate MetadataExtractor instance or None if unsupported.
    """
    suffix = file_path.suffix.lstrip(".").lower()
    try:
        file_type = FileType(suffix)
    except ValueError:
        return None

    extractor_class = EXTRACTOR_REGISTRY.get(file_type)
    if extractor_class:
        return extractor_class(file_path)
    return None


def extract_metadata(file_path: Path) -> ExtractionResult:
    """Convenience function to extract metadata from a file.

    Args:
        file_path: Path to the file.

    Returns:
        ExtractionResult with success status and metadata.
    """
    extractor = get_extractor(file_path)
    if not extractor:
        return ExtractionResult(
            success=False,
            error=f"Unsupported file type: {file_path.suffix}",
        )
    return extractor.extract()


__all__ = [
    "MetadataExtractor",
    "PDFExtractor",
    "DOCXExtractor",
    "XLSXExtractor",
    "PPTXExtractor",
    "LegacyOfficeExtractor",
    "OpenOfficeExtractor",
    "EXTRACTOR_REGISTRY",
    "get_extractor",
    "extract_metadata",
]
