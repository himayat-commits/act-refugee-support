"""Debug API search"""

import os
os.environ['USE_LIGHTWEIGHT'] = 'true'

from config_light import QdrantConfig
from search_engine_simple import SimpleSearchEngine

# Initialize
config = QdrantConfig()
search_engine = SimpleSearchEngine(config)

# Test search
print("Testing search...")
results = search_engine.search("food assistance", 3)

print(f"Found {len(results)} results")
for r in results:
    print(f"- {r.get('name')}: {r.get('description')[:50]}...")
