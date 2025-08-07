"""
Setup Qdrant Collections for OpenAI Embeddings
This script creates/recreates Qdrant collections with OpenAI embedding dimensions (1536)
"""

import os
import sys
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
import logging
from typing import List, Dict
import json

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class QdrantOpenAISetup:
    def __init__(self):
        """Initialize Qdrant client and OpenAI client"""
        # Qdrant configuration
        self.qdrant_host = os.getenv('QDRANT_HOST', 'localhost')
        self.qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY', None)
        
        # OpenAI configuration
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            sys.exit(1)
        
        # Initialize clients
        self.setup_clients()
        
        # Collection configuration with OpenAI dimensions
        self.vector_size = 1536  # OpenAI text-embedding-ada-002 dimension
        self.collections = {
            "act_refugee_resources": "General ACT refugee support resources",
            "act_resources": "ACT-specific services and organizations",
            "general_resources": "General refugee and migrant resources",
            "economic_integration_resources": "Employment, skills, and business resources",
            "critical_gaps_resources": "Resources addressing critical service gaps"
        }
    
    def setup_clients(self):
        """Setup Qdrant and OpenAI clients"""
        try:
            # Setup Qdrant client
            if self.qdrant_api_key:
                logger.info(f"Connecting to Qdrant Cloud at {self.qdrant_host}")
                self.qdrant_client = QdrantClient(
                    host=self.qdrant_host,
                    port=self.qdrant_port,
                    api_key=self.qdrant_api_key,
                    https=True
                )
            else:
                logger.info(f"Connecting to local Qdrant at {self.qdrant_host}:{self.qdrant_port}")
                self.qdrant_client = QdrantClient(
                    host=self.qdrant_host,
                    port=self.qdrant_port
                )
            
            # Setup OpenAI client
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("Successfully connected to OpenAI API")
            
        except Exception as e:
            logger.error(f"Failed to setup clients: {e}")
            sys.exit(1)
    
    def test_connections(self):
        """Test Qdrant and OpenAI connections"""
        try:
            # Test Qdrant
            collections = self.qdrant_client.get_collections()
            logger.info(f"✓ Qdrant connection successful. Found {len(collections.collections)} existing collections")
            
            # Test OpenAI
            test_embedding = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input="test"
            )
            logger.info(f"✓ OpenAI connection successful. Embedding dimension: {len(test_embedding.data[0].embedding)}")
            
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def list_existing_collections(self):
        """List all existing collections"""
        try:
            collections = self.qdrant_client.get_collections()
            if collections.collections:
                logger.info("\n📦 Existing collections:")
                for collection in collections.collections:
                    info = self.qdrant_client.get_collection(collection.name)
                    logger.info(f"  - {collection.name}: {info.points_count} points, vector size: {info.config.params.vectors.size}")
            else:
                logger.info("No existing collections found")
            return collections.collections
        except Exception as e:
            logger.error(f"Failed to list collections: {e}")
            return []
    
    def delete_collection(self, collection_name: str):
        """Delete a specific collection"""
        try:
            self.qdrant_client.delete_collection(collection_name=collection_name)
            logger.info(f"  ✓ Deleted collection: {collection_name}")
            return True
        except Exception as e:
            logger.warning(f"  ⚠ Could not delete {collection_name}: {e}")
            return False
    
    def create_collection(self, collection_name: str, description: str):
        """Create a new collection with OpenAI embedding dimensions"""
        try:
            self.qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"  ✓ Created collection: {collection_name} ({description})")
            return True
        except Exception as e:
            logger.error(f"  ✗ Failed to create {collection_name}: {e}")
            return False
    
    def recreate_all_collections(self, force_delete: bool = False):
        """Recreate all collections with OpenAI dimensions"""
        logger.info("\n🔄 Starting collection setup for OpenAI embeddings (1536 dimensions)")
        
        # Check existing collections
        existing = self.list_existing_collections()
        existing_names = [c.name for c in existing]
        
        # Handle existing collections
        if existing_names:
            if not force_delete:
                logger.warning("\n⚠️  WARNING: This will DELETE existing collections and their data!")
                response = input("Do you want to continue? (yes/no): ").strip().lower()
                if response != 'yes':
                    logger.info("Operation cancelled")
                    return False
            
            logger.info("\n🗑️  Deleting existing collections...")
            for collection_name in existing_names:
                if collection_name in self.collections:
                    self.delete_collection(collection_name)
        
        # Create new collections
        logger.info("\n✨ Creating new collections with OpenAI dimensions...")
        success_count = 0
        for collection_name, description in self.collections.items():
            if self.create_collection(collection_name, description):
                success_count += 1
        
        logger.info(f"\n✅ Successfully created {success_count}/{len(self.collections)} collections")
        return success_count == len(self.collections)
    
    def create_sample_data(self):
        """Create sample data for testing"""
        logger.info("\n📝 Creating sample data for testing...")
        
        sample_resources = [
            {
                "name": "Companion House",
                "description": "Provides medical services, counselling, and support for refugees and asylum seekers who have experienced torture and trauma.",
                "services": ["Medical care", "Counselling", "Trauma support", "Case management"],
                "contact": {
                    "phone": "02 6251 4550",
                    "website": "https://www.companionhouse.org.au",
                    "address": "41 Templeton Street, Cook ACT 2614"
                }
            },
            {
                "name": "Migrant and Refugee Settlement Services (MARSS)",
                "description": "Helps newly arrived migrants and refugees settle in Canberra with practical support and connections to services.",
                "services": ["Settlement support", "Employment assistance", "Housing help", "Community connections"],
                "contact": {
                    "phone": "02 6248 8577",
                    "website": "https://www.marss.org.au",
                    "address": "1/113 Canberra Avenue, Griffith ACT 2603"
                }
            },
            {
                "name": "Canberra Refugee Support",
                "description": "Volunteer organization providing practical support, advocacy, and friendship to refugees and asylum seekers.",
                "services": ["Advocacy", "Practical support", "Social connections", "Emergency assistance"],
                "contact": {
                    "phone": "0475 461 028",
                    "website": "https://actrefugee.org.au",
                    "email": "info@actrefugee.org.au"
                }
            }
        ]
        
        try:
            # Generate embeddings for sample data
            texts = [f"{r['name']}: {r['description']}" for r in sample_resources]
            
            logger.info("Generating OpenAI embeddings for sample data...")
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            
            # Prepare points for insertion
            points = []
            for i, (resource, embedding_data) in enumerate(zip(sample_resources, response.data)):
                point = PointStruct(
                    id=i + 1,
                    vector=embedding_data.embedding,
                    payload=resource
                )
                points.append(point)
            
            # Insert into main collection
            collection_name = "act_refugee_resources"
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            logger.info(f"✓ Inserted {len(points)} sample resources into {collection_name}")
            
            # Verify insertion
            collection_info = self.qdrant_client.get_collection(collection_name)
            logger.info(f"✓ Collection now contains {collection_info.points_count} points")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create sample data: {e}")
            return False
    
    def test_search(self):
        """Test search functionality with OpenAI embeddings"""
        logger.info("\n🔍 Testing search with OpenAI embeddings...")
        
        test_queries = [
            "I need help with trauma and counselling",
            "Help me find a job and settle in Canberra",
            "Emergency support for refugees"
        ]
        
        try:
            for query in test_queries:
                logger.info(f"\nSearching for: '{query}'")
                
                # Generate embedding for query
                response = self.openai_client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=query
                )
                query_vector = response.data[0].embedding
                
                # Search in Qdrant
                search_result = self.qdrant_client.search(
                    collection_name="act_refugee_resources",
                    query_vector=query_vector,
                    limit=2
                )
                
                if search_result:
                    for i, result in enumerate(search_result, 1):
                        logger.info(f"  {i}. {result.payload['name']} (score: {result.score:.3f})")
                else:
                    logger.info("  No results found")
            
            return True
            
        except Exception as e:
            logger.error(f"Search test failed: {e}")
            return False

def main():
    """Main setup function"""
    print("=" * 60)
    print("Qdrant Setup for OpenAI Embeddings")
    print("=" * 60)
    
    # Initialize setup
    setup = QdrantOpenAISetup()
    
    # Test connections
    logger.info("\n🔌 Testing connections...")
    if not setup.test_connections():
        logger.error("Connection test failed. Please check your credentials.")
        sys.exit(1)
    
    # Show menu
    print("\n" + "=" * 60)
    print("Setup Options:")
    print("1. Recreate all collections (DELETE existing data)")
    print("2. Create sample data in collections")
    print("3. Test search functionality")
    print("4. List existing collections only")
    print("5. Full setup (recreate + sample data + test)")
    print("0. Exit")
    print("=" * 60)
    
    choice = input("\nSelect option (0-5): ").strip()
    
    if choice == "1":
        setup.recreate_all_collections()
    elif choice == "2":
        setup.create_sample_data()
    elif choice == "3":
        setup.test_search()
    elif choice == "4":
        setup.list_existing_collections()
    elif choice == "5":
        # Full setup
        if setup.recreate_all_collections():
            setup.create_sample_data()
            setup.test_search()
    elif choice == "0":
        logger.info("Exiting...")
    else:
        logger.warning("Invalid option selected")
    
    print("\n" + "=" * 60)
    print("Setup complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
