# app/services/__init__.py
"""
External service integrations
"""

from .ai_service import AIService
from .weather_service import WeatherService

__all__ = [
    "AIService",
    "WeatherService"
]

async def initialize(self):
    """Initialize queue service"""
    print("🎯 Queue service ready")
    return True