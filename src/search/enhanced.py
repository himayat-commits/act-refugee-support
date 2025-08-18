"""
Enhanced Search Engine with Smart Filtering and Ranking
High Impact / Low Effort search improvements
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import math

from src.core.models import (
    EnhancedRefugeeResource,
    ServiceSearchFilters,
    ServiceRecommendation,
    UrgencyLevel,
    AccessibilityFeature,
)


class SmartSearchEngine:
    """Enhanced search engine with intelligent filtering and ranking"""

    def __init__(self, config):
        self.config = config
        self.client = config.get_client()
        # Config already stored in self.config for embeddings

    def smart_search(
        self, query: str, filters: ServiceSearchFilters, user_context: Optional[Dict] = None, limit: int = 10
    ) -> List[ServiceRecommendation]:
        """
        Perform smart search with filtering and ranking
        """
        # Step 1: Get base semantic search results (get more than needed for filtering)
        base_results = self._semantic_search(query, limit * 3)

        # Step 2: Apply filters
        filtered_results = self._apply_filters(base_results, filters)

        # Step 3: Calculate match scores
        scored_results = self._calculate_match_scores(filtered_results, query, filters, user_context)

        # Step 4: Sort by score and limit
        sorted_results = sorted(scored_results, key=lambda x: x.match_score, reverse=True)[:limit]

        return sorted_results

    def _semantic_search(self, query: str, limit: int) -> List[Dict]:
        """Basic semantic search using embeddings"""
        # Generate query embedding
        # Generate embedding using OpenAI
        query_embedding = self.config.get_embeddings(query)

        # Search in Qdrant
        results = self.client.search(
            collection_name="act_refugee_resources", query_vector=query_embedding, limit=limit, with_payload=True
        )

        return [
            {"id": hit.id, "score": hit.score, "resource": EnhancedRefugeeResource(**hit.payload)} for hit in results
        ]

    def _apply_filters(self, results: List[Dict], filters: ServiceSearchFilters) -> List[Dict]:
        """Apply smart filters to search results"""
        filtered = []

        for result in results:
            resource = result["resource"]

            # Check all filter conditions
            if not self._check_filters(resource, filters):
                continue

            filtered.append(result)

        return filtered

    def _check_filters(self, resource: EnhancedRefugeeResource, filters: ServiceSearchFilters) -> bool:
        """Check if resource matches all filter criteria"""

        # Location filters
        if filters.suburb and resource.location.suburb != filters.suburb:
            return False

        # Availability filters
        if filters.open_now and not self._is_open_now(resource):
            return False

        if filters.open_weekends:
            if not (resource.opening_hours.saturday != "Closed" or resource.opening_hours.sunday != "Closed"):
                return False

        if filters.no_appointment_needed and resource.service_availability.appointment_required:
            return False

        # Language filters
        if filters.language_required:
            languages = resource.language_support.primary_languages + list(
                resource.language_support.staff_languages.keys()
            )
            if filters.language_required not in languages:
                if not filters.interpreter_available:
                    return False

        # Accessibility filters
        if filters.wheelchair_accessible:
            if AccessibilityFeature.WHEELCHAIR not in resource.location.accessibility_features:
                return False

        if filters.accessibility_features:
            for feature in filters.accessibility_features:
                if feature not in resource.location.accessibility_features:
                    return False

        # Cost filters
        if filters.free_service and resource.financial_info.base_cost != "Free":
            return False

        if filters.bulk_billing and not resource.financial_info.bulk_billing:
            return False

        # Demographic filters
        if filters.family_friendly and not resource.demographic_support.family_friendly:
            return False

        if filters.youth_service and not resource.demographic_support.youth_programs:
            return False

        if filters.women_only_available and not resource.demographic_support.women_only_sessions:
            return False

        if filters.lgbtqia_inclusive and not resource.demographic_support.lgbtqia_inclusive:
            return False

        # Quality filters
        if filters.min_rating:
            if not resource.quality_metrics.average_rating:
                return False
            if resource.quality_metrics.average_rating < filters.min_rating:
                return False

        if filters.verified_only and not resource.quality_metrics.verified_service:
            return False

        # Urgency filters
        if filters.crisis_support and not resource.emergency_info.crisis_support:
            return False

        if filters.urgency_level:
            if resource.urgency_level != filters.urgency_level:
                return False

        return True

    def _is_open_now(self, resource: EnhancedRefugeeResource) -> bool:
        """Check if service is currently open"""
        now = datetime.now()
        day_name = now.strftime("%A").lower()
        current_time = now.time()

        # Get today's hours
        hours_str = getattr(resource.opening_hours, day_name, "Closed")

        if hours_str == "Closed":
            return False

        if hours_str == "24 hours":
            return True

        try:
            # Parse hours (format: "09:00-17:00")
            open_time_str, close_time_str = hours_str.split("-")
            open_time = datetime.strptime(open_time_str.strip(), "%H:%M").time()
            close_time = datetime.strptime(close_time_str.strip(), "%H:%M").time()

            return open_time <= current_time <= close_time
        except (ValueError, AttributeError):
            return False

    def _calculate_match_scores(
        self, results: List[Dict], query: str, filters: ServiceSearchFilters, user_context: Optional[Dict]
    ) -> List[ServiceRecommendation]:
        """Calculate comprehensive match scores for filtered results"""
        recommendations = []

        for result in results:
            resource = result["resource"]
            base_score = result["score"]  # Semantic similarity score

            # Calculate component scores
            relevance_score = base_score
            availability_score = self._calculate_availability_score(resource)
            quality_score = self._calculate_quality_score(resource)
            accessibility_score = self._calculate_accessibility_score(resource, user_context)
            urgency_score = self._calculate_urgency_score(resource, query)

            # Weighted final score
            final_score = (
                relevance_score * 0.35
                + availability_score * 0.20
                + quality_score * 0.20
                + accessibility_score * 0.15
                + urgency_score * 0.10
            )

            # Generate match reasons
            match_reasons = self._generate_match_reasons(
                resource,
                query,
                filters,
                {
                    "relevance": relevance_score,
                    "availability": availability_score,
                    "quality": quality_score,
                    "accessibility": accessibility_score,
                    "urgency": urgency_score,
                },
            )

            # Estimate wait time
            estimated_wait = self._estimate_wait_time(resource)

            # Check language and accessibility match
            language_match = self._check_language_match(resource, user_context)
            accessibility_match = self._check_accessibility_match(resource, user_context)

            recommendation = ServiceRecommendation(
                resource=resource,
                match_score=final_score,
                match_reasons=match_reasons,
                estimated_wait=estimated_wait,
                accessibility_match=accessibility_match,
                language_match=language_match,
            )

            recommendations.append(recommendation)

        return recommendations

    def _calculate_availability_score(self, resource: EnhancedRefugeeResource) -> float:
        """Calculate availability score based on multiple factors"""
        score = 0.5  # Base score

        # Currently open bonus
        if self._is_open_now(resource):
            score += 0.2

        # No appointment needed bonus
        if not resource.service_availability.appointment_required:
            score += 0.15

        # Online booking available
        if resource.service_availability.online_booking_available:
            score += 0.1

        # Consider typical wait time
        wait_time = resource.service_availability.typical_wait_time
        if wait_time:
            if "15" in wait_time or "immediate" in wait_time.lower():
                score += 0.05
            elif "hour" in wait_time and not "hours" in wait_time:
                score -= 0.05
            elif "hours" in wait_time:
                score -= 0.1

        return min(1.0, score)

    def _calculate_quality_score(self, resource: EnhancedRefugeeResource) -> float:
        """Calculate quality score based on ratings and feedback"""
        score = 0.5  # Base score

        # Rating score
        if resource.quality_metrics.average_rating:
            score = resource.quality_metrics.average_rating / 5.0

        # Verified service bonus
        if resource.quality_metrics.verified_service:
            score += 0.1

        # Accreditations bonus
        if resource.quality_metrics.accreditations:
            score += min(0.1, len(resource.quality_metrics.accreditations) * 0.02)

        # High recommendation rate bonus
        if resource.quality_metrics.recommendation_rate:
            if resource.quality_metrics.recommendation_rate > 80:
                score += 0.1

        # Recent update bonus
        days_since_update = (datetime.now() - resource.quality_metrics.last_updated).days
        if days_since_update < 30:
            score += 0.05
        elif days_since_update > 180:
            score -= 0.1

        return min(1.0, max(0.0, score))

    def _calculate_accessibility_score(self, resource: EnhancedRefugeeResource, user_context: Optional[Dict]) -> float:
        """Calculate accessibility score based on user needs"""
        score = 0.7  # Base score

        # Physical accessibility
        if AccessibilityFeature.WHEELCHAIR in resource.location.accessibility_features:
            score += 0.1

        # Language accessibility
        if resource.language_support.phone_interpreter:
            score += 0.1

        if resource.language_support.onsite_interpreters:
            score += 0.05

        # Financial accessibility
        if resource.financial_info.base_cost == "Free":
            score += 0.05

        # Family accessibility
        if resource.demographic_support.childcare_available:
            score += 0.05

        # Cultural accessibility
        if resource.language_support.cultural_liaison_available:
            score += 0.05

        # Location accessibility (if user location provided)
        if user_context and "location" in user_context:
            distance = self._calculate_distance(
                user_context["location"], (resource.location.latitude, resource.location.longitude)
            )
            if distance < 5:  # Within 5km
                score += 0.1
            elif distance > 20:  # More than 20km
                score -= 0.1

        return min(1.0, max(0.0, score))

    def _calculate_urgency_score(self, resource: EnhancedRefugeeResource, query: str) -> float:
        """Calculate urgency match score"""
        score = 0.5
        query_lower = query.lower()

        # Check for urgent keywords in query
        urgent_keywords = ["emergency", "urgent", "crisis", "immediate", "now", "help"]
        if any(keyword in query_lower for keyword in urgent_keywords):
            # Boost services that handle emergencies
            if resource.emergency_info.crisis_support:
                score += 0.3
            if resource.emergency_info.after_hours_available:
                score += 0.2
            if resource.urgency_level == UrgencyLevel.CRITICAL:
                score += 0.2

        # Standard query - slightly prefer non-emergency services
        else:
            if resource.urgency_level == UrgencyLevel.STANDARD:
                score += 0.1

        return min(1.0, score)

    def _generate_match_reasons(
        self, resource: EnhancedRefugeeResource, query: str, filters: ServiceSearchFilters, scores: Dict[str, float]
    ) -> List[str]:
        """Generate human-readable match reasons"""
        reasons = []

        # High relevance
        if scores["relevance"] > 0.8:
            reasons.append("Highly relevant to your search")

        # Availability
        if self._is_open_now(resource):
            reasons.append("Currently open")
        if not resource.service_availability.appointment_required:
            reasons.append("No appointment needed")

        # Quality
        if resource.quality_metrics.average_rating and resource.quality_metrics.average_rating >= 4.5:
            reasons.append(f"Highly rated ({resource.quality_metrics.average_rating}/5)")
        if resource.quality_metrics.verified_service:
            reasons.append("Verified service")

        # Cost
        if resource.financial_info.base_cost == "Free":
            reasons.append("Free service")
        elif resource.financial_info.bulk_billing:
            reasons.append("Bulk billing available")

        # Special features
        if resource.emergency_info.crisis_support:
            reasons.append("Crisis support available")
        if resource.language_support.cultural_liaison_available:
            reasons.append("Cultural liaison available")

        # Filter matches
        if filters.language_required:
            if filters.language_required in resource.language_support.primary_languages:
                reasons.append(f"{filters.language_required} speaking staff")

        return reasons if reasons else ["Matches your search criteria"]

    def _estimate_wait_time(self, resource: EnhancedRefugeeResource) -> Optional[str]:
        """Estimate wait time based on various factors"""
        # If current wait time is available, use it
        if resource.service_availability.current_wait_time:
            return resource.service_availability.current_wait_time

        # Otherwise use typical wait time
        if resource.service_availability.typical_wait_time:
            return resource.service_availability.typical_wait_time

        # Check if it's a busy period
        now = datetime.now()
        current_hour = now.strftime("%H:00")
        day_name = now.strftime("%A")

        for busy_period in resource.service_availability.busy_periods:
            if day_name in busy_period or current_hour in busy_period:
                return "Longer than usual (busy period)"

        for quiet_period in resource.service_availability.quiet_periods:
            if day_name in quiet_period or current_hour in quiet_period:
                return "Shorter than usual (quiet period)"

        # Default based on appointment requirements
        if resource.service_availability.appointment_required:
            return "By appointment"
        else:
            return "Variable - call ahead recommended"

    def _check_language_match(self, resource: EnhancedRefugeeResource, user_context: Optional[Dict]) -> bool:
        """Check if language needs are met"""
        if not user_context or "language" not in user_context:
            return True

        user_language = user_context["language"]

        # Check primary languages
        if user_language in resource.language_support.primary_languages:
            return True

        # Check staff languages
        if user_language in resource.language_support.staff_languages:
            return True

        # Check interpreter availability
        if (
            resource.language_support.phone_interpreter
            or user_language in resource.language_support.onsite_interpreters
        ):
            return True

        return False

    def _check_accessibility_match(self, resource: EnhancedRefugeeResource, user_context: Optional[Dict]) -> bool:
        """Check if accessibility needs are met"""
        if not user_context or "accessibility_needs" not in user_context:
            return True

        user_needs = user_context["accessibility_needs"]
        resource_features = resource.location.accessibility_features

        # Check if all user needs are met
        for need in user_needs:
            if need not in resource_features:
                return False

        return True

    def _calculate_distance(self, coord1: Tuple[float, float], coord2: Optional[Tuple[float, float]]) -> float:
        """Calculate distance between two coordinates in kilometers"""
        if not coord2 or not coord2[0] or not coord2[1]:
            return float("inf")

        # Haversine formula
        lat1, lon1 = coord1
        lat2, lon2 = coord2

        R = 6371  # Earth's radius in kilometers

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return R * c

    def get_service_by_filters(self, filters: ServiceSearchFilters, limit: int = 10) -> List[EnhancedRefugeeResource]:
        """Get services by filters without text search"""
        # Get all resources from collection
        all_resources = self.client.scroll(
            collection_name="act_refugee_resources", limit=1000, with_payload=True  # Get many resources
        )[0]

        # Convert to enhanced resources and filter
        filtered_resources = []
        for point in all_resources:
            try:
                resource = EnhancedRefugeeResource(**point.payload)
                if self._check_filters(resource, filters):
                    filtered_resources.append(resource)
                    if len(filtered_resources) >= limit:
                        break
            except (KeyError, AttributeError):
                continue

        return filtered_resources

    def get_open_now_services(self, category: Optional[str] = None) -> List[EnhancedRefugeeResource]:
        """Get all services that are currently open"""
        filters = ServiceSearchFilters(open_now=True)
        services = self.get_service_by_filters(filters, limit=50)

        if category:
            services = [s for s in services if s.category == category]

        return services

    def get_crisis_services(self) -> List[EnhancedRefugeeResource]:
        """Get all crisis/emergency services"""
        filters = ServiceSearchFilters(crisis_support=True, urgency_level=UrgencyLevel.CRITICAL)
        return self.get_service_by_filters(filters, limit=20)

    def get_free_services(self, category: Optional[str] = None) -> List[EnhancedRefugeeResource]:
        """Get all free services"""
        filters = ServiceSearchFilters(free_service=True)
        services = self.get_service_by_filters(filters, limit=100)

        if category:
            services = [s for s in services if s.category == category]

        return services
