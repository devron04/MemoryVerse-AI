"""
MemoryVerse AI — Career Intelligence API Route (Hero Feature)

POST /career/analyze (and POST /career/match) — matches raw Job Description against user digital identity.
Calculates match percentage, skill breakdowns, gap analysis, and generates grounded Resume & Cover Letter.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import (
    CareerAnalysisRequest,
    CareerAnalysisResponse,
    ErrorResponse,
)
from app.services.llm_client import LLMClient
from app.services.vector_store import VectorStore
from app.services.graph_store import GraphStore
from app.services.document_store import DocumentStore
from app.services.career_engine import CareerEngine, CareerEngineError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["career"])


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Dependency: create LLM client from settings."""
    return LLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


def get_document_store(settings: Settings = Depends(get_settings)) -> DocumentStore:
    """Dependency: create document store from settings."""
    return DocumentStore(data_dir=settings.data_dir)


@router.post(
    "/career/analyze",
    response_model=CareerAnalysisResponse,
    responses={500: {"model": ErrorResponse}},
)
@router.post(
    "/career/match",
    response_model=CareerAnalysisResponse,
    responses={500: {"model": ErrorResponse}},
)
async def analyze_career_match(
    request: CareerAnalysisRequest,
    settings: Settings = Depends(get_settings),
    llm_client: LLMClient = Depends(get_llm_client),
    doc_store: DocumentStore = Depends(get_document_store),
):
    """
    Perform Career Match analysis comparing target Job Description against verified digital identity records.

    Returns match score percentage, skill evidence citations, gap analysis,
    and grounded tailored Resume & Cover Letter.
    """
    if not request.job_description.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Empty Job Description",
                "detail": "Please paste a valid Job Description text.",
                "suggestion": "Paste the text of the job description you wish to apply for.",
            },
        )

    try:
        vector_store = VectorStore(settings)
        graph_store = GraphStore(settings)
        engine = CareerEngine(
            vector_store=vector_store,
            graph_store=graph_store,
            doc_store=doc_store,
            llm_client=llm_client,
        )
        response = engine.analyze_job_description(request)
        graph_store.close()
        return response
    except Exception as e:
        logger.error("Career match analysis error: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to analyze career match",
                "detail": str(e),
                "suggestion": "Ensure target Job Description is valid and try again.",
            },
        )
