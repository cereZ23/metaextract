"""Result processing and aggregation."""

from pathlib import Path

from metaextract.core.models import DocumentMetadata, ExtractionResult, ScanResults
from metaextract.extractors import extract_metadata, get_extractor
from metaextract.search.parser import extract_emails, extract_paths


class ResultProcessor:
    """Process and aggregate extraction results."""

    def __init__(self, domain: str = "local") -> None:
        """Initialize the processor.

        Args:
            domain: Domain being scanned.
        """
        self.domain = domain
        self.results = ScanResults(domain=domain)

    def process_file(self, file_path: Path, source_url: str | None = None) -> ExtractionResult:
        """Process a single file and add to results.

        Args:
            file_path: Path to the file to process.
            source_url: Optional URL the file was downloaded from.

        Returns:
            ExtractionResult from the extraction.
        """
        result = extract_metadata(file_path)

        if result.success and result.metadata:
            # Add source URL
            if source_url:
                result.metadata.source_url = source_url

            # Extract additional info from text content
            self._enrich_metadata(file_path, result.metadata)

            self.results.documents.append(result.metadata)
        else:
            error = result.error or "Unknown error"
            self.results.failed.append((str(file_path), error))

        return result

    def _enrich_metadata(self, file_path: Path, metadata: DocumentMetadata) -> None:
        """Enrich metadata with extracted emails and paths."""
        extractor = get_extractor(file_path)
        if not extractor:
            return

        # Extract text content
        text = extractor.extract_text()
        if not text:
            return

        # Extract emails from text
        emails = extract_emails(text)
        for email in emails:
            if email not in metadata.emails:
                metadata.emails.append(email)

        # Extract paths from text
        paths = extract_paths(text)
        for path in paths:
            if path not in metadata.paths:
                metadata.paths.append(path)

    def process_directory(self, directory: Path) -> ScanResults:
        """Process all supported files in a directory.

        Args:
            directory: Directory to process.

        Returns:
            Aggregated ScanResults.
        """
        from metaextract.core.models import FileType

        supported_extensions = {ft.value for ft in FileType}

        for file_path in directory.iterdir():
            if file_path.is_file():
                ext = file_path.suffix.lstrip(".").lower()
                if ext in supported_extensions:
                    self.process_file(file_path)

        return self.results

    def get_results(self) -> ScanResults:
        """Get the current results.

        Returns:
            Current ScanResults.
        """
        return self.results

    def deduplicate_users(self) -> list[str]:
        """Get deduplicated list of users.

        Returns:
            Sorted unique users.
        """
        return self.results.unique_users

    def deduplicate_software(self) -> list[str]:
        """Get deduplicated list of software.

        Returns:
            Sorted unique software.
        """
        return self.results.unique_software

    def deduplicate_emails(self) -> list[str]:
        """Get deduplicated list of emails.

        Returns:
            Sorted unique emails.
        """
        return self.results.unique_emails

    def deduplicate_paths(self) -> list[str]:
        """Get deduplicated list of paths.

        Returns:
            Sorted unique paths.
        """
        return self.results.unique_paths
