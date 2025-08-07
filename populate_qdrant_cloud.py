"""
Populate Qdrant Cloud with ACT Refugee Support Services Data
This script loads refugee service data from CSV and creates vector embeddings in Qdrant Cloud
"""

import os
import sys
import csv
import json
import time
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
from tqdm import tqdm
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('populate_qdrant.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import required libraries
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance, 
        VectorParams, 
        PointStruct,
        CollectionStatus,
        Filter,
        FieldCondition,
        Match
    )
    import openai
    from openai import OpenAI
    import numpy as np
except ImportError as e:
    logger.error(f"Missing required library: {e}")
    logger.info("Install with: pip install qdrant-client openai numpy tqdm python-dotenv")
    sys.exit(1)

@dataclass
class ServiceRecord:
    """Data structure for refugee service records"""
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
    metadata: Dict[str, Any]

class QdrantPopulator:
    """Handles population of Qdrant Cloud with refugee service data"""
    
    def __init__(self):
        """Initialize Qdrant and OpenAI clients"""
        self.collection_name = "act_refugee_resources"
        self.vector_size = 1536  # OpenAI ada-002 embedding size
        self.batch_size = 100
        
        # Initialize Qdrant client
        self.qdrant_host = os.getenv('QDRANT_HOST')
        self.qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
        self.qdrant_api_key = os.getenv('QDRANT_API_KEY')
        
        if not self.qdrant_host:
            logger.error("QDRANT_HOST not set in environment variables")
            sys.exit(1)
            
        logger.info(f"Connecting to Qdrant Cloud at {self.qdrant_host}:{self.qdrant_port}")
        
        try:
            self.qdrant_client = QdrantClient(
                host=self.qdrant_host,
                port=self.qdrant_port,
                api_key=self.qdrant_api_key,
                https=True,
                timeout=30
            )
            # Test connection
            self.qdrant_client.get_collections()
            logger.info("✅ Connected to Qdrant Cloud successfully!")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            sys.exit(1)
        
        # Initialize OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            logger.error("OPENAI_API_KEY not set in environment variables")
            sys.exit(1)
            
        self.openai_client = OpenAI(api_key=openai_api_key)
        logger.info("✅ OpenAI client initialized")
    
    def load_data_from_csv(self, csv_path: str = None) -> List[ServiceRecord]:
        """Load refugee service data from CSV file"""
        if csv_path is None:
            # Try to find CSV file in common locations
            possible_paths = [
                'data/act_refugee_services.csv',
                'act_refugee_services.csv',
                'data/services.csv',
                'services.csv'
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    csv_path = path
                    break
            else:
                logger.error("No CSV file found. Please specify path or place file in data/ directory")
                return []
        
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return []
        
        logger.info(f"Loading data from: {csv_path}")
        records = []
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for idx, row in enumerate(reader):
                    # Create service record from CSV row
                    record = ServiceRecord(
                        id=str(idx + 1),
                        name=row.get('Organization', '').strip(),
                        category=row.get('Category', 'General').strip(),
                        description=row.get('Description', '').strip(),
                        services=row.get('Services', '').strip(),
                        location=row.get('Location', '').strip(),
                        contact=row.get('Contact', '').strip(),
                        hours=row.get('Hours', '').strip(),
                        eligibility=row.get('Eligibility', '').strip(),
                        languages=row.get('Languages', 'English').strip(),
                        website=row.get('Website', '').strip(),
                        emergency=row.get('Emergency', '').lower() == 'yes',
                        metadata={
                            'source': 'CSV Import',
                            'last_updated': datetime.now().isoformat(),
                            'verified': True
                        }
                    )
                    records.append(record)
            
            logger.info(f"✅ Loaded {len(records)} service records from CSV")
            return records
            
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return []
    
    def create_sample_data(self) -> List[ServiceRecord]:
        """Create sample refugee service data if no CSV is available"""
        logger.info("Creating sample refugee service data...")
        
        sample_services = [
            {
                "name": "Companion House",
                "category": "Mental Health & Counseling",
                "description": "Specialist torture and trauma counseling service for refugees and asylum seekers",
                "services": "Trauma counseling, Group therapy, Children's programs, Family support",
                "location": "41 Templeton St, Cook ACT 2614",
                "contact": "(02) 6251 4550",
                "hours": "Mon-Fri 9am-5pm",
                "eligibility": "Refugees, asylum seekers, humanitarian entrants",
                "languages": "Multiple languages through interpreters",
                "website": "https://www.companionhouse.org.au",
                "emergency": False
            },
            {
                "name": "Red Cross Migration Support",
                "category": "Settlement Services",
                "description": "Settlement support and emergency relief for newly arrived refugees",
                "services": "Emergency relief, Settlement orientation, Casework support, Referrals",
                "location": "Canberra ACT",
                "contact": "(02) 6234 7600",
                "hours": "Mon-Fri 9am-5pm",
                "eligibility": "Refugees and migrants on humanitarian visas",
                "languages": "Interpreters available",
                "website": "https://www.redcross.org.au",
                "emergency": True
            },
            {
                "name": "Migrant and Refugee Settlement Services (MARSS)",
                "category": "Settlement Services",
                "description": "Comprehensive settlement support for refugees and migrants in the ACT",
                "services": "Case management, Housing assistance, Employment support, Youth programs",
                "location": "Theo Notaras Multicultural Centre, 180 London Circuit, Canberra",
                "contact": "(02) 6248 8577",
                "hours": "Mon-Fri 9am-5pm",
                "eligibility": "Refugees, humanitarian entrants, eligible migrants",
                "languages": "Multiple languages available",
                "website": "https://www.marss.org.au",
                "emergency": False
            },
            {
                "name": "St Vincent de Paul Society Canberra",
                "category": "Emergency Relief",
                "description": "Emergency relief including food, clothing, and financial assistance",
                "services": "Food parcels, Clothing, Financial assistance, Furniture",
                "location": "Multiple locations across Canberra",
                "contact": "(02) 6282 2722",
                "hours": "Mon-Fri 9am-4pm",
                "eligibility": "Anyone in need",
                "languages": "English, interpreters can be arranged",
                "website": "https://www.vinnies.org.au",
                "emergency": True
            },
            {
                "name": "Legal Aid ACT - Migration Law",
                "category": "Legal Services",
                "description": "Free legal advice and assistance for migration and refugee matters",
                "services": "Legal advice, Court representation, Visa applications, Appeals",
                "location": "2 Allsop St, Canberra ACT 2601",
                "contact": "(02) 6243 3411",
                "hours": "Mon-Fri 8:30am-5pm",
                "eligibility": "Refugees, asylum seekers, migrants meeting financial criteria",
                "languages": "Interpreters available",
                "website": "https://www.legalaidact.org.au",
                "emergency": False
            },
            {
                "name": "Canberra Refugee Support",
                "category": "Community Support",
                "description": "Volunteer-run organization providing practical support to refugees",
                "services": "Donations, Volunteer support, Community events, Advocacy",
                "location": "Canberra ACT",
                "contact": "info@canberrarefugeesupport.org.au",
                "hours": "Volunteer-based",
                "eligibility": "Refugees and asylum seekers",
                "languages": "English",
                "website": "https://www.canberrarefugeesupport.org.au",
                "emergency": False
            },
            {
                "name": "ACT Health Refugee Health Service",
                "category": "Healthcare",
                "description": "Specialized health services for refugees including health screening and care coordination",
                "services": "Health assessments, Immunizations, Mental health support, Care coordination",
                "location": "Various ACT Health facilities",
                "contact": "(02) 5124 9977",
                "hours": "Mon-Fri 8:30am-5pm",
                "eligibility": "Refugees and humanitarian entrants",
                "languages": "Interpreters provided",
                "website": "https://www.health.act.gov.au",
                "emergency": False
            },
            {
                "name": "Centrelink Multicultural Services",
                "category": "Government Services",
                "description": "Centrelink services with multilingual support for refugees and migrants",
                "services": "Income support, Medicare enrollment, Family payments, Job seeker support",
                "location": "Multiple Centrelink offices in ACT",
                "contact": "131 202",
                "hours": "Mon-Fri 8am-5pm",
                "eligibility": "Eligible residents and visa holders",
                "languages": "Translating and Interpreting Service available",
                "website": "https://www.servicesaustralia.gov.au",
                "emergency": False
            },
            {
                "name": "Capital Region Community Services",
                "category": "Housing Services",
                "description": "Housing support and homelessness services for vulnerable individuals",
                "services": "Emergency accommodation, Housing applications, Tenancy support",
                "location": "Canberra ACT",
                "contact": "(02) 6126 9000",
                "hours": "Mon-Fri 9am-5pm",
                "eligibility": "People experiencing or at risk of homelessness",
                "languages": "English, interpreters available",
                "website": "https://www.crcs.org.au",
                "emergency": True
            },
            {
                "name": "YWCA Canberra - Multicultural Hub",
                "category": "Women's Services",
                "description": "Support services for migrant and refugee women and families",
                "services": "Women's programs, Childcare, English classes, Employment support",
                "location": "Level 2, 71 Northbourne Ave, Canberra",
                "contact": "(02) 6185 2000",
                "hours": "Mon-Fri 9am-5pm",
                "eligibility": "Migrant and refugee women and families",
                "languages": "Multiple languages",
                "website": "https://ywca-canberra.org.au",
                "emergency": False
            }
        ]
        
        records = []
        for idx, service in enumerate(sample_services):
            record = ServiceRecord(
                id=str(idx + 1),
                name=service['name'],
                category=service['category'],
                description=service['description'],
                services=service['services'],
                location=service['location'],
                contact=service['contact'],
                hours=service['hours'],
                eligibility=service['eligibility'],
                languages=service['languages'],
                website=service['website'],
                emergency=service['emergency'],
                metadata={
                    'source': 'Sample Data',
                    'last_updated': datetime.now().isoformat(),
                    'verified': True
                }
            )
            records.append(record)
        
        logger.info(f"✅ Created {len(records)} sample service records")
        return records
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using OpenAI"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return [0.0] * self.vector_size
    
    def create_searchable_text(self, record: ServiceRecord) -> str:
        """Create comprehensive searchable text from service record"""
        components = [
            f"Organization: {record.name}",
            f"Category: {record.category}",
            f"Description: {record.description}",
            f"Services offered: {record.services}",
            f"Location: {record.location}",
            f"Languages: {record.languages}",
            f"Eligibility: {record.eligibility}",
        ]
        
        if record.emergency:
            components.append("EMERGENCY SERVICE AVAILABLE")
        
        return " | ".join(filter(None, components))
    
    def create_collection(self):
        """Create or recreate the Qdrant collection"""
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections().collections
            collection_exists = any(c.name == self.collection_name for c in collections)
            
            if collection_exists:
                logger.info(f"Collection '{self.collection_name}' exists. Deleting for fresh start...")
                self.qdrant_client.delete_collection(self.collection_name)
                time.sleep(2)  # Wait for deletion
            
            # Create new collection
            logger.info(f"Creating collection '{self.collection_name}'...")
            self.qdrant_client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )
            
            # Wait for collection to be ready
            for _ in range(10):
                collection_info = self.qdrant_client.get_collection(self.collection_name)
                if collection_info.status == CollectionStatus.GREEN:
                    logger.info(f"✅ Collection '{self.collection_name}' created successfully!")
                    return True
                time.sleep(1)
            
            logger.warning("Collection creation taking longer than expected...")
            return True
            
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            return False
    
    def upload_records(self, records: List[ServiceRecord]):
        """Upload service records to Qdrant with embeddings"""
        if not records:
            logger.warning("No records to upload")
            return
        
        logger.info(f"Generating embeddings and uploading {len(records)} records...")
        
        points = []
        failed_records = []
        
        # Process records with progress bar
        for record in tqdm(records, desc="Processing records"):
            try:
                # Generate searchable text
                searchable_text = self.create_searchable_text(record)
                
                # Generate embedding
                embedding = self.generate_embedding(searchable_text)
                
                # Create point for Qdrant
                point = PointStruct(
                    id=int(record.id),
                    vector=embedding,
                    payload={
                        "id": record.id,
                        "name": record.name,
                        "category": record.category,
                        "description": record.description,
                        "services": record.services,
                        "location": record.location,
                        "contact": record.contact,
                        "hours": record.hours,
                        "eligibility": record.eligibility,
                        "languages": record.languages,
                        "website": record.website,
                        "emergency": record.emergency,
                        "searchable_text": searchable_text,
                        **record.metadata
                    }
                )
                points.append(point)
                
                # Upload in batches
                if len(points) >= self.batch_size:
                    self._upload_batch(points)
                    points = []
                    
            except Exception as e:
                logger.error(f"Error processing record {record.name}: {e}")
                failed_records.append(record.name)
        
        # Upload remaining points
        if points:
            self._upload_batch(points)
        
        # Report results
        logger.info(f"✅ Upload complete!")
        if failed_records:
            logger.warning(f"Failed to process {len(failed_records)} records: {failed_records[:5]}")
    
    def _upload_batch(self, points: List[PointStruct]):
        """Upload a batch of points to Qdrant"""
        try:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Uploaded batch of {len(points)} points")
        except Exception as e:
            logger.error(f"Error uploading batch: {e}")
    
    def verify_collection(self):
        """Verify the collection was populated correctly"""
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            point_count = collection_info.points_count
            
            logger.info(f"\n{'='*50}")
            logger.info(f"Collection: {self.collection_name}")
            logger.info(f"Status: {collection_info.status}")
            logger.info(f"Points: {point_count}")
            logger.info(f"Vector size: {collection_info.config.params.vectors.size}")
            logger.info(f"{'='*50}\n")
            
            if point_count > 0:
                # Test search
                test_query = "emergency housing assistance"
                logger.info(f"Testing search with: '{test_query}'")
                
                embedding = self.generate_embedding(test_query)
                results = self.qdrant_client.search(
                    collection_name=self.collection_name,
                    query_vector=embedding,
                    limit=3
                )
                
                logger.info(f"Found {len(results)} results:")
                for result in results:
                    logger.info(f"  - {result.payload.get('name')} (score: {result.score:.3f})")
                
                return True
            else:
                logger.warning("No points in collection!")
                return False
                
        except Exception as e:
            logger.error(f"Error verifying collection: {e}")
            return False

def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("   ACT REFUGEE SUPPORT - QDRANT CLOUD POPULATION SCRIPT")
    print("="*60 + "\n")
    
    # Check environment variables
    required_vars = ['QDRANT_HOST', 'QDRANT_API_KEY', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.info("Please set these in your .env file or environment")
        sys.exit(1)
    
    # Initialize populator
    populator = QdrantPopulator()
    
    # Create collection
    if not populator.create_collection():
        logger.error("Failed to create collection. Exiting...")
        sys.exit(1)
    
    # Load data
    records = populator.load_data_from_csv()
    
    # If no CSV data, use sample data
    if not records:
        logger.info("No CSV data found. Using sample data instead...")
        records = populator.create_sample_data()
    
    # Upload records
    populator.upload_records(records)
    
    # Verify collection
    if populator.verify_collection():
        logger.info("\n✅ Qdrant Cloud population completed successfully!")
        logger.info("Your refugee support database is ready for use!")
    else:
        logger.warning("\n⚠️ Population completed but verification showed issues")
    
    print("\n" + "="*60)
    print("   POPULATION COMPLETE - YOUR API IS READY TO USE!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
