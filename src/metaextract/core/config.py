"""Configuration for metaextract."""

from dataclasses import dataclass, field
from pathlib import Path

from metaextract.core.models import FileType


@dataclass
class Config:
    """Configuration for a metaextract scan."""

    # Target
    domain: str = ""

    # File types to search
    file_types: list[FileType] = field(default_factory=lambda: [
        FileType.PDF,
        FileType.DOC,
        FileType.DOCX,
        FileType.XLS,
        FileType.XLSX,
        FileType.PPT,
        FileType.PPTX,
    ])

    # Search settings
    search_limit: int = 200

    # Download settings
    download_limit: int = 50
    max_concurrent_downloads: int = 5
    download_timeout: int = 30

    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("./downloads"))
    output_file: Path | None = None

    # Mode
    local_mode: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        """Ensure output_dir is a Path."""
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
        if isinstance(self.output_file, str):
            self.output_file = Path(self.output_file)
