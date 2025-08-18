"""Simplified search engine that works with the actual Qdrant data structure"""

import logging
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger(__name__)


@dataclass
class SimpleResource:
    """Simplified resource model matching our actual data"""

    id: str
    name: str
    category: str
    description: str
    services: str
    location: str
    contact: str
    hours: str
    eligibility: str
    languages: str
    website: str
    emergency: bool


class SimpleSearchEngine:
    def __init__(self, config):
        self.config = config
        self.client = config.get_client()
        self.config = config

    def search(self, query_text: str, limit: int = 3) -> List[Dict]:
        """Perform a simple search and return results"""
        try:
            # Generate embedding using OpenAI
            logger.info(f"Generating embedding for: {query_text}")
            query_embedding = self.config.get_embeddings(query_text)

            # Ensure it's a list (OpenAI returns list directly)
            if not isinstance(query_embedding, list):
                query_embedding = list(query_embedding)

            # Search in Qdrant
            logger.info(f"Searching in collection: {self.config.collection_name}")

            # Use search method (compatible with our setup)
            results = self.client.search(
                collection_name=self.config.collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True,
            )

            # Format results
            formatted_results = []
            for point in results:
                payload = point.payload
                formatted_results.append(
                    {
                        "id": payload.get("id", ""),
                        "name": payload.get("name", "Unknown Service"),
                        "category": payload.get("category", "General"),
                        "description": payload.get("description", ""),
                        "services": payload.get("services", ""),
                        "location": payload.get("location", ""),
                        "contact": payload.get("contact", ""),
                        "hours": payload.get("hours", ""),
                        "eligibility": payload.get("eligibility", ""),
                        "languages": payload.get("languages", "English"),
                        "website": payload.get("website", ""),
                        "emergency": payload.get("emergency", False),
                        "score": point.score,
                    }
                )

            logger.info(f"Found {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Error performing search: {e}", exc_info=True)
            return []

    def search_urgent_services(self, limit: int = 5) -> List[Dict]:
        """Search for emergency services"""
        try:
            # For now, just search for emergency-related terms
            return self.search("emergency urgent crisis help 24/7", limit)
        except Exception as e:
            logger.error(f"Error searching urgent services: {e}")
            return []
