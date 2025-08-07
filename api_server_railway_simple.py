"""
Railway-Optimized API Server with Robust Health Check
Minimal dependencies and guaranteed startup
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import os
import sys
from datetime import datetime
import logging
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="ACT Refugee Support API",
    description="Railway-optimized API for refugee support services",
    version="2.1.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global status tracking
service_status = {
    "database": "initializing",
    "search": "initializing",
    "start_time": datetime.now().isoformat()
}

# Request/Response models
class ChatQuery(BaseModel):
    message: str
    category: Optional[str] = None
    urgency: Optional[str] = None
    language: Optional[str] = None
    limit: int = 3
    user_id: Optional[str] = None
    context: Optional[Dict] = None

class VoiceflowResponse(BaseModel):
    success: bool
    message: str
    resources: List[Dict]
    quick_replies: Optional[List[str]] = None
    metadata: Optional[Dict] = None

# Initialize services with error handling
search_engine = None
config = None

def initialize_services():
    """Initialize services with graceful fallback"""
    global search_engine, config, service_status
    
    try:
        # Try to import and initialize the lightweight config
        logger.info("Attempting to initialize services...")
        
        # Use lightweight config for Railway
        from config_light import QdrantConfig
        config = QdrantConfig()
        service_status["database"] = "connected"
        logger.info("Database configuration loaded")
        
        # Try to import search engine
        from search_engine import SearchEngine
        search_engine = SearchEngine(config)
        service_status["search"] = "ready"
        logger.info("Search engine initialized")
        
    except ImportError as e:
        logger.warning(f"Import error during initialization: {e}")
        service_status["database"] = "import_error"
        service_status["search"] = "unavailable"
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        service_status["database"] = "error"
        service_status["search"] = "error"

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting API server...")
    initialize_services()
    logger.info(f"Service status: {service_status}")

# Health check endpoint - MUST be simple and always work
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "ACT Refugee Support API",
        "status": "online",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Simple health check that always returns 200"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check with component status"""
    uptime = (datetime.now() - datetime.fromisoformat(service_status["start_time"])).total_seconds()
    
    return {
        "status": "healthy",
        "service": "ACT Refugee Support API",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime,
        "components": {
            "api": "healthy",
            "database": service_status["database"],
            "search": service_status["search"]
        },
        "environment": {
            "railway": os.getenv("RAILWAY_ENVIRONMENT", "unknown"),
            "use_lightweight": os.getenv("USE_LIGHTWEIGHT", "true"),
            "port": os.getenv("PORT", "8000")
        }
    }

@app.post("/search", response_model=VoiceflowResponse)
async def search_resources(query: ChatQuery):
    """Main search endpoint with fallback responses"""
    try:
        # Check if search engine is available
        if not search_engine or service_status["search"] != "ready":
            # Return fallback response
            return VoiceflowResponse(
                success=True,
                message="I'm currently initializing. Here are some emergency contacts while I set up:",
                resources=[
                    {
                        "name": "Emergency Services",
                        "phone": "000",
                        "description": "For life-threatening emergencies",
                        "available": "24/7"
                    },
                    {
                        "name": "Translating and Interpreting Service",
                        "phone": "131 450",
                        "description": "Free telephone interpreting service",
                        "available": "24/7"
                    },
                    {
                        "name": "Lifeline Crisis Support",
                        "phone": "13 11 14",
                        "description": "Crisis support and suicide prevention",
                        "available": "24/7"
                    }
                ],
                quick_replies=["Emergency help", "Find services", "Speak my language"],
                metadata={"fallback": True}
            )
        
        # Use search engine if available
        from models import SearchQuery
        search_query = SearchQuery(
            query=query.message,
            limit=query.limit
        )
        
        results = search_engine.search(search_query)
        
        # Format results
        resources_formatted = []
        for result in results[:query.limit]:
            resource = result.resource if hasattr(result, 'resource') else result
            resources_formatted.append({
                "name": getattr(resource, 'name', 'Service'),
                "description": str(getattr(resource, 'description', ''))[:200],
                "phone": getattr(getattr(resource, 'contact', None), 'phone', 'Contact for info'),
                "website": getattr(getattr(resource, 'contact', None), 'website', ''),
                "services": ", ".join(getattr(resource, 'services_provided', [])[:3])
            })
        
        if resources_formatted:
            message = f"I found {len(resources_formatted)} services that can help:"
        else:
            message = "I couldn't find specific matches. Try different keywords or call 131 450 for help."
        
        return VoiceflowResponse(
            success=True,
            message=message,
            resources=resources_formatted,
            quick_replies=["Find more", "Emergency help", "Different search"],
            metadata={"results_count": len(resources_formatted)}
        )
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        # Return graceful error response
        return VoiceflowResponse(
            success=False,
            message="I'm having trouble searching right now. For immediate help, call 131 450 for interpreter services.",
            resources=[],
            quick_replies=["Try again", "Emergency contacts", "Help"],
            metadata={"error": str(e)}
        )

@app.post("/search/emergency")
async def search_emergency():
    """Emergency services endpoint - always returns critical contacts"""
    return VoiceflowResponse(
        success=True,
        message="⚠️ EMERGENCY SERVICES - Available 24/7:",
        resources=[
            {
                "name": "🚨 Emergency Services (Police, Fire, Ambulance)",
                "phone": "000",
                "description": "Life-threatening emergencies only",
                "available": "24/7",
                "urgency": "CRITICAL"
            },
            {
                "name": "📞 Telephone Interpreter Service",
                "phone": "131 450",
                "description": "Free interpreting in your language",
                "available": "24/7",
                "languages": "All languages"
            },
            {
                "name": "🏥 Health Direct",
                "phone": "1800 022 222",
                "description": "Non-emergency health advice",
                "available": "24/7",
                "urgency": "HIGH"
            },
            {
                "name": "💔 1800RESPECT",
                "phone": "1800 737 732",
                "description": "Domestic violence support",
                "available": "24/7",
                "urgency": "HIGH"
            },
            {
                "name": "🧠 Lifeline",
                "phone": "13 11 14",
                "description": "Crisis support and suicide prevention",
                "available": "24/7",
                "urgency": "HIGH"
            }
        ],
        quick_replies=["Call 000 now", "Find hospital", "Crisis counseling"],
        metadata={"type": "emergency", "critical": True}
    )

@app.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"message": "API is working", "timestamp": datetime.now().isoformat()}

# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "An error occurred",
        "message": "Please try again or contact support",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    
    # Log startup information
    logger.info(f"Starting Railway-optimized API server on port {port}")
    logger.info(f"Environment: {os.getenv('RAILWAY_ENVIRONMENT', 'local')}")
    logger.info(f"Lightweight mode: {os.getenv('USE_LIGHTWEIGHT', 'true')}")
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True
    )
