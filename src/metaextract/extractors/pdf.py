"""PDF metadata extractor using pdfminer.six."""

from pathlib import Path
from typing import Any, ClassVar

from pdfminer.high_level import extract_text
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfparser import PDFParser

from metaextract.core.models import DocumentMetadata, ExtractionResult, FileType
from metaextract.extractors.base import MetadataExtractor


class PDFExtractor(MetadataExtractor):
    """Extract metadata from PDF files using pdfminer.six."""

    SUPPORTED_TYPES: ClassVar[list[FileType]] = [FileType.PDF]

    def __init__(self, file_path: Path, password: str = "") -> None:
        """Initialize the PDF extractor.

        Args:
            file_path: Path to the PDF file.
            password: Optional password for encrypted PDFs.
        """
        super().__init__(file_path)
        self.password = password

    def extract(self) -> ExtractionResult:
        """Extract metadata from PDF."""
        try:
            metadata = self._create_base_metadata()

            with open(self.file_path, "rb") as fp:
                parser = PDFParser(fp)
                doc = PDFDocument(parser, password=self.password)

                if doc.info:
                    info = doc.info[0] if doc.info else {}
                    self._extract_info(info, metadata)

            self._metadata = metadata
            return ExtractionResult(success=True, metadata=metadata)

        except Exception as e:
            return ExtractionResult(success=False, error=str(e))

    def _extract_info(self, info: dict[str, Any], metadata: DocumentMetadata) -> None:
        """Extract metadata from PDF info dictionary."""
        # Extract author
        if author := info.get("Author"):
            author_str = self._decode_string(author)
            if author_str:
                metadata.author = author_str
                if author_str not in metadata.users:
                    metadata.users.append(author_str)

        # Extract creator (application that created the document)
        if creator := info.get("Creator"):
            creator_str = self._decode_string(creator)
            if creator_str:
                metadata.creator = creator_str
                if creator_str not in metadata.software:
                    metadata.software.append(creator_str)

        # Extract producer (PDF producer software)
        if producer := info.get("Producer"):
            producer_str = self._decode_string(producer)
            if producer_str:
                metadata.producer = producer_str
                if producer_str not in metadata.software:
                    metadata.software.append(producer_str)

        # Extract title
        if title := info.get("Title"):
            title_str = self._decode_string(title)
            # Title might contain path information
            if "/" in title_str or "\\" in title_str:
                metadata.paths.append(title_str)

        # Extract subject (might contain useful info)
        if subject := info.get("Subject"):
            subject_str = self._decode_string(subject)
            if "@" in subject_str:
                # Might be an email
                metadata.emails.append(subject_str)

        # Store raw metadata
        metadata.raw = {k: self._decode_string(v) if isinstance(v, bytes) else str(v)
                        for k, v in info.items()}

    def extract_text(self) -> str | None:
        """Extract text content for email parsing."""
        try:
            return extract_text(str(self.file_path), password=self.password)
        except Exception:
            return None
