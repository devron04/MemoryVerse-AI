"""
MemoryVerse AI — Swappable Storage Backend Service

Provides a unified interface for file storage operations.
Supports:
- CloudflareR2StorageBackend (Default cloud storage via S3/boto3 API, 10GB free, zero egress)
- LocalStorageBackend (Fallback for offline local dev)

Per Architecture.md & Rules.md: original files are preserved unmodified.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple

from app.config import Settings

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """
    Custom exception for file storage operations.
    Carries user-facing error message, technical detail, and actionable suggestion.
    """

    def __init__(self, message: str, detail: str = "", suggestion: str = ""):
        self.message = message
        self.detail = detail
        self.suggestion = suggestion
        super().__init__(message)


class StorageBackend(ABC):
    """
    Abstract storage backend interface.
    All storage handlers must implement save_file, get_file_bytes, and delete_file.
    """

    @abstractmethod
    def save_file(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> Tuple[str, str]:
        """
        Save file content to the storage backend.

        Args:
            file_content: Raw byte content of the file.
            filename: Target unique filename/key.
            mime_type: MIME type of the file.

        Returns:
            Tuple of (storage_key_or_path, download_url_or_path)
        """
        pass

    @abstractmethod
    def get_file_bytes(self, key_or_path: str) -> bytes:
        """
        Retrieve raw file bytes from storage.

        Args:
            key_or_path: Storage key or file path.

        Returns:
            Raw bytes of the file.
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


class CloudflareR2StorageBackend(StorageBackend):
    """
    Cloudflare R2 storage backend using S3-compatible boto3 API.
    Zero egress fees, 10GB free tier.
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str,
        public_url: str = "",
    ):
        self.account_id = account_id
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.bucket_name = bucket_name
        self.public_url = public_url.rstrip("/")

        self.endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"
        self._s3_client = None

    def _get_client(self):
        """Lazy initialization of boto3 S3 client."""
        if self._s3_client is None:
            try:
                import boto3
                from botocore.config import Config
            except ImportError:
                raise StorageError(
                    message="boto3 library is required for Cloudflare R2 storage",
                    detail="Package 'boto3' is not installed.",
                    suggestion="Run 'pip install boto3' to enable R2 storage.",
                )

            self._s3_client = boto3.client(
                "s3",
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                config=Config(signature_version="s3v4"),
                region_name="auto",
            )
        return self._s3_client

    def save_file(
        self, file_content: bytes, filename: str, mime_type: str
    ) -> Tuple[str, str]:
        client = self._get_client()
        try:
            client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_content,
                ContentType=mime_type,
            )
            logger.info(
                "Uploaded file '%s' to Cloudflare R2 bucket '%s' (%d bytes)",
                filename, self.bucket_name, len(file_content),
            )
            download_url = (
                f"{self.public_url}/{filename}"
                if self.public_url
                else f"r2://{self.bucket_name}/{filename}"
            )
            return (filename, download_url)
        except Exception as e:
            logger.error("Cloudflare R2 upload failed for '%s': %s", filename, str(e))
            raise StorageError(
                message="Failed to upload file to Cloudflare R2",
                detail=str(e),
                suggestion="Check R2 credentials, bucket name, and network connection.",
            )

    def get_file_bytes(self, key_or_path: str) -> bytes:
        client = self._get_client()
        try:
            response = client.get_object(Bucket=self.bucket_name, Key=key_or_path)
            return response["Body"].read()
        except Exception as e:
            logger.error("Cloudflare R2 fetch failed for key '%s': %s", key_or_path, str(e))
            raise StorageError(
                message="Failed to retrieve file from Cloudflare R2",
                detail=str(e),
                suggestion="Verify that the file key exists in the bucket.",
            )


def get_storage_backend(settings: Settings) -> StorageBackend:
    """
    Factory function to retrieve the active storage backend.

    Selects CloudflareR2StorageBackend if storage_type == 'r2' and credentials are provided,
    otherwise falls back to LocalStorageBackend for offline local dev.

    Args:
        settings: Application settings.

    Returns:
        Instance of StorageBackend.
    """
    if (
        settings.storage_type.lower() == "r2"
        and settings.r2_account_id
        and settings.r2_account_id != "your-cloudflare-account-id"
        and settings.r2_access_key_id
        and settings.r2_access_key_id != "your-r2-access-key-id"
    ):
        logger.info("Using Cloudflare R2 Storage Backend (bucket: %s)", settings.r2_bucket_name)
        return CloudflareR2StorageBackend(
            account_id=settings.r2_account_id,
            access_key_id=settings.r2_access_key_id,
            secret_access_key=settings.r2_secret_access_key,
            bucket_name=settings.r2_bucket_name,
            public_url=settings.r2_public_url,
        )

    logger.info("Using Local Filesystem Storage Backend (dir: %s)", settings.upload_dir)
    return LocalStorageBackend(upload_dir=settings.upload_dir)
