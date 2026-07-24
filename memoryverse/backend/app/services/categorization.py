"""
MemoryVerse AI — Category Validation Service

Validates and normalizes document categories assigned by the LLM.
In Phase 1, the LLM assigns the category directly; this module
ensures the assignment matches the DocumentCategory enum.
"""

import logging

from app.models.schemas import DocumentCategory

logger = logging.getLogger(__name__)


def validate_category(category_value: str) -> DocumentCategory:
    """
    Validate and normalize a category string to a DocumentCategory enum value.

    Handles case-insensitive matching and common variations.

    Args:
        category_value: The category string to validate.

    Returns:
        A valid DocumentCategory enum value.

    Raises:
        ValueError: If the category cannot be matched to any valid value.
    """
    # Direct match
    try:
        return DocumentCategory(category_value)
    except ValueError:
        pass

    # Case-insensitive match
    for cat in DocumentCategory:
        if cat.value.lower() == category_value.lower():
            logger.info(
                "Normalized category '%s' to '%s'", category_value, cat.value
            )
            return cat

    # Keyword-based fallback matching
    keyword_map = {
        DocumentCategory.PROJECTS: ["project", "report", "documentation"],
        DocumentCategory.SKILLS: ["skill", "training", "course", "learning"],
        DocumentCategory.CERTIFICATIONS: ["certificate", "certification", "diploma", "certified"],
        DocumentCategory.INTERNSHIPS: ["internship", "intern", "placement", "apprentice"],
        DocumentCategory.ACHIEVEMENTS: ["achievement", "award", "honor", "prize", "competition", "winner"],
        DocumentCategory.ACADEMICS: ["academic", "transcript", "marksheet", "grade", "semester", "degree"],
    }

    lower_val = category_value.lower()
    for cat, keywords in keyword_map.items():
        if any(kw in lower_val for kw in keywords):
            logger.info(
                "Matched category '%s' to '%s' via keyword", category_value, cat.value
            )
            return cat

    logger.warning("Could not match category '%s' to any known value", category_value)
    raise ValueError(
        f"Unknown category '{category_value}'. "
        f"Valid categories: {[c.value for c in DocumentCategory]}"
    )


def get_category_display_info(category: DocumentCategory) -> dict:
    """
    Get display metadata for a category (used by frontend).

    Args:
        category: A valid DocumentCategory.

    Returns:
        Dict with 'label', 'color_token' keys for UI rendering.
    """
    display_map = {
        DocumentCategory.PROJECTS: {
            "label": "Project",
            "color_token": "accent-sage",
        },
        DocumentCategory.SKILLS: {
            "label": "Skill",
            "color_token": "accent-sage",
        },
        DocumentCategory.CERTIFICATIONS: {
            "label": "Certification",
            "color_token": "accent-gold",
        },
        DocumentCategory.INTERNSHIPS: {
            "label": "Internship",
            "color_token": "accent-sage",
        },
        DocumentCategory.ACHIEVEMENTS: {
            "label": "Achievement",
            "color_token": "accent-gold",
        },
        DocumentCategory.ACADEMICS: {
            "label": "Academics",
            "color_token": "accent-sage",
        },
    }
    return display_map.get(category, {"label": category.value, "color_token": "accent-sage"})
