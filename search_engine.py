from typing import List, Optional, Dict, Any
from qdrant_client.models import Filter, FieldCondition, MatchValue, SearchRequest
from config import QdrantConfig
from models import SearchQuery, SearchResult, Resource, ResourceCategory
import logging

logger = logging.getLogger(__name__)

class SearchEngine:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client = config.get_client()
        self.embedding_model = config.get_embedding_model()
        
    def search(self, query: SearchQuery) -> List[SearchResult]:
        try:
            query_embedding = self.embedding_model.encode(query.query).tolist()
            
            filters = self._build_filters(query)
            
            search_results = self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_embedding,
                query_filter=filters,
                limit=query.limit,
                with_payload=True
            )
            
            results = []
            for result in search_results:
                resource = self._payload_to_resource(result.payload)
                search_result = SearchResult(
                    resource=resource,
                    score=result.score,
                    relevance_explanation=self._generate_relevance_explanation(
                        query.query, resource, result.score
                    )
                )
                results.append(search_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return []
    
    def search_by_category(self, category: ResourceCategory, limit: int = 20) -> List[Resource]:
        try:
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category.value)
                    )
                ]
            )
            
            results = self.client.scroll(
                collection_name=self.config.collection_name,
                scroll_filter=filter_condition,
                limit=limit,
                with_payload=True
            )
            
            resources = []
            for point in results[0]:
                resource = self._payload_to_resource(point.payload)
                resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.error(f"Error searching by category: {e}")
            return []
    
    def search_urgent_services(self, limit: int = 10) -> List[Resource]:
        try:
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="urgency_level",
                        match=MatchValue(value="critical")
                    )
                ]
            )
            
            results = self.client.scroll(
                collection_name=self.config.collection_name,
                scroll_filter=filter_condition,
                limit=limit,
                with_payload=True
            )
            
            resources = []
            for point in results[0]:
                resource = self._payload_to_resource(point.payload)
                resources.append(resource)
            
            if len(resources) < limit:
                high_urgency_filter = Filter(
                    must=[
                        FieldCondition(
                            key="urgency_level",
                            match=MatchValue(value="high")
                        )
                    ]
                )
                
                high_urgency_results = self.client.scroll(
                    collection_name=self.config.collection_name,
                    scroll_filter=high_urgency_filter,
                    limit=limit - len(resources),
                    with_payload=True
                )
                
                for point in high_urgency_results[0]:
                    resource = self._payload_to_resource(point.payload)
                    resources.append(resource)
            
            return resources
            
        except Exception as e:
            logger.error(f"Error searching urgent services: {e}")
            return []
    
    def search_by_language(self, language: str, limit: int = 20) -> List[Resource]:
        try:
            query = f"Services available in {language} language support interpreter {language}"
            query_embedding = self.embedding_model.encode(query).tolist()
            
            search_results = self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_embedding,
                limit=limit * 2,
                with_payload=True
            )
            
            resources = []
            for result in search_results:
                resource = self._payload_to_resource(result.payload)
                if language.lower() in [lang.lower() for lang in resource.languages_available]:
                    resources.append(resource)
                elif "interpreter" in " ".join(resource.languages_available).lower():
                    resources.append(resource)
                
                if len(resources) >= limit:
                    break
            
            return resources
            
        except Exception as e:
            logger.error(f"Error searching by language: {e}")
            return []
    
    def get_resource_by_id(self, resource_id: str) -> Optional[Resource]:
        try:
            filter_condition = Filter(
                must=[
                    FieldCondition(
                        key="id",
                        match=MatchValue(value=resource_id)
                    )
                ]
            )
            
            results = self.client.scroll(
                collection_name=self.config.collection_name,
                scroll_filter=filter_condition,
                limit=1,
                with_payload=True
            )
            
            if results[0]:
                return self._payload_to_resource(results[0][0].payload)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting resource by ID: {e}")
            return None
    
    def _build_filters(self, query: SearchQuery) -> Optional[Filter]:
        conditions = []
        
        if query.categories:
            category_conditions = []
            for category in query.categories:
                category_conditions.append(
                    FieldCondition(
                        key="category",
                        match=MatchValue(value=category.value)
                    )
                )
            if category_conditions:
                conditions.append(Filter(should=category_conditions))
        
        if query.urgency:
            conditions.append(
                FieldCondition(
                    key="urgency_level",
                    match=MatchValue(value=query.urgency)
                )
            )
        
        if conditions:
            return Filter(must=conditions)
        
        return None
    
    def _payload_to_resource(self, payload: Dict[str, Any]) -> Resource:
        from models import ContactInfo
        from datetime import datetime
        
        contact = ContactInfo(
            phone=payload.get("contact_phone"),
            email=payload.get("contact_email"),
            website=payload.get("contact_website"),
            address=payload.get("contact_address"),
            hours=payload.get("contact_hours")
        )
        
        return Resource(
            id=payload["id"],
            name=payload["name"],
            description=payload["description"],
            category=ResourceCategory(payload["category"]),
            subcategory=payload.get("subcategory"),
            contact=contact,
            eligibility=payload.get("eligibility"),
            services_provided=payload.get("services_provided", []),
            languages_available=payload.get("languages_available", ["English"]),
            cost=payload.get("cost", "Free"),
            location=payload.get("location", "Canberra, ACT"),
            urgency_level=payload.get("urgency_level", "standard"),
            keywords=payload.get("keywords", []),
            last_updated=datetime.fromisoformat(payload.get("last_updated", datetime.now().isoformat())),
            additional_info=payload.get("additional_info")
        )
    
    def _generate_relevance_explanation(self, query: str, resource: Resource, score: float) -> str:
        explanation = f"Match score: {score:.2f}. "
        
        query_words = query.lower().split()
        matches = []
        
        if any(word in resource.name.lower() for word in query_words):
            matches.append("name")
        if any(word in resource.description.lower() for word in query_words):
            matches.append("description")
        if any(word in " ".join(resource.keywords).lower() for word in query_words):
            matches.append("keywords")
        
        if matches:
            explanation += f"Query matches found in: {', '.join(matches)}"
        else:
            explanation += "Semantic similarity match"
        
        return explanation