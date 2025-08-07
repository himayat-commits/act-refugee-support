import uuid
from typing import List, Dict, Any
from qdrant_client.models import PointStruct
from config import QdrantConfig, CollectionManager
from models import Resource, ResourceCategory
import logging

logger = logging.getLogger(__name__)

class DataIngestion:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client = config.get_client()
        self.embedding_model = config.get_embedding_model()
        self.collection_manager = CollectionManager(config)
        
    def create_embedding_text(self, resource: Resource) -> str:
        text_parts = [
            f"Service: {resource.name}",
            f"Category: {resource.category.value.replace('_', ' ')}",
            f"Description: {resource.description}",
            f"Services: {', '.join(resource.services_provided)}",
            f"Location: {resource.location}",
            f"Eligibility: {resource.eligibility or 'All migrants and refugees'}",
            f"Languages: {', '.join(resource.languages_available)}",
            f"Keywords: {', '.join(resource.keywords)}"
        ]
        
        if resource.subcategory:
            text_parts.append(f"Subcategory: {resource.subcategory}")
            
        return " | ".join(text_parts)
    
    def resource_to_payload(self, resource: Resource) -> Dict[str, Any]:
        return {
            "id": resource.id,
            "name": resource.name,
            "description": resource.description,
            "category": resource.category.value,
            "subcategory": resource.subcategory,
            "contact_phone": resource.contact.phone,
            "contact_email": resource.contact.email,
            "contact_website": resource.contact.website,
            "contact_address": resource.contact.address,
            "contact_hours": resource.contact.hours,
            "eligibility": resource.eligibility,
            "services_provided": resource.services_provided,
            "languages_available": resource.languages_available,
            "cost": resource.cost,
            "location": resource.location,
            "urgency_level": resource.urgency_level,
            "keywords": resource.keywords,
            "last_updated": resource.last_updated.isoformat(),
            "additional_info": resource.additional_info
        }
    
    def ingest_resources(self, resources: List[Resource]) -> bool:
        try:
            self.collection_manager.create_collection()
            
            points = []
            for resource in resources:
                embedding_text = self.create_embedding_text(resource)
                embedding = self.embedding_model.encode(embedding_text).tolist()
                
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding,
                    payload=self.resource_to_payload(resource)
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=self.config.collection_name,
                points=points
            )
            
            logger.info(f"Successfully ingested {len(resources)} resources")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting resources: {e}")
            return False
    
    def update_resource(self, resource: Resource) -> bool:
        try:
            embedding_text = self.create_embedding_text(resource)
            embedding = self.embedding_model.encode(embedding_text).tolist()
            
            point = PointStruct(
                id=resource.id,
                vector=embedding,
                payload=self.resource_to_payload(resource)
            )
            
            self.client.upsert(
                collection_name=self.config.collection_name,
                points=[point]
            )
            
            logger.info(f"Successfully updated resource: {resource.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating resource: {e}")
            return False
    
    def delete_resource(self, resource_id: str) -> bool:
        try:
            self.client.delete(
                collection_name=self.config.collection_name,
                points_selector=[resource_id]
            )
            
            logger.info(f"Successfully deleted resource: {resource_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting resource: {e}")
            return False