"""OpenOffice/LibreOffice (ODS, ODP, ODT) metadata extractor."""

import zipfile
from typing import ClassVar

from lxml import etree

from metaextract.core.models import DocumentMetadata, ExtractionResult, FileType
from metaextract.extractors.base import MetadataExtractor


class OpenOfficeExtractor(MetadataExtractor):
    """Extract metadata from OpenOffice/LibreOffice files (ODS, ODP, ODT)."""

    SUPPORTED_TYPES: ClassVar[list[FileType]] = [FileType.ODS, FileType.ODP, FileType.ODT]

    # ODF namespaces
    NAMESPACES = {
        "office": "urn:oasis:names:tc:opendocument:xmlns:office:1.0",
        "dc": "http://purl.org/dc/elements/1.1/",
        "meta": "urn:oasis:names:tc:opendocument:xmlns:meta:1.0",
    }

    def extract(self) -> ExtractionResult:
        """Extract metadata from OpenOffice file."""
        try:
            metadata = self._create_base_metadata()

            if not zipfile.is_zipfile(str(self.file_path)):
                return ExtractionResult(
                    success=False,
                    error="Not a valid OpenDocument file",
                )

            with zipfile.ZipFile(self.file_path, "r") as zf:
                # Check for meta.xml
                if "meta.xml" not in zf.namelist():
                    return ExtractionResult(
                        success=False,
                        error="meta.xml not found in document",
                    )

                meta_xml = zf.read("meta.xml")
                root = etree.fromstring(meta_xml)

                # Find the office:meta element
                meta_elem = root.find("office:meta", self.NAMESPACES)
                if meta_elem is not None:
                    self._extract_meta(meta_elem, metadata)

            self._metadata = metadata
            return ExtractionResult(success=True, metadata=metadata)

        except Exception as e:
            return ExtractionResult(success=False, error=str(e))

    def _extract_meta(self, meta_elem: etree._Element, metadata: DocumentMetadata) -> None:
        """Extract metadata from meta.xml element."""
        # Extract creator (author)
        creator = meta_elem.find("dc:creator", self.NAMESPACES)
        if creator is not None and creator.text:
            metadata.author = self._clean_string(creator.text)
            if metadata.author and metadata.author not in metadata.users:
                metadata.users.append(metadata.author)

        # Extract initial creator
        initial_creator = meta_elem.find("meta:initial-creator", self.NAMESPACES)
        if initial_creator is not None and initial_creator.text:
            initial = self._clean_string(initial_creator.text)
            if initial and initial not in metadata.users:
                metadata.users.append(initial)

        # Extract generator (software)
        generator = meta_elem.find("meta:generator", self.NAMESPACES)
        if generator is not None and generator.text:
            metadata.application = self._clean_string(generator.text)
            if metadata.application not in metadata.software:
                metadata.software.append(metadata.application)

        # Extract template
        template = meta_elem.find("meta:template", self.NAMESPACES)
        if template is not None:
            href = template.get("{http://www.w3.org/1999/xlink}href")
            if href:
                metadata.template = href
                if "/" in href or "\\" in href:
                    metadata.paths.append(href)

        # Extract dates
        creation_date = meta_elem.find("meta:creation-date", self.NAMESPACES)
        if creation_date is not None and creation_date.text:
            try:
                from datetime import datetime
                metadata.created = datetime.fromisoformat(creation_date.text.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        modification_date = meta_elem.find("dc:date", self.NAMESPACES)
        if modification_date is not None and modification_date.text:
            try:
                from datetime import datetime
                metadata.modified = datetime.fromisoformat(modification_date.text.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        # Build raw metadata
        metadata.raw = {
            "creator": creator.text if creator is not None else None,
            "initial_creator": initial_creator.text if initial_creator is not None else None,
            "generator": generator.text if generator is not None else None,
            "creation_date": creation_date.text if creation_date is not None else None,
            "date": modification_date.text if modification_date is not None else None,
        }

        # Extract title and subject
        title = meta_elem.find("dc:title", self.NAMESPACES)
        if title is not None:
            metadata.raw["title"] = title.text

        subject = meta_elem.find("dc:subject", self.NAMESPACES)
        if subject is not None:
            metadata.raw["subject"] = subject.text

    def extract_text(self) -> str | None:
        """Extract text content from document."""
        try:
            with zipfile.ZipFile(self.file_path, "r") as zf:
                if "content.xml" not in zf.namelist():
                    return None

                content_xml = zf.read("content.xml")
                root = etree.fromstring(content_xml)

                # Extract all text nodes
                texts = []
                for elem in root.iter():
                    if elem.text:
                        texts.append(elem.text)
                    if elem.tail:
                        texts.append(elem.tail)

                return " ".join(texts)
        except Exception:
            return None
