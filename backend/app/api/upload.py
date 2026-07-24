"""
MemoryVerse AI — Upload API Route

POST /upload — accepts multipart file upload (PDF, DOCX, PNG, JPG/JPEG).
Orchestrates: save original → extract text → LLM categorization → store metadata → sync Neo4j Graph → index Qdrant Vector Store.

Per Rules.md §5: original files are never modified or deleted.
Per Rules.md §3: per-document error isolation (one failure doesn't block others).
"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends

from app.config import Settings, get_settings
from app.models.schemas import (
    DocumentRecord,
    ErrorResponse,
    UploadResponse,
)
from app.services.extraction import extract_text, ExtractionError, SUPPORTED_TYPES
from app.services.llm_client import LLMClient
from app.services.llm_extraction import extract_structured_data, LLMExtractionError
from app.services.document_store import DocumentStore
from app.services.storage import get_storage_backend, StorageError
from app.services.graph_store import GraphStore
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["upload"])

ALLOWED_MIME_TYPES = set(SUPPORTED_TYPES.keys())
MIME_ALIASES = {
    "image/jpg": "image/jpeg",
}


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Dependency: create LLM client from settings."""
    return LLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


def get_document_store(settings: Settings = Depends(get_settings)) -> DocumentStore:
    """Dependency: create document store from settings."""
    return DocumentStore(data_dir=settings.data_dir)


@router.post(
    "/upload",
    response_model=UploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file type"},
        422: {"model": ErrorResponse, "description": "Extraction error"},
        500: {"model": ErrorResponse, "description": "Processing error"},
    },
)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    llm_client: LLMClient = Depends(get_llm_client),
    doc_store: DocumentStore = Depends(get_document_store),
):
    """
    Upload a document for extraction, categorization, Knowledge Graph sync, and Qdrant Vector indexing.
    """
    mime_type = file.content_type or ""
    mime_type = MIME_ALIASES.get(mime_type, mime_type)

    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Unsupported file type: {mime_type}",
                "detail": f"File '{file.filename}' has type '{mime_type}'",
                "suggestion": "Upload a PDF, DOCX, PNG, or JPG/JPEG file.",
            },
        )

    try:
        content = await file.read()
    except Exception as e:
        logger.error("Failed to read upload payload: %s", str(e))
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Failed to read uploaded file data",
                "detail": str(e),
                "suggestion": "Try uploading the file again.",
            },
        )

    doc_id = str(uuid.uuid4())
    original_filename = file.filename or f"upload_{doc_id}"
    file_ext = Path(original_filename).suffix
    stored_filename = f"{doc_id}{file_ext}"

    # Temporary local save for text extraction/OCR
    temp_local_path = Path(settings.upload_dir) / stored_filename
    try:
        temp_local_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_local_path, "wb") as buffer:
            buffer.write(content)
    except Exception as e:
        logger.error("Failed to write temporary local file: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to process uploaded file locally",
                "detail": str(e),
                "suggestion": "Try uploading again.",
            },
        )

    # Extract text
    try:
        extracted_text = extract_text(
            file_path=str(temp_local_path),
            mime_type=mime_type,
            tesseract_cmd=settings.tesseract_cmd,
        )
    except ExtractionError as e:
        logger.error("Text extraction failed for '%s': %s", original_filename, e.message)
        raise HTTPException(
            status_code=422,
            detail={
                "error": e.message,
                "detail": e.detail,
                "suggestion": e.suggestion,
            },
        )

    # Save to storage backend
    storage_backend = get_storage_backend(settings)
    try:
        storage_key, file_url = storage_backend.save_file(
            file_content=content,
            filename=stored_filename,
            mime_type=mime_type,
        )
    except StorageError as e:
        logger.error("Storage backend save failed for '%s': %s", original_filename, e.message)
        raise HTTPException(
            status_code=500,
            detail={
                "error": e.message,
                "detail": e.detail,
                "suggestion": e.suggestion,
            },
        )

    # LLM structured extraction
    try:
        extraction_result = extract_structured_data(
            llm_client=llm_client,
            text=extracted_text,
            filename=original_filename,
        )
    except LLMExtractionError as e:
        logger.error("LLM extraction failed for '%s': %s", original_filename, e.message)
        raise HTTPException(
            status_code=500,
            detail={
                "error": e.message,
                "detail": e.detail,
                "suggestion": e.suggestion,
            },
        )

    # Save document record
    record = DocumentRecord(
        id=doc_id,
        filename=original_filename,
        original_file_path=storage_key,
        mime_type=mime_type,
        category=extraction_result.category,
        title=extraction_result.title,
        issuer=extraction_result.issuer,
        date=extraction_result.date,
        entities=extraction_result.entities,
        confidence=extraction_result.confidence,
        summary=extraction_result.summary,
        extracted_text=extracted_text,
    )

    try:
        doc_store.add(record)
    except Exception as e:
        logger.error("Failed to store metadata for '%s': %s", original_filename, str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to store document metadata",
                "detail": str(e),
                "suggestion": "Try uploading the file again.",
            },
        )

    # Phase 2: Neo4j Knowledge Graph Sync
    try:
        graph_store = GraphStore(settings)
        graph_store.sync_document(record, llm_client=llm_client)
        graph_store.close()
    except Exception as e:
        logger.warning("Graph sync warning for '%s': %s", original_filename, str(e))

    # Phase 3: Qdrant Cloud Vector Indexing
    try:
        vector_store = VectorStore(settings)
        vector_store.index_document(record, llm_client=llm_client)
    except Exception as e:
        logger.warning("Vector store indexing warning for '%s': %s", original_filename, str(e))

    return UploadResponse(
        document=doc_store.to_response(record),
    )
