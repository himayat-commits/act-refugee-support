import logging
import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantConfig:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        self.api_key = os.getenv("QDRANT_API_KEY", None)
        self.collection_name = "act_refugee_resources"
        self.vector_size = 1536  # OpenAI embedding size
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.embedding_model = "text-embedding-3-small"  # or text-embedding-ada-002
        self._openai_client = None

    def get_client(self):
        if self.api_key:
            return QdrantClient(host=self.host, port=self.port, api_key=self.api_key)
        else:
            return QdrantClient(host=self.host, port=self.port)

    def get_openai_client(self):
        if self._openai_client is None:
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            self._openai_client = OpenAI(api_key=self.openai_api_key)
            logger.info("OpenAI client initialized")
        return self._openai_client

    def get_embeddings(self, texts):
        """Generate embeddings using OpenAI API"""
        client = self.get_openai_client()
        
        # Handle single text or list of texts
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            response = client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
            
            # Return single embedding if single text was provided
            if len(texts) == 1:
                return embeddings[0]
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise


class CollectionManager:
    def __init__(self, config: QdrantConfig):
        self.config = config
        self.client = config.get_client()
        self.config = config

    def create_collection(self):
        try:
            collections = self.client.get_collections()
            if self.config.collection_name in [c.name for c in collections.collections]:
                logger.info(f"Collection {self.config.collection_name} already exists")
                return

            self.client.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(size=self.config.vector_size, distance=Distance.COSINE),
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
