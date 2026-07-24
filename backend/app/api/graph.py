"""
MemoryVerse AI — Graph API Route

GET /graph — retrieves the Knowledge Graph (nodes, edges, and relationship explanations).
Queries Neo4j AuraDB and returns nodes & edges formatted for frontend rendering.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException

from app.config import Settings, get_settings
from app.models.schemas import GraphDataResponse, ErrorResponse
from app.services.graph_store import GraphStore, GraphStoreError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["graph"])


@router.get(
    "/graph",
    response_model=GraphDataResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_graph(
    settings: Settings = Depends(get_settings),
):
    """
    Get the full constellation Knowledge Graph.

    Returns:
        GraphDataResponse with nodes, luminous edges, and relationship explanations.
    """
    graph_store = GraphStore(settings)
    try:
        data = graph_store.get_graph_data()
        graph_store.close()
        return data
    except GraphStoreError as e:
        graph_store.close()
        logger.error("Failed to fetch graph data: %s", e.message)
        raise HTTPException(
            status_code=500,
            detail={
                "error": e.message,
                "detail": e.detail,
                "suggestion": "Check Neo4j database connectivity and credentials.",
            },
        )
