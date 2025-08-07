from pydantic import BaseModel
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

class ResourceCategory(str, Enum):
    LEGAL_AID = "legal_aid"
    HEALTHCARE = "healthcare"
    HOUSING = "housing"
    EDUCATION = "education"
    EMPLOYMENT = "employment"
    LANGUAGE_LEARNING = "language_learning"
    EMERGENCY_SERVICES = "emergency_services"
    COMMUNITY_SUPPORT = "community_support"
    FINANCIAL_ASSISTANCE = "financial_assistance"
    MENTAL_HEALTH = "mental_health"
    GOVERNMENT_PROGRAMS = "government_programs"
    CHILDREN_SERVICES = "children_services"
    WOMEN_SERVICES = "women_services"
    DISABILITY_SUPPORT = "disability_support"

class ContactInfo(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    hours: Optional[str] = None

class Resource(BaseModel):
    id: str
    name: str
    description: str
    category: ResourceCategory
    subcategory: Optional[str] = None
    contact: ContactInfo
    eligibility: Optional[str] = None
    services_provided: List[str]
    languages_available: List[str] = ["English"]
    cost: str = "Free"
    location: str = "Canberra, ACT"
    urgency_level: str = "standard"
    keywords: List[str] = []
    last_updated: datetime = datetime.now()
    additional_info: Optional[Dict] = None
    
class SearchQuery(BaseModel):
    query: str
    categories: Optional[List[ResourceCategory]] = None
    language: Optional[str] = None
    urgency: Optional[str] = None
    limit: int = 10

class SearchResult(BaseModel):
    resource: Resource
    score: float
    relevance_explanation: Optional[str] = None