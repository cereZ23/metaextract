"""DuckDuckGo search engine implementation."""

import asyncio
import random
import re
from html import unescape
from urllib.parse import unquote, urlparse

import aiohttp

from metaextract.core.exceptions import SearchError
from metaextract.core.models import SearchResult
from metaextract.search.base import SearchEngine

# Pool of realistic User-Agent strings for rotation
USER_AGENTS = [
    # Chrome on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Chrome on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    # Firefox on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    # Firefox on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    # Safari on macOS
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    # Edge on Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    # Chrome on Linux
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class DuckDuckGoSearch(SearchEngine):
    """DuckDuckGo search engine implementation."""

    BASE_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, domain: str, delay: float = 2.0, rotate_ua: bool = True) -> None:
        """Initialize DuckDuckGo search.

        Args:
            domain: Target domain to search.
            delay: Delay between requests for rate limiting.
            rotate_ua: Whether to rotate User-Agent between requests.
        """
        super().__init__(domain)
        self.delay = delay
        self.rotate_ua = rotate_ua
        self._session: aiohttp.ClientSession | None = None
        self._ua_index = 0

    def _get_headers(self) -> dict[str, str]:
        """Get headers with rotated User-Agent if enabled."""
        ua = random.choice(USER_AGENTS) if self.rotate_ua else USER_AGENTS[0]

        return {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": random.choice(["en-US,en;q=0.9", "en-GB,en;q=0.9", "en;q=0.8"]),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp session."""
        if self._session is None or self._session.closed:
            # Create session without default headers - we'll set them per-request
            self._session = aiohttp.ClientSession()
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

                # Get fresh headers with rotated User-Agent for each request
                headers = self._get_headers()

                async with session.post(
                    self.BASE_URL,
                    data={"q": query, "b": ""},
                    headers=headers,
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
            # Avoid duplicates
            if (
                url
                and self._is_valid_file_url(url, file_type)
                and not any(r.url == url for r in results)
            ):
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
            return not (self.domain and self.domain not in parsed.netloc)
        except Exception:
            return False

    async def close(self) -> None:
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
