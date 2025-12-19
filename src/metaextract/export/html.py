"""HTML export for metaextract results."""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape

from metaextract.core.models import ScanResults


class HTMLExporter:
    """Export scan results to HTML format."""

    def __init__(self) -> None:
        """Initialize the HTML exporter with Jinja2 environment."""
        self.env = Environment(
            loader=PackageLoader("metaextract.export", "templates"),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def export(self, results: ScanResults, output_path: Path) -> None:
        """Export results to an HTML file.

        Args:
            results: Scan results to export.
            output_path: Path to save the HTML file.
        """
        html = self.export_string(results)
        Path(output_path).write_text(html, encoding="utf-8")

    def export_string(self, results: ScanResults) -> str:
        """Export results to an HTML string.

        Args:
            results: Scan results to export.

        Returns:
            HTML string representation.
        """
        template = self.env.get_template("report.html.j2")

        return template.render(
            domain=results.domain,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            stats=results.stats,
            users=results.unique_users,
            software=results.unique_software,
            emails=results.unique_emails,
            paths=results.unique_paths,
            documents=results.documents,
            failed=results.failed,
        )
