# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MetaExtract v3.0** is a modern Python 3.12+ OSINT tool that extracts metadata from public documents. It searches for documents via DuckDuckGo, downloads them asynchronously, and extracts metadata (usernames, software versions, file paths, email addresses) useful for security assessments.

This is a complete rewrite of the original metagoofil tool with modern architecture.

## Installation

```bash
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

## Running the Tool

```bash
# Search a domain for documents and extract metadata
metaextract -d example.com -t pdf,docx -l 200 -n 50 -o downloads -f report.html

# Local analysis mode - analyze existing documents in a directory
metaextract --local -o ./documents -f report.json

# With verbose output
metaextract -d example.com -t pdf -v -f report.html
```

**Options:**
- `-d, --domain`: Target domain to search
- `-t, --filetypes`: File types (pdf, doc, docx, xls, xlsx, ppt, pptx, ods, odp, odt)
- `-l, --limit`: Search result limit per file type (default 200)
- `-n, --download-limit`: File download limit per type (default 50)
- `-o, --output-dir`: Output directory for downloaded files
- `-f, --output-file`: Output report file (HTML or JSON based on extension)
- `--local`: Analyze local files only (no search/download)
- `--json`: Force JSON output format
- `-v, --verbose`: Verbose output

## Architecture

```
src/metaextract/
├── __init__.py         # Package init with version
├── __main__.py         # Entry point: python -m metaextract
├── cli.py              # Click-based CLI with Rich output
├── core/
│   ├── config.py       # Configuration dataclass
│   ├── models.py       # Pydantic models (DocumentMetadata, ScanResults, etc.)
│   └── exceptions.py   # Custom exception hierarchy
├── search/
│   ├── base.py         # Abstract SearchEngine
│   ├── duckduckgo.py   # DuckDuckGo async search implementation
│   └── parser.py       # Email/URL/path extraction
├── download/
│   └── downloader.py   # Async aiohttp downloader with concurrency
├── extractors/
│   ├── base.py         # Abstract MetadataExtractor base class
│   ├── pdf.py          # PDF via pdfminer.six
│   ├── docx.py         # DOCX via python-docx
│   ├── xlsx.py         # XLSX via openpyxl
│   ├── pptx.py         # PPTX via python-pptx
│   ├── legacy_office.py # DOC/XLS/PPT via olefile
│   └── openoffice.py   # ODS/ODP/ODT via zipfile + lxml
├── processing/
│   └── processor.py    # Result aggregation and deduplication
└── export/
    ├── html.py         # Jinja2 HTML report generator
    ├── json.py         # JSON export
    └── templates/
        └── report.html.j2
```

## Key Dependencies

- **aiohttp**: Async HTTP for search and downloads
- **pdfminer.six**: PDF metadata extraction
- **python-docx/openpyxl/python-pptx**: Modern Office format extraction
- **olefile**: Legacy Office format (DOC/XLS/PPT) extraction
- **lxml**: XML parsing for OpenDocument formats
- **click + rich**: CLI with rich terminal output
- **pydantic**: Data validation and models
- **jinja2**: HTML report templates

## Development Commands

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=metaextract

# Lint
ruff check .

# Type check
mypy src/metaextract
```

## Extractor Interface

All extractors inherit from `MetadataExtractor` and implement:
- `extract() -> ExtractionResult`: Extract metadata from file
- `extract_text() -> str | None`: Extract text content for email/path parsing

## Data Flow

1. **Search**: `DuckDuckGoSearch` finds document URLs matching domain + filetype
2. **Download**: `AsyncDownloader` fetches files concurrently via aiohttp
3. **Extract**: Format-specific extractor parses metadata
4. **Process**: `ResultProcessor` aggregates and deduplicates results
5. **Export**: `HTMLExporter` or `JSONExporter` generates report

## Notes

- This is a security assessment tool - ensure authorized use only
- DuckDuckGo may rate limit; the tool includes delays between requests
- Legacy original code is preserved in discovery/, extractors/, etc. for reference
