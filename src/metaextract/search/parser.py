"""Text parsing utilities for extracting emails, URLs, and hostnames."""

import re
from typing import Pattern

# Compiled regex patterns for efficiency
EMAIL_PATTERN: Pattern[str] = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

URL_PATTERN: Pattern[str] = re.compile(
    r"https?://[^\s<>\"')\]}>]+",
    re.IGNORECASE,
)

# Pattern for extracting hostnames/subdomains
HOSTNAME_PATTERN: Pattern[str] = re.compile(
    r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}\b"
)

# Common false positives to filter out
EMAIL_BLACKLIST = {
    "example.com",
    "example.org",
    "test.com",
    "localhost",
    "domain.com",
}

# File extensions that look like TLDs but aren't
FALSE_TLDS = {
    ".pdf",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".ppt",
    ".pptx",
    ".zip",
    ".rar",
    ".exe",
    ".dll",
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
}


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text.

    Args:
        text: Text content to search.

    Returns:
        List of unique email addresses found.
    """
    if not text:
        return []

    emails: set[str] = set()

    for match in EMAIL_PATTERN.finditer(text):
        email = match.group(0).lower()

        # Filter out false positives
        domain = email.split("@")[1] if "@" in email else ""
        if domain in EMAIL_BLACKLIST:
            continue

        # Filter out file extensions mistaken as emails
        if any(email.endswith(ext) for ext in FALSE_TLDS):
            continue

        emails.add(email)

    return sorted(emails)


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text.

    Args:
        text: Text content to search.

    Returns:
        List of unique URLs found.
    """
    if not text:
        return []

    urls: set[str] = set()

    for match in URL_PATTERN.finditer(text):
        url = match.group(0)

        # Clean trailing punctuation
        while url and url[-1] in ".,;:!?)>]}":
            url = url[:-1]

        if url:
            urls.add(url)

    return sorted(urls)


def extract_hostnames(text: str, domain: str | None = None) -> list[str]:
    """Extract hostnames from text, optionally filtering by domain.

    Args:
        text: Text content to search.
        domain: Optional domain to filter results (e.g., 'example.com').

    Returns:
        List of unique hostnames found.
    """
    if not text:
        return []

    hostnames: set[str] = set()

    for match in HOSTNAME_PATTERN.finditer(text):
        hostname = match.group(0).lower()

        # Skip if it's likely a file path
        if any(hostname.endswith(ext) for ext in FALSE_TLDS):
            continue

        # Filter by domain if specified
        if domain:
            if not hostname.endswith(domain.lower()):
                continue

        hostnames.add(hostname)

    return sorted(hostnames)


def extract_paths(text: str) -> list[str]:
    """Extract file paths from text.

    Args:
        text: Text content to search.

    Returns:
        List of unique file paths found.
    """
    if not text:
        return []

    paths: set[str] = set()

    # Windows paths: C:\Users\...
    windows_pattern = re.compile(r"[A-Za-z]:\\[^\s<>\"']+")
    for match in windows_pattern.finditer(text):
        path = match.group(0)
        # Clean trailing punctuation
        while path and path[-1] in ".,;:!?)>]}":
            path = path[:-1]
        if path:
            paths.add(path)

    # Unix paths: /home/user/...
    unix_pattern = re.compile(r"/(?:[^\s<>\"'/]+/)+[^\s<>\"']+")
    for match in unix_pattern.finditer(text):
        path = match.group(0)
        while path and path[-1] in ".,;:!?)>]}":
            path = path[:-1]
        if path and len(path) > 3:  # Avoid false positives
            paths.add(path)

    # UNC paths: \\server\share
    unc_pattern = re.compile(r"\\\\[^\s<>\"']+")
    for match in unc_pattern.finditer(text):
        path = match.group(0)
        while path and path[-1] in ".,;:!?)>]}":
            path = path[:-1]
        if path:
            paths.add(path)

    return sorted(paths)
