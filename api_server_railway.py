"""
Railway-optimized API Server
Handles all imports conditionally and provides graceful fallbacks
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import os
import sys
from datetime import datetime
import logging
import time

# Set up logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Try to import enhanced modules, but don't fail if they're not available
try:
    from error_handler import CustomLogger, ErrorCategory, APIErrorResponse, PerformanceMonitor
    enhanced_logging = True
    custom_logger = CustomLogger("api_server")
    perf_monitor = PerformanceMonitor(custom_logger)
except ImportError as e:
    logger.warning(f"Enhanced error handling not available: {e}")
    enhanced_logging = False
    custom_logger = None
    perf_monitor = None

try:
    from cache_manager import get_cache_manager, cache_result, RateLimiter
    cache_enabled = True
    cache_manager = get_cache_manager()
    rate_limiter = RateLimiter(cache_manager)
except ImportError as e:
    logger.warning(f"Caching not available: {e}")
    cache_enabled = False
    cache_manager = None
    rate_limiter = None

# Use lightweight config for Railway
if os.getenv("USE_LIGHTWEIGHT", "true").lower() == "true":
    from config_light import QdrantConfig
else:
    from config import QdrantConfig

# Import core modules
from search_engine import SearchEngine
from search_economic_integration import EconomicIntegrationSearch
from models import SearchQuery, ResourceCategory

# Initialize FastAPI app
app = FastAPI(
    title="ACT Refugee Support API",
    description="API for Voiceflow integration with ACT Refugee & Migrant Support Database",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication
security = HTTPBearer(auto_error=False)

# Initialize search engines with error handling
try:
    config = QdrantConfig()
    search_engine = SearchEngine(config)
    economic_search = EconomicIntegrationSearch(config)
    logger.info("Search engines initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize search engines: {e}")
    # Create mock search engines for health checks
    search_engine = None
    economic_search = None

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

# Middleware for performance monitoring
@app.middleware("http")
async def add_process_time_header(request, call_next):
    """Add performance monitoring to all requests"""
    start_time = time.time()
    
    # Get client IP for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    
    # Check rate limit if available
    if rate_limiter:
        if not rate_limiter.check_rate_limit(client_ip, limit=60, window=60):
            if enhanced_logging:
                return APIErrorResponse.rate_limit_exceeded(retry_after=60)
            else:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Process request
    response = await call_next(request)
    
    # Log performance
    process_time = (time.time() - start_time) * 1000
    response.headers["X-Process-Time"] = str(process_time)
    
    if perf_monitor:
        perf_monitor.check_api_performance(str(request.url.path), process_time)
    
    if enhanced_logging and custom_logger:
        custom_logger.log_api_request(
            method=request.method,
            path=str(request.url.path),
            status_code=response.status_code,
            duration_ms=process_time
        )
    
    return response

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key if AUTH is enabled"""
    if os.getenv("ENABLE_AUTH", "false").lower() == "true":
        if not credentials or credentials.credentials != os.getenv("API_KEY"):
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": "ACT Refugee Support API",
        "version": "2.0.0",
        "status": "active",
        "endpoints": ["/health", "/search", "/search/emergency", "/search/economic", "/docs"],
        "features": {
            "caching": cache_enabled,
            "enhanced_logging": enhanced_logging,
            "rate_limiting": rate_limiter is not None
        }
    }

@app.get("/health")
def health_check():
    """Health check endpoint with detailed status"""
    health_status = {
        "status": "healthy",
        "service": "ACT Refugee Support API",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "api": "healthy",
            "search_engine": "healthy" if search_engine else "unavailable",
            "cache": "healthy" if cache_enabled else "disabled",
            "logging": "enhanced" if enhanced_logging else "basic"
        }
    }
    
    # Add cache stats if available
    if cache_manager:
        try:
            health_status["cache_stats"] = cache_manager.get_stats()
        except:
            pass
    
    return health_status

@app.post("/search", response_model=VoiceflowResponse)
async def search_resources(
    query: ChatQuery,
    authenticated: bool = Depends(verify_api_key)
):
    """Main search endpoint with caching and error handling"""
    start_time = time.time()
    
    try:
        # Check if search engine is available
        if not search_engine:
            raise HTTPException(
                status_code=503,
                detail="Search service temporarily unavailable"
            )
        
        # Log query if enhanced logging is available
        if enhanced_logging and custom_logger:
            custom_logger.log_search_query(
                query=query.message,
                results_count=0,  # Will update later
                duration_ms=0,
                user_id=query.user_id
            )
        
        # Check cache first
        if cache_manager:
            cached_results = cache_manager.get_cached_search(
                query.message, 
                "act_refugee_resources", 
                query.limit
            )
            if cached_results:
                logger.info("Returning cached search results")
                return VoiceflowResponse(
                    success=True,
                    message="Here are the cached results:",
                    resources=cached_results[:query.limit],
                    quick_replies=generate_quick_replies("general", len(cached_results)),
                    metadata={"cached": True}
                )
        
        # Detect intent
        intent = detect_intent(query.message)
        logger.info(f"Detected intent: {intent}")
        
        # Perform search
        search_query = SearchQuery(
            query=query.message,
            limit=query.limit
        )
        
        if query.category:
            try:
                search_query.categories = [ResourceCategory(query.category)]
            except:
                logger.warning(f"Invalid category: {query.category}")
        
        if query.urgency:
            search_query.urgency = query.urgency
        
        # Execute search
        results = search_engine.search(search_query)
        
        # Format results
        resources_formatted = format_resources_for_voiceflow(results)
        
        # Cache results if caching is enabled
        if cache_manager and resources_formatted:
            cache_manager.cache_search_results(
                query.message,
                "act_refugee_resources",
                query.limit,
                resources_formatted
            )
        
        # Generate response
        if resources_formatted:
            message = f"I found {len(resources_formatted)} services that can help you:"
        else:
            message = get_no_results_message(intent, query.language)
        
        # Track performance
        duration_ms = (time.time() - start_time) * 1000
        if perf_monitor:
            perf_monitor.check_query_performance(query.message, duration_ms)
        
        return VoiceflowResponse(
            success=True,
            message=message,
            resources=resources_formatted,
            quick_replies=generate_quick_replies(intent, len(resources_formatted)),
            metadata={
                "intent": intent,
                "results_count": len(resources_formatted),
                "search_timestamp": datetime.now().isoformat(),
                "duration_ms": duration_ms
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        if enhanced_logging and custom_logger:
            custom_logger.log_error(e, category=ErrorCategory.API_ERROR)
        
        if enhanced_logging:
            return APIErrorResponse.internal_error(request_id=str(time.time()))
        else:
            raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/search/emergency")
async def search_emergency(authenticated: bool = Depends(verify_api_key)):
    """Emergency search endpoint"""
    if not search_engine:
        raise HTTPException(status_code=503, detail="Service unavailable")
    
    try:
        urgent_services = search_engine.search_urgent_services(limit=5)
        
        resources_formatted = []
        for resource in urgent_services:
            resources_formatted.append({
                "name": f"🚨 {resource.name}",
                "phone": resource.contact.phone,
                "available": resource.contact.hours,
                "description": resource.description[:150],
                "urgency": resource.urgency_level,
                "languages": ", ".join(resource.languages_available[:3])
            })
        
        return VoiceflowResponse(
            success=True,
            message="⚠️ EMERGENCY SERVICES - Available 24/7:",
            resources=resources_formatted,
            quick_replies=["Call 000 now", "Find hospital", "Crisis counseling", "Domestic violence help"],
            metadata={"type": "emergency", "critical": True}
        )
    except Exception as e:
        logger.error(f"Emergency search error: {e}")
        raise HTTPException(status_code=500, detail="Emergency search failed")

# Helper functions
def detect_intent(message: str) -> str:
    """Detect user intent from message"""
    message_lower = message.lower()
    
    if any(word in message_lower for word in ["emergency", "urgent", "help now", "crisis"]):
        return "emergency"
    elif any(word in message_lower for word in ["job", "work", "employment", "career"]):
        return "employment"
    elif any(word in message_lower for word in ["house", "housing", "accommodation", "shelter"]):
        return "housing"
    elif any(word in message_lower for word in ["english", "language", "amep", "learn"]):
        return "education"
    elif any(word in message_lower for word in ["visa", "immigration", "lawyer", "legal"]):
        return "legal"
    elif any(word in message_lower for word in ["doctor", "health", "medical", "hospital"]):
        return "healthcare"
    else:
        return "general"

def format_resources_for_voiceflow(results) -> List[Dict]:
    """Format search results for Voiceflow"""
    if not results:
        return []
    
    resources_formatted = []
    for result in results[:10]:  # Limit to 10 results
        resource = result.resource if hasattr(result, 'resource') else result
        
        formatted = {
            "name": resource.name if hasattr(resource, 'name') else "Unknown Service",
            "description": str(resource.description)[:200] + "..." if hasattr(resource, 'description') else "",
            "phone": getattr(resource.contact, 'phone', "No phone") if hasattr(resource, 'contact') else "No phone",
            "website": getattr(resource.contact, 'website', "") if hasattr(resource, 'contact') else "",
            "services": ", ".join(resource.services_provided[:3]) if hasattr(resource, 'services_provided') else "",
            "cost": getattr(resource, 'cost', "Contact for pricing")
        }
        
        resources_formatted.append(formatted)
    
    return resources_formatted

def generate_quick_replies(intent: str, results_count: int) -> List[str]:
    """Generate quick reply suggestions"""
    base_replies = {
        "emergency": ["Call 000", "Find hospital", "Crisis support"],
        "employment": ["Skills assessment", "Find job", "Free training"],
        "housing": ["Emergency shelter", "Rental help", "Share house"],
        "general": ["Emergency help", "Find services", "Speak my language"]
    }
    
    return base_replies.get(intent, base_replies["general"])[:3]

def get_no_results_message(intent: str, language: Optional[str]) -> str:
    """Get appropriate no-results message"""
    messages = {
        "emergency": "For emergencies, call 000 immediately.",
        "employment": "Contact Centrelink on 13 28 50 for employment services.",
        "housing": "Call Homelessness Australia on 1800 326 713 for housing help.",
        "general": "Try searching with different words or call 131 450 for help in your language."
    }
    
    return "I couldn't find specific services. " + messages.get(intent, messages["general"])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
