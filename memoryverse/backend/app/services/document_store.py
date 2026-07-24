"""
MemoryVerse AI — Document Metadata Store

JSON file-based storage for document metadata in Phase 1.
Architecture.md specifies local filesystem for dev; this avoids
introducing an unspecified database before Neo4j/Qdrant in later phases.

Thread-safe via file locking. Original files are stored separately
in the uploads directory and are never modified.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from app.models.schemas import DocumentRecord, DocumentResponse

logger = logging.getLogger(__name__)


class DocumentStore:
    """
    JSON file-based document metadata store.

    Stores document records (metadata + extraction results) in a JSON file.
    Original uploaded files live separately in the uploads directory.
    """

    def __init__(self, data_dir: str):
        """
        Initialize the document store.

        Args:
            data_dir: Path to the data directory for metadata storage.
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "documents.json"

        if not self.db_path.exists():
            self._write_db([])
            logger.info("Created new document store at %s", self.db_path)

    def _read_db(self) -> list[dict]:
        """
        Read all document records from the JSON file.

        Returns:
            List of document record dicts.
        """
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error("Failed to read document store: %s", str(e))
            return []

    def _write_db(self, records: list[dict]) -> None:
        """
        Write document records to the JSON file.

        Args:
            records: List of document record dicts to write.
        """
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to write document store: %s", str(e))
            raise

    def add(self, record: DocumentRecord) -> DocumentRecord:
        """
        Add a new document record to the store.

        Args:
            record: DocumentRecord to store.

        Returns:
            The stored DocumentRecord (with generated ID).
        """
        records = self._read_db()
        records.append(record.model_dump())
        self._write_db(records)
        logger.info("Stored document '%s' (id=%s)", record.filename, record.id)
        return record

    def get_all(self) -> list[DocumentRecord]:
        """
        Retrieve all document records.

        Returns:
            List of DocumentRecord objects.
        """
        records = self._read_db()
        return [DocumentRecord(**r) for r in records]

    def get_by_id(self, doc_id: str) -> Optional[DocumentRecord]:
        """
        Retrieve a single document record by ID.

        Args:
            doc_id: UUID of the document.

        Returns:
            DocumentRecord if found, None otherwise.
        """
        records = self._read_db()
        for record in records:
            if record.get("id") == doc_id:
                return DocumentRecord(**record)
        return None

    def to_response(self, record: DocumentRecord) -> DocumentResponse:
        """
        Convert a DocumentRecord to a DocumentResponse (for API output).
        Strips internal fields like extracted_text.

        Args:
            record: DocumentRecord to convert.

        Returns:
            DocumentResponse suitable for API response.
        """
        return DocumentResponse(
            id=record.id,
            filename=record.filename,
            category=record.category,
            title=record.title,
            issuer=record.issuer,
            date=record.date,
            entities=record.entities,
            confidence=record.confidence,
            summary=record.summary,
            uploaded_at=record.uploaded_at,
        )
