"""
MemoryVerse AI — Chat RAG Search API Route

POST /chat — evidence-grounded Conversational RAG interface.
Queries Qdrant Cloud for vector chunks, synthesizes evidence with Gemini 3.6 Flash,
and returns cited answers linked directly to uploaded original files.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    ErrorResponse,
)
from app.services.llm_client import LLMClient
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """Dependency: create LLM client from settings."""
    return LLMClient(api_key=settings.gemini_api_key, model=settings.gemini_model)


@router.post(
    "/chat",
    response_model=ChatResponse,
    responses={500: {"model": ErrorResponse}},
)
async def chat_rag_search(
    request: ChatRequest,
    settings: Settings = Depends(get_settings),
    llm_client: LLMClient = Depends(get_llm_client),
):
    """
    Perform evidence-grounded RAG search across uploaded digital identity records.

    Retrieves vector chunks from Qdrant Cloud and synthesizes an answer with citations.
    """
    query = request.message.strip()
    if not query:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Empty message query",
                "detail": "Please provide a valid question or search query.",
                "suggestion": "Ask a question about your certificates, skills, or projects.",
            },
        )

    # 1. Retrieve vector chunks from Qdrant Cloud
    try:
        vector_store = VectorStore(settings)
        hits = vector_store.search(query=query, llm_client=llm_client, limit=4)
    except Exception as e:
        logger.warning("Vector retrieval failed during chat RAG: %s", str(e))
        hits = []

    # 2. Build Citations
    citations = [
        Citation(
            document_id=hit.document_id,
            title=hit.title,
            category=hit.category,
            snippet=hit.snippet,
            score=hit.score,
        )
        for hit in hits
    ]

    # 3. Handle case where no documents exist in vector store
    if not hits:
        fallback_prompt = (
            f"User Question: '{query}'\n\n"
            "Note: The user's digital identity repository is currently empty or has no matching records.\n"
            "Respond politely explaining that no matching documents were found in their MemoryVerse repository, "
            "and suggest uploading relevant certificates, project reports, or resumes to enable identity-grounded answers."
        )
        try:
            raw_res = llm_client.generate_json(
                f"{fallback_prompt}\nReturn JSON format: {{\"answer\": \"...\"}}"
            )
            answer = raw_res.get("answer", "No matching documents found in your digital identity repository. Upload documents to get evidence-grounded answers.")
        except Exception:
            answer = "No matching documents found in your digital identity repository. Please upload certificates or project reports in the Upload section to get started!"

        return ChatResponse(
            answer=answer,
            citations=[],
            confidence=0.5,
        )

    # 4. Synthesize Grounded Answer with Gemini 3.6 Flash
    context_blocks = "\n---\n".join([
        f"[Doc ID: {hit.document_id}] Title: '{hit.title}' | Category: {hit.category.value}\nSnippet: {hit.snippet}"
        for hit in hits
    ])

    rag_prompt = (
        f"You are MemoryVerse AI — a Living Digital Identity Assistant.\n"
        f"Answer the user's question using ONLY the provided verified document evidence below.\n"
        f"Be helpful, professional, and directly state what evidence is found in their records.\n\n"
        f"Verified Document Evidence:\n{context_blocks}\n\n"
        f"User Question: '{query}'\n\n"
        f"Return JSON format: {{\"answer\": \"...\", \"confidence\": 0.95}}"
    )

    try:
        rag_res = llm_client.generate_json(rag_prompt)
        answer = rag_res.get("answer", "Based on your verified digital identity records, here are the matching details.")
        confidence = float(rag_res.get("confidence", 0.9))
    except Exception as e:
        logger.error("LLM RAG synthesis error: %s", str(e))
        answer = f"Based on your uploaded document '{hits[0].title}', here is the relevant record: {hits[0].snippet[:200]}..."
        confidence = 0.85

    return ChatResponse(
        answer=answer,
        citations=citations,
        confidence=confidence,
    )
