"""Async file downloader with concurrency control."""

import asyncio
from collections.abc import Callable
from pathlib import Path
from urllib.parse import unquote, urlparse

import aiohttp

from metaextract.core.models import DownloadResult


class AsyncDownloader:
    """Async file downloader with concurrency control."""

    def __init__(
        self,
        output_dir: Path,
        max_concurrent: int = 5,
        timeout: int = 30,
        progress_callback: Callable[[str, int, int], None] | None = None,
    ) -> None:
        """Initialize the downloader.

        Args:
            output_dir: Directory to save downloaded files.
            max_concurrent: Maximum concurrent downloads.
            timeout: Request timeout in seconds.
            progress_callback: Optional callback for progress updates.
                               Called with (filename, current, total).
        """
        self.output_dir = Path(output_dir)
        self.max_concurrent = max_concurrent
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.progress_callback = progress_callback
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
        }

    async def download_files(
        self,
        urls: list[str],
        limit: int | None = None,
    ) -> list[DownloadResult]:
        """Download multiple files concurrently.

        Args:
            urls: List of URLs to download.
            limit: Maximum number of files to download (None for all).

        Returns:
            List of DownloadResult objects.
        """
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        urls_to_download = urls[:limit] if limit else urls
        total = len(urls_to_download)

        async with aiohttp.ClientSession(
            headers=self._headers,
            timeout=self.timeout,
        ) as session:
            tasks = [
                self._download_file(session, url, idx, total)
                for idx, url in enumerate(urls_to_download)
            ]
            return await asyncio.gather(*tasks)

    async def _download_file(
        self,
        session: aiohttp.ClientSession,
        url: str,
        index: int,
        total: int,
    ) -> DownloadResult:
        """Download a single file with semaphore control."""
        async with self._semaphore:
            try:
                filename = self._extract_filename(url)
                local_path = self.output_dir / filename

                # Handle duplicate filenames
                local_path = self._get_unique_path(local_path)

                # Skip if already exists
                if local_path.exists():
                    return DownloadResult(
                        url=url,
                        local_path=str(local_path),
                        success=True,
                    )

                async with session.get(url, allow_redirects=True) as response:
                    if response.status == 200:
                        content = await response.read()

                        # Verify we got actual content
                        if len(content) < 100:
                            return DownloadResult(
                                url=url,
                                local_path=None,
                                success=False,
                                error="File too small or empty",
                            )

                        local_path.write_bytes(content)

                        if self.progress_callback:
                            self.progress_callback(filename, index + 1, total)

                        return DownloadResult(
                            url=url,
                            local_path=str(local_path),
                            success=True,
                        )
                    else:
                        return DownloadResult(
                            url=url,
                            local_path=None,
                            success=False,
                            error=f"HTTP {response.status}",
                        )

            except TimeoutError:
                return DownloadResult(
                    url=url,
                    local_path=None,
                    success=False,
                    error="Timeout",
                )
            except aiohttp.ClientError as e:
                return DownloadResult(
                    url=url,
                    local_path=None,
                    success=False,
                    error=f"Network error: {e}",
                )
            except Exception as e:
                return DownloadResult(
                    url=url,
                    local_path=None,
                    success=False,
                    error=str(e),
                )

    def _extract_filename(self, url: str) -> str:
        """Extract filename from URL."""
        parsed = urlparse(url)
        path = unquote(parsed.path)

        # Get the last part of the path
        filename = path.split("/")[-1]

        # Remove query parameters
        if "?" in filename:
            filename = filename.split("?")[0]

        # Fallback if no filename
        if not filename:
            filename = "downloaded_file"

        # Sanitize filename
        filename = self._sanitize_filename(filename)

        return filename

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to be safe for filesystem."""
        # Remove or replace unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            filename = filename.replace(char, "_")

        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = name[:190] + ("." + ext if ext else "")

        return filename

    def _get_unique_path(self, path: Path) -> Path:
        """Get a unique path if file already exists."""
        if not path.exists():
            return path

        stem = path.stem
        suffix = path.suffix
        counter = 1

        while path.exists():
            path = path.parent / f"{stem}_{counter}{suffix}"
            counter += 1

        return path
