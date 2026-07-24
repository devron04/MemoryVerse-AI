"""
MemoryVerse AI — Qdrant Cloud Vector Store Integration

Handles document text chunking, embedding generation with Gemini API,
and vector indexing/search in Qdrant Cloud.

Per Architecture.md §5: Qdrant is accessed strictly through this vector_store.py wrapper.
Per Rules.md §3: all operations wrapped in explicit try/except blocks with loud error handling.
"""

import logging
import uuid
from typing import Optional
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import Settings
from app.models.schemas import DocumentRecord, SearchHit, DocumentCategory, ExtractedEntity
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

COLLECTION_NAME = "memoryverse_documents"
EMBEDDING_MODEL = "models/gemini-embedding-001"
VECTOR_DIM = 3072  # Dimension for gemini-embedding-001


class VectorStoreError(Exception):
    """Custom exception for Qdrant Vector Store operations."""

    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)


class VectorStore:
    """
    Qdrant Cloud client wrapper for MemoryVerse Vector DB.
    """

    def __init__(self, settings: Settings):
        self.url = settings.qdrant_url
        self.api_key = settings.qdrant_api_key
        self._client: Optional[QdrantClient] = None

    def _get_client(self) -> QdrantClient:
        """Lazy initialization of Qdrant client."""
        if self._client is None:
            if not self.url:
                raise VectorStoreError(
                    message="Qdrant connection URL missing in settings",
                    detail="QDRANT_URL is empty.",
                )
            try:
                self._client = QdrantClient(
                    url=self.url,
                    api_key=self.api_key or None,
                    check_compatibility=False,
                )
                logger.info("Connected to Qdrant Cloud at %s", self.url)
            except Exception as e:
                logger.error("Failed to connect to Qdrant Cloud: %s", str(e))
                raise VectorStoreError(
                    message="Failed to connect to Qdrant Vector Database",
                    detail=str(e),
                )
        return self._client

    def ensure_collection(self) -> None:
        """Ensure Qdrant collection exists."""
        client = self._get_client()
        try:
            collections = [c.name for c in client.get_collections().collections]
            if COLLECTION_NAME not in collections:
                client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
                )
                logger.info("Created collection '%s' in Qdrant Cloud", COLLECTION_NAME)
        except Exception as e:
            logger.error("Failed to check/create Qdrant collection: %s", str(e))
            raise VectorStoreError(
                message="Failed to initialize Qdrant vector collection",
                detail=str(e),
            )

    def _chunk_text(self, text: str, chunk_size: int = 500) -> list[str]:
        """Split text into semantic paragraph chunks."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        chunks = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) <= chunk_size:
                current += ("\n\n" if current else "") + p
            else:
                if current:
                    chunks.append(current)
                current = p
        if current:
            chunks.append(current)
        return chunks if chunks else [text]

    def index_document(self, record: DocumentRecord, llm_client: LLMClient) -> int:
        """
        Chunk document text, generate embeddings using Gemini API, and index points in Qdrant Cloud.

        Args:
            record: DocumentRecord containing extracted metadata and text.
            llm_client: LLMClient instance to call embedding API.

        Returns:
            Number of indexed vector chunks.
        """
        self.ensure_collection()
        client = self._get_client()

        text_to_index = record.extracted_text or record.summary or record.title
        chunks = self._chunk_text(text_to_index)

        points = []
        for i, chunk in enumerate(chunks):
            try:
                # Generate 3072-dim embedding using Gemini API
                embed_res = llm_client.client.models.embed_content(
                    model=EMBEDDING_MODEL,
                    contents=chunk,
                )
                vector = embed_res.embeddings[0].values

                point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{record.id}_{i}"))
                payload = {
                    "document_id": record.id,
                    "title": record.title,
                    "category": record.category.value,
                    "filename": record.filename,
                    "issuer": record.issuer or "",
                    "date": record.date or "",
                    "snippet": chunk,
                    "confidence": record.confidence,
                    "entities": [e.model_dump() for e in record.entities],
                }

                points.append(PointStruct(id=point_id, vector=vector, payload=payload))
            except Exception as e:
                logger.warning("Failed to embed chunk %d for doc '%s': %s", i, record.title, str(e))

        if points:
            try:
                client.upsert(collection_name=COLLECTION_NAME, points=points)
                logger.info("Successfully indexed %d chunks for document '%s' in Qdrant Cloud", len(points), record.title)
            except Exception as e:
                logger.error("Failed to upsert points to Qdrant Cloud: %s", str(e))
                raise VectorStoreError(
                    message="Failed to store vector embeddings in Qdrant Cloud",
                    detail=str(e),
                )

        return len(points)

    def search(
        self,
        query: str,
        llm_client: LLMClient,
        category: Optional[str] = None,
        limit: int = 5,
    ) -> list[SearchHit]:
        """
        Perform vector similarity search against Qdrant Cloud collection.

        Args:
            query: Search query text.
            llm_client: LLMClient for embedding the search query.
            category: Optional document category filter.
            limit: Maximum number of search hits to return.

        Returns:
            List of ranked SearchHit objects.
        """
        self.ensure_collection()
        client = self._get_client()

        # Embed query text
        try:
            embed_res = llm_client.client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=query,
            )
            query_vector = embed_res.embeddings[0].values
        except Exception as e:
            logger.error("Failed to generate query embedding: %s", str(e))
            raise VectorStoreError(
                message="Failed to generate embedding for search query",
                detail=str(e),
            )

        # Optional Qdrant filter
        search_filter = None
        if category and category != "All":
            search_filter = Filter(
                must=[FieldCondition(key="category", match=MatchValue(value=category))]
            )

        try:
            results = client.query_points(
                collection_name=COLLECTION_NAME,
                query=query_vector,
                query_filter=search_filter,
                limit=limit,
            )

            hits = []
            for point in results.points:
                payload = point.payload or {}
                entities_raw = payload.get("entities", [])
                entities = [ExtractedEntity(**e) for e in entities_raw] if entities_raw else []

                doc_id = payload.get("document_id", "")
                hits.append(
                    SearchHit(
                        document_id=doc_id,
                        title=payload.get("title", "Untitled Document"),
                        category=DocumentCategory(payload.get("category", "Projects")),
                        snippet=payload.get("snippet", ""),
                        score=round(float(point.score), 4),
                        file_url=f"http://localhost:8000/api/documents/{doc_id}/file",
                        entities=entities,
                    )
                )

            return hits
        except Exception as e:
            logger.error("Failed to perform vector search in Qdrant Cloud: %s", str(e))
            raise VectorStoreError(
                message="Failed to perform vector search in Qdrant Cloud",
                detail=str(e),
            )
