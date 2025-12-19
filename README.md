# MetaExtract

Document metadata extraction tool for OSINT - Modern Python 3.12+ rewrite of Metagoofil.

## Features

- Async architecture with aiohttp for concurrent downloads
- DuckDuckGo search integration (no API key required)
- Support for PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, ODS, ODP, ODT
- Rich CLI with progress indicators
- HTML and JSON report export
- Extracts usernames, email addresses, software versions, and file paths
- **Anti-rate-limiting**: User-Agent rotation and configurable delays

## Installation

### Using Virtual Environment (Recommended)

```bash
# Clone the repository
git clone https://github.com/cereZ23/metaextract.git
cd metaextract

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate     # Windows

# Install the package
pip install -e .

# Run metaextract
metaextract --help
```

### Using Docker

```bash
# Build the image
docker build -t metaextract .

# Run with a domain
docker run --rm -v $(pwd)/output:/app/output metaextract -d example.com -t pdf,docx -o /app/output -f /app/output/report.html

# Analyze local files
docker run --rm -v $(pwd)/documents:/app/documents -v $(pwd)/output:/app/output metaextract --local -o /app/documents -f /app/output/report.html
```

### Using pip directly

```bash
pip install -e .
```

## Usage

```bash
# Search a domain for documents and extract metadata
metaextract -d example.com -t pdf,docx -n 50 -f report.html

# Search with specific file types
metaextract -d example.com -t pdf,doc,xls,ppt -n 20 -o ./downloads -f report.html

# Analyze local files only
metaextract --local -o ./documents -f report.json

# Verbose output
metaextract -d example.com -t pdf -v -f report.html

# JSON output
metaextract -d example.com -t pdf --json -f report.json

# With longer delay to avoid rate limiting
metaextract -d example.com -t pdf --delay 5 -f report.html
```

## Options

| Option | Description |
|--------|-------------|
| `-d, --domain` | Target domain to search |
| `-t, --filetypes` | File types to search (comma-separated: pdf,doc,docx,xls,xlsx,ppt,pptx,ods,odp,odt) |
| `-l, --limit` | Limit of search results per file type (default: 200) |
| `-n, --download-limit` | Maximum files to download per type (default: 50) |
| `-o, --output-dir` | Directory to save downloaded files (default: ./downloads) |
| `-f, --output-file` | Output report file (HTML or JSON based on extension) |
| `--local` | Analyze local files only (no search/download) |
| `--json` | Force JSON output format |
| `-v, --verbose` | Verbose output |
| `--delay` | Delay between searches in seconds (default: 3.0) - helps avoid rate limiting |
| `--no-rotate-ua` | Disable User-Agent rotation (enabled by default) |

## Output

MetaExtract extracts and reports:

- **Users**: Author names, last modified by
- **Software**: Applications used to create documents (Microsoft Word, Adobe Acrobat, etc.)
- **Emails**: Email addresses found in document content
- **Paths**: File paths, server names, and templates

Reports are generated in HTML (styled, interactive) or JSON (machine-readable) format.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Type checking
mypy src/metaextract
```

## License

GPL-2.0

## Credits

Original Metagoofil by Christian Martorella (Edge-Security.com)
