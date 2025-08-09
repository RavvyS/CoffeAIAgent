# app/models/__init__.py
"""
Data models for the Coffee Shop AI Agent
"""

from .conversation import (
    MessageRole,
    MessageType,
    ConversationMessage,
    OrderItem,
    CurrentOrder,
    CustomerPreferences,
    MoodIndicators,
    WeatherContext,
    ContextFlags,
    ConversationSession,
    AIResponse
)

from .customer import (
    CustomerStatus,
    OrderStatus,
    PaymentMethod,
    CustomerProfile,
    HistoricalOrder,
    CustomerInsights,
    LoyaltyTransaction,
    CustomerFeedback,
    CustomerSegment
)

__all__ = [
    # Conversation models
    "MessageRole",
    "MessageType", 
    "ConversationMessage",
    "OrderItem",
    "CurrentOrder",
    "CustomerPreferences",
    "MoodIndicators",
    "WeatherContext",
    "ContextFlags",
    "ConversationSession",
    "AIResponse",
    # Customer models
    "CustomerStatus",
    "OrderStatus",
    "PaymentMethod",
    "CustomerProfile",
    "HistoricalOrder",
    "CustomerInsights",
    "LoyaltyTransaction",
    "CustomerFeedback",
    "CustomerSegment"
]