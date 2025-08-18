"""
Event-Driven Microservices Architecture for ACT Refugee Support API
Orchestrator and core services implementation for Voiceflow integration
"""

import asyncio
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.core.config import QdrantConfig

# Import existing components
from src.search.simple import SimpleSearchEngine

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="ACT Refugee Support API v2 - Orchestrated",
    description="Event-driven microservices architecture for Voiceflow integration",
    version="2.0.0",
)

# Enable CORS for Voiceflow
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify Voiceflow domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================
# Data Models
# ====================


class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    STANDARD = "standard"
    LOW = "low"


class IntentType(str, Enum):
    EMERGENCY = "emergency"
    EXPLOITATION = "exploitation"
    DIGITAL_HELP = "digital_help"
    ECONOMIC = "economic"
    HOUSING = "housing"
    HEALTH = "health"
    LEGAL = "legal"
    EDUCATION = "education"
    FAMILY = "family"
    GENERAL = "general"


class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = None
    language: Optional[str] = "English"
    location: Optional[str] = "Canberra"
    context: Optional[Dict[str, Any]] = {}
    user_profile: Optional[Dict[str, Any]] = {}


class ServiceInfo(BaseModel):
    name: str
    description: str
    phone: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    hours: Optional[str] = None
    languages: Optional[List[str]] = None
    services_provided: Optional[List[str]] = None
    eligibility: Optional[str] = None
    cost: Optional[str] = "Free"
    urgency_indicator: Optional[bool] = False


class OrchestrationResponse(BaseModel):
    success: bool
    message: str
    services: List[Dict]
    call_scripts: Optional[List[str]] = None
    quick_replies: Optional[List[str]] = None
    next_steps: Optional[List[str]] = None
    metadata: Dict[str, Any]


# ====================
# Intent Classifier
# ====================


class IntentClassifier:
    """Classifies user intent from message"""

    def __init__(self):
        self.emergency_keywords = [
            "emergency",
            "urgent",
            "help now",
            "crisis",
            "000",
            "police",
            "ambulance",
            "fire",
            "suicide",
            "danger",
            "domestic violence",
            "assault",
            "hurt",
            "bleeding",
        ]

        self.exploitation_keywords = [
            "exploitation",
            "underpaid",
            "wage theft",
            "unfair",
            "boss",
            "unsafe work",
            "employer",
            "not paid",
            "rights",
        ]

        self.digital_keywords = [
            "mygov",
            "online",
            "computer",
            "internet",
            "email",
            "digital",
            "website",
            "centrelink",
            "app",
            "phone",
        ]

        self.economic_keywords = [
            "job",
            "work",
            "employment",
            "career",
            "skill",
            "qualification",
            "business",
            "entrepreneur",
            "training",
        ]

        self.housing_keywords = [
            "house",
            "housing",
            "rent",
            "accommodation",
            "homeless",
            "shelter",
            "eviction",
            "tenant",
            "lease",
        ]

    async def classify(self, message: str) -> Dict:
        """Classify message intent and urgency"""
        message_lower = message.lower()

        # Check for emergency first
        is_emergency = any(keyword in message_lower for keyword in self.emergency_keywords)

        # Determine primary intent
        if is_emergency:
            intent_type = IntentType.EMERGENCY
            urgency = UrgencyLevel.CRITICAL
            confidence = 0.95
        elif any(keyword in message_lower for keyword in self.exploitation_keywords):
            intent_type = IntentType.EXPLOITATION
            urgency = UrgencyLevel.HIGH
            confidence = 0.9
        elif any(keyword in message_lower for keyword in self.digital_keywords):
            intent_type = IntentType.DIGITAL_HELP
            urgency = UrgencyLevel.STANDARD
            confidence = 0.85
        elif any(keyword in message_lower for keyword in self.economic_keywords):
            intent_type = IntentType.ECONOMIC
            urgency = UrgencyLevel.STANDARD
            confidence = 0.85
        elif any(keyword in message_lower for keyword in self.housing_keywords):
            intent_type = IntentType.HOUSING
            urgency = UrgencyLevel.HIGH if "homeless" in message_lower else UrgencyLevel.STANDARD
            confidence = 0.85
        else:
            intent_type = IntentType.GENERAL
            urgency = UrgencyLevel.STANDARD
            confidence = 0.7

        return {
            "type": intent_type,
            "is_emergency": is_emergency,
            "urgency": urgency,
            "confidence": confidence,
            "boost_factors": self._get_boost_factors(message_lower),
        }

    def _get_boost_factors(self, message: str) -> Dict:
        """Get search boost factors based on message content"""
        factors = {}

        if "free" in message or "no cost" in message:
            factors["free_services"] = 2.0

        if "today" in message or "now" in message:
            factors["immediate_availability"] = 1.5

        if "near" in message or "close" in message:
            factors["location_proximity"] = 1.5

        return factors


# ====================
# Context Analyzer
# ====================


class ContextAnalyzer:
    """Analyzes conversation context and predicts needs"""

    def __init__(self):
        self.pattern_rules = {
            "new_arrival": ["just arrived", "new to", "recently came", "first time"],
            "family_needs": ["children", "family", "kids", "spouse", "wife", "husband"],
            "financial_stress": ["no money", "can't afford", "expensive", "cost", "free"],
            "isolation": ["alone", "lonely", "no friends", "isolated", "depressed"],
            "language_barrier": ["don't speak", "english difficult", "translator", "interpreter"],
        }

    async def analyze(self, request: Dict) -> Dict:
        """Analyze request context and hidden needs"""
        message = request.get("message", "").lower()
        user_profile = request.get("user_profile", {})
        context = request.get("context", {})

        # Detect patterns
        patterns = self._detect_patterns(message)

        # Predict hidden needs
        hidden_needs = await self._predict_hidden_needs(patterns, user_profile)

        # Calculate urgency
        urgency = self._calculate_urgency(message, patterns)

        # Determine conversation stage
        conversation_stage = self._determine_stage(context.get("conversation_history", []))

        return {
            "patterns": patterns,
            "hidden_needs": hidden_needs,
            "urgency": urgency,
            "conversation_stage": conversation_stage,
            "user_situation": self._analyze_situation(patterns, hidden_needs),
        }

    def _detect_patterns(self, message: str) -> List[str]:
        """Detect patterns in user message"""
        detected = []

        for pattern_name, keywords in self.pattern_rules.items():
            if any(keyword in message for keyword in keywords):
                detected.append(pattern_name)

        return detected

    async def _predict_hidden_needs(self, patterns: List[str], user_profile: Dict) -> List[Dict]:
        """Predict additional needs based on patterns"""
        hidden_needs = []

        if "new_arrival" in patterns:
            hidden_needs.extend(
                [
                    {"type": "medicare", "label": "Medicare registration"},
                    {"type": "bank", "label": "Bank account setup"},
                    {"type": "school", "label": "School enrollment"},
                ]
            )

        if "family_needs" in patterns:
            hidden_needs.extend(
                [
                    {"type": "childcare", "label": "Childcare services"},
                    {"type": "family_support", "label": "Family support groups"},
                    {"type": "parenting", "label": "Parenting resources"},
                ]
            )

        if "financial_stress" in patterns:
            hidden_needs.extend(
                [
                    {"type": "emergency_relief", "label": "Emergency financial aid"},
                    {"type": "food_bank", "label": "Food assistance"},
                    {"type": "vouchers", "label": "Essential item vouchers"},
                ]
            )

        if "isolation" in patterns:
            hidden_needs.extend(
                [
                    {"type": "community", "label": "Community groups"},
                    {"type": "mental_health", "label": "Mental health support"},
                    {"type": "social", "label": "Social activities"},
                ]
            )

        return hidden_needs

    def _calculate_urgency(self, message: str, patterns: List[str]) -> str:
        """Calculate message urgency level"""
        if any(word in message for word in ["emergency", "urgent", "now", "immediately"]):
            return UrgencyLevel.CRITICAL
        elif any(word in message for word in ["today", "tonight", "eviction", "no food"]):
            return UrgencyLevel.HIGH
        elif "financial_stress" in patterns or "isolation" in patterns:
            return UrgencyLevel.STANDARD
        else:
            return UrgencyLevel.LOW

    def _determine_stage(self, history: List) -> str:
        """Determine conversation stage"""
        if not history:
            return "greeting"
        elif len(history) == 1:
            return "needs_assessment"
        elif len(history) < 5:
            return "service_matching"
        else:
            return "follow_up"

    def _analyze_situation(self, patterns: List[str], hidden_needs: List[Dict]) -> str:
        """Analyze overall user situation"""
        if len(patterns) >= 3:
            return "complex_needs"
        elif "new_arrival" in patterns:
            return "new_arrival_support"
        elif "financial_stress" in patterns:
            return "financial_assistance"
        elif hidden_needs:
            return "multiple_needs"
        else:
            return "standard_query"


# ====================
# Emergency Handler
# ====================


class EmergencyHandler:
    """Handles emergency situations with immediate response"""

    def __init__(self):
        self.emergency_services = {
            "general": {
                "name": "🚨 Emergency Services (000)",
                "phone": "000",
                "description": "Police, Fire, Ambulance - Life threatening emergencies",
                "available": "24/7",
                "languages": "All languages via interpreter",
            },
            "crisis": {
                "name": "🚨 Lifeline Crisis Support",
                "phone": "13 11 14",
                "description": "Crisis support and suicide prevention",
                "available": "24/7",
                "languages": "English (interpreter available)",
            },
            "domestic_violence": {
                "name": "🚨 1800RESPECT",
                "phone": "1800 737 732",
                "description": "Domestic violence support and counseling",
                "available": "24/7",
                "languages": "Multiple languages",
            },
            "mental_health": {
                "name": "🚨 Mental Health Crisis Team",
                "phone": "1800 648 911",
                "description": "ACT mental health crisis support",
                "available": "24/7",
                "languages": "Interpreter available",
            },
            "child_protection": {
                "name": "🚨 Child Protection",
                "phone": "1300 556 729",
                "description": "Report child abuse or get help",
                "available": "24/7",
                "languages": "Interpreter available",
            },
        }

    async def handle(self, request: Dict, intent: Dict, context: Dict) -> Dict:
        """Handle emergency request"""
        emergency_type = self._classify_emergency(request["message"])

        # Get immediate services
        immediate_services = self._get_immediate_services(emergency_type)

        # Generate immediate action steps
        action_steps = self._generate_immediate_actions(emergency_type)

        # Generate call scripts
        call_scripts = self._generate_call_scripts(immediate_services, request.get("language", "English"))

        return {
            "type": emergency_type,
            "services": immediate_services,
            "immediate_actions": action_steps,
            "call_scripts": call_scripts,
            "follow_up": self._get_follow_up_services(emergency_type),
        }

    def _classify_emergency(self, message: str) -> str:
        """Classify type of emergency"""
        message_lower = message.lower()

        if any(word in message_lower for word in ["suicide", "kill myself", "end my life"]):
            return "suicide"
        elif any(word in message_lower for word in ["domestic", "violence", "abuse", "hit", "hurt me"]):
            return "domestic_violence"
        elif any(word in message_lower for word in ["child", "kids", "danger"]):
            return "child_protection"
        elif any(word in message_lower for word in ["mental", "breakdown", "panic", "anxiety"]):
            return "mental_health"
        else:
            return "general"

    def _get_immediate_services(self, emergency_type: str) -> List[Dict]:
        """Get immediate emergency services"""
        services = []

        # Always include 000
        services.append(self.emergency_services["general"])

        # Add specific service
        if emergency_type in self.emergency_services:
            services.append(self.emergency_services[emergency_type])

        # Add crisis support
        if emergency_type in ["suicide", "mental_health"]:
            services.append(self.emergency_services["crisis"])

        return services

    def _generate_immediate_actions(self, emergency_type: str) -> List[str]:
        """Generate immediate action steps"""
        if emergency_type == "general":
            return [
                "Call 000 immediately",
                "Stay safe and wait for help",
                "If you need an interpreter, say your language after connecting",
            ]
        elif emergency_type == "domestic_violence":
            return [
                "Go to a safe place immediately",
                "Call 000 if in immediate danger",
                "Call 1800 737 732 for confidential support",
                "Do not delete this conversation - you may need evidence",
            ]
        elif emergency_type == "suicide":
            return [
                "You are not alone - help is available",
                "Call 13 11 14 to speak with someone now",
                "Go to nearest hospital emergency if in immediate danger",
                "Text or online chat available if you can't call",
            ]
        else:
            return [
                "Call the emergency number provided",
                "Explain your situation clearly",
                "Ask for an interpreter if needed",
            ]

    def _generate_call_scripts(self, services: List[Dict], language: str) -> List[str]:
        """Generate scripts for calling services"""
        scripts = []

        if language != "English":
            scripts.append(f"I need an interpreter for {language}")

        scripts.extend(
            ["I need emergency help", "My location is [your address]", "I am a refugee/migrant and need assistance"]
        )

        return scripts

    def _get_follow_up_services(self, emergency_type: str) -> List[str]:
        """Get follow-up services after emergency"""
        if emergency_type == "domestic_violence":
            return ["Legal aid", "Safe housing", "Counseling services"]
        elif emergency_type == "mental_health":
            return ["Ongoing counseling", "Support groups", "Mental health plan"]
        else:
            return ["Medical follow-up", "Support services", "Community assistance"]


# ====================
# Search Engine Wrapper
# ====================


class SearchEngineWrapper:
    """Wraps search functionality with intent-specific filtering"""

    def __init__(self):
        config = QdrantConfig()
        self.simple_search = SimpleSearchEngine(config)

    async def search_general(self, query: str, context: Dict, boost: Dict) -> List[Dict]:
        """General search with boost factors"""
        results = self.simple_search.search(query, limit=5)
        return self._format_results(results)

    async def search_confidential(self, query: str, context: Dict) -> List[Dict]:
        """Search for confidential/exploitation services"""
        # Add exploitation-related terms to query
        enhanced_query = f"{query} exploitation rights legal confidential wage"
        results = self.simple_search.search(enhanced_query, limit=3)

        # Mark as confidential
        formatted = self._format_results(results)
        for service in formatted:
            service["confidential"] = True
            service["note"] = "🔒 Your visa will NOT be checked"

        return formatted

    async def search_digital_support(self, query: str, context: Dict) -> List[Dict]:
        """Search for digital support services"""
        enhanced_query = f"{query} computer digital online MyGov internet help"
        results = self.simple_search.search(enhanced_query, limit=3)
        return self._format_results(results)

    def _format_results(self, results: List) -> List[Dict]:
        """Format search results"""
        formatted = []

        for result in results:
            if isinstance(result, dict):
                formatted.append(
                    {
                        "name": result.get("name", "Unknown Service"),
                        "description": result.get("description", ""),
                        "phone": result.get("contact", ""),
                        "website": result.get("website", ""),
                        "location": result.get("location", "Canberra"),
                        "hours": result.get("hours", "Contact for hours"),
                        "languages": result.get("languages", ["English"]),
                        "services_provided": result.get("services", "").split(",")[:3],
                        "cost": "Free" if "free" in result.get("description", "").lower() else "Contact for cost",
                        "eligibility": result.get("eligibility", "All welcome"),
                    }
                )

        return formatted


# ====================
# Response Formatter
# ====================


class ResponseFormatter:
    """Formats responses for Voiceflow consumption"""

    def __init__(self):
        self.quick_reply_templates = {
            IntentType.EMERGENCY: ["Call 000 now", "Crisis counseling", "Find hospital", "Get safe housing"],
            IntentType.EXPLOITATION: ["Report anonymously", "Know my rights", "Recover wages", "Get legal help"],
            IntentType.DIGITAL_HELP: ["MyGov help", "Get free computer", "Internet access", "Learn computer skills"],
            IntentType.ECONOMIC: ["Find jobs", "Skills assessment", "Start business", "Free training"],
            IntentType.HOUSING: ["Emergency shelter", "Rental assistance", "Housing application", "Tenant rights"],
        }

    async def format(
        self, services: List[Dict], suggestions: List[Dict], intent: Dict, context: Dict, language: str
    ) -> Dict:
        """Format complete response"""

        # Generate message
        message = self._generate_message(
            intent=intent, services_count=len(services), urgency=context.get("urgency"), language=language
        )

        # Format services for display
        formatted_services = self._format_services(services, language)

        # Create call scripts
        call_scripts = self._create_call_scripts(services=formatted_services[:3], language=language)

        # Generate quick replies
        quick_replies = self._generate_quick_replies(intent=intent, suggestions=suggestions)

        # Generate next steps
        next_steps = self._generate_next_steps(services, context)

        return {
            "success": True,
            "message": message,
            "services": formatted_services,
            "call_scripts": call_scripts,
            "quick_replies": quick_replies,
            "next_steps": next_steps,
            "metadata": {
                "intent": intent["type"],
                "confidence": intent["confidence"],
                "urgency": context.get("urgency"),
                "hidden_needs": context.get("hidden_needs", []),
                "method": "event_driven_orchestration",
                "timestamp": datetime.now().isoformat(),
            },
        }

    async def format_emergency(self, emergency_data: Dict, language: str) -> Dict:
        """Format emergency response"""
        return {
            "success": True,
            "message": "⚠️ EMERGENCY - Immediate help available:",
            "services": emergency_data["services"],
            "call_scripts": emergency_data["call_scripts"],
            "quick_replies": ["Call 000", "I'm safe now", "Need interpreter", "Other help"],
            "next_steps": emergency_data["immediate_actions"],
            "metadata": {
                "intent": IntentType.EMERGENCY,
                "urgency": UrgencyLevel.CRITICAL,
                "emergency_type": emergency_data["type"],
                "method": "emergency_handler",
                "timestamp": datetime.now().isoformat(),
            },
        }

    def _generate_message(self, intent: Dict, services_count: int, urgency: str, language: str) -> str:
        """Generate appropriate message based on context"""

        if urgency == UrgencyLevel.CRITICAL:
            return "⚠️ This is urgent. Here's immediate help:"
        elif intent["type"] == IntentType.EXPLOITATION:
            return "🔒 CONFIDENTIAL HELP - Your visa status will NOT be checked:"
        elif services_count == 0:
            return "I couldn't find exact matches, but here are services that might help:"
        elif services_count == 1:
            return "I found one service that can help you:"
        else:
            return f"I found {services_count} services that can help you:"

    def _format_services(self, services: List[Dict], language: str) -> List[Dict]:
        """Format services for display"""
        formatted = []

        for service in services[:5]:  # Limit to 5 services
            formatted_service = {
                "name": service.get("name", "Unknown Service"),
                "description": service.get("description", "")[:200],
                "phone": service.get("phone", "Contact for details"),
                "website": service.get("website", ""),
                "location": service.get("location", "Canberra"),
                "hours": service.get("hours", "Contact for hours"),
                "languages": service.get("languages", ["English"]),
                "cost": service.get("cost", "Contact for cost"),
            }

            # Add visual indicators
            if service.get("confidential"):
                formatted_service["name"] = "🔒 " + formatted_service["name"]
            elif service.get("urgency_indicator"):
                formatted_service["name"] = "🚨 " + formatted_service["name"]
            elif "free" in service.get("cost", "").lower():
                formatted_service["name"] = "✅ " + formatted_service["name"]

            formatted.append(formatted_service)

        return formatted

    def _create_call_scripts(self, services: List[Dict], language: str) -> List[str]:
        """Create call scripts for services"""
        scripts = []

        if language != "English":
            scripts.append(f"Hello, I need help in {language}")

        for service in services:
            script = f"Hello, I'm calling about {service['name'].replace('🔒', '').replace('✅', '').replace('🚨', '').strip()}"
            scripts.append(script)

        scripts.append("I am a refugee/migrant and need assistance")

        return scripts[:5]  # Limit to 5 scripts

    def _generate_quick_replies(self, intent: Dict, suggestions: List[Dict]) -> List[str]:
        """Generate quick reply options"""

        # Get template replies for intent
        template = self.quick_reply_templates.get(
            intent["type"], ["Tell me more", "Other services", "Emergency help", "Start over"]
        )

        # Add suggestions if available
        if suggestions:
            suggestion_labels = [s["label"] for s in suggestions[:2]]
            return template[:2] + suggestion_labels

        return template

    def _generate_next_steps(self, services: List[Dict], context: Dict) -> List[str]:
        """Generate next steps for user"""
        steps = []

        if context.get("urgency") == UrgencyLevel.CRITICAL:
            steps.append("Call emergency services immediately")

        if services:
            steps.append(f"Call {services[0]['name']} first")
            steps.append("Save these contact numbers")

        if context.get("hidden_needs"):
            steps.append("Consider getting help with related needs")

        steps.append("Ask for an interpreter if needed")

        return steps[:4]  # Limit to 4 steps


# ====================
# Proactive Suggester
# ====================


class ProactiveSuggester:
    """Suggests additional services based on context"""

    async def suggest(self, services: List[Dict], intent: Dict, context: Dict) -> List[Dict]:
        """Generate proactive suggestions"""
        suggestions = []

        # Based on intent
        if intent["type"] == IntentType.HOUSING:
            suggestions.extend(
                [
                    {"type": "financial", "label": "Financial assistance"},
                    {"type": "furniture", "label": "Free furniture"},
                    {"type": "utilities", "label": "Utility connection help"},
                ]
            )
        elif intent["type"] == IntentType.ECONOMIC:
            suggestions.extend(
                [
                    {"type": "skills", "label": "Skills recognition"},
                    {"type": "resume", "label": "Resume help"},
                    {"type": "interview", "label": "Interview preparation"},
                ]
            )

        # Based on hidden needs
        if context.get("hidden_needs"):
            for need in context["hidden_needs"][:2]:
                suggestions.append(need)

        return suggestions[:3]  # Limit suggestions


# ====================
# Conversation Orchestrator
# ====================


class ConversationOrchestrator:
    """Main orchestrator for conversation flow"""

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.context_analyzer = ContextAnalyzer()
        self.emergency_handler = EmergencyHandler()
        self.search_engine = SearchEngineWrapper()
        self.response_formatter = ResponseFormatter()
        self.proactive_suggester = ProactiveSuggester()

    async def process_request(self, request: Dict) -> Dict:
        """Process incoming request through orchestration pipeline"""

        try:
            # Step 1: Parallel analysis
            intent_task = asyncio.create_task(self.intent_classifier.classify(request["message"]))
            context_task = asyncio.create_task(self.context_analyzer.analyze(request))

            intent, context = await asyncio.gather(intent_task, context_task)

            # Step 2: Check for emergency
            if intent["is_emergency"]:
                emergency_response = await self.emergency_handler.handle(
                    request=request, intent=intent, context=context
                )
                return await self.response_formatter.format_emergency(
                    emergency_response, language=request.get("language", "English")
                )

            # Step 3: Route to appropriate search
            if intent["type"] == IntentType.EXPLOITATION:
                services = await self.search_engine.search_confidential(query=request["message"], context=context)
            elif intent["type"] == IntentType.DIGITAL_HELP:
                services = await self.search_engine.search_digital_support(query=request["message"], context=context)
            else:
                services = await self.search_engine.search_general(
                    query=request["message"], context=context, boost=intent.get("boost_factors", {})
                )

            # Step 4: Get proactive suggestions
            suggestions = await self.proactive_suggester.suggest(services=services, intent=intent, context=context)

            # Step 5: Format comprehensive response
            response = await self.response_formatter.format(
                services=services,
                suggestions=suggestions,
                intent=intent,
                context=context,
                language=request.get("language", "English"),
            )

            return response

        except Exception as e:
            logger.error(f"Orchestration error: {str(e)}")

            # Return fallback response
            return {
                "success": False,
                "message": "I'm having trouble accessing services right now. For immediate help:",
                "services": [
                    {
                        "name": "Emergency Services",
                        "phone": "000",
                        "description": "Police, Fire, Ambulance",
                        "available": "24/7",
                    },
                    {
                        "name": "Interpreter Service",
                        "phone": "131 450",
                        "description": "24/7 interpretation in your language",
                        "available": "24/7",
                    },
                ],
                "quick_replies": ["Try again", "Emergency help", "Call interpreter"],
                "metadata": {"error": True, "fallback": True, "timestamp": datetime.now().isoformat()},
            }


# ====================
# API Endpoints
# ====================

# Initialize orchestrator
orchestrator = ConversationOrchestrator()


@app.get("/")
def root():
    return {
        "service": "ACT Refugee Support API v2",
        "version": "2.0.0",
        "architecture": "Event-Driven Microservices",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ACT Refugee Support Orchestrator",
        "components": {
            "intent_classifier": "operational",
            "context_analyzer": "operational",
            "emergency_handler": "operational",
            "search_engine": "operational",
            "response_formatter": "operational",
        },
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/v2/chat", response_model=OrchestrationResponse)
async def unified_chat_endpoint(request: ChatRequest):
    """
    Main orchestrated endpoint for Voiceflow integration
    Handles all types of queries with intelligent routing
    """

    # Process through orchestrator
    response = await orchestrator.process_request(
        {
            "message": request.message,
            "user_id": request.user_id,
            "language": request.language or "English",
            "location": request.location or "Canberra",
            "context": request.context or {},
            "user_profile": request.user_profile or {},
        }
    )

    return response


@app.post("/api/v2/emergency")
async def emergency_quick_access():
    """Direct emergency endpoint for critical situations"""

    # Create emergency request
    request = {"message": "emergency help needed", "language": "English"}

    # Get emergency services immediately
    handler = EmergencyHandler()
    emergency_data = await handler.handle(
        request=request,
        intent={"type": IntentType.EMERGENCY, "is_emergency": True},
        context={"urgency": UrgencyLevel.CRITICAL},
    )

    # Format response
    formatter = ResponseFormatter()
    return await formatter.format_emergency(emergency_data, "English")


# ====================
# Voiceflow Webhook Endpoint
# ====================


@app.post("/voiceflow/webhook")
async def voiceflow_webhook(payload: Dict[str, Any]):
    """
    Direct webhook endpoint for Voiceflow
    Accepts Voiceflow's native payload format
    """

    # Extract message from Voiceflow payload
    user_message = payload.get("query", payload.get("message", ""))
    user_id = payload.get("user", {}).get("id", "unknown")

    # Create chat request
    chat_request = ChatRequest(
        message=user_message,
        user_id=user_id,
        language=payload.get("language", "English"),
        context=payload.get("context", {}),
        user_profile=payload.get("user", {}),
    )

    # Process through main endpoint
    response = await unified_chat_endpoint(chat_request)

    # Format for Voiceflow
    return {
        "success": response.success,
        "message": response.message,
        "cards": [
            {
                "title": service["name"],
                "description": service["description"],
                "buttons": (
                    [{"label": f"Call {service['phone']}", "value": service["phone"]}] if service.get("phone") else []
                ),
            }
            for service in response.services[:3]
        ],
        "quick_replies": response.quick_replies,
        "metadata": response.metadata,
    }


if __name__ == "__main__":
    import uvicorn

    # Use PORT_V2 environment variable or default to 8002
    port = int(os.getenv("PORT_V2", os.getenv("PORT", 8002)))
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security
    logger.info(f"Starting orchestrated API v2 on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
