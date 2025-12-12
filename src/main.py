"""
MynEra Aira - Production FastAPI Application
Deployed on DigitalOcean with Qdrant Cloud integration
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from src.config import settings
from src.services.llm_service import llm_service
from src.services.data_loader import data_loader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==========================================
# 🚀 FastAPI Application
# ==========================================

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="MynEra Aira - IT Career Consultant & RAG System",
    docs_url="/docs",
    redoc_url="/redoc"
)

# ==========================================
# 🌐 CORS Configuration
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 📊 Request/Response Models
# ==========================================

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    user_id: Optional[str] = "anonymous"

class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[Dict]] = []
    recommendations: Optional[List[Dict]] = []
    needs_clarification: Optional[bool] = False
    follow_up_questions: Optional[List[str]] = []

class SyncResponse(BaseModel):
    status: str
    message: str

# ==========================================
# 🔥 API Endpoints
# ==========================================

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint that processes user messages and returns AI responses.
    
    - **message**: User's message/question
    - **history**: Conversation history (optional)
    - **user_id**: User identifier (optional, defaults to "anonymous")
    """
    try:
        logger.info(f"📩 Received chat request from user: {request.user_id}")
        
        # Convert ChatMessage objects to dict format for llm_service
        history_dicts = [
            {"role": msg.role, "content": msg.content} 
            for msg in request.history
        ]
        
        # Call LLM service
        response = llm_service.get_response(
            query=request.message,
            conversation_history=history_dicts,
            user_id=request.user_id
        )
        
        logger.info(f"✅ Response generated successfully")
        
        # Convert response to dict format
        return ChatResponse(
            answer=response.answer,
            sources=[src.model_dump() for src in response.sources] if response.sources else [],
            recommendations=[rec.model_dump() for rec in response.recommendations] if response.recommendations else [],
            needs_clarification=response.needs_clarification,
            follow_up_questions=response.follow_up_questions
        )
        
    except Exception as e:
        logger.error(f"❌ Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns the application status and version.
    """
    return {
        "status": "active",
        "version": settings.VERSION,
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT
    }

@app.post("/admin/sync", response_model=SyncResponse)
async def sync_data(background_tasks: BackgroundTasks):
    """
    Admin endpoint to trigger data synchronization.
    Loads data from JSON files and syncs to Qdrant Vector Database.
    
    This runs as a background task to avoid blocking the response.
    """
    try:
        logger.info("🔄 Admin sync triggered")
        
        # Add sync task to background
        background_tasks.add_task(perform_sync)
        
        return SyncResponse(
            status="initiated",
            message="Data synchronization started in background"
        )
        
    except Exception as e:
        logger.error(f"❌ Error initiating sync: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to initiate sync")

# ==========================================
# 🔧 Background Tasks
# ==========================================

def perform_sync():
    """Background task to perform data synchronization."""
    try:
        logger.info("📊 Starting data sync...")
        data_loader.reindex_all(recreate_collections=False)
        logger.info("✅ Data sync completed successfully")
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}", exc_info=True)

# ==========================================
# 🎯 Application Startup
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.VERSION} starting...")
    logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🔧 Debug Mode: {settings.DEBUG_MODE}")
    logger.info("✅ Application ready")

@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("👋 Application shutting down...")

# ==========================================
# 🏃 Run Application (Development)
# ==========================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG_MODE
    )
