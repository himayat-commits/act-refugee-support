"""
Hybrid Smart Router for Voiceflow Integration
Optimal approach for ACT Refugee & Migrant Support Assistant
"""

import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.api.orchestrator import ContextAnalyzer, IntentClassifier

# Import existing components
from src.core.config import QdrantConfig
from src.search.simple import SimpleSearchEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ACT Refugee Support - Hybrid Smart Router",
    description="Optimal Voiceflow integration with intelligent routing",
    version="3.0.0",
)

# CORS configuration for Voiceflow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.himayat.com.au", "https://creator.voiceflow.com", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Data Models ====================


class QueryComplexity(str, Enum):
    EMERGENCY = "emergency"
    COMPLEX = "complex"
    MODERATE = "moderate"
    SIMPLE = "simple"


class VoiceflowRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    language: Optional[str] = "English"
    location: Optional[str] = "Canberra, ACT"
    context: Optional[Dict[str, Any]] = {}
    user_profile: Optional[Dict[str, Any]] = {}


class RouterResponse(BaseModel):
    success: bool
    routing_path: str
    message: str
    services: List[Dict]
    call_scripts: Optional[List[str]] = None
    quick_replies: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None
    conversation_context: Optional[Dict] = None
    metadata: Dict[str, Any]


# ==================== Smart Router ====================


class SmartRouter:
    """Intelligent request router with fallback mechanisms"""

    def __init__(self):
        self.config = QdrantConfig()
        self.simple_search = SimpleSearchEngine(self.config)
        self.intent_classifier = IntentClassifier()
        self.context_analyzer = ContextAnalyzer()
        self.emergency_contacts = self._load_emergency_contacts()

    def _load_emergency_contacts(self) -> Dict:
        """Load emergency contact information"""
        return {
            "police_fire_ambulance": {
                "number": "000",
                "description": "Emergency services - Police, Fire, Ambulance",
                "available": "24/7",
            },
            "crisis_support": {
                "number": "13 11 14",
                "description": "Lifeline - Crisis support and suicide prevention",
                "available": "24/7",
            },
            "domestic_violence": {
                "number": "1800 737 732",
                "description": "1800RESPECT - Domestic violence support",
                "available": "24/7",
            },
            "interpreter": {
                "number": "131 450",
                "description": "Translating and Interpreting Service",
                "available": "24/7",
            },
            "mental_health": {
                "number": "1800 648 911",
                "description": "Mental Health Crisis Line",
                "available": "24/7",
            },
        }

    async def analyze_complexity(self, request: VoiceflowRequest) -> QueryComplexity:
        """Determine query complexity for routing"""
        message_lower = request.query.lower()

        # Check for emergency indicators
        emergency_keywords = [
            "emergency",
            "urgent",
            "help now",
            "crisis",
            "000",
            "suicide",
            "violence",
            "danger",
            "hurt",
            "bleeding",
        ]
        if any(keyword in message_lower for keyword in emergency_keywords):
            return QueryComplexity.EMERGENCY

        # Check for complex multi-intent queries
        intent_indicators = 0
        if "and" in message_lower or "also" in message_lower:
            intent_indicators += 1
        if len(message_lower.split()) > 15:
            intent_indicators += 1
        if request.context and len(request.context) > 2:
            intent_indicators += 1

        if intent_indicators >= 2:
            return QueryComplexity.COMPLEX
        elif intent_indicators == 1:
            return QueryComplexity.MODERATE
        else:
            return QueryComplexity.SIMPLE

    async def route_request(self, request: VoiceflowRequest) -> RouterResponse:
        """Main routing logic with intelligent path selection"""
        try:
            # Analyze request complexity
            complexity = await self.analyze_complexity(request)
            logger.info(f"Request complexity: {complexity} for query: {request.query[:50]}...")

            # Route based on complexity
            if complexity == QueryComplexity.EMERGENCY:
                return await self.handle_emergency(request, complexity)
            elif complexity == QueryComplexity.COMPLEX:
                return await self.handle_complex_query(request, complexity)
            elif complexity == QueryComplexity.MODERATE:
                return await self.handle_moderate_query(request, complexity)
            else:
                return await self.handle_simple_query(request, complexity)

        except Exception as e:
            logger.error(f"Routing error: {e}")
            # Fallback to simple search
            return await self.fallback_handler(request, str(e))

    async def handle_emergency(self, request: VoiceflowRequest, complexity: QueryComplexity) -> RouterResponse:
        """Handle emergency requests with immediate response"""
        logger.info("Handling emergency request")

        # Get intent classification
        intent_data = await self.intent_classifier.classify(request.query)

        # Prepare emergency response
        emergency_services = []
        call_scripts = []

        # Add primary emergency contact
        emergency_services.append(
            {
                "name": "⚠️ EMERGENCY - CALL 000",
                "description": "For immediate police, fire, or ambulance assistance",
                "contact": "000",
                "urgency": "IMMEDIATE",
                "available": "24/7",
            }
        )

        # Add relevant crisis services based on query
        if "mental" in request.query.lower() or "suicide" in request.query.lower():
            emergency_services.append(
                {
                    "name": "Mental Health Crisis Line",
                    "description": "Immediate mental health support",
                    "contact": self.emergency_contacts["mental_health"]["number"],
                    "available": "24/7",
                }
            )
            call_scripts.append(
                "If calling 000: 'I need mental health crisis support. My location is [your location].'"
            )

        if "violence" in request.query.lower() or "abuse" in request.query.lower():
            emergency_services.append(
                {
                    "name": "Domestic Violence Support",
                    "description": "Confidential support for domestic violence",
                    "contact": self.emergency_contacts["domestic_violence"]["number"],
                    "available": "24/7",
                }
            )
            call_scripts.append("If unsafe to talk: Text 'HELP' to 0458 427 535")

        # Add interpreter service
        if request.language != "English":
            emergency_services.append(
                {
                    "name": "Interpreter Service",
                    "description": f"Free interpreting in {request.language}",
                    "contact": self.emergency_contacts["interpreter"]["number"],
                    "available": "24/7",
                }
            )
            call_scripts.append(f"Say: 'I need an interpreter for {request.language}'")

        # Search for additional relevant services
        search_results = self.simple_search.search(request.query, limit=2)
        for result in search_results:
            if result.get("emergency", False):
                emergency_services.append(result)

        return RouterResponse(
            success=True,
            routing_path="emergency_handler",
            message="🚨 EMERGENCY SUPPORT NEEDED - Here are immediate contacts:",
            services=emergency_services,
            call_scripts=call_scripts,
            quick_replies=["I am safe now", "I need more help", "Connect me to counselor", "Find nearest hospital"],
            next_steps=[
                "Call 000 immediately if in danger",
                "Save these emergency numbers",
                "Reach a safe location",
                "Tell someone you trust",
            ],
            metadata={
                "complexity": complexity.value,
                "intent": intent_data,
                "timestamp": datetime.now().isoformat(),
                "priority": "CRITICAL",
            },
        )

    async def handle_complex_query(self, request: VoiceflowRequest, complexity: QueryComplexity) -> RouterResponse:
        """Handle complex multi-intent queries with orchestration"""
        logger.info("Handling complex query with orchestration")

        try:
            # Use advanced intent classification
            intent_data = await self.intent_classifier.classify(request.query)
            context_data = await self.context_analyzer.analyze(request.dict())

            # Perform multiple searches for different aspects
            all_services = []

            # Primary search
            primary_results = self.simple_search.search(request.query, limit=3)
            all_services.extend(primary_results)

            # Context-based additional searches
            if context_data.get("patterns"):
                for pattern in context_data["patterns"]:
                    if pattern == "new_arrival":
                        arrival_results = self.simple_search.search(
                            "settlement services orientation English classes", limit=2
                        )
                        all_services.extend(arrival_results)
                    elif pattern == "family_needs":
                        family_results = self.simple_search.search("children school family support", limit=2)
                        all_services.extend(family_results)

            # Remove duplicates
            seen_ids = set()
            unique_services = []
            for service in all_services:
                if service.get("id") not in seen_ids:
                    seen_ids.add(service.get("id"))
                    unique_services.append(service)

            # Generate comprehensive response
            message = self._generate_complex_response_message(unique_services, intent_data, context_data)

            # Generate contextual quick replies
            quick_replies = self._generate_contextual_quick_replies(intent_data, context_data)

            return RouterResponse(
                success=True,
                routing_path="complex_orchestrator",
                message=message,
                services=unique_services[:5],  # Limit to top 5
                quick_replies=quick_replies,
                next_steps=self._generate_next_steps(unique_services, context_data),
                conversation_context={
                    "identified_needs": context_data.get("patterns", []),
                    "intent": intent_data["type"].value,
                    "previous_query": request.query,
                },
                metadata={
                    "complexity": complexity.value,
                    "intent": intent_data,
                    "context": context_data,
                    "timestamp": datetime.now().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Complex handler error: {e}")
            # Fallback to moderate handler
            return await self.handle_moderate_query(request, QueryComplexity.MODERATE)

    async def handle_moderate_query(self, request: VoiceflowRequest, complexity: QueryComplexity) -> RouterResponse:
        """Handle moderate complexity queries"""
        logger.info("Handling moderate query")

        # Perform enhanced search
        results = self.simple_search.search(request.query, limit=4)

        if results:
            message = f"I found {len(results)} services that can help with your needs:"

            # Add language note if applicable
            if request.language != "English":
                message += f"\n\n📌 Services with {request.language} support are highlighted."
        else:
            message = "I couldn't find exact matches, but here are some general support services:"
            # Get general services
            results = self.simple_search.search("support services assistance", limit=3)

        return RouterResponse(
            success=True,
            routing_path="moderate_handler",
            message=message,
            services=results,
            quick_replies=["Tell me more", "Different service", "How to contact", "Emergency help"],
            metadata={"complexity": complexity.value, "timestamp": datetime.now().isoformat()},
        )

    async def handle_simple_query(self, request: VoiceflowRequest, complexity: QueryComplexity) -> RouterResponse:
        """Handle simple queries with direct search"""
        logger.info("Handling simple query")

        # Direct search
        results = self.simple_search.search(request.query, limit=3)

        if results:
            message = "Here are services that can help:"
        else:
            message = "I couldn't find specific matches. Try describing what you need differently, or call 131 450 for interpreter assistance."
            results = []

        return RouterResponse(
            success=True,
            routing_path="simple_search",
            message=message,
            services=results,
            quick_replies=["More options", "Contact details", "Different search", "Speak to someone"],
            metadata={"complexity": complexity.value, "timestamp": datetime.now().isoformat()},
        )

    async def fallback_handler(self, request: VoiceflowRequest, error_context: str) -> RouterResponse:
        """Fallback handler when primary routes fail"""
        logger.warning(f"Using fallback handler due to: {error_context}")

        # Provide basic emergency contacts
        basic_services = [
            {
                "name": "Emergency Services",
                "description": "Police, Fire, Ambulance",
                "contact": "000",
                "available": "24/7",
            },
            {
                "name": "Interpreter Service",
                "description": "Free telephone interpreting",
                "contact": "131 450",
                "available": "24/7",
            },
            {"name": "Lifeline", "description": "Crisis support", "contact": "13 11 14", "available": "24/7"},
        ]

        return RouterResponse(
            success=True,
            routing_path="fallback",
            message="I'm having trouble processing your request, but here are essential services that are always available:",
            services=basic_services,
            quick_replies=["Try again", "Emergency help", "Call interpreter"],
            metadata={"complexity": "fallback", "error": error_context, "timestamp": datetime.now().isoformat()},
        )

    def _generate_complex_response_message(self, services: List[Dict], intent_data: Dict, context_data: Dict) -> str:
        """Generate comprehensive message for complex queries"""
        message_parts = []

        # Opening based on urgency
        if intent_data["urgency"] == "critical":
            message_parts.append("⚠️ I understand you need urgent help.")
        elif intent_data["urgency"] == "high":
            message_parts.append("I can see this is important to you.")
        else:
            message_parts.append("I understand you're looking for support.")

        # Add context-aware message
        if "new_arrival" in context_data.get("patterns", []):
            message_parts.append("As someone new to Australia, these services can help you settle:")
        elif "family_needs" in context_data.get("patterns", []):
            message_parts.append("For your family's needs, I recommend these services:")
        else:
            message_parts.append(f"Based on your needs, I found {len(services)} relevant services:")

        return " ".join(message_parts)

    def _generate_contextual_quick_replies(self, intent_data: Dict, context_data: Dict) -> List[str]:
        """Generate context-aware quick reply options"""
        replies = []

        # Add intent-specific replies
        intent_type = intent_data["type"].value
        if intent_type == "economic":
            replies.extend(["Job search help", "Skills recognition", "Training courses"])
        elif intent_type == "housing":
            replies.extend(["Emergency shelter", "Rental assistance", "Bond help"])
        elif intent_type == "health":
            replies.extend(["Find a doctor", "Mental health", "Hospital locations"])

        # Add pattern-specific replies
        if "language_barrier" in context_data.get("patterns", []):
            replies.append("Interpreter service")
        if "financial_stress" in context_data.get("patterns", []):
            replies.append("Financial assistance")

        # Always include these
        replies.extend(["Different help", "Emergency contacts"])

        return replies[:6]  # Limit to 6 quick replies

    def _generate_next_steps(self, services: List[Dict], context_data: Dict) -> List[str]:
        """Generate actionable next steps"""
        steps = []

        if services:
            # Add service-specific steps
            for service in services[:2]:
                if service.get("contact"):
                    steps.append(f"Call {service['name']} at {service['contact']}")

        # Add context-specific steps
        if "new_arrival" in context_data.get("patterns", []):
            steps.append("Register with Centrelink for support payments")
            steps.append("Enroll in free English classes")

        if "language_barrier" in context_data.get("patterns", []):
            steps.append("Save 131 450 for free interpreter service")

        # General steps
        steps.append("Save important contact numbers in your phone")

        return steps[:4]  # Limit to 4 steps


# ==================== Initialize Router ====================

router = SmartRouter()

# ==================== API Endpoints ====================


@app.get("/")
async def root():
    return {
        "service": "ACT Refugee Support - Smart Router",
        "status": "operational",
        "version": "3.0.0",
        "endpoints": ["/voiceflow", "/health", "/test"],
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        test_results = router.simple_search.search("test", limit=1)
        db_status = "connected" if test_results is not None else "error"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "error"

    return {
        "status": "healthy",
        "components": {
            "router": "operational",
            "database": db_status,
            "intent_classifier": "operational",
            "context_analyzer": "operational",
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/voiceflow")
async def voiceflow_endpoint(request: Dict):
    """Main Voiceflow integration endpoint"""
    try:
        # Convert Voiceflow format to our format
        voiceflow_request = VoiceflowRequest(
            query=request.get("query", request.get("message", "")),
            user_id=request.get("user_id"),
            session_id=request.get("session_id"),
            language=request.get("language", "English"),
            location=request.get("location", "Canberra, ACT"),
            context=request.get("context", {}),
            user_profile=request.get("user_profile", {}),
        )

        # Route the request
        response = await router.route_request(voiceflow_request)

        # Convert to Voiceflow response format
        return {
            "success": response.success,
            "message": response.message,
            "services": response.services,
            "buttons": response.quick_replies,  # Voiceflow uses 'buttons' for quick replies
            "next_steps": response.next_steps,
            "metadata": response.metadata,
        }

    except Exception as e:
        logger.error(f"Voiceflow endpoint error: {e}")
        return {
            "success": False,
            "message": "I'm having trouble processing your request. For immediate help, call 000 for emergencies or 131 450 for interpreter service.",
            "services": [],
            "buttons": ["Try again", "Emergency contacts"],
            "metadata": {"error": str(e)},
        }


@app.post("/test")
async def test_endpoint(request: VoiceflowRequest):
    """Test endpoint for debugging"""
    response = await router.route_request(request)
    return response


# ==================== Run Server ====================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security
    uvicorn.run(app, host=host, port=port)
