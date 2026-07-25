"""
MemoryVerse AI — Swappable Storage Backend Service

Provides a unified interface for file storage operations.
Supports:
- SupabaseStorageBackend (Primary cloud storage via REST API using httpx)
- LocalStorageBackend (Fallback for offline local dev)

Per Architecture.md & Rules.md: original files are preserved unmodified.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Tuple
import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """
    Custom exception for file storage operations.
    """

    def __init__(self, message: str, detail: str = "", suggestion: str = ""):
        self.message = message
        self.detail = detail
        self.suggestion = suggestion
        super().__init__(message)


class StorageBackend(ABC):
    """
    Abstract storage backend interface.
    """

    @abstractmethod
    def save_file(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> Tuple[str, str]:
        """
        Save file content to the storage backend.

        Returns:
            Tuple of (storage_key_or_path, download_url_or_path)
        """
        pass

    @abstractmethod
    def get_file_bytes(self, key_or_path: str) -> bytes:
        """
        Retrieve raw file bytes from storage.
        """
        pass


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage backend for offline dev/testing.
    """

    def __init__(self, upload_dir: str):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def save_file(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> Tuple[str, str]:
        file_path = self.upload_dir / filename
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.info("Saved file locally to %s (%d bytes)", file_path, len(file_content))
            return (str(file_path), str(file_path))
        except Exception as e:
            logger.error("Failed to save local file '%s': %s", filename, str(e))
            raise StorageError(
                message="Failed to save file to local storage",
                detail=str(e),
                suggestion="Check directory write permissions.",
            )

    def get_file_bytes(self, key_or_path: str) -> bytes:
        path = Path(key_or_path)
        if not path.exists():
            raise StorageError(
                message="File not found on local disk",
                detail=f"Path '{key_or_path}' does not exist.",
                suggestion="Re-upload the file.",
            )
        try:
            with open(path, "rb") as f:
                return f.read()
        except Exception as e:
            raise StorageError(
                message="Failed to read file from local storage",
                detail=str(e),
            )


class SupabaseStorageBackend(StorageBackend):
    """
    Supabase Storage backend using REST API with httpx.
    """

    def __init__(self, supabase_url: str, supabase_key: str, bucket_name: str = "memoryverse-files"):
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_key = supabase_key
        self.bucket_name = bucket_name

    def save_file(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> Tuple[str, str]:
        upload_endpoint = f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{filename}"
        headers = {
            "Authorization": f"Bearer {self.supabase_key}",
            "apikey": self.supabase_key,
            "Content-Type": mime_type,
            "x-upsert": "true",
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.post(upload_endpoint, headers=headers, content=file_content)
                if res.status_code not in [200, 201]:
                    logger.error("Supabase Storage upload error (%d): %s", res.status_code, res.text)
                    raise StorageError(
                        message="Failed to upload file to Supabase Storage",
                        detail=f"Status {res.status_code}: {res.text}",
                        suggestion="Check Supabase bucket permissions and credentials.",
                    )

            logger.info("Uploaded file '%s' to Supabase Storage bucket '%s'", filename, self.bucket_name)
            public_url = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{filename}"
            return (filename, public_url)
        except StorageError:
            raise
        except Exception as e:
            logger.error("Supabase Storage upload exception for '%s': %s", filename, str(e))
            raise StorageError(
                message="Failed to upload file to Supabase Storage",
                detail=str(e),
                suggestion="Verify Supabase URL and network connectivity.",
            )

    def get_file_bytes(self, key_or_path: str) -> bytes:
        download_endpoint = f"{self.supabase_url}/storage/v1/object/authenticated/{self.bucket_name}/{key_or_path}"
        headers = {
            "Authorization": f"Bearer {self.supabase_key}",
            "apikey": self.supabase_key,
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                res = client.get(download_endpoint, headers=headers)
                if res.status_code != 200:
                    public_endpoint = f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{key_or_path}"
                    res = client.get(public_endpoint, headers=headers)

                if res.status_code != 200:
                    raise StorageError(
                        message="Failed to retrieve file from Supabase Storage",
                        detail=f"Status {res.status_code}: {res.text}",
                    )
                return res.content
        except StorageError:
            raise
        except Exception as e:
            logger.error("Supabase Storage fetch exception for '%s': %s", key_or_path, str(e))
            raise StorageError(
                message="Failed to retrieve file from Supabase Storage",
                detail=str(e),
            )


def get_storage_backend(settings: Settings) -> StorageBackend:
    """
    Factory function to retrieve the active storage backend.

    Selects SupabaseStorageBackend if storage_type == 'supabase' and valid credentials exist,
    otherwise falls back to LocalStorageBackend for local dev.
    """
    stype = settings.storage_type.lower()

    if (
        stype == "supabase"
        and settings.supabase_url
        and settings.supabase_key
        and "your-supabase" not in settings.supabase_url
    ):
        logger.info("Using Supabase Storage Backend (bucket: %s)", settings.supabase_bucket_name)
        return SupabaseStorageBackend(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_key,
            bucket_name=settings.supabase_bucket_name,
        )

    logger.info("Using Local Filesystem Storage Backend (dir: %s)", settings.upload_dir)
    return LocalStorageBackend(upload_dir=settings.upload_dir)
