"""
Gemini API client for generating personalized recommendations.

Handles API errors, automatic key rotation, and retry logic.
"""

import asyncio
import json
from typing import Any

import structlog
from backend.src.config import settings
from backend.src.gemini.key_pool import AllKeysExhaustedException, GeminiAPIKeyPool
from backend.src.gemini.prompts import RECOMMENDATION_PROMPT
from google import genai
from google.genai import errors as genai_errors

logger = structlog.get_logger(__name__)


class GeminiRecommendationService:
    """
    Service for generating personalized recommendations via Gemini API.

    Features:
    - Automatic key rotation on rate limits (429)
    - Invalid key handling (401)
    - Network error retry with exponential backoff
    - Robust JSON parsing with fallback

    Error Handling:
    - 429 (Rate Limit) → automatic key rotation
    - 401 (Invalid Key) → skip key, move to next
    - Network errors → retry with exponential delay
    """

    def __init__(self, key_pool: GeminiAPIKeyPool):
        """
        Initialize recommendation service.

        Args:
            key_pool: GeminiAPIKeyPool instance for managing API keys
        """
        self.key_pool = key_pool

    async def generate_recommendations(self, user_stats: dict[str, Any]) -> dict[str, Any]:
        """
        Generate personalized recommendations based on user statistics.

        Args:
            user_stats: User order statistics from OrderStatsService

        Returns:
            {
                "summary": str | None,
                "tips": list[str]
            }

        Raises:
            AllKeysExhaustedException: If all API keys are exhausted or invalid
        """
        max_retries = len(self.key_pool.keys)

        for attempt in range(max_retries):
            try:
                # Get API key and create client
                api_key = await self.key_pool.get_api_key()
                client = genai.Client(api_key=api_key)

                # Format prompt with user data
                prompt = self._format_prompt(user_stats)

                logger.info(
                    "Generating recommendations",
                    attempt=attempt + 1,
                    orders_count=user_stats.get("orders_count", 0),
                )

                # Call Gemini API with timeout
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=settings.GEMINI_MODEL, contents=prompt
                    ),
                    timeout=30.0
                )

                # Parse and return response
                result = self._parse_response(response.text)

                logger.info("Recommendations generated successfully")

                return result

            except genai_errors.ClientError as e:
                # ClientError is the base class for API errors
                error_code = getattr(e, "code", None)

                if error_code == 429:  # Rate limit exceeded
                    logger.warning(
                        "Rate limit exceeded, rotating key",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                    )
                    await self.key_pool.rotate_key()
                    continue

                elif error_code == 401:  # Invalid API key
                    logger.error(
                        "Invalid API key, rotating",
                        attempt=attempt + 1,
                    )
                    current_index = await self.key_pool._get_current_key_index()
                    await self.key_pool.mark_key_invalid(current_index)
                    await self.key_pool.rotate_key()
                    continue

                else:
                    # Other API errors - don't retry
                    logger.error(
                        "Gemini API error",
                        error_code=error_code,
                        error_message=str(e),
                    )
                    raise

            except Exception as e:
                logger.error(
                    "Unexpected error during recommendation generation",
                    error=str(e),
                    attempt=attempt + 1,
                )
                # For network errors, try next key
                if attempt < max_retries - 1:
                    await self.key_pool.rotate_key()
                    continue
                raise

        # All retries exhausted
        logger.error("All API keys exhausted")
        raise AllKeysExhaustedException(
            "Failed to generate recommendations: all API keys exhausted"
        )

    def _format_prompt(self, user_stats: dict[str, Any]) -> str:
        """
        Format the recommendation prompt with user statistics.

        Args:
            user_stats: User statistics dictionary

        Returns:
            Formatted prompt string
        """
        # Format categories distribution
        categories = user_stats.get("categories", {})
        categories_str = ", ".join(
            [f"{cat}: {data['count']} ({data['percent']}%)" for cat, data in categories.items()]
        )

        # Format favorite dishes
        favorite_dishes = user_stats.get("favorite_dishes", [])
        favorite_str = ", ".join([f"{dish['name']} ({dish['count']}x)" for dish in favorite_dishes])

        # Format prompt
        prompt = RECOMMENDATION_PROMPT.format(
            orders_count=user_stats.get("orders_count", 0),
            categories=categories_str if categories_str else "нет данных",
            unique_dishes=user_stats.get("unique_dishes", 0),
            total_available=user_stats.get("total_dishes_available", 0),
            favorite_dishes=favorite_str if favorite_str else "нет данных",
        )

        return prompt

    def _parse_response(self, text: str) -> dict[str, Any]:
        """
        Parse JSON response from Gemini API.

        Handles malformed JSON and extracts JSON from markdown code blocks.

        Args:
            text: Raw response text from Gemini

        Returns:
            Parsed recommendations dict with fallback to empty structure
        """
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in text:
                json_start = text.find("```json") + 7
                json_end = text.find("```", json_start)
                json_text = text[json_start:json_end].strip()
            elif "```" in text:
                json_start = text.find("```") + 3
                json_end = text.find("```", json_start)
                json_text = text[json_start:json_end].strip()
            else:
                json_text = text.strip()

            # Parse JSON
            parsed = json.loads(json_text)

            # Validate structure
            if not isinstance(parsed, dict):
                logger.warning("Gemini response is not a dict, returning empty")
                return {"summary": None, "tips": []}

            summary = parsed.get("summary")
            tips = parsed.get("tips", [])

            # Ensure tips is a list
            if not isinstance(tips, list):
                tips = []

            return {"summary": summary, "tips": tips}

        except json.JSONDecodeError as e:
            logger.warning(
                "Failed to parse Gemini response as JSON",
                error=str(e),
                text_preview=text[:200],
            )
            return {"summary": None, "tips": []}

        except Exception as e:
            logger.error(
                "Unexpected error parsing Gemini response",
                error=str(e),
            )
            return {"summary": None, "tips": []}


# Singleton instance
_recommendation_service: GeminiRecommendationService | None = None


def get_recommendation_service() -> GeminiRecommendationService:
    """
    Get singleton instance of GeminiRecommendationService.

    Initializes with the global key pool on first call.

    Returns:
        GeminiRecommendationService instance
    """
    global _recommendation_service

    if _recommendation_service is None:
        from backend.src.gemini.key_pool import get_key_pool

        _recommendation_service = GeminiRecommendationService(get_key_pool())

    return _recommendation_service
