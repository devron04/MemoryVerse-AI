"""
MemoryVerse AI — Application Configuration

Loads environment variables via Pydantic BaseSettings.
All external service keys are validated on startup.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Cloud defaults: Gemini 2.5 Flash, Cloudflare R2, Qdrant Cloud, Neo4j AuraDB.
    """

    # --- LLM (Gemini 2.5 Flash) ---
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key for structured extraction and categorization",
    )
    gemini_model: str = Field(
        default="gemini-2.5-flash",
        description="Gemini model identifier",
    )

    # --- File Storage (Cloudflare R2 default / Local fallback) ---
    storage_type: str = Field(
        default="r2",
        description="Storage backend: 'r2' (default cloud) or 'local' (offline testing)",
    )
    upload_dir: str = Field(
        default="./uploads",
        description="Directory for local file storage fallback",
    )
    data_dir: str = Field(
        default="./data",
        description="Directory for metadata storage (JSON-based in Phase 1)",
    )

    # Cloudflare R2 Credentials
    r2_account_id: str = Field(
        default="",
        description="Cloudflare Account ID",
    )
    r2_access_key_id: str = Field(
        default="",
        description="Cloudflare R2 Access Key ID",
    )
    r2_secret_access_key: str = Field(
        default="",
        description="Cloudflare R2 Secret Access Key",
    )
    r2_bucket_name: str = Field(
        default="memoryverse-files",
        description="Cloudflare R2 Bucket Name",
    )
    r2_public_url: str = Field(
        default="",
        description="Optional public URL prefix for R2 bucket",
    )

    # --- Qdrant Cloud (Phase 3) ---
    qdrant_url: str = Field(
        default="",
        description="Qdrant Cloud cluster URL",
    )
    qdrant_api_key: str = Field(
        default="",
        description="Qdrant Cloud API key",
    )

    # --- Neo4j AuraDB (Phase 2) ---
    neo4j_uri: str = Field(
        default="",
        description="Neo4j AuraDB connection URI",
    )
    neo4j_user: str = Field(
        default="neo4j",
        description="Neo4j username",
    )
    neo4j_password: str = Field(
        default="",
        description="Neo4j password",
    )

    # --- Tesseract OCR ---
    tesseract_cmd: str = Field(
        default="",
        description="Path to Tesseract executable (leave empty to use system PATH)",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


def get_settings() -> Settings:
    """
    Create and return a validated Settings instance.

    Raises:
        ValidationError: If required environment variables are missing.
    """
    return Settings()


def ensure_directories(settings: Settings) -> None:
    """
    Create upload and data directories if they don't exist.

    Args:
        settings: Application settings with directory paths.
    """
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
