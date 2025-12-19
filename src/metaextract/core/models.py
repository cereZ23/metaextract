"""Data models for metaextract."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """Supported file types for metadata extraction."""

    PDF = "pdf"
    DOC = "doc"
    DOCX = "docx"
    XLS = "xls"
    XLSX = "xlsx"
    PPT = "ppt"
    PPTX = "pptx"
    ODS = "ods"
    ODP = "odp"
    ODT = "odt"


class DocumentMetadata(BaseModel):
    """Extracted metadata from a document."""

    filename: str
    file_type: FileType
    source_url: str | None = None

    # User information
    author: str | None = None
    creator: str | None = None
    last_modified_by: str | None = None
    users: list[str] = Field(default_factory=list)

    # Software information
    producer: str | None = None
    application: str | None = None
    app_version: str | None = None
    software: list[str] = Field(default_factory=list)

    # Paths and servers
    template: str | None = None
    paths: list[str] = Field(default_factory=list)

    # Extracted content
    emails: list[str] = Field(default_factory=list)

    # Dates
    created: datetime | None = None
    modified: datetime | None = None

    # Raw metadata for debugging
    raw: dict[str, Any] = Field(default_factory=dict)


class ExtractionResult(BaseModel):
    """Result of metadata extraction."""

    success: bool
    metadata: DocumentMetadata | None = None
    error: str | None = None


class DownloadResult(BaseModel):
    """Result of a file download."""

    url: str
    local_path: str | None = None
    success: bool
    error: str | None = None


class SearchResult(BaseModel):
    """A single search result."""

    url: str
    title: str | None = None


class ScanResults(BaseModel):
    """Aggregated results from a full scan."""

    domain: str
    documents: list[DocumentMetadata] = Field(default_factory=list)
    failed: list[tuple[str, str]] = Field(default_factory=list)

    @property
    def unique_users(self) -> list[str]:
        """Get unique usernames across all documents."""
        users: set[str] = set()
        for doc in self.documents:
            users.update(doc.users)
        return sorted(users)

    @property
    def unique_software(self) -> list[str]:
        """Get unique software names across all documents."""
        software: set[str] = set()
        for doc in self.documents:
            software.update(doc.software)
        return sorted(software)

    @property
    def unique_emails(self) -> list[str]:
        """Get unique email addresses across all documents."""
        emails: set[str] = set()
        for doc in self.documents:
            emails.update(doc.emails)
        return sorted(emails)

    @property
    def unique_paths(self) -> list[str]:
        """Get unique paths across all documents."""
        paths: set[str] = set()
        for doc in self.documents:
            paths.update(doc.paths)
        return sorted(paths)

    @property
    def stats(self) -> dict[str, int]:
        """Get summary statistics."""
        return {
            "total_documents": len(self.documents),
            "failed_extractions": len(self.failed),
            "unique_users": len(self.unique_users),
            "unique_software": len(self.unique_software),
            "unique_emails": len(self.unique_emails),
            "unique_paths": len(self.unique_paths),
        }
