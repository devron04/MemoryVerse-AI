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

    Cloud defaults: Gemini 3.6 Flash, Supabase Storage, Qdrant Cloud, Neo4j AuraDB.
    """

    # --- LLM (Gemini 3.6 Flash) ---
    gemini_api_key: str = Field(
        ...,
        description="Google Gemini API key for structured extraction and categorization",
    )
    gemini_model: str = Field(
        default="gemini-3.6-flash",
        description="Gemini model identifier",
    )

    # --- File Storage (Supabase Storage / Local fallback) ---
    storage_type: str = Field(
        default="supabase",
        description="Storage backend: 'supabase' or 'local'",
    )
    upload_dir: str = Field(
        default="./uploads",
        description="Directory for local file storage fallback",
    )
    data_dir: str = Field(
        default="./data",
        description="Directory for metadata storage",
    )

    # Supabase Storage Credentials (1GB Free, easy setup)
    supabase_url: str = Field(
        default="",
        description="Supabase Project URL (e.g. https://xxxx.supabase.co)",
    )
    supabase_key: str = Field(
        default="",
        description="Supabase API key (service_role secret key)",
    )
    supabase_bucket_name: str = Field(
        default="memoryverse-files",
        description="Supabase Storage Bucket Name",
    )

    # --- Qdrant Cloud ---
    qdrant_url: str = Field(
        default="",
        description="Qdrant Cloud cluster URL",
    )
    qdrant_api_key: str = Field(
        default="",
        description="Qdrant Cloud API key",
    )

    # --- Neo4j AuraDB ---
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
        description="Path to Tesseract executable",
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
    """
    return Settings()


def ensure_directories(settings: Settings) -> None:
    """
    Create upload and data directories if they don't exist.
    """
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)
