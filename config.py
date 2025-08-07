import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantConfig:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        self.api_key = os.getenv("QDRANT_API_KEY", None)
        self.collection_name = "act_refugee_resources"
        self.vector_size = 384
        self.use_local_embeddings = os.getenv("USE_LOCAL_EMBEDDINGS", "true").lower() == "true"
        
    def get_client(self):
        if self.api_key:
            return QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key
            )
        else:
            return QdrantClient(
                host=self.host,
                port=self.port
            )
    
    def get_embedding_model(self):
        if self.use_local_embeddings:
            return SentenceTransformer('all-MiniLM-L6-v2')
        else:
            raise NotImplementedError("OpenAI embeddings not implemented in this example")

class CollectionManager:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client = config.get_client()
        self.embedding_model = config.get_embedding_model()
        
    def create_collection(self):
        try:
            collections = self.client.get_collections()
            if self.config.collection_name in [c.name for c in collections.collections]:
                logger.info(f"Collection {self.config.collection_name} already exists")
                return
            
            self.client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(
                    size=self.config.vector_size,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created collection: {self.config.collection_name}")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            raise
    
    def delete_collection(self):
        try:
            self.client.delete_collection(collection_name=self.config.collection_name)
            logger.info(f"Deleted collection: {self.config.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise