"""
Test Script for Live Railway Deployment
Run this to verify your API is working correctly
"""

import requests
import json
from datetime import datetime
import sys

# IMPORTANT: Replace this with your actual Railway URL
# You can find it in your Railway dashboard
RAILWAY_URL = "https://your-app-name.railway.app"  # <-- CHANGE THIS!

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_health_check():
    """Test the basic health check endpoint"""
    print_header("Testing Health Check")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/health", timeout=5)
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API")
        print(f"Make sure to update RAILWAY_URL in this script!")
        print(f"Current URL: {RAILWAY_URL}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_detailed_health():
    """Test the detailed health endpoint"""
    print_header("Testing Detailed Health Check")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/health/detailed", timeout=5)
        
        if response.status_code == 200:
            print("✅ Detailed health check passed!")
            data = response.json()
            print(f"Service: {data.get('service')}")
            print(f"Version: {data.get('version')}")
            print(f"Components:")
            for component, status in data.get('components', {}).items():
                emoji = "✅" if status == "healthy" or status == "ready" else "⚠️"
                print(f"  {emoji} {component}: {status}")
            return True
        else:
            print(f"❌ Detailed health check failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_emergency_services():
    """Test the emergency services endpoint"""
    print_header("Testing Emergency Services")
    
    try:
        response = requests.post(f"{RAILWAY_URL}/search/emergency", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Emergency services endpoint working!")
            print(f"Found {len(data.get('resources', []))} emergency services:")
            
            for service in data.get('resources', [])[:3]:  # Show first 3
                print(f"\n  📞 {service.get('name')}")
                print(f"     Phone: {service.get('phone')}")
                print(f"     Available: {service.get('available', 'N/A')}")
            
            return True
        else:
            print(f"❌ Emergency services failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search_endpoint():
    """Test the main search endpoint"""
    print_header("Testing Search Endpoint")
    
    test_queries = [
        {
            "message": "I need medical help",
            "limit": 3,
            "language": "English"
        },
        {
            "message": "housing assistance",
            "limit": 2
        },
        {
            "message": "emergency",
            "limit": 5,
            "urgency": "high"
        }
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nTest {i}: Searching for '{query['message']}'")
        
        try:
            response = requests.post(
                f"{RAILWAY_URL}/search",
                json=query,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    resources = data.get('resources', [])
                    print(f"  ✅ Search successful! Found {len(resources)} results")
                    
                    if resources:
                        print("  First result:")
                        first = resources[0]
                        print(f"    - {first.get('name', 'Unknown')}")
                        print(f"    - {first.get('phone', 'No phone')}")
                    elif data.get('metadata', {}).get('fallback'):
                        print("  ℹ️ Using fallback data (database not connected)")
                    else:
                        print("  ⚠️ No results found")
                else:
                    print(f"  ❌ Search failed: {data.get('message')}")
            else:
                print(f"  ❌ Search failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            return False
    
    return True

def test_api_documentation():
    """Check if API documentation is available"""
    print_header("Testing API Documentation")
    
    try:
        response = requests.get(f"{RAILWAY_URL}/docs", timeout=5)
        
        if response.status_code == 200:
            print("✅ API documentation is available!")
            print(f"   Visit: {RAILWAY_URL}/docs")
            return True
        else:
            print(f"⚠️ API documentation returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"⚠️ Could not access documentation: {e}")
        return False

def run_performance_test():
    """Test API response times"""
    print_header("Performance Test")
    
    endpoints = [
        ("GET", "/health"),
        ("POST", "/search/emergency"),
    ]
    
    for method, endpoint in endpoints:
        try:
            start_time = datetime.now()
            
            if method == "GET":
                response = requests.get(f"{RAILWAY_URL}{endpoint}", timeout=10)
            else:
                response = requests.post(f"{RAILWAY_URL}{endpoint}", timeout=10)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if response.status_code == 200:
                if response_time < 1:
                    print(f"✅ {method} {endpoint}: {response_time:.2f}s (Excellent)")
                elif response_time < 2:
                    print(f"⚠️ {method} {endpoint}: {response_time:.2f}s (Good)")
                else:
                    print(f"❌ {method} {endpoint}: {response_time:.2f}s (Slow)")
            else:
                print(f"❌ {method} {endpoint}: Failed with status {response.status_code}")
                
        except Exception as e:
            print(f"❌ {method} {endpoint}: Error - {e}")

def main():
    """Run all tests"""
    print("\n" + "🚀 ACT REFUGEE SUPPORT API - LIVE TESTING 🚀".center(60))
    print(f"Testing URL: {RAILWAY_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if "your-app-name" in RAILWAY_URL:
        print("\n" + "⚠️  WARNING  ⚠️".center(60))
        print("You need to update RAILWAY_URL in this script!")
        print("1. Go to your Railway dashboard")
        print("2. Copy your deployment URL")
        print("3. Replace 'your-app-name' in this script")
        print("")
        return
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Detailed Health", test_detailed_health),
        ("Emergency Services", test_emergency_services),
        ("Search Endpoint", test_search_endpoint),
        ("API Documentation", test_api_documentation),
        ("Performance", run_performance_test)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"Error running {name}: {e}")
            results.append((name, False))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:.<30} {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Your API is working perfectly!")
    elif passed > 0:
        print("\n⚠️ Some tests failed. Check the details above.")
        print("This is normal if you haven't set up the database yet.")
    else:
        print("\n❌ All tests failed. Please check your deployment.")
    
    # Next steps
    print_header("NEXT STEPS")
    
    if passed == total:
        print("1. Set up Qdrant database (cloud.qdrant.io)")
        print("2. Add database credentials to Railway environment")
        print("3. Run populate_database.py to add service data")
        print("4. Integrate with Voiceflow")
    else:
        print("1. Check your Railway deployment logs")
        print("2. Ensure all environment variables are set")
        print("3. Verify the deployment URL is correct")
        print("4. Check if the service is running")

if __name__ == "__main__":
    main()
