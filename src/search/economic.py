import logging
from typing import Any, Dict, List

from src.core.config import QdrantConfig
from src.core.models import Resource, ResourceCategory, SearchQuery
from src.search.engine import SearchEngine

logger = logging.getLogger(__name__)


class EconomicIntegrationSearch(SearchEngine):
    """Extended search engine with specialized methods for economic integration queries"""

    def __init__(self, config: QdrantConfig):
        super().__init__(config)

    def search_skill_underutilization_solutions(self, profession: str = None, limit: int = 10) -> List[Resource]:
        """Find resources to address skill underutilization for specific professions"""
        try:
            base_query = (
                "skills assessment qualification recognition bridging program professional registration career pathway"
            )
            if profession:
                base_query = f"{profession} {base_query}"

            query = SearchQuery(query=base_query, categories=[ResourceCategory.EMPLOYMENT], limit=limit)

            results = self.search(query)
            return [r.resource for r in results]

        except Exception as e:
            logger.error(f"Error searching skill underutilization solutions: {e}")
            return []

    def search_entrepreneurship_support(self, stage: str = "startup", limit: int = 10) -> List[Resource]:
        """Find entrepreneurship and business support based on business stage"""
        stage_keywords = {
            "idea": "business idea planning mentoring feasibility",
            "startup": "startup NEIS microfinance business plan incubator",
            "growth": "scaling expansion investment accelerator export",
            "social": "social enterprise impact sustainable community",
        }

        query_text = f"business entrepreneur {stage_keywords.get(stage, 'business support')}"

        query = SearchQuery(query=query_text, categories=[ResourceCategory.EMPLOYMENT], limit=limit)

        results = self.search(query)
        return [r.resource for r in results]

    def search_career_pathways(self, industry: str = None, experience_level: str = None) -> List[Resource]:
        """Find career pathway resources for specific industries and experience levels"""
        query_parts = ["career pathway professional development placement"]

        if industry:
            industry_map = {
                "health": "health medical nurse doctor AHPRA",
                "it": "IT technology software programming developer",
                "engineering": "engineer technical construction",
                "trades": "trade apprenticeship vocational certificate",
                "business": "business management finance accounting",
            }
            query_parts.append(industry_map.get(industry.lower(), industry))

        if experience_level:
            level_map = {
                "entry": "entry level graduate junior apprentice",
                "mid": "experienced professional skilled",
                "senior": "senior management executive leadership",
            }
            query_parts.append(level_map.get(experience_level.lower(), experience_level))

        query = SearchQuery(query=" ".join(query_parts), limit=15)

        results = self.search(query)
        return [r.resource for r in results]

    def search_vocational_training(self, free_only: bool = False, sector: str = None) -> List[Resource]:
        """Find vocational training opportunities"""
        query_text = "vocational training certificate TAFE apprenticeship course"

        if sector:
            query_text += f" {sector}"

        if free_only:
            query_text += " free JobTrainer subsidized"

        query = SearchQuery(
            query=query_text, categories=[ResourceCategory.EDUCATION, ResourceCategory.EMPLOYMENT], limit=12
        )

        results = self.search(query)

        if free_only:
            filtered = [
                r.resource
                for r in results
                if "free" in r.resource.cost.lower() or "subsidized" in r.resource.cost.lower()
            ]
            return filtered

        return [r.resource for r in results]

    def search_mentoring_programs(self, profession: str = None, gender_specific: str = None) -> List[Resource]:
        """Find mentoring and professional networking opportunities"""
        query_text = "mentoring mentor professional network networking guidance"

        if profession:
            query_text += f" {profession}"

        if gender_specific:
            query_text += f" {gender_specific}"

        query = SearchQuery(query=query_text, limit=10)

        results = self.search(query)
        return [r.resource for r in results]

    def search_financial_support_for_business(self, amount_needed: str = None) -> List[Resource]:
        """Find financial support for business creation and growth"""
        query_text = "business loan microfinance grant funding capital investment finance"

        amount_map = {
            "micro": "microfinance small loan under 10000",
            "small": "small business loan 10000 50000",
            "medium": "business loan investment 50000 above",
        }

        if amount_needed:
            query_text += f" {amount_map.get(amount_needed, '')}"

        query = SearchQuery(
            query=query_text, categories=[ResourceCategory.EMPLOYMENT, ResourceCategory.FINANCIAL_ASSISTANCE], limit=10
        )

        results = self.search(query)
        return [r.resource for r in results]

    def get_economic_integration_pathway(self, user_profile: Dict[str, Any]) -> Dict[str, List[Resource]]:
        """Generate a comprehensive economic integration pathway based on user profile"""
        pathway = {}

        # Skills assessment if they have overseas qualifications
        if user_profile.get("has_overseas_qualification"):
            pathway["skills_recognition"] = self.search_skill_underutilization_solutions(
                profession=user_profile.get("profession"), limit=3
            )

        # Language support if needed
        if user_profile.get("needs_english_support"):
            language_query = SearchQuery(
                query="English workplace professional language vocational",
                categories=[ResourceCategory.LANGUAGE_LEARNING, ResourceCategory.EDUCATION],
                limit=3,
            )
            results = self.search(language_query)
            pathway["language_support"] = [r.resource for r in results]

        # Career development based on goals
        if user_profile.get("employment_goal") == "professional":
            pathway["career_development"] = self.search_career_pathways(
                industry=user_profile.get("industry"), experience_level=user_profile.get("experience_level")
            )[:3]
        elif user_profile.get("employment_goal") == "business":
            pathway["business_support"] = self.search_entrepreneurship_support(
                stage=user_profile.get("business_stage", "idea")
            )[:3]
        elif user_profile.get("employment_goal") == "trade":
            pathway["vocational_training"] = self.search_vocational_training(
                free_only=True, sector=user_profile.get("trade_interest")
            )[:3]

        # Mentoring for everyone
        pathway["mentoring"] = self.search_mentoring_programs(
            profession=user_profile.get("profession"), gender_specific=user_profile.get("gender")
        )[:2]

        # Financial support if needed
        if user_profile.get("needs_financial_support"):
            pathway["financial_assistance"] = self.search_financial_support_for_business(
                amount_needed=user_profile.get("funding_level", "micro")
            )[:2]

        return pathway
