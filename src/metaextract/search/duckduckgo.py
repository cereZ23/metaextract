"""DuckDuckGo search engine implementation."""

import asyncio
import random
import re
from html import unescape
from urllib.parse import unquote, urlparse

import aiohttp

from metaextract.core.models import SearchResult
from metaextract.core.exceptions import SearchError
from metaextract.search.base import SearchEngine


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search engine implementation."""

    BASE_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, domain: str, delay: float = 2.0) -> None:
        """Initialize DuckDuckGo search.

        Args:
            domain: Target domain to search.
            delay: Delay between requests for rate limiting.
        """
        super().__init__(domain)
        self.delay = delay
        self._session: aiohttp.ClientSession | None = None
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(headers=self._headers)
        return self._session

    async def search_files(
        self,
        file_type: str,
        limit: int = 100,
        max_retries: int = 3,
    ) -> list[SearchResult]:
        """Search DuckDuckGo for files of a specific type."""
        query = f"filetype:{file_type} site:{self.domain}"
        results: list[SearchResult] = []

        session = await self._get_session()

        for attempt in range(max_retries):
            try:
                # Add jitter to delay
                jitter = random.uniform(0.5, 1.5)
                if attempt > 0:
                    wait_time = self.delay * (attempt + 1) * jitter
                    await asyncio.sleep(wait_time)

                async with session.post(
                    self.BASE_URL,
                    data={"q": query, "b": ""},
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as response:
                    # Handle rate limiting (202, 429)
                    if response.status in (202, 429):
                        if attempt < max_retries - 1:
                            continue
                        raise SearchError(
                            f"Rate limited (status {response.status})",
                            query=query,
                        )

                    if response.status != 200:
                        raise SearchError(
                            f"Search failed with status {response.status}",
                            query=query,
                        )

                    html = await response.text()
                    results = self._parse_results(html, file_type)
                    break

            except aiohttp.ClientError as e:
                if attempt < max_retries - 1:
                    continue
                raise SearchError(f"Network error: {e}", query=query) from e

        # Rate limiting between searches
        await asyncio.sleep(self.delay + random.uniform(0.5, 1.5))

        return results[:limit]

    def _parse_results(self, html: str, file_type: str) -> list[SearchResult]:
        """Parse DuckDuckGo HTML results."""
        results: list[SearchResult] = []

        # Pattern to find result links
        # DuckDuckGo wraps URLs in their redirect
        link_pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>([^<]*)</a>',
            re.IGNORECASE,
        )

        # Also look for direct file links
        file_pattern = re.compile(
            rf'href="([^"]*\.{re.escape(file_type)}[^"]*)"',
            re.IGNORECASE,
        )

        # Parse result links
        for match in link_pattern.finditer(html):
            url = match.group(1)
            title = unescape(match.group(2).strip())

            # DuckDuckGo uses uddg parameter for actual URL
            if "uddg=" in url:
                actual_url = self._extract_uddg_url(url)
                if actual_url and self._is_valid_file_url(actual_url, file_type):
                    results.append(SearchResult(url=actual_url, title=title))
            elif self._is_valid_file_url(url, file_type):
                results.append(SearchResult(url=url, title=title))

        # Also search for direct file links in the page
        for match in file_pattern.finditer(html):
            url = match.group(1)
            url = self._clean_url(url)
            if url and self._is_valid_file_url(url, file_type):
                # Avoid duplicates
                if not any(r.url == url for r in results):
                    results.append(SearchResult(url=url))

        return results

    def _extract_uddg_url(self, url: str) -> str | None:
        """Extract actual URL from DuckDuckGo redirect."""
        try:
            # uddg parameter contains the actual URL
            if "uddg=" in url:
                start = url.find("uddg=") + 5
                end = url.find("&", start)
                if end == -1:
                    end = len(url)
                encoded_url = url[start:end]
                return unquote(encoded_url)
        except Exception:
            pass
        return None

    def _clean_url(self, url: str) -> str:
        """Clean and normalize a URL."""
        url = unescape(url)
        url = unquote(url)

        # Ensure proper scheme
        if url.startswith("//"):
            url = "https:" + url
        elif not url.startswith(("http://", "https://")):
            return ""

        return url

    def _is_valid_file_url(self, url: str, file_type: str) -> bool:
        """Check if URL is a valid file URL."""
        try:
            parsed = urlparse(url)

            # Must have valid scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                return False

            # Check file extension
            path_lower = parsed.path.lower()
            if not path_lower.endswith(f".{file_type.lower()}"):
                return False

            # Optionally check domain if specified
            if self.domain and self.domain not in parsed.netloc:
                return False

            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
