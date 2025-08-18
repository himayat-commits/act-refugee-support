#!/usr/bin/env python3
"""
Test deployment status for Railway and Qdrant
"""

import os
import sys
import requests
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Load environment variables
load_dotenv()


def test_qdrant_connection():
    """Test if Qdrant Cloud is accessible and working"""
    print("\n🔍 Testing Qdrant Cloud Connection...")
    print("=" * 50)

    try:
        host = os.getenv("QDRANT_HOST")
        port = int(os.getenv("QDRANT_PORT", 6333))
        api_key = os.getenv("QDRANT_API_KEY")

        if not host:
            print("❌ QDRANT_HOST not set in .env file")
            return False

        print(f"Host: {host}")
        print(f"Port: {port}")
        print(f"API Key: {'Set' if api_key else 'Not set'}")

        # Connect to Qdrant Cloud
        print("\nConnecting to Qdrant Cloud...")
        client = QdrantClient(host=host, port=port, api_key=api_key, https=True)  # Qdrant Cloud uses HTTPS

        # Test connection by getting collections
        collections = client.get_collections()
        print(f"✅ Connected successfully!")
        print(f"Found {len(collections.collections)} collections:")

        for collection in collections.collections:
            # Get collection info
            info = client.get_collection(collection.name)
            print(f"  - {collection.name}: {info.points_count} points, vectors: {info.config.params.vectors.size}D")

        # Check for our specific collection
        collection_names = [c.name for c in collections.collections]
        if "act_refugee_resources" in collection_names:
            print(f"\n✅ Main collection 'act_refugee_resources' exists")
            collection_info = client.get_collection("act_refugee_resources")
            print(f"   Points: {collection_info.points_count}")
            print(f"   Status: {collection_info.status}")
        else:
            print(f"\n⚠️  Main collection 'act_refugee_resources' not found")

        return True

    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        if "401" in str(e) or "Unauthorized" in str(e):
            print("   Check your API key configuration")
        elif "404" in str(e) or "Not Found" in str(e):
            print("   Check your host configuration")
        return False


def test_railway_deployment():
    """Test if Railway deployment is accessible"""
    print("\n🔍 Testing Railway Deployment...")
    print("=" * 50)

    # Check for common Railway deployment URLs
    possible_urls = [
        "https://act-refugee-support.up.railway.app",
        "https://act-refugee-support-new.up.railway.app",
        "https://act-refugee-support-production.up.railway.app",
    ]

    print("Checking possible Railway URLs...")

    for url in possible_urls:
        try:
            print(f"\nTesting: {url}")
            # Test health endpoint
            response = requests.get(f"{url}/health", timeout=5)

            if response.status_code == 200:
                print(f"✅ Railway deployment is LIVE at {url}")
                print(f"   Health check response: {response.json()}")

                # Test API docs
                docs_response = requests.get(f"{url}/docs", timeout=5)
                if docs_response.status_code == 200:
                    print(f"   API documentation available at {url}/docs")

                return True
            else:
                print(f"   Status code: {response.status_code}")

        except requests.exceptions.ConnectionError:
            print(f"   Connection failed - deployment may not exist")
        except requests.exceptions.Timeout:
            print(f"   Request timed out")
        except Exception as e:
            print(f"   Error: {e}")

    print("\n❌ No active Railway deployment found")
    print("\nTo deploy to Railway:")
    print("1. Push your code to GitHub")
    print("2. Connect your repo to Railway")
    print("3. Set environment variables in Railway dashboard")
    print("4. Deploy!")

    return False


def test_local_server():
    """Test if local server can start"""
    print("\n🔍 Testing Local Server...")
    print("=" * 50)

    try:
        # Check if main server file exists
        if os.path.exists("api_server.py"):
            print("✅ api_server.py exists")

            # Try importing it
            import api_server

            print("✅ api_server.py imports successfully")

            # Check for FastAPI app
            if hasattr(api_server, "app"):
                print("✅ FastAPI app found")
                return True
            else:
                print("⚠️  FastAPI app not found in api_server.py")
        else:
            print("❌ api_server.py not found")

    except ImportError as e:
        print(f"❌ Cannot import api_server.py: {e}")
    except Exception as e:
        print(f"❌ Error testing local server: {e}")

    return False


def main():
    """Run all deployment tests"""
    print("=" * 60)
    print("🚀 DEPLOYMENT STATUS CHECK")
    print("=" * 60)

    results = {}

    # Test Qdrant
    results["qdrant"] = test_qdrant_connection()

    # Test Railway
    results["railway"] = test_railway_deployment()

    # Test Local Setup
    results["local"] = test_local_server()

    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)

    print(f"\nQdrant Cloud: {'✅ WORKING' if results['qdrant'] else '❌ NOT WORKING'}")
    print(f"Railway Deployment: {'✅ DEPLOYED' if results['railway'] else '❌ NOT DEPLOYED'}")
    print(f"Local Server: {'✅ READY' if results['local'] else '⚠️  NEEDS SETUP'}")

    if results["qdrant"] and not results["railway"]:
        print("\n💡 Next Step: Deploy to Railway")
        print("   Your Qdrant database is ready, but the API is not deployed.")
        print("   Follow the Railway deployment guide to complete setup.")
    elif not results["qdrant"]:
        print("\n💡 Next Step: Fix Qdrant Connection")
        print("   Check your .env file and ensure Qdrant Cloud credentials are correct.")
    elif results["qdrant"] and results["railway"]:
        print("\n✨ Everything is working! Your deployment is live.")

    return 0 if all(results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
