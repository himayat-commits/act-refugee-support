from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import os
from datetime import datetime
import logging

from config import QdrantConfig
from search_engine import SearchEngine
from search_economic_integration import EconomicIntegrationSearch
from models import SearchQuery, ResourceCategory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ACT Refugee Support API",
    description="API for Voiceflow integration with ACT Refugee & Migrant Support Database",
    version="1.0.0"
)

# Enable CORS for Voiceflow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Voiceflow domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Optional: Add authentication
security = HTTPBearer(auto_error=False)

# Initialize search engines
config = QdrantConfig()
search_engine = SearchEngine(config)
economic_search = EconomicIntegrationSearch(config)

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

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key if AUTH is enabled"""
    if os.getenv("ENABLE_AUTH", "false").lower() == "true":
        if not credentials or credentials.credentials != os.getenv("API_KEY"):
            raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return True

@app.get("/")
def root():
    return {
        "service": "ACT Refugee Support API",
        "status": "active",
        "endpoints": ["/health", "/search", "/search/emergency", "/search/economic", "/docs"]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ACT Refugee Support API",
        "timestamp": datetime.now().isoformat(),
        "database": "connected"
    }

@app.post("/search", response_model=VoiceflowResponse)
async def search_resources(
    query: ChatQuery,
    authenticated: bool = Depends(verify_api_key)
):
    """Main endpoint for Voiceflow to search resources"""
    try:
        logger.info(f"Search query received: {query.message[:100]}")
        
        # Detect intent from message
        intent = detect_intent(query.message)
        logger.info(f"Detected intent: {intent}")
        
        # Handle special intents
        if intent == "emergency":
            return await search_emergency()
        elif intent == "digital_help":
            return await search_digital_support(query)
        elif intent == "exploitation":
            return await search_exploitation_help(query)
        
        # Create search query
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
            
        # Perform search
        results = search_engine.search(search_query)
        
        # If no results, try economic integration search
        if not results and any(word in query.message.lower() for word in ["job", "work", "skill", "qualification", "business"]):
            return await search_economic_integration(query)
        
        # Format for Voiceflow
        resources_formatted = format_resources_for_voiceflow(results)
        
        # Generate response message
        if resources_formatted:
            message = f"I found {len(resources_formatted)} services that can help you:"
            
            # Add language-specific note if services available
            if query.language and query.language != "English":
                message += f"\n\n*Services available in {query.language} or with interpreter support are marked*"
        else:
            message = get_no_results_message(intent, query.language)
        
        # Add quick replies for common follow-ups
        quick_replies = generate_quick_replies(intent, len(resources_formatted))
        
        return VoiceflowResponse(
            success=True,
            message=message,
            resources=resources_formatted,
            quick_replies=quick_replies,
            metadata={
                "intent": intent,
                "results_count": len(resources_formatted),
                "search_timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search/emergency")
async def search_emergency(authenticated: bool = Depends(verify_api_key)):
    """Quick endpoint for emergency services"""
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

@app.post("/search/economic")
async def search_economic_integration(
    query: ChatQuery,
    authenticated: bool = Depends(verify_api_key)
):
    """Specialized endpoint for economic integration queries"""
    
    message_lower = query.message.lower()
    
    # Determine specific economic need
    if any(word in message_lower for word in ["skill", "qualification", "degree", "recognition"]):
        resources = economic_search.search_skill_underutilization_solutions(limit=query.limit)
        response_message = "Here are services to help recognize your qualifications:"
    elif any(word in message_lower for word in ["business", "entrepreneur", "startup", "loan"]):
        resources = economic_search.search_entrepreneurship_support(stage="startup", limit=query.limit)
        response_message = "Here are business and entrepreneurship support services:"
    elif any(word in message_lower for word in ["mentor", "network", "professional"]):
        resources = economic_search.search_mentoring_programs(limit=query.limit)
        response_message = "Here are mentoring and networking opportunities:"
    elif any(word in message_lower for word in ["training", "course", "certificate", "tafe"]):
        resources = economic_search.search_vocational_training(free_only=True, limit=query.limit)
        response_message = "Here are training opportunities (many are FREE):"
    else:
        resources = economic_search.search_career_pathways(limit=query.limit)
        response_message = "Here are employment and career services:"
    
    resources_formatted = []
    for resource in resources:
        resources_formatted.append({
            "name": resource.name,
            "description": resource.description[:200] + "...",
            "contact": resource.contact.phone or resource.contact.website,
            "services": ", ".join(resource.services_provided[:3]),
            "cost": resource.cost,
            "eligibility": resource.eligibility[:100] if resource.eligibility else "All migrants"
        })
    
    return VoiceflowResponse(
        success=True,
        message=response_message,
        resources=resources_formatted,
        quick_replies=["Skills assessment", "Start a business", "Free training", "Find a mentor", "Job search help"],
        metadata={"type": "economic_integration"}
    )

@app.post("/search/digital")
async def search_digital_support(
    query: ChatQuery,
    authenticated: bool = Depends(verify_api_key)
):
    """Handle digital literacy and online service queries"""
    search_query = SearchQuery(
        query="MyGov digital help computer internet online email Centrelink",
        limit=3
    )
    
    results = search_engine.search(search_query)
    resources_formatted = format_resources_for_voiceflow(results)
    
    return VoiceflowResponse(
        success=True,
        message="📱 Here's help with digital services and online systems:",
        resources=resources_formatted,
        quick_replies=["MyGov help", "Get free computer", "Internet access", "Email setup"],
        metadata={"type": "digital_support"}
    )

@app.post("/search/exploitation")
async def search_exploitation_help(
    query: ChatQuery,
    authenticated: bool = Depends(verify_api_key)
):
    """Handle workplace exploitation and rights queries"""
    search_query = SearchQuery(
        query="exploitation wage theft workplace rights underpaid unsafe work",
        limit=3
    )
    
    results = search_engine.search(search_query)
    resources_formatted = format_resources_for_voiceflow(results)
    
    # Add critical notice
    for resource in resources_formatted:
        resource["important"] = "⚠️ CONFIDENTIAL - No visa checks"
    
    return VoiceflowResponse(
        success=True,
        message="🔒 CONFIDENTIAL HELP - Your visa status will NOT be checked:",
        resources=resources_formatted,
        quick_replies=["Report anonymously", "Know my rights", "Recover wages", "Get legal help"],
        metadata={"type": "exploitation", "confidential": True}
    )

def format_resources_for_voiceflow(results) -> List[Dict]:
    """Format search results for Voiceflow display"""
    resources_formatted = []
    
    for i, result in enumerate(results):
        resource = result.resource if hasattr(result, 'resource') else result
        
        # Build formatted resource
        formatted = {
            "name": resource.name,
            "description": resource.description[:200] + "..." if len(resource.description) > 200 else resource.description,
            "phone": resource.contact.phone or "No phone",
            "website": resource.contact.website or "No website",
            "address": resource.contact.address or "Contact for address",
            "hours": resource.contact.hours or "Contact for hours",
            "services": ", ".join(resource.services_provided[:3]) if resource.services_provided else "Multiple services",
            "cost": resource.cost,
            "languages": ", ".join(resource.languages_available[:3]) if resource.languages_available else "English",
            "urgency": resource.urgency_level
        }
        
        # Add special markers
        if resource.urgency_level == "critical":
            formatted["name"] = "🚨 " + formatted["name"]
        elif resource.cost.lower() == "free":
            formatted["name"] = "✅ " + formatted["name"]
        
        resources_formatted.append(formatted)
    
    return resources_formatted

def detect_intent(message: str) -> str:
    """Enhanced intent detection based on keywords and patterns"""
    message_lower = message.lower()
    
    # Emergency intents
    if any(word in message_lower for word in ["emergency", "urgent", "help now", "crisis", "000", "police", "ambulance"]):
        return "emergency"
    
    # Digital/online help
    if any(word in message_lower for word in ["mygov", "online", "computer", "internet", "email", "digital", "website"]):
        return "digital_help"
    
    # Exploitation/rights
    if any(word in message_lower for word in ["exploitation", "underpaid", "wage theft", "unfair", "boss", "unsafe work"]):
        return "exploitation"
    
    # Employment/skills
    if any(word in message_lower for word in ["job", "work", "employment", "career", "skill", "qualification"]):
        return "employment"
    
    # Housing
    if any(word in message_lower for word in ["house", "housing", "rent", "accommodation", "homeless", "shelter"]):
        return "housing"
    
    # Language/education
    if any(word in message_lower for word in ["english", "language", "amep", "learn", "school", "education", "study"]):
        return "education"
    
    # Legal
    if any(word in message_lower for word in ["visa", "immigration", "lawyer", "legal", "citizenship", "passport"]):
        return "legal"
    
    # Healthcare
    if any(word in message_lower for word in ["doctor", "health", "medical", "hospital", "sick", "medicine", "mental"]):
        return "healthcare"
    
    # Financial
    if any(word in message_lower for word in ["money", "payment", "centrelink", "financial", "loan", "benefit"]):
        return "financial"
    
    # Family
    if any(word in message_lower for word in ["family", "parent", "children", "reunion", "sponsor"]):
        return "family"
    
    return "general"

def generate_quick_replies(intent: str, results_count: int) -> List[str]:
    """Generate contextual quick reply suggestions"""
    
    # Base quick replies
    base_replies = {
        "emergency": ["Call 000", "Find hospital", "Crisis support", "Safe place"],
        "digital_help": ["MyGov help", "Get computer", "Learn online", "Email setup"],
        "exploitation": ["Report anonymously", "Know my rights", "Get wages back", "Legal help"],
        "employment": ["Skills assessment", "Find job", "Start business", "Free training"],
        "housing": ["Emergency shelter", "Rental help", "Share house", "Bond assistance"],
        "education": ["English classes", "School enrollment", "Adult education", "University"],
        "legal": ["Visa help", "Free lawyer", "Immigration", "Work rights"],
        "healthcare": ["Find doctor", "Mental health", "Hospital", "Medicare"],
        "financial": ["Centrelink", "Emergency money", "No interest loan", "Budget help"],
        "family": ["Family reunion", "Parent visa", "Children services", "Parenting help"],
        "general": ["Emergency help", "New arrival", "Find services", "Speak my language"]
    }
    
    quick_replies = base_replies.get(intent, base_replies["general"])
    
    # Add contextual replies based on results
    if results_count == 0:
        quick_replies.append("Try another search")
    elif results_count < 3:
        quick_replies.append("Show more options")
    
    return quick_replies[:4]  # Limit to 4 for Voiceflow display

def get_no_results_message(intent: str, language: Optional[str]) -> str:
    """Get appropriate no-results message based on context"""
    
    base_message = "I couldn't find specific services matching your search. "
    
    # Add intent-specific guidance
    intent_messages = {
        "emergency": "For emergencies, call 000 immediately. For crisis support, call Lifeline on 13 11 14.",
        "digital_help": "Visit your local library for free computer and internet access.",
        "employment": "Contact Centrelink on 13 28 50 for employment services.",
        "housing": "Call Homelessness Australia on 1800 326 713 for immediate housing help.",
        "general": "Try searching with different words or call 131 450 for help in your language."
    }
    
    return base_message + intent_messages.get(intent, intent_messages["general"])

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)