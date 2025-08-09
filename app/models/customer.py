from pydantic import BaseModel, Field, EmailStr
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class CustomerStatus(str, Enum):
    """Customer status levels"""
    NEW = "new"
    REGULAR = "regular"
    VIP = "vip"
    INACTIVE = "inactive"

class OrderStatus(str, Enum):
    """Order status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    """Payment methods"""
    CASH = "cash"
    CARD = "card"
    MOBILE = "mobile"
    GIFT_CARD = "gift_card"

class CustomerProfile(BaseModel):
    """Complete customer profile"""
    customer_id: str
    
    # Basic information
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    
    # Account details
    status: CustomerStatus = CustomerStatus.NEW
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_visit: Optional[datetime] = None
    visit_count: int = 0
    
    # Preferences (detailed customer preferences)
    dietary_restrictions: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    favorite_drinks: List[str] = Field(default_factory=list)
    disliked_items: List[str] = Field(default_factory=list)
    
    # Ordering behavior
    usual_visit_times: List[str] = Field(default_factory=list)  # time ranges
    average_order_value: float = 0.0
    preferred_payment: Optional[PaymentMethod] = None
    
    # Personalization settings
    conversation_style: Dict[str, Any] = Field(default_factory=dict)
    marketing_preferences: Dict[str, bool] = Field(default_factory=dict)
    
    # Loyalty information
    loyalty_points: int = 0
    total_spent: float = 0.0
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }
    
    def update_visit(self):
        """Update visit information"""
        self.last_visit = datetime.utcnow()
        self.visit_count += 1
        
        # Update status based on visit count
        if self.visit_count >= 10:
            self.status = CustomerStatus.VIP
        elif self.visit_count >= 3:
            self.status = CustomerStatus.REGULAR

class HistoricalOrder(BaseModel):
    """Historical order record"""
    order_id: str
    customer_id: str
    session_id: Optional[str] = None
    
    # Order details
    items: List[Dict[str, Any]]  # Simplified item structure for history
    subtotal: float
    tax: float
    total: float
    
    # Order metadata
    status: OrderStatus
    payment_method: Optional[PaymentMethod] = None
    order_type: str = "in_store"  # in_store, takeaway, delivery
    
    # Timing
    ordered_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Context when order was made
    weather_condition: Optional[str] = None
    customer_mood: Optional[List[str]] = None
    
    # Feedback
    rating: Optional[int] = None  # 1-5 stars
    feedback: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class CustomerInsights(BaseModel):
    """Customer behavior insights"""
    customer_id: str
    
    # Ordering patterns
    most_ordered_items: List[Dict[str, Any]] = Field(default_factory=list)
    preferred_order_times: List[str] = Field(default_factory=list)
    seasonal_preferences: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Spending behavior
    average_order_value: float = 0.0
    spending_trend: str = "stable"  # increasing, stable, decreasing
    price_sensitivity: str = "medium"  # low, medium, high
    
    # Interaction preferences
    prefers_recommendations: bool = True
    response_to_upselling: str = "neutral"  # positive, neutral, negative
    conversation_style_preference: str = "friendly"  # brief, friendly, detailed
    
    # Calculated metrics
    customer_lifetime_value: float = 0.0
    churn_risk: str = "low"  # low, medium, high
    next_visit_prediction: Optional[datetime] = None
    
    # Last updated
    calculated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class LoyaltyTransaction(BaseModel):
    """Loyalty points transaction"""
    transaction_id: str
    customer_id: str
    
    # Transaction details
    points_change: int  # positive for earned, negative for redeemed
    transaction_type: str  # earned, redeemed, bonus, expired
    description: str
    
    # Related order
    order_id: Optional[str] = None
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class CustomerFeedback(BaseModel):
    """Customer feedback and ratings"""
    feedback_id: str
    customer_id: str
    session_id: Optional[str] = None
    order_id: Optional[str] = None
    
    # Feedback content
    rating: int = Field(..., ge=1, le=5)  # 1-5 stars
    feedback_text: Optional[str] = None
    feedback_category: str = "general"  # food, service, atmosphere, ai_assistant
    
    # Context
    created_at: datetime = Field(default_factory=datetime.utcnow)
    feedback_source: str = "chat"  # chat, email, survey
    
    # Response
    responded_at: Optional[datetime] = None
    response_text: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class CustomerSegment(BaseModel):
    """Customer segmentation model"""
    segment_name: str
    description: str
    criteria: Dict[str, Any]
    
    # Segment characteristics
    typical_order_value: float
    visit_frequency: str  # daily, weekly, monthly, occasional
    price_sensitivity: str
    preferred_items: List[str]
    
    # Marketing approach
    recommended_messaging: str
    promotional_strategy: str
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }