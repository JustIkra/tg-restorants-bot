"""
Gemini API integration module.

Provides API key pool management and client wrapper for Gemini API.
"""

from .client import (
    GeminiRecommendationService,
    get_recommendation_service,
)
from .key_pool import (
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
