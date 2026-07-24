"""
MemoryVerse AI — Pydantic Models / Schemas

All request/response schemas for API endpoints and internal service boundaries.
Per Rules.md: never pass raw dicts across service boundaries — use Pydantic models.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DocumentCategory(str, Enum):
    """
    Document categories per PRD.md Section 4.2.
    """
    PROJECTS = "Projects"
    SKILLS = "Skills"
    CERTIFICATIONS = "Certifications"
    INTERNSHIPS = "Internships"
    ACHIEVEMENTS = "Achievements"
    ACADEMICS = "Academics"


class EntityType(str, Enum):
    """
    Types of entities extracted from documents.
    """
    SKILL = "skill"
    TECHNOLOGY = "technology"
    ORGANIZATION = "organization"
    ROLE = "role"
    DOCUMENT = "document"


# ---------------------------------------------------------------------------
# Extracted data models (internal, from LLM)
# ---------------------------------------------------------------------------

class ExtractedEntity(BaseModel):
    name: str = Field(..., description="Entity display name")
    type: EntityType = Field(..., description="Entity classification")


class LLMExtractionResult(BaseModel):
    category: DocumentCategory
    title: str = Field(..., description="Extracted or inferred document title")
    issuer: Optional[str] = Field(None, description="Issuing organization, if applicable")
    date: Optional[str] = Field(None, description="Associated date in ISO format, if found")
    entities: list[ExtractedEntity] = Field(
        default_factory=list,
        description="Extracted entities",
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence score for the extraction (0.0–1.0)",
    )
    summary: Optional[str] = Field(None, description="Brief summary of the document content")


# ---------------------------------------------------------------------------
# Document storage model
# ---------------------------------------------------------------------------

class DocumentRecord(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_file_path: str
    mime_type: str
    category: DocumentCategory
    title: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    entities: list[ExtractedEntity] = Field(default_factory=list)
    confidence: float
    summary: Optional[str] = None
    extracted_text: str = ""
    uploaded_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
    )


# ---------------------------------------------------------------------------
# Graph & Timeline Models (Phase 2)
# ---------------------------------------------------------------------------

class GraphNode(BaseModel):
    id: str
    name: str
    type: str
    category: Optional[str] = None
    color: str
    val: int = 15
    source_doc_id: Optional[str] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str
    explanation: str


class GraphDataResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    total_edges: int


class TimelineEvent(BaseModel):
    id: str
    date: str
    title: str
    category: DocumentCategory
    summary: Optional[str] = None
    issuer: Optional[str] = None
    document_id: str
    entities: list[ExtractedEntity] = Field(default_factory=list)


class TimelineResponse(BaseModel):
    events: list[TimelineEvent]
    total: int


# ---------------------------------------------------------------------------
# Search & Chat Models (Phase 3)
# ---------------------------------------------------------------------------

class SearchHit(BaseModel):
    document_id: str
    title: str
    category: DocumentCategory
    snippet: str
    score: float = Field(..., description="Cosine similarity match score (0.0 - 1.0)")
    file_url: str
    entities: list[ExtractedEntity] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    hits: list[SearchHit]
    total: int


class Citation(BaseModel):
    document_id: str
    title: str
    category: DocumentCategory
    snippet: str
    score: float


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str
    citations: list[Citation] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(..., description="User question or search query")
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(0.9, ge=0.0, le=1.0)


# ---------------------------------------------------------------------------
# Career Intelligence Models (Phase 4 — Hero Feature)
# ---------------------------------------------------------------------------

class CareerAnalysisRequest(BaseModel):
    """
    Request model for Career Match Job Description analysis.
    """
    job_title: str = Field(..., description="Target job title (e.g. 'Senior AI Engineer')")
    company: Optional[str] = Field(None, description="Company name (optional)")
    job_description: str = Field(..., description="Raw text of the target job description")


class SkillMatch(BaseModel):
    """
    A single requirement match or gap against user records.
    """
    skill: str
    status: str = Field(..., description="'matched' or 'gap'")
    confidence: float = Field(0.8, ge=0.0, le=1.0)
    evidence_doc_id: Optional[str] = None
    evidence_title: Optional[str] = None
    evidence_snippet: Optional[str] = None


class CareerAnalysisResponse(BaseModel):
    """
    Response model for Career Match analysis.
    """
    overall_score: float = Field(..., description="Overall match percentage (0.0 - 100.0)")
    skills_score: float = Field(..., description="Skills match sub-score (0.0 - 100.0)")
    experience_score: float = Field(..., description="Experience match sub-score (0.0 - 100.0)")
    matched_skills: list[SkillMatch] = Field(default_factory=list)
    missing_gaps: list[str] = Field(default_factory=list)
    tailored_resume: str = Field(..., description="Markdown tailored resume grounded in real records")
    cover_letter: str = Field(..., description="Markdown tailored cover letter citing real records")
    citations: list[Citation] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# API response models
# ---------------------------------------------------------------------------

class DocumentResponse(BaseModel):
    id: str
    filename: str
    category: DocumentCategory
    title: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    entities: list[ExtractedEntity] = Field(default_factory=list)
    confidence: float
    summary: Optional[str] = None
    uploaded_at: str


class UploadResponse(BaseModel):
    message: str = "Document uploaded and processed successfully"
    document: DocumentResponse


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Short error description")
    detail: Optional[str] = Field(None, description="Technical detail")
    suggestion: Optional[str] = Field(
        None, description="Actionable suggestion for the user"
    )


class StubResponse(BaseModel):
    message: str
    phase: str = Field(..., description="Phase in which this feature will be built")
