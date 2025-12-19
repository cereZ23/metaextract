"""Abstract base class for search engines."""

from abc import ABC, abstractmethod

from metaextract.core.models import SearchResult


class SearchEngine(ABC):
    """Abstract base class for search engines."""

    def __init__(self, domain: str) -> None:
        """Initialize the search engine.

        Args:
            domain: Target domain to search for files.
        """
        self.domain = domain

    @abstractmethod
    async def search_files(
        self,
        file_type: str,
        limit: int = 100,
    ) -> list[SearchResult]:
        """Search for files of a specific type on a domain.

        Args:
            file_type: File extension to search for (e.g., 'pdf', 'docx')
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects with file URLs
        """
        ...

    @abstractmethod
    async def close(self) -> None:
        """Close any open connections."""
        ...
