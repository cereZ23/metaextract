"""Custom exceptions for metaextract."""


class MetaExtractError(Exception):
    """Base exception for all metaextract errors."""

    pass


class ExtractionError(MetaExtractError):
    """Error during metadata extraction."""

    def __init__(self, message: str, filename: str | None = None) -> None:
        self.filename = filename
        super().__init__(message)


class SearchError(MetaExtractError):
    """Error during search operations."""

    def __init__(self, message: str, query: str | None = None) -> None:
        self.query = query
        super().__init__(message)


class DownloadError(MetaExtractError):
    """Error during file download."""

    def __init__(self, message: str, url: str | None = None) -> None:
        self.url = url
        super().__init__(message)


class UnsupportedFileTypeError(ExtractionError):
    """Raised when attempting to extract from an unsupported file type."""

    def __init__(self, file_type: str, filename: str | None = None) -> None:
        self.file_type = file_type
        super().__init__(f"Unsupported file type: {file_type}", filename)


class PasswordProtectedError(ExtractionError):
    """Raised when a document is password protected."""

    pass
