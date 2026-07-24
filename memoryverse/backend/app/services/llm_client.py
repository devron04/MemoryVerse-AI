"""
MemoryVerse AI — LLM Client Wrapper

Single point of contact for all Gemini API calls.
Per Architecture.md §5: one place to change models, add retries, or swap providers.
Per Rules.md §3: retries once on malformed JSON before surfacing an error.

Uses the official google-genai SDK.
"""

import json
import logging
from typing import Optional

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Wrapper around the Google Gemini API.

    Centralizes all LLM calls so model changes, retries, and error
    handling are managed in one place.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        """
        Initialize the Gemini client.

        Args:
            api_key: Google Gemini API key.
            model: Model identifier (default: gemini-2.5-flash).
        """
        self.client = genai.Client(api_key=api_key)
        self.model = model
        logger.info("LLM client initialized with model: %s", model)

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
    ) -> dict:
        """
        Send a prompt to Gemini and parse the response as JSON.

        Per Rules.md §3: if the response is malformed JSON, retries once
        with a stricter prompt before raising an error. Never fabricates
        a fallback response.

        Args:
            prompt: The user/task prompt to send.
            system_instruction: Optional system instruction for the model.
            temperature: Sampling temperature (lower = more deterministic).

        Returns:
            Parsed JSON response as a Python dict.

        Raises:
            LLMError: If the API call fails or JSON parsing fails after retry.
        """
        config = types.GenerateContentConfig(
            temperature=temperature,
            response_mime_type="application/json",
        )
        if system_instruction:
            config.system_instruction = system_instruction

        # First attempt
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            return self._parse_json_response(response.text)
        except json.JSONDecodeError:
            logger.warning(
                "LLM returned malformed JSON on first attempt — retrying with stricter prompt"
            )
        except LLMError:
            raise
        except Exception as e:
            logger.error("LLM API call failed: %s", str(e))
            raise LLMError(
                message="Failed to get a response from the AI model",
                detail=str(e),
            )

        # Retry with stricter prompt (per Rules.md §3)
        strict_prompt = (
            f"{prompt}\n\n"
            "CRITICAL: You MUST respond with valid JSON only. "
            "No markdown, no code fences, no explanatory text. "
            "Just the raw JSON object."
        )
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=strict_prompt,
                config=config,
            )
            return self._parse_json_response(response.text)
        except json.JSONDecodeError as e:
            logger.error("LLM returned malformed JSON on retry: %s", str(e))
            raise LLMError(
                message="AI model returned an invalid response format",
                detail=f"Expected valid JSON but got malformed output after retry: {str(e)}",
            )
        except LLMError:
            raise
        except Exception as e:
            logger.error("LLM API retry call failed: %s", str(e))
            raise LLMError(
                message="Failed to get a response from the AI model on retry",
                detail=str(e),
            )

    def _parse_json_response(self, text: str) -> dict:
        """
        Parse LLM response text as JSON, stripping any markdown fences.

        Args:
            text: Raw response text from the LLM.

        Returns:
            Parsed JSON as a dict.

        Raises:
            json.JSONDecodeError: If the text is not valid JSON.
        """
        cleaned = text.strip()
        # Strip markdown code fences if present
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first line (```json or ```) and last line (```)
            lines = [l for l in lines if not l.strip().startswith("```")]
            cleaned = "\n".join(lines).strip()

        return json.loads(cleaned)


class LLMError(Exception):
    """
    Custom exception for LLM call failures.
    Carries a user-facing message and technical detail.
    """

    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)
