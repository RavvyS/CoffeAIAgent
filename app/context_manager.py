import redis.asyncio as redis
import os  # Add this line
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

from app.utils.config import settings

class ContextManager:
    """Manages conversation context and session data using Redis"""
    
    def __init__(self):
        # Initialize Redis connection
        self.redis_client = None
        self.connected = False
        
        # Default session expiration (2 hours for coffee shop visit)
        self.session_ttl = 7200  # 2 hours in seconds
        
        # Context structure template
        self.default_context = {
            "session_id": None,
            "created_at": None,
            "last_updated": None,
            "customer_preferences": {},
            "conversation_history": [],
            "current_order": {"items": [], "total": 0.0},
            "mood_indicators": [],
            "weather": None,
            "context_flags": {},
            "personalization_enabled": False,
            "customer_id": None
        }
    
    async def _get_redis_client(self):
        """Get or create Redis client connection"""
        if not self.redis_client:
            try:
                # Try Redis Cloud URL first (for production)
                if settings.REDIS_URL:
                    self.redis_client = redis.from_url(
                        settings.REDIS_URL,
                        encoding='utf-8',
                        decode_responses=True
                    )
                else:
                    # Local Redis for development
                    self.redis_client = redis.Redis(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        password=settings.REDIS_PASSWORD,
                        encoding='utf-8',
                        decode_responses=True
                    )
                
                # Test connection
                await self.redis_client.ping()
                self.connected = True
                print("✅ Redis connection established")
                
            except Exception as e:
                print(f"❌ Redis connection failed: {str(e)}")
                print("🔄 Falling back to in-memory storage (not persistent)")
                self.redis_client = None
                self.connected = False
                # Initialize in-memory fallback
                self._memory_store = {}
        
        return self.redis_client
    
    async def test_connection(self) -> bool:
        """Test Redis connection"""
        try:
            client = await self._get_redis_client()
            if client:
                await client.ping()
                return True
        except:
            pass
        return False
    
    async def initialize_session(self, session_id: str, customer_id: Optional[str] = None) -> dict:
        """Initialize new session context"""
        context = self.default_context.copy()
        context.update({
            "session_id": session_id,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "customer_id": customer_id
        })
        
        await self._save_context(session_id, context)
        print(f"🎯 Session initialized: {session_id}")
        
        return context
    
    async def get_session_context(self, session_id: str) -> dict:
        """Get current session context"""
        try:
            client = await self._get_redis_client()
            
            if client and self.connected:
                # Get from Redis
                context_data = await client.get(f"session:{session_id}")
                if context_data:
                    context = json.loads(context_data)
                    # Update last accessed time
                    context["last_updated"] = datetime.utcnow().isoformat()
                    await self._save_context(session_id, context)
                    return context
            else:
                # Fallback to in-memory storage
                if hasattr(self, '_memory_store') and session_id in self._memory_store:
                    return self._memory_store[session_id]
            
            # If no context found, initialize new one
            return await self.initialize_session(session_id)
            
        except Exception as e:
            print(f"❌ Error getting session context {session_id}: {str(e)}")
            return await self.initialize_session(session_id)
    
    async def _save_context(self, session_id: str, context: dict):
        """Save context to Redis or memory fallback"""
        try:
            context["last_updated"] = datetime.utcnow().isoformat()
            
            client = await self._get_redis_client()
            
            if client and self.connected:
                # Save to Redis with TTL
                await client.setex(
                    f"session:{session_id}",
                    self.session_ttl,
                    json.dumps(context, default=str)
                )
            else:
                # Fallback to in-memory storage
                if not hasattr(self, '_memory_store'):
                    self._memory_store = {}
                self._memory_store[session_id] = context
                
        except Exception as e:
            print(f"❌ Error saving context for {session_id}: {str(e)}")
    
    async def update_context(self, session_id: str, updates: dict):
        """Update specific fields in session context"""
        context = await self.get_session_context(session_id)
        context.update(updates)
        await self._save_context(session_id, context)
    
    async def update_conversation_history(self, session_id: str, role: str, message: str):
        """Add message to conversation history"""
        context = await self.get_session_context(session_id)
        
        # Add new message
        new_message = {
            "role": role,
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        context["conversation_history"].append(new_message)
        
        # Keep only last 20 messages to manage memory
        if len(context["conversation_history"]) > 20:
            context["conversation_history"] = context["conversation_history"][-20:]
        
        await self._save_context(session_id, context)
    
    async def add_order_item(self, session_id: str, item: dict):
        """Add item to current order"""
        context = await self.get_session_context(session_id)
        
        context["current_order"]["items"].append({
            "id": str(uuid.uuid4()),
            "name": item.get("name"),
            "size": item.get("size", "medium"),
            "price": item.get("price", 0.0),
            "customizations": item.get("customizations", []),
            "added_at": datetime.utcnow().isoformat()
        })
        
        # Recalculate total
        total = sum(item.get("price", 0.0) for item in context["current_order"]["items"])
        context["current_order"]["total"] = round(total, 2)
        
        await self._save_context(session_id, context)
    
    async def remove_order_item(self, session_id: str, item_id: str):
        """Remove item from current order"""
        context = await self.get_session_context(session_id)
        
        context["current_order"]["items"] = [
            item for item in context["current_order"]["items"] 
            if item.get("id") != item_id
        ]
        
        # Recalculate total
        total = sum(item.get("price", 0.0) for item in context["current_order"]["items"])
        context["current_order"]["total"] = round(total, 2)
        
        await self._save_context(session_id, context)
    
    async def clear_order(self, session_id: str):
        """Clear current order"""
        await self.update_context(session_id, {
            "current_order": {"items": [], "total": 0.0}
        })
    
    async def update_customer_preferences(self, session_id: str, preferences: dict):
        """Update customer preferences"""
        context = await self.get_session_context(session_id)
        context["customer_preferences"].update(preferences)
        await self._save_context(session_id, context)
    
    async def set_mood_indicators(self, session_id: str, mood_data: dict):
        """Set current mood indicators"""
        await self.update_context(session_id, {
            "mood_indicators": mood_data,
            "mood_detected_at": datetime.utcnow().isoformat()
        })
    
    async def get_conversation_summary(self, session_id: str, last_n_messages: int = 5) -> List[dict]:
        """Get recent conversation history"""
        context = await self.get_session_context(session_id)
        history = context.get("conversation_history", [])
        return history[-last_n_messages:] if history else []
    
    async def extend_session(self, session_id: str, additional_seconds: int = 3600):
        """Extend session TTL"""
        try:
            client = await self._get_redis_client()
            if client and self.connected:
                current_ttl = await client.ttl(f"session:{session_id}")
                if current_ttl > 0:
                    new_ttl = current_ttl + additional_seconds
                    await client.expire(f"session:{session_id}", new_ttl)
                    print(f"⏰ Extended session {session_id} by {additional_seconds}s")
        except Exception as e:
            print(f"❌ Error extending session {session_id}: {str(e)}")
    
    async def cleanup_session(self, session_id: str, delay: int = 0):
        """Clean up session data (optionally after delay)"""
        if delay > 0:
            await asyncio.sleep(delay)
        
        try:
            client = await self._get_redis_client()
            if client and self.connected:
                await client.delete(f"session:{session_id}")
            elif hasattr(self, '_memory_store') and session_id in self._memory_store:
                del self._memory_store[session_id]
                
            print(f"🧹 Cleaned up session: {session_id}")
        except Exception as e:
            print(f"❌ Error cleaning up session {session_id}: {str(e)}")
    
    async def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        try:
            client = await self._get_redis_client()
            if client and self.connected:
                keys = await client.keys("session:*")
                return [key.replace("session:", "") for key in keys]
            elif hasattr(self, '_memory_store'):
                return list(self._memory_store.keys())
            return []
        except Exception as e:
            print(f"❌ Error getting active sessions: {str(e)}")
            return []
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            print("👋 Redis connection closed")