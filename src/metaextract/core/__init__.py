"""Core module for metaextract."""

from metaextract.core.config import Config
from metaextract.core.exceptions import (
    DownloadError,
    ExtractionError,
    MetaExtractError,
    SearchError,
)
from metaextract.core.models import (
    DocumentMetadata,
    ExtractionResult,
    FileType,
    ScanResults,
)

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
