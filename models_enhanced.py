"""
Enhanced Data Models for ACT Refugee Support System
High Impact / Low Effort improvements to data structure
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, time
from enum import Enum

# ============= ENUMS =============

class ServiceStatus(str, Enum):
    OPEN = "open"
    CLOSED = "closed"
    BUSY = "busy"
    AT_CAPACITY = "at_capacity"
    APPOINTMENT_ONLY = "appointment_only"

class UrgencyLevel(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    STANDARD = "standard"

class AccessibilityFeature(str, Enum):
    WHEELCHAIR = "wheelchair_accessible"
    HEARING_LOOP = "hearing_loop"
    BRAILLE = "braille_signage"
    ACCESSIBLE_TOILET = "accessible_toilets"
    LIFT = "lift_available"
    ASSISTANCE_ANIMALS = "assistance_animals_welcome"
    LARGE_PRINT = "large_print_materials"
    EASY_READ = "easy_read_materials"

# ============= ENHANCED MODELS =============

class OpeningHours(BaseModel):
    """Detailed opening hours with special conditions"""
    monday: Optional[str] = Field(None, example="09:00-17:00")
    tuesday: Optional[str] = Field(None, example="09:00-17:00")
    wednesday: Optional[str] = Field(None, example="09:00-17:00")
    thursday: Optional[str] = Field(None, example="09:00-19:00")
    friday: Optional[str] = Field(None, example="09:00-17:00")
    saturday: Optional[str] = Field(None, example="10:00-14:00")
    sunday: Optional[str] = Field(None, example="Closed")
    public_holidays: str = Field(default="Closed", example="Closed except emergencies")
    notes: Optional[str] = Field(None, example="Extended hours during Ramadan")

class LocationEnhanced(BaseModel):
    """Enhanced location information with accessibility"""
    address: str = Field(..., example="123 Main St, Civic ACT 2601")
    suburb: Optional[str] = Field(None, example="Civic")
    postcode: Optional[str] = Field(None, example="2601")
    
    # GPS Coordinates (can be auto-populated via geocoding)
    latitude: Optional[float] = Field(None, example=-35.2809)
    longitude: Optional[float] = Field(None, example=149.1300)
    
    # Accessibility
    accessibility_features: List[AccessibilityFeature] = Field(default_factory=list)
    accessibility_notes: Optional[str] = Field(None, example="Ramp at side entrance")
    
    # Transport
    nearest_bus_stop: Optional[str] = Field(None, example="City Bus Station Platform 4")
    parking_available: bool = Field(default=False)
    parking_notes: Optional[str] = Field(None, example="Free 2-hour street parking")

class LanguageSupport(BaseModel):
    """Comprehensive language support information"""
    primary_languages: List[str] = Field(default_factory=lambda: ["English"])
    
    # Staff languages
    staff_languages: Dict[str, str] = Field(
        default_factory=dict,
        example={"Arabic": "Mon-Fri", "Mandarin": "Tue, Thu"}
    )
    
    # Interpreter services
    onsite_interpreters: List[str] = Field(default_factory=list)
    phone_interpreter: bool = Field(default=True)
    phone_interpreter_service: str = Field(default="TIS National 131 450")
    video_interpreter: bool = Field(default=False)
    
    # Materials
    translated_materials: List[str] = Field(
        default_factory=list,
        example=["Arabic", "Simplified Chinese", "Vietnamese"]
    )
    
    # Cultural support
    cultural_liaison_available: bool = Field(default=False)
    cultural_liaison_communities: List[str] = Field(default_factory=list)

class ServiceAvailability(BaseModel):
    """Real-time and general availability information"""
    # General availability
    appointment_required: bool = Field(default=False)
    walk_ins_accepted: bool = Field(default=True)
    online_booking_available: bool = Field(default=False)
    booking_link: Optional[str] = Field(None, example="https://book.service.com")
    
    # Wait times
    typical_wait_time: Optional[str] = Field(None, example="30-45 minutes")
    current_wait_time: Optional[str] = Field(None, example="15 minutes")
    
    # Capacity
    drop_in_hours: Optional[str] = Field(None, example="Mon-Wed 2pm-4pm")
    busy_periods: List[str] = Field(
        default_factory=list,
        example=["Monday mornings", "Friday afternoons"]
    )
    quiet_periods: List[str] = Field(
        default_factory=list,
        example=["Tuesday afternoons", "Thursday mornings"]
    )

class FinancialInformation(BaseModel):
    """Detailed cost and financial assistance information"""
    # Basic costs
    base_cost: str = Field(default="Free", example="Free")
    consultation_cost: Optional[str] = Field(None, example="$50")
    
    # Concessions
    healthcare_card_discount: Optional[str] = Field(None, example="50% discount")
    pensioner_discount: Optional[str] = Field(None, example="Free")
    student_discount: Optional[str] = Field(None, example="30% discount")
    
    # Payment
    payment_methods: List[str] = Field(
        default_factory=lambda: ["Cash", "Card"],
        example=["Cash", "Card", "EFTPOS", "Payment plan"]
    )
    
    # Funding
    bulk_billing: bool = Field(default=False)
    ndis_registered: bool = Field(default=False)
    medicare_accepted: bool = Field(default=False)
    private_health_accepted: List[str] = Field(default_factory=list)
    
    # Financial assistance
    financial_assistance_available: bool = Field(default=False)
    assistance_details: Optional[str] = Field(
        None, 
        example="Emergency relief funds available for those in crisis"
    )

class QualityMetrics(BaseModel):
    """Service quality and user feedback metrics"""
    # Ratings
    average_rating: Optional[float] = Field(None, ge=0, le=5, example=4.5)
    total_reviews: int = Field(default=0, example=127)
    
    # Satisfaction
    recommendation_rate: Optional[int] = Field(None, ge=0, le=100, example=89)
    client_satisfaction: Optional[int] = Field(None, ge=0, le=100, example=91)
    
    # Outcomes
    success_rate: Optional[int] = Field(None, ge=0, le=100, example=85)
    average_resolution_time: Optional[str] = Field(None, example="3 days")
    
    # Trust indicators
    verified_service: bool = Field(default=False)
    accreditations: List[str] = Field(default_factory=list)
    last_updated: datetime = Field(default_factory=datetime.now)
    
    # Feedback snippets
    recent_feedback: List[Dict[str, Any]] = Field(
        default_factory=list,
        example=[{
            "date": "2024-11-01",
            "rating": 5,
            "comment": "Very helpful and respectful staff"
        }]
    )

class DemographicSupport(BaseModel):
    """Support for specific demographic groups"""
    # Families
    family_friendly: bool = Field(default=True)
    childcare_available: bool = Field(default=False)
    childcare_details: Optional[str] = Field(None, example="Free childcare during appointments")
    
    # Age groups
    youth_programs: bool = Field(default=False)
    youth_age_range: Optional[str] = Field(None, example="12-25 years")
    seniors_programs: bool = Field(default=False)
    
    # Gender-specific
    women_only_sessions: Optional[str] = Field(None, example="Tuesdays 2-4pm")
    men_only_sessions: Optional[str] = Field(None, example="Thursdays 6-8pm")
    
    # LGBTQIA+
    lgbtqia_inclusive: bool = Field(default=True)
    rainbow_tick_accredited: bool = Field(default=False)
    
    # Cultural groups
    culturally_specific_programs: Dict[str, str] = Field(
        default_factory=dict,
        example={"Afghan community": "Wednesdays", "Syrian community": "Fridays"}
    )

class ServicePathway(BaseModel):
    """Service pathways and connections"""
    # Prerequisites
    prerequisites: List[str] = Field(
        default_factory=list,
        example=["Must be registered with Centrelink", "Need referral from GP"]
    )
    
    # Next steps
    typical_next_steps: List[str] = Field(
        default_factory=list,
        example=["Apply for housing", "Enroll in English classes"]
    )
    
    # Partner services
    commonly_used_with: List[str] = Field(
        default_factory=list,
        example=["Companion House", "Legal Aid ACT"]
    )
    
    # Referrals
    referral_required: bool = Field(default=False)
    referral_sources: List[str] = Field(default_factory=list)
    can_refer_to: List[str] = Field(default_factory=list)

class EmergencyInformation(BaseModel):
    """Emergency and crisis support information"""
    crisis_support: bool = Field(default=False)
    after_hours_available: bool = Field(default=False)
    after_hours_number: Optional[str] = Field(None, example="1800 XXX XXX")
    
    emergency_procedures: Optional[str] = Field(
        None,
        example="For immediate crisis support, present at emergency department"
    )
    
    crisis_response_time: Optional[str] = Field(None, example="Immediate")
    priority_populations: List[str] = Field(
        default_factory=list,
        example=["Families with children", "Unaccompanied minors", "Torture survivors"]
    )

class EnhancedRefugeeResource(BaseModel):
    """Complete enhanced refugee resource model"""
    # Basic Information (existing)
    id: Optional[str] = Field(None)
    name: str = Field(..., example="Companion House")
    description: str = Field(..., min_length=10, max_length=1000)
    category: str = Field(..., example="Healthcare")
    
    # Enhanced Location
    location: LocationEnhanced
    opening_hours: OpeningHours
    
    # Contact (existing + enhanced)
    contact_phone: str = Field(..., example="02 6251 4550")
    contact_email: Optional[str] = Field(None, example="info@service.org.au")
    contact_website: Optional[str] = Field(None, example="https://service.org.au")
    
    # Service Details
    services_provided: List[str] = Field(..., min_items=1)
    service_availability: ServiceAvailability
    
    # Language & Culture
    language_support: LanguageSupport
    
    # Financial
    financial_info: FinancialInformation
    
    # Quality
    quality_metrics: QualityMetrics
    
    # Demographics
    demographic_support: DemographicSupport
    
    # Pathways
    service_pathway: ServicePathway
    
    # Emergency
    emergency_info: EmergencyInformation
    
    # Metadata
    urgency_level: UrgencyLevel = Field(default=UrgencyLevel.STANDARD)
    last_verified: datetime = Field(default_factory=datetime.now)
    update_frequency: str = Field(default="Monthly", example="Weekly")
    data_sources: List[str] = Field(
        default_factory=list,
        example=["Provider website", "Government directory", "User feedback"]
    )
    
    # Tags for better search
    tags: List[str] = Field(
        default_factory=list,
        example=["trauma-informed", "bulk-billing", "no-appointment", "24-7"]
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ============= QUICK WIN FEATURES =============

class ServiceSearchFilters(BaseModel):
    """Enhanced search filters for better matching"""
    # Location filters
    suburb: Optional[str] = None
    max_distance_km: Optional[float] = None
    
    # Availability filters
    open_now: Optional[bool] = None
    open_weekends: Optional[bool] = None
    no_appointment_needed: Optional[bool] = None
    
    # Language filters
    language_required: Optional[str] = None
    interpreter_available: Optional[bool] = None
    
    # Accessibility filters
    wheelchair_accessible: Optional[bool] = None
    accessibility_features: Optional[List[AccessibilityFeature]] = None
    
    # Cost filters
    free_service: Optional[bool] = None
    bulk_billing: Optional[bool] = None
    concession_available: Optional[bool] = None
    
    # Demographic filters
    family_friendly: Optional[bool] = None
    youth_service: Optional[bool] = None
    women_only_available: Optional[bool] = None
    lgbtqia_inclusive: Optional[bool] = None
    
    # Quality filters
    min_rating: Optional[float] = None
    verified_only: Optional[bool] = None
    
    # Urgency
    crisis_support: Optional[bool] = None
    urgency_level: Optional[UrgencyLevel] = None

class ServiceRecommendation(BaseModel):
    """AI-powered service recommendations"""
    resource: EnhancedRefugeeResource
    match_score: float = Field(..., ge=0, le=1)
    match_reasons: List[str] = Field(...)
    estimated_wait: Optional[str] = None
    accessibility_match: bool = Field(default=True)
    language_match: bool = Field(default=True)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserFeedback(BaseModel):
    """User feedback model for quality improvement"""
    resource_id: str
    user_id: Optional[str] = None  # Can be anonymous
    rating: int = Field(..., ge=1, le=5)
    
    # Detailed ratings
    staff_rating: Optional[int] = Field(None, ge=1, le=5)
    accessibility_rating: Optional[int] = Field(None, ge=1, le=5)
    wait_time_rating: Optional[int] = Field(None, ge=1, le=5)
    outcome_rating: Optional[int] = Field(None, ge=1, le=5)
    
    # Feedback
    comment: Optional[str] = Field(None, max_length=500)
    would_recommend: bool = Field(default=True)
    
    # Service details
    service_date: Optional[datetime] = None
    service_type: Optional[str] = None
    wait_time_experienced: Optional[str] = None
    
    # Verification
    verified_user: bool = Field(default=False)
    helpful_count: int = Field(default=0)
    
    # Metadata
    submitted_at: datetime = Field(default_factory=datetime.now)
    language: str = Field(default="English")
    
    # Tags
    tags: List[str] = Field(
        default_factory=list,
        example=["helpful-staff", "long-wait", "accessible", "interpreter-provided"]
    )

class ServiceAlert(BaseModel):
    """Service alerts and announcements"""
    id: Optional[str] = None
    resource_id: str
    alert_type: str = Field(..., example="closure")  # closure, reduced_hours, high_demand, new_service
    title: str = Field(..., example="Temporary Closure")
    message: str = Field(..., example="Closed for staff training on Dec 15")
    
    # Timing
    start_date: datetime
    end_date: Optional[datetime] = None
    
    # Severity
    severity: str = Field(default="info")  # info, warning, critical
    
    # Actions
    alternative_service: Optional[str] = None
    action_required: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: str = Field(default="system")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
