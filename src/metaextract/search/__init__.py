"""Search modules for metaextract."""

from metaextract.search.base import SearchEngine
from metaextract.search.duckduckgo import DuckDuckGoSearch
from metaextract.search.parser import extract_emails, extract_urls, extract_hostnames

__all__ = [
    "SearchEngine",
    "DuckDuckGoSearch",
    "extract_emails",
    "extract_urls",
    "extract_hostnames",
]
