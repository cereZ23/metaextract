"""Abstract base class for metadata extractors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from metaextract.core.models import DocumentMetadata, ExtractionResult, FileType


class MetadataExtractor(ABC):
    """Abstract base class for metadata extractors."""

    # Class attribute: list of file types this extractor handles
    SUPPORTED_TYPES: ClassVar[list[FileType]] = []

    def __init__(self, file_path: Path) -> None:
        """Initialize the extractor.

        Args:
            file_path: Path to the file to extract metadata from.
        """
        self.file_path = Path(file_path)
        self._metadata: DocumentMetadata | None = None

    @abstractmethod
    def extract(self) -> ExtractionResult:
        """Extract metadata from the file.

        Returns:
            ExtractionResult with success status and metadata or error.
        """
        ...

    @abstractmethod
    def extract_text(self) -> str | None:
        """Extract text content for email/hostname parsing.

        Returns:
            Extracted text or None if not supported.
        """
        ...

    @classmethod
    def supports(cls, file_type: FileType) -> bool:
        """Check if this extractor supports the given file type."""
        return file_type in cls.SUPPORTED_TYPES

    def _create_base_metadata(self) -> DocumentMetadata:
        """Create a base metadata object with filename and type."""
        suffix = self.file_path.suffix.lstrip(".").lower()
        try:
            file_type = FileType(suffix)
        except ValueError:
            file_type = FileType.PDF  # Fallback

        return DocumentMetadata(
            filename=self.file_path.name,
            file_type=file_type,
        )

    @staticmethod
    def _decode_string(value: bytes | str) -> str:
        """Decode bytes to string, handling various encodings."""
        if isinstance(value, bytes):
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    return value.decode(encoding)
                except UnicodeDecodeError:
                    continue
            return value.decode("utf-8", errors="replace")
        return str(value) if value else ""

    @staticmethod
    def _clean_string(value: str | None) -> str:
        """Clean a string value by stripping whitespace."""
        if value is None:
            return ""
        return str(value).strip()
