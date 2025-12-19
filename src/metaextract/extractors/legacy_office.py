"""Legacy MS Office (DOC/XLS/PPT) metadata extractor using olefile."""

from pathlib import Path
from typing import ClassVar

import olefile

from metaextract.core.models import DocumentMetadata, ExtractionResult, FileType
from metaextract.extractors.base import MetadataExtractor


class LegacyOfficeExtractor(MetadataExtractor):
    """Extract metadata from legacy MS Office files (DOC, XLS, PPT) using olefile."""

    SUPPORTED_TYPES: ClassVar[list[FileType]] = [FileType.DOC, FileType.XLS, FileType.PPT]

    def extract(self) -> ExtractionResult:
        """Extract metadata from legacy Office file."""
        try:
            metadata = self._create_base_metadata()

            if not olefile.isOleFile(str(self.file_path)):
                return ExtractionResult(
                    success=False,
                    error="Not a valid OLE file",
                )

            ole = olefile.OleFileIO(str(self.file_path))

            try:
                # Get metadata from OLE
                meta = ole.get_metadata()

                # Extract author
                if meta.author:
                    author = self._decode_string(meta.author)
                    if author:
                        metadata.author = author
                        if author not in metadata.users:
                            metadata.users.append(author)

                # Extract last saved by
                if meta.last_saved_by:
                    last_saved = self._decode_string(meta.last_saved_by)
                    if last_saved:
                        metadata.last_modified_by = last_saved
                        if last_saved not in metadata.users:
                            metadata.users.append(last_saved)

                # Extract application
                if meta.creating_application:
                    app = self._decode_string(meta.creating_application)
                    if app:
                        metadata.application = app
                        if app not in metadata.software:
                            metadata.software.append(app)

                # Extract dates
                metadata.created = meta.create_time
                metadata.modified = meta.last_saved_time

                # Extract template
                if meta.template:
                    template = self._decode_string(meta.template)
                    if template:
                        metadata.template = template
                        # Template might contain path info
                        if "/" in template or "\\" in template:
                            metadata.paths.append(template)

                # Store raw metadata
                metadata.raw = {
                    "author": self._decode_string(meta.author) if meta.author else None,
                    "last_saved_by": self._decode_string(meta.last_saved_by) if meta.last_saved_by else None,
                    "creating_application": self._decode_string(meta.creating_application) if meta.creating_application else None,
                    "create_time": str(meta.create_time) if meta.create_time else None,
                    "last_saved_time": str(meta.last_saved_time) if meta.last_saved_time else None,
                    "template": self._decode_string(meta.template) if meta.template else None,
                    "revision_number": self._decode_string(meta.revision_number) if meta.revision_number else None,
                    "total_edit_time": str(meta.total_edit_time) if meta.total_edit_time else None,
                    "num_pages": str(meta.num_pages) if meta.num_pages else None,
                    "num_words": str(meta.num_words) if meta.num_words else None,
                    "num_chars": str(meta.num_chars) if meta.num_chars else None,
                    "title": self._decode_string(meta.title) if meta.title else None,
                    "subject": self._decode_string(meta.subject) if meta.subject else None,
                    "keywords": self._decode_string(meta.keywords) if meta.keywords else None,
                    "comments": self._decode_string(meta.comments) if meta.comments else None,
                    "company": self._decode_string(meta.company) if meta.company else None,
                    "manager": self._decode_string(meta.manager) if meta.manager else None,
                }

                # Company might be useful
                if meta.company:
                    company = self._decode_string(meta.company)
                    if company:
                        metadata.raw["company"] = company

                # Manager might be a username
                if meta.manager:
                    manager = self._decode_string(meta.manager)
                    if manager and manager not in metadata.users:
                        metadata.users.append(manager)

            finally:
                ole.close()

            self._metadata = metadata
            return ExtractionResult(success=True, metadata=metadata)

        except Exception as e:
            return ExtractionResult(success=False, error=str(e))

    def extract_text(self) -> str | None:
        """Extract text content. Limited support for legacy formats."""
        # Text extraction from legacy formats is complex and would require
        # additional libraries like textract or antiword
        # For now, return None - emails should be extracted from DOCX versions
        return None
