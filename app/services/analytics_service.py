import json
from datetime import datetime
from typing import Dict, List, Optional, Any

class AnalyticsService:
    """Analytics service for tracking coffee shop metrics"""
    
    def __init__(self):
        self.redis_client = None
        self.in_memory_store = {}
        print("📊 Analytics service initialized (in-memory mode)")
    
    async def _get_redis_client(self):
        """Get Redis client (placeholder for compatibility)"""
        return None
    
    async def track_conversation_start(self, session_id: str, context: Dict = None):
        """Track new conversation start"""
        print(f"📊 Tracking conversation start: {session_id}")
        # Store in memory for now
        self.in_memory_store[f"session_{session_id}"] = {
            "started_at": datetime.utcnow().isoformat(),
            "context": context or {}
        }
    
    async def track_message(self, session_id: str, role: str, message_length: int, 
                          response_time: float = None):
        """Track individual message"""
        print(f"📊 Tracking message: {role} - {message_length} chars")
        
    async def track_session_end(self, session_id: str, duration: float, 
                               messages_count: int, order_completed: bool):
        """Track conversation end"""
        print(f"📊 Tracking session end: {session_id} - {duration:.2f}s")
    
    async def track_order_event(self, session_id: str, event_type: str, order_data: Dict):
        """Track order-related events"""
        print(f"📊 Order event: {event_type} for {session_id}")
    
    async def track_mood_detection(self, session_id: str, moods: List[str], confidence: float):
        """Track mood detection events"""
        print(f"📊 Mood detected: {moods} (confidence: {confidence:.2f})")
    
    async def track_recommendation(self, session_id: str, rec_type: str, recommendations: List, accepted: bool):
        """Track recommendation events"""
        print(f"📊 Recommendation: {rec_type} - accepted: {accepted}")
    
    async def track_weather_recommendation(self, session_id: str, weather_category: str, drinks: List):
        """Track weather-based recommendations"""
        print(f"📊 Weather rec: {weather_category} - {len(drinks)} drinks")
    
    async def get_dashboard_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Get dashboard metrics - mock data for now"""
        return {
            "overview": {
                "total_conversations": 1247,
                "total_orders": 342,
                "conversion_rate": 27.4,
                "customer_satisfaction": 4.2
            }
        }