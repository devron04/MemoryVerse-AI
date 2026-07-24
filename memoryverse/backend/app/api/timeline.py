"""
MemoryVerse AI — Timeline API Route

GET /timeline — retrieves the chronological growth timeline of user achievements and documents.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import TimelineResponse, ErrorResponse
from app.services.document_store import DocumentStore
from app.services.graph_store import GraphStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["timeline"])


def get_document_store(settings: Settings = Depends(get_settings)) -> DocumentStore:
    """Dependency: create document store from settings."""
    return DocumentStore(data_dir=settings.data_dir)


@router.get(
    "/timeline",
    response_model=TimelineResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_timeline(
    settings: Settings = Depends(get_settings),
    doc_store: DocumentStore = Depends(get_document_store),
):
    """
    Get the chronological growth timeline.

    Returns:
        TimelineResponse with sorted timeline events.
    """
    try:
        doc_records = doc_store.get_all()
        graph_store = GraphStore(settings)
        timeline_data = graph_store.get_timeline(doc_records)
        graph_store.close()
        return timeline_data
    except Exception as e:
        logger.error("Failed to generate timeline events: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to retrieve growth timeline data",
                "detail": str(e),
                "suggestion": "Check backend logs or try again.",
            },
        )
