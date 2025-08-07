"""
Advanced Search System with Hybrid Search and Re-ranking
Combines semantic search with filters, keyword matching, and personalization
"""

from typing import List, Dict, Optional, Tuple
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import re
from collections import defaultdict
import logging

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchMode(Enum):
    SEMANTIC = "semantic"
    KEYWORD = "keyword"
    HYBRID = "hybrid"
    EMERGENCY = "emergency"

@dataclass
class UserContext:
    """User context for personalized search"""
    user_id: Optional[str] = None
    language: Optional[str] = "English"
    location: Optional[Tuple[float, float]] = None  # (latitude, longitude)
    previous_queries: List[str] = None
    clicked_resources: List[str] = None
    urgency_level: str = "standard"
    accessibility_needs: List[str] = None

class AdvancedSearch:
    def __init__(self, config):
        self.config = config
        self.qdrant_client = config.get_client()
        self.openai_client = OpenAI()
        self.search_history = defaultdict(list)
        
    def extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove common words
        stop_words = {'i', 'need', 'help', 'with', 'for', 'the', 'a', 'an', 'and', 'or', 'but'}
        words = query.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Add synonyms for common terms
        synonym_map = {
            'job': ['employment', 'work', 'career'],
            'house': ['housing', 'accommodation', 'shelter'],
            'doctor': ['medical', 'health', 'clinic'],
            'lawyer': ['legal', 'immigration', 'visa'],
            'money': ['financial', 'payment', 'centrelink']
        }
        
        expanded_keywords = keywords.copy()
        for keyword in keywords:
            if keyword in synonym_map:
                expanded_keywords.extend(synonym_map[keyword])
        
        return list(set(expanded_keywords))
    
    def build_filters(self, user_context: UserContext, keywords: List[str]) -> Optional[Filter]:
        """Build Qdrant filters based on context and keywords"""
        conditions = []
        
        # Language filter
        if user_context.language and user_context.language != "English":
            conditions.append(
                FieldCondition(
                    key="languages_available",
                    match=MatchValue(value=user_context.language)
                )
            )
        
        # Urgency filter
        if user_context.urgency_level == "critical":
            conditions.append(
                FieldCondition(
                    key="urgency_level",
                    match=MatchValue(value="critical")
                )
            )
        
        # Quality score filter (only high-quality resources)
        conditions.append(
            FieldCondition(
                key="quality_score",
                range=Range(gte=0.6)  # Only resources with 60%+ quality
            )
        )
        
        if conditions:
            return Filter(must=conditions)
        return None
    
    def semantic_search(
        self, 
        query: str, 
        collection_name: str,
        limit: int = 10,
        filters: Optional[Filter] = None
    ) -> List[Dict]:
        """Perform semantic search using embeddings"""
        # Generate query embedding
        response = self.openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=query
        )
        query_vector = response.data[0].embedding
        
        # Search in Qdrant
        results = self.qdrant_client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=filters,
            limit=limit,
            with_payload=True
        )
        
        return [
            {
                'resource': hit.payload,
                'score': hit.score,
                'id': hit.id
            }
            for hit in results
        ]
    
    def keyword_search(
        self,
        keywords: List[str],
        collection_name: str,
        limit: int = 10
    ) -> List[Dict]:
        """Perform keyword-based search"""
        # Build text search conditions
        conditions = []
        for keyword in keywords:
            conditions.append(
                FieldCondition(
                    key="description",
                    match=MatchValue(value=keyword)
                )
            )
        
        if not conditions:
            return []
        
        filter_obj = Filter(should=conditions)
        
        # Scroll through collection with filter
        results = self.qdrant_client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_obj,
            limit=limit,
            with_payload=True
        )
        
        return [
            {
                'resource': point.payload,
                'score': 0.5,  # Default score for keyword matches
                'id': point.id
            }
            for point in results[0]
        ]
    
    def hybrid_search(
        self,
        query: str,
        collection_name: str,
        user_context: UserContext,
        limit: int = 10,
        semantic_weight: float = 0.7
    ) -> List[Dict]:
        """Combine semantic and keyword search with re-ranking"""
        keywords = self.extract_keywords(query)
        filters = self.build_filters(user_context, keywords)
        
        # Perform both searches
        semantic_results = self.semantic_search(query, collection_name, limit * 2, filters)
        keyword_results = self.keyword_search(keywords, collection_name, limit)
        
        # Merge and re-rank results
        merged_results = self.merge_results(
            semantic_results, 
            keyword_results,
            semantic_weight
        )
        
        # Apply personalization
        if user_context.user_id:
            merged_results = self.personalize_results(merged_results, user_context)
        
        # Re-rank based on multiple factors
        ranked_results = self.rerank_results(merged_results, query, user_context)
        
        return ranked_results[:limit]
    
    def merge_results(
        self,
        semantic_results: List[Dict],
        keyword_results: List[Dict],
        semantic_weight: float
    ) -> List[Dict]:
        """Merge semantic and keyword search results"""
        result_map = {}
        
        # Add semantic results
        for result in semantic_results:
            result_id = result['id']
            result_map[result_id] = {
                **result,
                'final_score': result['score'] * semantic_weight
            }
        
        # Add/update with keyword results
        keyword_weight = 1 - semantic_weight
        for result in keyword_results:
            result_id = result['id']
            if result_id in result_map:
                # Combine scores if already present
                result_map[result_id]['final_score'] += result['score'] * keyword_weight
            else:
                result_map[result_id] = {
                    **result,
                    'final_score': result['score'] * keyword_weight
                }
        
        return list(result_map.values())
    
    def personalize_results(
        self,
        results: List[Dict],
        user_context: UserContext
    ) -> List[Dict]:
        """Personalize results based on user history"""
        # Boost previously clicked resources
        if user_context.clicked_resources:
            for result in results:
                if result['id'] in user_context.clicked_resources:
                    result['final_score'] *= 0.9  # Slight penalty for repetition
        
        # Boost based on location proximity
        if user_context.location and results:
            for result in results:
                if 'coordinates' in result['resource']:
                    distance = self.calculate_distance(
                        user_context.location,
                        result['resource']['coordinates']
                    )
                    # Boost closer resources
                    proximity_boost = max(0, 1 - (distance / 50))  # 50km radius
                    result['final_score'] *= (1 + proximity_boost * 0.3)
        
        return results
    
    def rerank_results(
        self,
        results: List[Dict],
        query: str,
        user_context: UserContext
    ) -> List[Dict]:
        """Re-rank results based on multiple factors"""
        for result in results:
            resource = result['resource']
            
            # Factor 1: Freshness (recently updated resources)
            if 'last_updated' in resource:
                days_old = (datetime.now() - resource['last_updated']).days
                freshness_score = max(0, 1 - (days_old / 365))
                result['final_score'] *= (1 + freshness_score * 0.1)
            
            # Factor 2: Verification status
            if resource.get('verification_status') == 'verified':
                result['final_score'] *= 1.2
            
            # Factor 3: Service availability (24/7 services for urgent needs)
            if user_context.urgency_level == 'critical':
                if '24/7' in resource.get('contact_hours', ''):
                    result['final_score'] *= 1.5
            
            # Factor 4: Language match
            if user_context.language in resource.get('languages_available', []):
                result['final_score'] *= 1.3
            
            # Factor 5: Accessibility
            if user_context.accessibility_needs:
                accessible_features = resource.get('accessibility_features', [])
                match_count = sum(1 for need in user_context.accessibility_needs 
                                if need in accessible_features)
                if match_count > 0:
                    result['final_score'] *= (1 + match_count * 0.2)
        
        # Sort by final score
        return sorted(results, key=lambda x: x['final_score'], reverse=True)
    
    def calculate_distance(self, coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates in kilometers"""
        if not coord2:
            return float('inf')
        
        # Simplified distance calculation (Haversine formula)
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        R = 6371  # Earth's radius in kilometers
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def emergency_search(self, location: Optional[Tuple[float, float]] = None) -> List[Dict]:
        """Quick emergency search for critical services"""
        emergency_query = "emergency crisis urgent help 24/7 immediate support"
        
        context = UserContext(
            urgency_level="critical",
            location=location
        )
        
        # Search across all emergency-related collections
        results = []
        emergency_collections = [
            "act_refugee_resources",
            "critical_gaps_resources"
        ]
        
        for collection in emergency_collections:
            collection_results = self.hybrid_search(
                emergency_query,
                collection,
                context,
                limit=5,
                semantic_weight=0.5  # Balance semantic and keyword for emergencies
            )
            results.extend(collection_results)
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results[:10]
    
    def explain_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Add explanations for why each result was returned"""
        keywords = self.extract_keywords(query)
        
        for result in results:
            resource = result['resource']
            explanations = []
            
            # Check keyword matches
            description_lower = resource.get('description', '').lower()
            matched_keywords = [kw for kw in keywords if kw in description_lower]
            if matched_keywords:
                explanations.append(f"Matches: {', '.join(matched_keywords)}")
            
            # Check category matches
            if 'auto_categories' in resource:
                explanations.append(f"Categories: {', '.join(resource['auto_categories'])}")
            
            # Check special features
            if resource.get('urgency_level') == 'critical':
                explanations.append("Emergency service")
            
            if resource.get('cost') == 'free':
                explanations.append("Free service")
            
            if resource.get('verification_status') == 'verified':
                explanations.append("Verified provider")
            
            result['explanation'] = " | ".join(explanations) if explanations else "Semantic match"
        
        return results
    
    def track_search(self, user_id: str, query: str, results: List[Dict]):
        """Track search for analytics and improvement"""
        self.search_history[user_id].append({
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'results_count': len(results),
            'top_results': [r['id'] for r in results[:3]]
        })
    
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions based on partial query"""
        suggestions = []
        
        # Common search patterns
        common_searches = [
            "emergency help",
            "find a doctor",
            "legal assistance",
            "housing support",
            "job search help",
            "English classes",
            "mental health support",
            "visa assistance",
            "centrelink help",
            "free food"
        ]
        
        # Filter suggestions based on partial query
        partial_lower = partial_query.lower()
        suggestions = [s for s in common_searches if partial_lower in s.lower()]
        
        return suggestions[:5]
