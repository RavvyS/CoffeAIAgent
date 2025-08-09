from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
from datetime import datetime

class WebSocketManager:
    """Manages WebSocket connections for real-time chat"""
    
    def __init__(self):
        # Store active connections: session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Store connection metadata
        self.connection_info: Dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept and store new WebSocket connection"""
        await websocket.accept()
        
        # Store connection
        self.active_connections[session_id] = websocket
        self.connection_info[session_id] = {
            "connected_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "message_count": 0
        }
        
        print(f"✅ WebSocket connected: {session_id}")
        print(f"📊 Active connections: {len(self.active_connections)}")
    
    async def disconnect(self, session_id: str):
        """Remove WebSocket connection"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        if session_id in self.connection_info:
            connection_duration = datetime.utcnow() - self.connection_info[session_id]["connected_at"]
            print(f"👋 WebSocket disconnected: {session_id} (duration: {connection_duration})")
            del self.connection_info[session_id]
        
        print(f"📊 Active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, session_id: str, message: dict):
        """Send message to specific session"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_json(message)
                
                # Update activity tracking
                if session_id in self.connection_info:
                    self.connection_info[session_id]["last_activity"] = datetime.utcnow()
                    self.connection_info[session_id]["message_count"] += 1
                
                return True
            except Exception as e:
                print(f"❌ Error sending message to {session_id}: {str(e)}")
                # Remove broken connection
                await self.disconnect(session_id)
                return False
        return False
    
    async def broadcast(self, message: dict, exclude_session: str = None):
        """Send message to all active connections (except excluded session)"""
        disconnected_sessions = []
        
        for session_id, websocket in self.active_connections.items():
            if session_id == exclude_session:
                continue
                
            try:
                await websocket.send_json(message)
                
                # Update activity tracking
                if session_id in self.connection_info:
                    self.connection_info[session_id]["last_activity"] = datetime.utcnow()
                    self.connection_info[session_id]["message_count"] += 1
                    
            except Exception as e:
                print(f"❌ Error broadcasting to {session_id}: {str(e)}")
                disconnected_sessions.append(session_id)
        
        # Clean up broken connections
        for session_id in disconnected_sessions:
            await self.disconnect(session_id)
    
    async def send_typing_indicator(self, session_id: str, typing: bool = True):
        """Send typing indicator to specific session"""
        message = {
            "type": "typing",
            "typing": typing,
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.send_personal_message(session_id, message)
    
    async def send_system_message(self, session_id: str, message: str, message_type: str = "system"):
        """Send system message to specific session"""
        system_message = {
            "type": message_type,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        return await self.send_personal_message(session_id, system_message)
    
    def get_connection_stats(self) -> dict:
        """Get statistics about active connections"""
        total_connections = len(self.active_connections)
        
        if total_connections == 0:
            return {
                "total_connections": 0,
                "average_duration": 0,
                "total_messages": 0
            }
        
        now = datetime.utcnow()
        total_duration = 0
        total_messages = 0
        
        for info in self.connection_info.values():
            duration = (now - info["connected_at"]).total_seconds()
            total_duration += duration
            total_messages += info["message_count"]
        
        return {
            "total_connections": total_connections,
            "average_duration": total_duration / total_connections,
            "total_messages": total_messages,
            "connections": {
                session_id: {
                    "duration": (now - info["connected_at"]).total_seconds(),
                    "message_count": info["message_count"],
                    "last_activity": info["last_activity"].isoformat()
                }
                for session_id, info in self.connection_info.items()
            }
        }
    
    async def cleanup_inactive_connections(self, max_inactive_minutes: int = 30):
        """Remove connections that have been inactive for too long"""
        now = datetime.utcnow()
        inactive_sessions = []
        
        for session_id, info in self.connection_info.items():
            minutes_inactive = (now - info["last_activity"]).total_seconds() / 60
            if minutes_inactive > max_inactive_minutes:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            await self.send_system_message(
                session_id, 
                "Your session has expired due to inactivity. Please refresh to start a new chat.",
                "session_expired"
            )
            await self.disconnect(session_id)
        
        if inactive_sessions:
            print(f"🧹 Cleaned up {len(inactive_sessions)} inactive connections")
    
    def is_connected(self, session_id: str) -> bool:
        """Check if session is currently connected"""
        return session_id in self.active_connections
    
    def get_active_session_ids(self) -> List[str]:
        """Get list of all active session IDs"""
        return list(self.active_connections.keys())