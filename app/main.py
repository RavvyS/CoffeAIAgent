from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import uuid
import asyncio
from datetime import datetime
import os
from pathlib import Path

from pydantic import BaseModel

from app.websocket_manager import WebSocketManager
from app.context_manager import ContextManager
from app.services.ai_service import AIService
from app.services.weather_service import WeatherService
from app.services.payment_service import PaymentService, MockPaymentService
from app.services.emotional_support_service import EmotionalSupportService
from app.services.queue_service import VirtualQueueService
from app.services.analytics_service import AnalyticsService  # NEW
from app.routers.analytics import router as analytics_router  # NEW
from app.models.payment import PaymentRequest, PaymentResponse, Order
from app.models.queue import QueueEntry, QueueType, Appointment, AppointmentType
from app.utils.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Coffee Shop AI Agent",
    description="Intelligent conversational agent for coffee shop ordering",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(analytics_router)  # NEW

# Initialize managers and services
websocket_manager = WebSocketManager()
context_manager = ContextManager()
ai_service = AIService()
weather_service = WeatherService()
analytics_service = AnalyticsService()  # NEW

# Initialize other services
payment_service = MockPaymentService() if settings.DEBUG else PaymentService()
emotional_support_service = EmotionalSupportService()
queue_service = VirtualQueueService()

# Load menu data
def load_menu():
    menu_path = Path("data/menu.json")
    if menu_path.exists():
        with open(menu_path, 'r') as f:
            return json.load(f)
    return {"error": "Menu not found"}

menu_data = load_menu()

@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    """Serve the main chat interface"""
    with open("static/index.html", 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/menu")
async def get_menu():
    """Get coffee shop menu"""
    return menu_data

@app.get("/analytics/dashboard", response_class=HTMLResponse)  # NEW
async def get_analytics_dashboard():
    """Serve analytics dashboard"""
    try:
        with open("static/analytics.html", 'r') as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Analytics dashboard not found")

@app.get("/manifest.json")  # NEW - PWA Manifest
async def get_manifest():
    """Serve PWA manifest"""
    try:
        with open("static/manifest.json", 'r') as f:
            manifest = json.load(f)
        return manifest
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Manifest not found")

# Payment endpoints
@app.post("/api/payment/create-intent")
async def create_payment_intent(payment_request: PaymentRequest):
    """Create payment intent"""
    try:
        result = await payment_service.create_payment_intent(
            amount=payment_request.amount,
            currency=payment_request.currency,
            metadata=payment_request.metadata
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/payment/confirm")
async def confirm_payment(payment_id: str):
    """Confirm payment"""
    try:
        result = await payment_service.confirm_payment(payment_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Queue endpoints
@app.post("/api/queue/join")
async def join_queue(entry: QueueEntry):
    """Join virtual queue"""
    try:
        result = await queue_service.add_to_queue(entry)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/queue/status/{queue_id}")
async def get_queue_status(queue_id: str):
    """Get queue status"""
    try:
        result = await queue_service.get_queue_status(queue_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail="Queue entry not found")

@app.post("/api/appointments/book")
async def book_appointment(appointment: Appointment):
    """Book appointment"""
    try:
        result = await queue_service.book_appointment(appointment)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    """WebSocket endpoint for real-time chat"""
    
    # Generate session ID if not provided
    if not session_id or session_id == "new":
        session_id = str(uuid.uuid4())
    
    # Accept WebSocket connection
    await websocket_manager.connect(websocket, session_id)
    
    try:
        # Track conversation start - NEW
        await analytics_service.track_conversation_start(session_id, {
            "user_agent": websocket.headers.get("user-agent", ""),
            "origin": websocket.headers.get("origin", "")
        })
        
        # Send welcome message
        await websocket.send_json({
            "type": "system",
            "message": "Welcome to our Coffee Shop! How can I help you today?",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Initialize session context
        await context_manager.initialize_session(session_id)
        
        # Track session metrics - NEW
        session_start_time = datetime.utcnow()
        message_count = 0
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            message_type = data.get("type", "message")
            content = data.get("message", "")
            
            if message_type == "message" and content.strip():
                message_count += 1  # NEW
                
                # Track user message - NEW
                await analytics_service.track_message(session_id, "user", len(content))
                
                # Process user message
                start_time = datetime.utcnow()  # NEW
                response = await process_user_message(
                    session_id, 
                    content, 
                    data.get("context", {})
                )
                response_time = (datetime.utcnow() - start_time).total_seconds()  # NEW
                
                # Track AI response - NEW
                await analytics_service.track_message(
                    session_id, "assistant", len(response["message"]), response_time
                )
                
                # Track recommendations if any - NEW
                if response.get("recommendations"):
                    await analytics_service.track_recommendation(
                        session_id, 
                        "ai_suggestion", 
                        response["recommendations"], 
                        False  # Not accepted yet
                    )
                
                # Send AI response
                await websocket.send_json({
                    "type": "assistant",
                    "message": response["message"],
                    "session_id": session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "context": response.get("context", {}),
                    "suggestions": response.get("suggestions", [])
                })
            
            elif message_type == "ping":
                # Handle ping/keepalive
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "order_action":  # NEW - Track order events
                action = data.get("action", "")
                order_data = data.get("order_data", {})
                await analytics_service.track_order_event(session_id, action, order_data)
                
    except WebSocketDisconnect:
        print(f"Client {session_id} disconnected")
    except Exception as e:
        print(f"WebSocket error for {session_id}: {str(e)}")
    finally:
        await websocket_manager.disconnect(session_id)
        
        # Track session end - NEW
        if 'session_start_time' in locals() and 'message_count' in locals():
            session_duration = (datetime.utcnow() - session_start_time).total_seconds()
            # Check if order was completed (you can add logic to determine this)
            order_completed = False  # Implement logic to check if order was completed
            
            await analytics_service.track_session_end(
                session_id, session_duration, message_count, order_completed
            )
        
        # Optionally clean up session data after some time
        # await context_manager.cleanup_session(session_id, delay=3600)

async def process_user_message(session_id: str, message: str, user_context: dict = None):
    """Process user message and generate AI response"""
    try:
        # Get current session context
        context = await context_manager.get_session_context(session_id)
        
        # Update context with user message
        await context_manager.update_conversation_history(
            session_id, 
            "user", 
            message
        )
        
        # Add any additional context from client
        if user_context:
            await context_manager.update_context(session_id, {
                "client_context": user_context
            })
        
        # Get weather data if not cached
        if not context.get("weather"):
            weather_data = await weather_service.get_current_weather()
            await context_manager.update_context(session_id, {
                "weather": weather_data
            })
            
            # Track weather recommendation - NEW
            if weather_data and weather_data.get("recommendations"):
                await analytics_service.track_weather_recommendation(
                    session_id,
                    weather_data.get("category", "unknown"),
                    weather_data.get("recommendations", {}).get("drinks", [])
                )
        
        # Check for emotional support needs - Enhanced
        emotional_response = await emotional_support_service.analyze_message(message, context)
        if emotional_response.get("support_needed"):
            # Track mood detection - NEW
            await analytics_service.track_mood_detection(
                session_id,
                emotional_response.get("detected_moods", []),
                emotional_response.get("confidence", 0.0)
            )
            
            # Update context with emotional support
            await context_manager.update_context(session_id, {
                "emotional_state": emotional_response
            })
        
        # Generate AI response
        ai_response = await ai_service.generate_response(
            message=message,
            context=context,
            menu=menu_data
        )
        
        # Enhance response with emotional support if needed
        if emotional_response.get("support_needed"):
            ai_response = await emotional_support_service.enhance_response(
                ai_response, emotional_response
            )
        
        # Update context with AI response
        await context_manager.update_conversation_history(
            session_id,
            "assistant", 
            ai_response["message"]
        )
        
        # Update any context changes from AI processing
        if ai_response.get("context_updates"):
            await context_manager.update_context(
                session_id, 
                ai_response["context_updates"]
            )
        
        return ai_response
        
    except Exception as e:
        print(f"Error processing message for {session_id}: {str(e)}")
        return {
            "message": "I apologize, but I'm having trouble processing your request right now. Could you please try again?",
            "error": True
        }

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    print("🚀 Coffee Shop AI Agent starting up...")
    
    # Test Redis connection
    redis_status = await context_manager.test_connection()
    print(f"📊 Redis connection: {'✅ Connected' if redis_status else '❌ Failed'}")
    
    # Test AI service
    ai_status = await ai_service.test_connection()
    print(f"🤖 AI service: {'✅ Ready' if ai_status else '❌ Failed'}")
    
    # Initialize payment service
    await payment_service.initialize()
    print(f"💳 Payment service: {'✅ Ready' if payment_service else '❌ Failed'}")
    
    # Initialize queue service
    await queue_service.initialize()
    print(f"🚶‍♂️ Queue service: {'✅ Ready' if queue_service else '❌ Failed'}")
    
    # Test analytics service - NEW
    try:
        await analytics_service._get_redis_client()
        print("📈 Analytics service: ✅ Ready")
    except Exception as e:
        print(f"📈 Analytics service: ❌ Failed - {str(e)}")
    
    print("☕ Coffee Shop AI Agent is ready to serve!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("👋 Coffee Shop AI Agent shutting down...")
    
    # Close all services
    await context_manager.close()
    
    if hasattr(payment_service, 'close'):
        await payment_service.close()
    
    if hasattr(queue_service, 'close'):
        await queue_service.close()
    
    print("✅ Cleanup complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )


# Add this data model for queue requests
class QueueJoinRequest(BaseModel):
    customer_name: str
    queue_type: str = "walk_in"
    party_size: int = 1
    customer_phone: str = None
    session_id: str = None

# Replace or add this endpoint
@app.post("/api/queue/join")
async def join_queue_api(request: QueueJoinRequest):
    """Join virtual queue via API - Fixed version"""
    try:
        # Simple queue simulation for now
        import uuid
        import random
        
        queue_id = f"queue_{uuid.uuid4().hex[:8]}"
        position = random.randint(1, 5)  # Mock position
        wait_time = position * 5  # Mock wait time
        
        return {
            "success": True,
            "message": f"Welcome {request.customer_name}! You're #{position} in line. Estimated wait: {wait_time} minutes. We'll notify you when it's your turn!",
            "queue_entry": {
                "queue_id": queue_id,
                "position": position,
                "estimated_wait_time": wait_time,
                "customer_name": request.customer_name,
                "party_size": request.party_size,
                "status": "waiting",
                "queue_type": request.queue_type
            }
        }
        
    except Exception as e:
        print(f"❌ Queue join error: {str(e)}")
        return {
            "success": False,
            "error": f"Unable to join queue: {str(e)}"
        }