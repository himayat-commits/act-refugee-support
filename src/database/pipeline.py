"""
Enhanced Data Pipeline for Resource Ingestion
Handles validation, deduplication, and batch processing
"""

import json
import csv
from typing import List, Dict, Optional
import hashlib
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
import logging
from openai import OpenAI
from qdrant_client.models import PointStruct
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Supported data source types"""

    CSV = "csv"
    JSON = "json"
    API = "api"
    MANUAL = "manual"
    SCRAPER = "scraper"


class ResourceValidator(BaseModel):
    """Enhanced resource validation with data quality checks"""

    name: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10, max_length=2000)
    services_provided: List[str] = Field(default_factory=list)
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    contact_website: Optional[str] = None
    contact_address: Optional[str] = None
    languages_available: List[str] = Field(default_factory=list)
    cost: str = Field(default="Contact for pricing")
    eligibility: Optional[str] = None
    urgency_level: str = Field(default="standard")
    last_updated: datetime = Field(default_factory=datetime.now)
    data_source: DataSource = Field(default=DataSource.MANUAL)
    verification_status: str = Field(default="unverified")

    @validator("contact_phone")
    def validate_phone(cls, v):
        if v and not v.replace(" ", "").replace("-", "").replace("+", "").isdigit():
            raise ValueError("Invalid phone number format")
        return v

    @validator("contact_email")
    def validate_email(cls, v):
        if v and "@" not in v:
            raise ValueError("Invalid email format")
        return v

    @validator("contact_website")
    def validate_website(cls, v):
        if v and not (v.startswith("http://") or v.startswith("https://")):
            v = f"https://{v}"
        return v


class DataPipeline:
    def __init__(self, config=None):
        """Initialize data pipeline with configuration"""
        self.config = config
        self.openai_client = OpenAI()
        self.qdrant_client = self.config.get_client() if config else None
        self.processed_hashes = set()
        self.stats = {"total_processed": 0, "successful": 0, "failed": 0, "duplicates": 0}

    def generate_resource_id(self, resource: Dict) -> str:
        """Generate unique ID for resource based on content"""
        content = f"{resource['name']}_{resource.get('contact_phone', '')}_{resource.get('contact_email', '')}"
        return hashlib.md5(content.encode()).hexdigest()

    def detect_duplicates(self, resources: List[Dict]) -> List[Dict]:
        """Detect and remove duplicate resources"""
        unique_resources = []
        for resource in resources:
            resource_id = self.generate_resource_id(resource)
            if resource_id not in self.processed_hashes:
                self.processed_hashes.add(resource_id)
                unique_resources.append(resource)
            else:
                self.stats["duplicates"] += 1
                logger.warning(f"Duplicate detected: {resource['name']}")
        return unique_resources

    def validate_resources(self, resources: List[Dict]) -> List[Dict]:
        """Validate resources using Pydantic model"""
        validated = []
        for resource in resources:
            try:
                validated_resource = ResourceValidator(**resource)
                validated.append(validated_resource.dict())
                self.stats["successful"] += 1
            except Exception as e:
                logger.error(f"Validation failed for {resource.get('name', 'Unknown')}: {e}")
                self.stats["failed"] += 1
        return validated

    def enrich_resource(self, resource: Dict) -> Dict:
        """Enrich resource with additional metadata"""
        # Add geocoding for addresses
        if resource.get("contact_address"):
            # TODO: Add geocoding API integration
            resource["coordinates"] = None

        # Add category classification
        resource["auto_categories"] = self.classify_resource(resource)

        # Add quality score
        resource["quality_score"] = self.calculate_quality_score(resource)

        return resource

    def classify_resource(self, resource: Dict) -> List[str]:
        """Auto-classify resource into categories using keywords"""
        categories = []
        text = f"{resource['name']} {resource['description']} {' '.join(resource.get('services_provided', []))}"
        text_lower = text.lower()

        category_keywords = {
            "healthcare": ["health", "medical", "doctor", "hospital", "mental", "counseling"],
            "legal": ["legal", "lawyer", "visa", "immigration", "citizenship"],
            "education": ["education", "school", "training", "english", "language", "amep"],
            "employment": ["job", "work", "employment", "career", "skill"],
            "housing": ["housing", "accommodation", "shelter", "rent", "homeless"],
            "emergency": ["emergency", "crisis", "urgent", "24/7", "immediate"],
            "financial": ["financial", "money", "loan", "centrelink", "payment"],
        }

        for category, keywords in category_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                categories.append(category)

        return categories

    def calculate_quality_score(self, resource: Dict) -> float:
        """Calculate data quality score for resource"""
        score = 0.0
        max_score = 10.0

        # Check completeness
        if resource.get("name"):
            score += 1
        if resource.get("description") and len(resource["description"]) > 50:
            score += 1
        if resource.get("contact_phone"):
            score += 1
        if resource.get("contact_email"):
            score += 1
        if resource.get("contact_website"):
            score += 1
        if resource.get("contact_address"):
            score += 1
        if resource.get("services_provided"):
            score += 1
        if resource.get("languages_available"):
            score += 1
        if resource.get("cost"):
            score += 1
        if resource.get("verification_status") == "verified":
            score += 1

        return score / max_score

    async def batch_generate_embeddings(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """Generate embeddings in batches to optimize API usage"""
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            try:
                response = self.openai_client.embeddings.create(model="text-embedding-ada-002", input=batch)
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Embedding generation failed for batch {i}: {e}")
                # Return zero embeddings for failed batch
                embeddings.extend([[0.0] * 1536 for _ in batch])

        return embeddings

    async def ingest_from_csv(self, file_path: str, collection_name: str) -> Dict:
        """Ingest resources from CSV file"""
        resources = []

        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                # Map CSV columns to resource fields
                resource = {
                    "name": row.get("name", ""),
                    "description": row.get("description", ""),
                    "services_provided": row.get("services", "").split(","),
                    "contact_phone": row.get("phone", ""),
                    "contact_email": row.get("email", ""),
                    "contact_website": row.get("website", ""),
                    "contact_address": row.get("address", ""),
                    "languages_available": row.get("languages", "").split(","),
                    "cost": row.get("cost", "Contact for pricing"),
                    "data_source": DataSource.CSV,
                }
                resources.append(resource)

        return await self.process_resources(resources, collection_name)

    async def ingest_from_json(self, file_path: str, collection_name: str) -> Dict:
        """Ingest resources from JSON file"""
        with open(file_path, "r", encoding="utf-8") as file:
            resources = json.load(file)

        # Add source metadata
        for resource in resources:
            resource["data_source"] = DataSource.JSON

        return await self.process_resources(resources, collection_name)

    async def process_resources(self, resources: List[Dict], collection_name: str) -> Dict:
        """Process and ingest resources into Qdrant"""
        logger.info(f"Processing {len(resources)} resources for {collection_name}")

        # Step 1: Remove duplicates
        unique_resources = self.detect_duplicates(resources)
        logger.info(f"Unique resources after deduplication: {len(unique_resources)}")

        # Step 2: Validate
        validated_resources = self.validate_resources(unique_resources)
        logger.info(f"Valid resources: {len(validated_resources)}")

        # Step 3: Enrich
        enriched_resources = [self.enrich_resource(r) for r in validated_resources]

        # Step 4: Generate embeddings
        texts = [f"{r['name']}: {r['description']}" for r in enriched_resources]
        embeddings = await self.batch_generate_embeddings(texts)

        # Step 5: Prepare points for Qdrant
        points = []
        for i, (resource, embedding) in enumerate(zip(enriched_resources, embeddings)):
            point = PointStruct(id=self.generate_resource_id(resource), vector=embedding, payload=resource)
            points.append(point)

        # Step 6: Upsert to Qdrant
        if self.qdrant_client and points:
            operation_info = self.qdrant_client.upsert(collection_name=collection_name, points=points, wait=True)
            logger.info(f"Uploaded {len(points)} resources to {collection_name}")

        self.stats["total_processed"] = len(resources)

        return self.stats

    def export_statistics(self, output_path: str = "ingestion_stats.json"):
        """Export ingestion statistics"""
        stats_with_timestamp = {**self.stats, "timestamp": datetime.now().isoformat()}

        with open(output_path, "w") as f:
            json.dump(stats_with_timestamp, f, indent=2)

        logger.info(f"Statistics exported to {output_path}")
        return stats_with_timestamp


# Example usage
async def main():
    """Example usage of the data pipeline"""
    from src.core.config import QdrantConfig

    config = QdrantConfig()
    pipeline = DataPipeline(config)

    # Ingest from different sources
    # await pipeline.ingest_from_csv('resources.csv', 'act_resources')
    # await pipeline.ingest_from_json('resources.json', 'general_resources')

    # Export statistics
    pipeline.export_statistics()


if __name__ == "__main__":
    asyncio.run(main())
