"""MetaExtract - Document metadata extraction tool for OSINT."""

__version__ = "3.0.0"
__author__ = "Christian Martorella"
__email__ = "cmartorella@edge-security.com"

from metaextract.core.models import (
    DocumentMetadata,
    ExtractionResult,
    FileType,
    ScanResults,
)
from metaextract.extractors import extract_metadata, get_extractor

__all__ = [
    "__version__",
    "FileType",
    "DocumentMetadata",
    "ExtractionResult",
    "ScanResults",
    "extract_metadata",
    "get_extractor",
]
