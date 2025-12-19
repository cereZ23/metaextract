"""Core module for metaextract."""

from metaextract.core.exceptions import (
    MetaExtractError,
    ExtractionError,
    SearchError,
    DownloadError,
)
from metaextract.core.models import (
    FileType,
    DocumentMetadata,
    ExtractionResult,
    ScanResults,
)
from metaextract.core.config import Config

__all__ = [
    "MetaExtractError",
    "ExtractionError",
    "SearchError",
    "DownloadError",
    "FileType",
    "DocumentMetadata",
    "ExtractionResult",
    "ScanResults",
    "Config",
]
