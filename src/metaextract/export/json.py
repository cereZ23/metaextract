"""JSON export for metaextract results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from metaextract.core.models import ScanResults


class JSONExporter:
    """Export scan results to JSON format."""

    def export(self, results: ScanResults, output_path: Path) -> None:
        """Export results to a JSON file.

        Args:
            results: Scan results to export.
            output_path: Path to save the JSON file.
        """
        data = self._serialize_results(results)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=self._json_serializer)

    def export_string(self, results: ScanResults) -> str:
        """Export results to a JSON string.

        Args:
            results: Scan results to export.

        Returns:
            JSON string representation.
        """
        data = self._serialize_results(results)
        return json.dumps(data, indent=2, default=self._json_serializer)

    def _serialize_results(self, results: ScanResults) -> dict[str, Any]:
        """Serialize ScanResults to a dictionary."""
        return {
            "meta": {
                "domain": results.domain,
                "generated_at": datetime.now().isoformat(),
                "stats": results.stats,
            },
            "summary": {
                "users": results.unique_users,
                "software": results.unique_software,
                "emails": results.unique_emails,
                "paths": results.unique_paths,
            },
            "documents": [
                self._serialize_document(doc)
                for doc in results.documents
            ],
            "failed": [
                {"file": file, "error": error}
                for file, error in results.failed
            ],
        }

    def _serialize_document(self, doc: Any) -> dict[str, Any]:
        """Serialize a DocumentMetadata to a dictionary."""
        return {
            "filename": doc.filename,
            "file_type": doc.file_type.value if hasattr(doc.file_type, "value") else str(doc.file_type),
            "source_url": doc.source_url,
            "author": doc.author,
            "creator": doc.creator,
            "last_modified_by": doc.last_modified_by,
            "users": doc.users,
            "producer": doc.producer,
            "application": doc.application,
            "app_version": doc.app_version,
            "software": doc.software,
            "template": doc.template,
            "paths": doc.paths,
            "emails": doc.emails,
            "created": doc.created.isoformat() if doc.created else None,
            "modified": doc.modified.isoformat() if doc.modified else None,
        }

    @staticmethod
    def _json_serializer(obj: Any) -> str:
        """Custom JSON serializer for non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "value"):  # Enum
            return obj.value
        return str(obj)
