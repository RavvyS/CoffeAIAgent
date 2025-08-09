# app/main_production.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import json
import uuid
import asyncio
import time
from datetime import datetime
import os
from pathlib import Path
import logging
from contextlib import asynccontextmanager

# Production imports
from app.websocket_manager import WebSocketManager
from app.context_manager import ContextManager
from app.services.ai_service import AIService
from app.services.weather_service import WeatherService
from app.services.analytics_service import AnalyticsService
from app.routers.analytics import router as analytics_router
from production_config import production_settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, production_settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services globally
websocket_manager = WebSocketManager()
context_manager = ContextManager()
ai_service = AIService()
weather_service = WeatherService()
analytics_service = AnalyticsService()

# Load menu data
def load_menu():
    menu_path = Path("data/menu.json")
    if menu_path.exists():
        with open(menu_path, 'r') as f:
            return json.load(f)
    return {"error": "Menu not found"}

menu_data = load_menu()

# Lifespan manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 Coffee Shop AI Agent starting up...")
    
    # Test connections
    redis_status = await context_manager.test_connection()
    logger.info(f"📊 Redis connection: {'✅ Connected' if redis_status else '❌ Failed'}")
    
    ai_status = await ai_service.test_connection()
    logger.info(f"🤖 AI service: {'✅ Ready' if ai_status else '❌ Failed'}")
    
    # Start background tasks
    asyncio.create_task(periodic_cleanup())
    asyncio.create_task(health_check_monitor())
    
    logger.info("☕ Coffee Shop AI Agent is ready to serve!")
    
    yield
    
    # Shutdown
    logger.info("👋 Coffee Shop AI Agent shutting down...")
    await context_manager.close()
    logger.info("✅ Cleanup complete")

# Initialize FastAPI app with production settings
app = FastAPI(
    title="Coffee Shop AI Agent",
    description="Intelligent conversational agent for coffee shop ordering",
    version="1.0.0",
    docs_url="/docs" if production_settings.DEBUG else None,
    redoc_url="/redoc" if production_settings.DEBUG else None,
    lifespan=lifespan
)

# Production middlewares
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=production_settings.ALLOWED_HOSTS
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=production_settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"]
)

# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.4f}s "
        f"ID: {request_id}"
    )
    
    return response

# Rate limiting middleware
from collections import defaultdict
request_counts = defaultdict(list)

@app.middleware("http")
async def rate_limit(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    
    # Clean old requests
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < 60
    ]
    
    # Check rate limit
    if len(request_counts[client_ip]) >= production_settings.MAX_REQUESTS_PER_MINUTE:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "retry_after": 60}
        )
    
    request_counts[client_ip].append(now)
    return await call_next(request)

# Mount static files with caching headers
class StaticFilesWithCaching(StaticFiles):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            response = await super().__call__(scope, receive, send)
            # Add caching headers for static files
            if hasattr(response, 'headers'):
                response.headers["Cache-Control"] = "public, max-age=86400"  # 24 hours
        return response

app.mount("/static", StaticFilesWithCaching(directory="static"), name="static")

# Include routers
app.include_router(analytics_router)

# Health check endpoints
@app.get("/health")
async def health_check():
    """Detailed health check for monitoring"""
    try:
        # Check Redis
        redis_status = await context_manager.test_connection()
        
        # Check AI service
        ai_status = await ai_service.test_connection()
        
        # Check active connections
        active_connections = len(websocket_manager.active_connections)
        
        health_status = {
            "status": "healthy" if redis_status and ai_status else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "redis": "healthy" if redis_status else "unhealthy",
                "ai": "healthy" if ai_status else "unhealthy",
                "websocket": "healthy"
            },
            "metrics": {
                "active_connections": active_connections,
                "uptime": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
            }
        }
        
        status_code = 200 if health_status["status"] == "healthy" else 503
        return JSONResponse(content=health_status, status_code=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            },
            status_code=503
        )

@app.get("/health/live")
async def liveness_check():
    """Simple liveness check for Kubernetes/Docker"""
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}

@app.get("/health/ready")
async def readiness_check():
    """Readiness check for load balancers"""
    redis_ready = await context_manager.test_connection()
    ai_ready = await ai_service.test_connection()
    
    if redis_ready and ai_ready:
        return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
    else:
        return JSONResponse(
            content={"status": "not_ready", "timestamp": datetime.utcnow().isoformat()},
            status_code=503
        )

# Metrics endpoint for monitoring
@app.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint"""
    try:
        active_sessions = await context_manager.get_active_sessions()
        connection_stats = websocket_manager.get_connection_stats()
        
        metrics = [
            f"coffee_shop_active_sessions {len(active_sessions)}",
            f"coffee_shop_active_connections {connection_stats['total_connections']}",
            f"coffee_shop_total_messages {connection_stats['total_messages']}",
            f"coffee_shop_avg_session_duration {connection_stats['average_duration']:.2f}",
        ]
        
        return "\n".join(metrics)
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Metrics unavailable")

# Main routes
@app.get("/", response_class=HTMLResponse)
async def get_chat_page():
    """Serve the main chat interface"""
    try:
        with open("static/index.html", 'r') as f:
            html_content = f.read()
        
        # Inject production settings
        html_content = html_content.replace(
            "<!-- PRODUCTION_CONFIG -->",
            f"""
            <script>
                window.PRODUCTION_MODE = true;
                window.API_BASE_URL = '{os.getenv("API_BASE_URL", "")}';
                window.WS_BASE_URL = '{os.getenv("WS_BASE_URL", "")}';
            </script>
            """
        )
        
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Chat interface not found")

@app.get("/analytics/dashboard", response_class=HTMLResponse)
async def get_analytics_dashboard():
    """Serve analytics dashboard"""
    try:
        with open("static/analytics.html", 'r') as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Analytics dashboard not found")

@app.get("/menu")
async def get_menu():
    """Get coffee shop menu"""
    return menu_data

@app.get("/manifest.json")
async def get_manifest():
    """Serve PWA manifest"""
    try:
        with open("static/manifest.json", 'r') as f:
            manifest = json.load(f)
        return manifest
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Manifest not found")

# WebSocket endpoint with production optimizations
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str = None):
    """WebSocket endpoint for real-time chat"""
    
    # Generate session ID if not provided
    if not session_id or session_id == "new":
        session_id = str(uuid.uuid4())
    
    client_ip = websocket.client.host
    logger.info(f"WebSocket connection attempt from {client_ip}, session: {session_id}")
    
    # Check connection limits
    if len(websocket_manager.active_connections) >= production_settings.MAX_CONNECTIONS_PER_IP * 10:
        await websocket.close(code=1008, reason="Server at capacity")
        return
    
    # Accept connection
    await websocket_manager.connect(websocket, session_id)
    
    try:
        # Track session start
        await analytics_service.track_conversation_start(session_id, {
            "client_ip": client_ip,
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
        
        session_start_time = time.time()
        message_count = 0
        
        while True:
            # Receive message with timeout
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(), 
                    timeout=production_settings.WEBSOCKET_PING_TIMEOUT
                )
            except asyncio.TimeoutError:
                # Send ping
                await websocket.send_json({"type": "ping"})
                continue
            
            message_type = data.get("type", "message")
            content = data.get("message", "")
            
            if message_type == "message" and content.strip():
                message_count += 1
                
                # Track message
                await analytics_service.track_message(
                    session_id, "user", len(content)
                )
                
                # Process user message
                start_time = time.time()
                response = await process_user_message(
                    session_id, 
                    content, 
                    data.get("context", {})
                )
                response_time = time.time() - start_time
                
                # Track AI response
                await analytics_service.track_message(
                    session_id, "assistant", len(response["message"]), response_time
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
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {str(e)}")
    finally:
        await websocket_manager.disconnect(session_id)
        
        # Track session end
        session_duration = time.time() - session_start_time
        await analytics_service.track_session_end(
            session_id, session_duration, message_count, False
        )

async def process_user_message(session_id: str, message: str, user_context: dict = None):
    """Process user message with production error handling"""
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
            try:
                weather_data = await asyncio.wait_for(
                    weather_service.get_current_weather(),
                    timeout=5.0
                )
                await context_manager.update_context(session_id, {
                    "weather": weather_data
                })
            except asyncio.TimeoutError:
                logger.warning("Weather service timeout")
        
        # Generate AI response with timeout
        try:
            ai_response = await asyncio.wait_for(
                ai_service.generate_response(
                    message=message,
                    context=context,
                    menu=menu_data
                ),
                timeout=production_settings.AI_REQUEST_TIMEOUT
            )
        except asyncio.TimeoutError:
            logger.warning("AI service timeout")
            ai_response = {
                "message": "I apologize for the delay. Let me help you with that. Could you please repeat your request?",
                "error": True
            }
        
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
        logger.error(f"Error processing message for {session_id}: {str(e)}")
        return {
            "message": "I apologize, but I'm having trouble processing your request right now. Our team has been notified and we'll resolve this shortly. Please try again in a moment.",
            "error": True
        }

# Background tasks
async def periodic_cleanup():
    """Periodic cleanup of inactive connections and expired sessions"""
    while True:
        try:
            # Clean up inactive WebSocket connections
            await websocket_manager.cleanup_inactive_connections(30)  # 30 minutes
            
            # Clean up expired sessions (done automatically by Redis TTL)
            
            # Sleep for 15 minutes
            await asyncio.sleep(900)
        except Exception as e:
            logger.error(f"Periodic cleanup error: {str(e)}")
            await asyncio.sleep(60)  # Retry in 1 minute

async def health_check_monitor():
    """Monitor service health and log issues"""
    while True:
        try:
            redis_ok = await context_manager.test_connection()
            ai_ok = await ai_service.test_connection()
            
            if not redis_ok:
                logger.error("Redis health check failed")
            if not ai_ok:
                logger.error("AI service health check failed")
            
            # Sleep for 5 minutes
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"Health monitor error: {str(e)}")
            await asyncio.sleep(60)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, 'request_id', 'unknown'),
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Store startup time
app.state.start_time = time.time()

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "app.main_production:app",
        host=host,
        port=port,
        log_level=production_settings.LOG_LEVEL.lower(),
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*"
    )