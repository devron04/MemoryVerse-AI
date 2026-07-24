"""
MemoryVerse AI — Documents API Routes

GET /documents         — list all uploaded documents with metadata.
GET /documents/{id}    — get a single document's metadata.
GET /documents/{id}/file — download the original unmodified file.
"""

import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.config import Settings, get_settings
from app.models.schemas import (
    DocumentListResponse,
    DocumentResponse,
    ErrorResponse,
)
from app.services.document_store import DocumentStore
from app.services.storage import get_storage_backend, StorageError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])


def get_document_store(settings: Settings = Depends(get_settings)) -> DocumentStore:
    """Dependency: create document store from settings."""
    return DocumentStore(data_dir=settings.data_dir)


@router.get(
    "/documents",
    response_model=DocumentListResponse,
)
async def list_documents(
    doc_store: DocumentStore = Depends(get_document_store),
):
    """
    List all uploaded documents with their extracted metadata.

    Returns:
        DocumentListResponse with list of documents and total count.
    """
    records = doc_store.get_all()
    documents = [doc_store.to_response(r) for r in records]
    return DocumentListResponse(
        documents=documents,
        total=len(documents),
    )


@router.get(
    "/documents/{doc_id}",
    response_model=DocumentResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_document(
    doc_id: str,
    doc_store: DocumentStore = Depends(get_document_store),
):
    """
    Get metadata for a single uploaded document.

    Args:
        doc_id: UUID of the document.

    Returns:
        DocumentResponse with the document's metadata.
    """
    record = doc_store.get_by_id(doc_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Document not found",
                "detail": f"No document with ID '{doc_id}'",
                "suggestion": "Check the document ID and try again.",
            },
        )
    return doc_store.to_response(record)


@router.get(
    "/documents/{doc_id}/file",
    responses={404: {"model": ErrorResponse}},
)
async def download_document_file(
    doc_id: str,
    settings: Settings = Depends(get_settings),
    doc_store: DocumentStore = Depends(get_document_store),
):
    """
    Download the original, unmodified uploaded file.

    Per PRD.md and Rules.md: original files are never modified.
    This endpoint retrieves and serves the byte-for-byte original from the active storage backend.

    Args:
        doc_id: UUID of the document.
        settings: Application settings.
        doc_store: Document metadata store.

    Returns:
        Response containing original file bytes with Content-Disposition header.
    """
    record = doc_store.get_by_id(doc_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Document not found",
                "detail": f"No document with ID '{doc_id}'",
                "suggestion": "Check the document ID and try again.",
            },
        )

    storage_backend = get_storage_backend(settings)
    try:
        file_bytes = storage_backend.get_file_bytes(record.original_file_path)
    except StorageError as e:
        logger.error(
            "Failed to retrieve original file for document '%s': %s",
            doc_id, e.message,
        )
        raise HTTPException(
            status_code=404,
            detail={
                "error": e.message,
                "detail": e.detail,
                "suggestion": e.suggestion,
            },
        )

    return Response(
        content=file_bytes,
        media_type=record.mime_type,
        headers={
            "Content-Disposition": f'inline; filename="{record.filename}"',
        },
    )
