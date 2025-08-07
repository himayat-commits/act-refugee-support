import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging
import openai
from typing import List, Union

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QdrantConfig:
    def __init__(self):
        self.host = os.getenv("QDRANT_HOST", "localhost")
        self.port = int(os.getenv("QDRANT_PORT", 6333))
        self.api_key = os.getenv("QDRANT_API_KEY", None)
        self.collection_name = "act_refugee_resources"
        self.vector_size = 1536  # OpenAI embedding dimension
        self.use_local_embeddings = os.getenv("USE_LOCAL_EMBEDDINGS", "false").lower() == "true"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
    def get_client(self):
        if self.api_key:
            return QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key,
                https=True
            )
        else:
            return QdrantClient(
                host=self.host,
                port=self.port
            )
    
    def get_embedding_model(self):
        """Returns a lightweight embedding model using OpenAI"""
        return OpenAIEmbedding(self.openai_api_key)

class OpenAIEmbedding:
    """Lightweight OpenAI embedding wrapper"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        if api_key:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
        else:
            logger.warning("No OpenAI API key provided, using mock embeddings")
            self.client = None
    
    def encode(self, texts: Union[str, List[str]], convert_to_tensor=False):
        """Encode texts using OpenAI embeddings"""
        if self.client is None:
            # Return mock embeddings for testing
            import numpy as np
            if isinstance(texts, str):
                return np.random.randn(1536).tolist()
            return [np.random.randn(1536).tolist() for _ in texts]
        
        if isinstance(texts, str):
            texts = [texts]
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-ada-002",
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
            
            if len(embeddings) == 1 and isinstance(texts, str):
                return embeddings[0]
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            # Return random embeddings as fallback
            import numpy as np
            if len(texts) == 1:
                return np.random.randn(1536).tolist()
            return [np.random.randn(1536).tolist() for _ in texts]

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
