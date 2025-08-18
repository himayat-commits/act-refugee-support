"""Test Qdrant connection and search directly"""

import os

from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()

# Initialize clients
qdrant_client = QdrantClient(
    host=os.getenv("QDRANT_HOST"),
    port=int(os.getenv("QDRANT_PORT", 6333)),
    api_key=os.getenv("QDRANT_API_KEY"),
    https=True,
)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Check collection
collection_info = qdrant_client.get_collection("act_refugee_resources")
print(f"Collection status: {collection_info.status}")
print(f"Points count: {collection_info.points_count}")

# Test search
query = "food assistance"
print(f"\nSearching for: '{query}'")

# Generate embedding
response = openai_client.embeddings.create(model="text-embedding-ada-002", input=query)
embedding = response.data[0].embedding

# Search

results = qdrant_client.query_points(collection_name="act_refugee_resources", query=embedding, limit=3)

print(f"\nFound {len(results.points)} results:")
for point in results.points:
    print(f"- {point.payload.get('name')} (score: {point.score:.3f})")
    print(f"  Services: {point.payload.get('services')[:100]}...")
