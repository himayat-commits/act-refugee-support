"""
Test script for the deployed Railway API
"""

from datetime import datetime

import requests

# Your Railway deployment URL
API_URL = "https://act-refugee-support-production.up.railway.app"


def test_health():
    """Test the health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        print("✅ Health check passed:", response.json())
    else:
        print("❌ Health check failed:", response.status_code)
    print()


def test_search(query):
    """Test the search endpoint"""
    print(f"Testing search with query: '{query}'")

    # Prepare the Voiceflow-style request
    payload = {"user_id": "test_user_123", "timestamp": datetime.now().isoformat(), "query": query}

    try:
        response = requests.post(f"{API_URL}/voiceflow", json=payload, headers={"Content-Type": "application/json"})

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search successful!")
            print(f"   Found {len(data.get('results', []))} results")
            print("\nResults:")
            for i, result in enumerate(data.get("results", []), 1):
                print(f"\n{i}. {result.get('name', 'N/A')}")
                print(f"   Category: {result.get('category', 'N/A')}")
                print(f"   Location: {result.get('location', 'N/A')}")
                print(f"   Contact: {result.get('contact', 'N/A')}")
                print(f"   Score: {result.get('score', 0):.3f}")
                if result.get("services"):
                    print(f"   Services: {result['services'][:100]}...")
        else:
            print(f"❌ Search failed with status {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Error during search: {e}")
    print()


def test_root():
    """Test the root endpoint"""
    print("Testing root endpoint...")
    response = requests.get(API_URL)
    if response.status_code == 200:
        print("✅ Root endpoint accessible:", response.json())
    else:
        print("❌ Root endpoint failed:", response.status_code)
    print()


def main():
    print("=" * 60)
    print("TESTING DEPLOYED RAILWAY API")
    print(f"URL: {API_URL}")
    print("=" * 60)
    print()

    # Test health endpoint
    test_health()

    # Test root endpoint
    test_root()

    # Test various search queries
    test_queries = [
        "I need food assistance",
        "housing help",
        "medical services",
        "legal aid for refugees",
        "employment support",
    ]

    for query in test_queries:
        test_search(query)
        print("-" * 40)


if __name__ == "__main__":
    main()
