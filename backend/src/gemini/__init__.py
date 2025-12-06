"""
Gemini API integration module.

Provides API key pool management and client wrapper for Gemini API.
"""

from backend.src.gemini.client import (
    GeminiRecommendationService,
    get_recommendation_service,
)
from backend.src.gemini.key_pool import (
    AllKeysExhaustedException,
    GeminiAPIKeyPool,
    get_key_pool,
)

__all__ = [
    "GeminiAPIKeyPool",
    "get_key_pool",
    "AllKeysExhaustedException",
    "GeminiRecommendationService",
    "get_recommendation_service",
]
