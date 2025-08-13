import os
import logging
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
import uvicorn

from tool import get_diet_agent_chain

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Global variables for application state
app_state = {
    "agent_chains": {},  # Store agent chains per session
    "memories": {},      # Store memories per session
    "startup_time": None
}

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    app_state["startup_time"] = datetime.now()
    logger.info("AI Dietitian API starting up...")
    
    yield
    
    # Shutdown
    logger.info("AI Dietitian API shutting down...")
    # Clean up any resources if needed
    app_state["agent_chains"].clear()
    app_state["memories"].clear()

# FastAPI app initialization
app = FastAPI(
    title="AI Dietitian API",
    description="A production-ready API for personalized diet planning using AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure appropriately for production
)

# Pydantic models
class ChatMessage(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Session ID must contain only alphanumeric characters, hyphens, and underscores')
        return v

class ChatResponse(BaseModel):
    response: str
    session_id: str
    timestamp: datetime
    status: str = "success"

class InitSessionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('session_id')
    @classmethod
    def validate_session_id(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Session ID must contain only alphanumeric characters, hyphens, and underscores')
        return v

class SessionResponse(BaseModel):
    session_id: str
    status: str
    message: str
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    uptime_seconds: float
    active_sessions: int

# Dependency to get API key
async def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract and validate API key from Authorization header"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide Gemini API key in Authorization header as Bearer token"
        )
    
    api_key = credentials.credentials
    if not api_key or not api_key.startswith('AI'):  # Basic validation for Gemini API key format
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format. Please provide a valid Gemini API key"
        )
    
    return api_key

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred",
            "status": "error",
            "timestamp": datetime.now().isoformat()
        }
    )

# Routes
@app.get("/", response_model=dict)
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Dietitian API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "chat": "/chat",
            "init_session": "/init-session",
            "clear_session": "/clear-session/{session_id}"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    uptime = (datetime.now() - app_state["startup_time"]).total_seconds() if app_state["startup_time"] else 0
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        uptime_seconds=uptime,
        active_sessions=len(app_state["agent_chains"])
    )

@app.post("/init-session", response_model=SessionResponse)
async def initialize_session(
    request: InitSessionRequest,
    api_key: str = Depends(get_api_key)
):
    """Initialize a new chat session"""
    try:
        session_id = request.session_id
        
        # Check if session already exists
        if session_id in app_state["agent_chains"]:
            return SessionResponse(
                session_id=session_id,
                status="exists",
                message="Session already initialized",
                timestamp=datetime.now()
            )
        
        # Initialize the agent chain and memory
        agent_chain, memory = get_diet_agent_chain(api_key)
        
        # Store in application state
        app_state["agent_chains"][session_id] = agent_chain
        app_state["memories"][session_id] = memory
        
        logger.info(f"Initialized session: {session_id}")
        
        return SessionResponse(
            session_id=session_id,
            status="initialized",
            message="Session successfully initialized. You can now start chatting!",
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize session {request.session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize session: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    api_key: str = Depends(get_api_key)
):
    """Main chat endpoint for interacting with the AI Dietitian"""
    try:
        session_id = request.session_id
        user_message = request.message
        
        # Check if session exists, if not initialize it
        if session_id not in app_state["agent_chains"]:
            agent_chain, memory = get_diet_agent_chain(api_key)
            app_state["agent_chains"][session_id] = agent_chain
            app_state["memories"][session_id] = memory
            logger.info(f"Auto-initialized session: {session_id}")
        
        # Get the agent chain and memory for this session
        agent_chain = app_state["agent_chains"][session_id]
        memory = app_state["memories"][session_id]
        
        # Get chat history
        chat_history = memory.load_memory_variables({}).get("chat_history", [])
        
        # Generate response
        response = agent_chain.invoke({
            "chat_history": chat_history,
            "input": user_message
        })
        
        ai_response = response.content
        
        # Update memory
        memory.save_context({"input": user_message}, {"output": ai_response})
        
        logger.info(f"Generated response for session {session_id}")
        
        return ChatResponse(
            response=ai_response,
            session_id=session_id,
            timestamp=datetime.now(),
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Chat error for session {request.session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )

@app.delete("/clear-session/{session_id}", response_model=SessionResponse)
async def clear_session(session_id: str):
    """Clear a specific session"""
    try:
        if session_id in app_state["agent_chains"]:
            del app_state["agent_chains"][session_id]
            del app_state["memories"][session_id]
            logger.info(f"Cleared session: {session_id}")
            message = "Session cleared successfully"
            status_msg = "cleared"
        else:
            message = "Session not found"
            status_msg = "not_found"
        
        return SessionResponse(
            session_id=session_id,
            status=status_msg,
            message=message,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Failed to clear session {session_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear session: {str(e)}"
        )

@app.get("/sessions", response_model=dict)
async def list_sessions():
    """List all active sessions (for monitoring)"""
    return {
        "active_sessions": list(app_state["agent_chains"].keys()),
        "total_sessions": len(app_state["agent_chains"]),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )