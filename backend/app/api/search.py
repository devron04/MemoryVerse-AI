"""
MemoryVerse AI — Search API Route

GET /search and POST /search — natural language vector similarity search against Qdrant Cloud.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import Settings, get_settings
from app.models.schemas import SearchResponse, ErrorResponse
from app.services.llm_client import LLMClient
from app.services.vector_store import VectorStore, VectorStoreError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["search"])


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Dependency: create LLM client from settings."""
    return LLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


@router.get(
    "/search",
    response_model=SearchResponse,
    responses={500: {"model": ErrorResponse}},
)
async def search_documents_get(
    q: str = Query(..., description="Natural language search query"),
    category: Optional[str] = Query(None, description="Optional document category filter"),
    limit: int = Query(5, ge=1, le=20),
    settings: Settings = Depends(get_settings),
    llm_client: LLMClient = Depends(get_llm_client),
):
    """
    Semantic vector search across uploaded documents via Qdrant Cloud.

    Returns ranked document hits with match scores and snippets.
    """
    if not q.strip():
        return SearchResponse(query=q, hits=[], total=0)

    try:
        vector_store = VectorStore(settings)
        hits = vector_store.search(
            query=q,
            llm_client=llm_client,
            category=category,
            limit=limit,
        )
        return SearchResponse(
            query=q,
            hits=hits,
            total=len(hits),
        )
    except VectorStoreError as e:
        logger.error("Search failed for query '%s': %s", q, e.message)
        raise HTTPException(
            status_code=500,
            detail={
                "error": e.message,
                "detail": e.detail,
                "suggestion": "Check Qdrant Cloud cluster settings and credentials.",
            },
        )
