from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageType(str, Enum):
    """Types of messages"""
    TEXT = "text"
    ORDER = "order"
    RECOMMENDATION = "recommendation"
    SYSTEM_NOTIFICATION = "system_notification"

class ConversationMessage(BaseModel):
    """Individual message in conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: MessageType = MessageType.TEXT
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class OrderItem(BaseModel):
    """Item in customer order"""
    id: str
    name: str
    size: str = "medium"
    price: float
    customizations: List[str] = Field(default_factory=list)
    added_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class CurrentOrder(BaseModel):
    """Current order state"""
    items: List[OrderItem] = Field(default_factory=list)
    total: float = 0.0
    tax: float = 0.0
    final_total: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def calculate_totals(self, tax_rate: float = 0.08):
        """Calculate order totals"""
        self.total = sum(item.price for item in self.items)
        self.tax = round(self.total * tax_rate, 2)
        self.final_total = round(self.total + self.tax, 2)
        self.updated_at = datetime.utcnow()
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class CustomerPreferences(BaseModel):
    """Customer dietary and preference information"""
    dietary_restrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    favorite_drinks: List[str] = Field(default_factory=list)
    preferred_temperature: Optional[str] = None  # hot, iced, either
    preferred_size: Optional[str] = None  # small, medium, large
    milk_preference: Optional[str] = None  # whole, oat, almond, soy, etc.
    sweetness_level: Optional[str] = None  # none, low, medium, high
    caffeine_preference: Optional[str] = None  # regular, decaf, half-caff
    
    # Behavioral preferences
    prefers_recommendations: bool = True
    likes_seasonal_items: bool = True
    price_conscious: bool = False
    health_conscious: bool = False

class MoodIndicators(BaseModel):
    """Customer mood and context indicators"""
    mood_tags: List[str] = Field(default_factory=list)  # stressed, happy, tired, etc.
    energy_level: Optional[str] = None  # low, medium, high
    time_pressure: Optional[str] = None  # relaxed, normal, rushed
    occasion: Optional[str] = None  # work_break, meeting, celebration, etc.
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class WeatherContext(BaseModel):
    """Weather context for recommendations"""
    temperature: float
    condition: str  # clear, rainy, cloudy, etc.
    description: str
    feels_like: float
    humidity: int
    category: str  # cold, hot, rainy, sunny, mild
    recommendations: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "openweathermap"
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class ContextFlags(BaseModel):
    """Various context flags for conversation state"""
    order_intent: bool = False
    menu_requested: bool = False
    help_requested: bool = False
    weather_mentioned: bool = False
    price_mentioned: bool = False
    dietary_discussed: bool = False
    recommendation_given: bool = False
    ready_to_checkout: bool = False
    first_visit: bool = True

class ConversationSession(BaseModel):
    """Complete conversation session context"""
    session_id: str
    customer_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    
    # Conversation data
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    
    # Customer context
    customer_preferences: CustomerPreferences = Field(default_factory=CustomerPreferences)
    mood_indicators: MoodIndicators = Field(default_factory=MoodIndicators)
    
    # Order and business context
    current_order: CurrentOrder = Field(default_factory=CurrentOrder)
    weather_context: Optional[WeatherContext] = None
    context_flags: ContextFlags = Field(default_factory=ContextFlags)
    
    # Session metadata
    client_context: Dict[str, Any] = Field(default_factory=dict)
    personalization_enabled: bool = False
    
    def add_message(self, role: MessageRole, content: str, message_type: MessageType = MessageType.TEXT):
        """Add message to conversation history"""
        message = ConversationMessage(
            role=role,
            content=content,
            message_type=message_type
        )
        self.conversation_history.append(message)
        self.last_updated = datetime.utcnow()
        
        # Keep only last N messages to manage memory
        max_history = 50
        if len(self.conversation_history) > max_history:
            self.conversation_history = self.conversation_history[-max_history:]
    
    def get_recent_messages(self, count: int = 5) -> List[ConversationMessage]:
        """Get recent messages from conversation"""
        return self.conversation_history[-count:] if self.conversation_history else []
    
    def update_preferences(self, preferences: Dict[str, Any]):
        """Update customer preferences"""
        for key, value in preferences.items():
            if hasattr(self.customer_preferences, key):
                setattr(self.customer_preferences, key, value)
        self.last_updated = datetime.utcnow()
    
    def set_mood(self, mood_data: MoodIndicators):
        """Set current mood indicators"""
        self.mood_indicators = mood_data
        self.last_updated = datetime.utcnow()
    
    def add_order_item(self, item: OrderItem):
        """Add item to current order"""
        self.current_order.items.append(item)
        self.current_order.calculate_totals()
        self.last_updated = datetime.utcnow()
    
    def remove_order_item(self, item_id: str) -> bool:
        """Remove item from current order"""
        original_count = len(self.current_order.items)
        self.current_order.items = [
            item for item in self.current_order.items 
            if item.id != item_id
        ]
        
        if len(self.current_order.items) < original_count:
            self.current_order.calculate_totals()
            self.last_updated = datetime.utcnow()
            return True
        return False
    
    def clear_order(self):
        """Clear current order"""
        self.current_order = CurrentOrder()
        self.last_updated = datetime.utcnow()
    
    def to_context_dict(self) -> Dict[str, Any]:
        """Convert session to context dictionary for AI"""
        return {
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "conversation_history": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in self.conversation_history[-10:]  # Last 10 messages
            ],
            "customer_preferences": self.customer_preferences.dict(),
            "mood_indicators": self.mood_indicators.dict() if self.mood_indicators.mood_tags else {},
            "current_order": self.current_order.dict(),
            "weather": self.weather_context.dict() if self.weather_context else None,
            "context_flags": self.context_flags.dict(),
            "personalization_enabled": self.personalization_enabled
        }
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AIResponse(BaseModel):
    """AI service response model"""
    message: str
    context_updates: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: bool = False
    error_details: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }