"""
MemoryVerse AI — LLM Structured Extraction Service

Sends extracted text to Gemini 2.5 Flash for structured extraction:
category, title, issuer, date, entities, and confidence score.

Returns validated Pydantic models — never raw dicts (per Rules.md §2).
"""

import logging

from app.models.schemas import (
    DocumentCategory,
    EntityType,
    ExtractedEntity,
    LLMExtractionResult,
)
from app.services.llm_client import LLMClient, LLMError

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_PROMPT = """You are a document analysis assistant for MemoryVerse AI.
Your job is to extract structured metadata from document text.

You must classify each document into exactly ONE of these categories:
- Projects: Project reports, project documentation, project proposals
- Skills: Skill assessments, skill certificates, training completion
- Certifications: Certificates, diplomas, professional certifications
- Internships: Internship letters, internship completion certificates, offer letters
- Achievements: Awards, competition results, honors, recognitions
- Academics: Transcripts, marksheets, academic records, coursework

Extract the following fields:
- category: One of the categories above (exactly as spelled)
- title: The document's title or a concise descriptive title
- issuer: The organization/institution that issued this document (null if not applicable)
- date: The most relevant date in ISO format YYYY-MM-DD (null if not found)
- entities: A list of entities found, each with a "name" and "type" (skill, technology, organization, or role)
- confidence: Your confidence in the extraction accuracy (0.0 to 1.0)
- summary: A one-sentence summary of what this document is about

Be precise and extract only what's actually present in the text.
Do NOT fabricate or infer information that isn't in the document."""

EXTRACTION_PROMPT_TEMPLATE = """Analyze the following document text and extract structured metadata.

Respond with a JSON object in this exact format:
{{
    "category": "Projects" | "Skills" | "Certifications" | "Internships" | "Achievements" | "Academics",
    "title": "string",
    "issuer": "string or null",
    "date": "YYYY-MM-DD or null",
    "entities": [
        {{"name": "string", "type": "skill" | "technology" | "organization" | "role"}}
    ],
    "confidence": 0.0 to 1.0,
    "summary": "string"
}}

DOCUMENT TEXT:
---
{text}
---"""


def extract_structured_data(
    llm_client: LLMClient,
    text: str,
    filename: str = "",
) -> LLMExtractionResult:
    """
    Send extracted document text to the LLM for structured extraction.

    Args:
        llm_client: Initialized LLM client wrapper.
        text: Raw text extracted from the document.
        filename: Original filename (for logging context).

    Returns:
        Validated LLMExtractionResult Pydantic model.

    Raises:
        LLMExtractionError: If extraction fails or the LLM returns invalid data.
    """
    # Truncate very long texts to avoid token limits
    max_chars = 15000
    truncated = text[:max_chars] if len(text) > max_chars else text
    if len(text) > max_chars:
        logger.info(
            "Text for '%s' truncated from %d to %d chars for LLM extraction",
            filename, len(text), max_chars,
        )

    prompt = EXTRACTION_PROMPT_TEMPLATE.format(text=truncated)

    try:
        raw_result = llm_client.generate_json(
            prompt=prompt,
            system_instruction=EXTRACTION_SYSTEM_PROMPT,
            temperature=0.1,
        )
    except LLMError as e:
        logger.error("LLM extraction failed for '%s': %s", filename, e.message)
        raise LLMExtractionError(
            message=f"AI extraction failed for '{filename}'",
            detail=e.detail,
            suggestion="The AI model couldn't process this document. Try uploading it again, "
                       "or check that the document contains readable text.",
        )

    # Validate and parse the raw dict into a Pydantic model
    try:
        result = _parse_extraction_result(raw_result)
        logger.info(
            "Successfully extracted metadata for '%s': category=%s, confidence=%.2f",
            filename, result.category.value, result.confidence,
        )
        return result
    except (KeyError, ValueError, TypeError) as e:
        logger.error(
            "Failed to parse LLM extraction result for '%s': %s. Raw: %s",
            filename, str(e), raw_result,
        )
        raise LLMExtractionError(
            message=f"AI returned unexpected data format for '{filename}'",
            detail=str(e),
            suggestion="Try uploading the document again. If this persists, "
                       "the document format may not be supported.",
        )


def _parse_extraction_result(raw: dict) -> LLMExtractionResult:
    """
    Parse and validate raw LLM output into a LLMExtractionResult.

    Args:
        raw: Raw dict from LLM JSON response.

    Returns:
        Validated LLMExtractionResult.

    Raises:
        ValueError: If required fields are missing or have invalid values.
    """
    # Normalize category string to enum
    category_str = raw.get("category", "")
    try:
        category = DocumentCategory(category_str)
    except ValueError:
        # Try case-insensitive match
        category_lower = category_str.lower()
        matched = None
        for cat in DocumentCategory:
            if cat.value.lower() == category_lower:
                matched = cat
                break
        if matched is None:
            raise ValueError(
                f"Invalid category '{category_str}'. "
                f"Must be one of: {[c.value for c in DocumentCategory]}"
            )
        category = matched

    # Parse entities
    entities = []
    for entity_raw in raw.get("entities", []):
        try:
            entity_type = EntityType(entity_raw.get("type", "skill"))
        except ValueError:
            entity_type = EntityType.SKILL  # safe fallback for type
        entities.append(
            ExtractedEntity(
                name=entity_raw.get("name", "Unknown"),
                type=entity_type,
            )
        )

    # Clamp confidence to valid range
    confidence = float(raw.get("confidence", 0.5))
    confidence = max(0.0, min(1.0, confidence))

    return LLMExtractionResult(
        category=category,
        title=raw.get("title", "Untitled Document"),
        issuer=raw.get("issuer"),
        date=raw.get("date"),
        entities=entities,
        confidence=confidence,
        summary=raw.get("summary"),
    )


class LLMExtractionError(Exception):
    """
    Custom exception for LLM extraction failures.
    Carries user-facing message, detail, and suggestion per Rules.md §3.
    """

    def __init__(self, message: str, detail: str = "", suggestion: str = ""):
        self.message = message
        self.detail = detail
        self.suggestion = suggestion
        super().__init__(message)
