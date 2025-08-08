"""
Test script for ACT Refugee Support API v2 Orchestrator
Tests all major endpoints and scenarios locally
"""

import requests
import json
from typing import Dict, List
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8002"

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_test_header(test_name: str):
    """Print formatted test header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}TEST: {test_name}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")

def print_response(response: Dict, truncate: bool = True):
    """Print formatted response"""
    print(f"\n{Colors.OKBLUE}Response:{Colors.ENDC}")
    
    if "message" in response:
        print(f"  Message: {response['message']}")
    
    if "services" in response and response["services"]:
        print(f"  Services Found: {len(response['services'])}")
        for i, service in enumerate(response["services"][:3], 1):
            print(f"    {i}. {service.get('name', 'Unknown')}")
            if truncate:
                desc = service.get('description', '')[:100]
                if len(service.get('description', '')) > 100:
                    desc += "..."
                print(f"       {desc}")
            if service.get('phone'):
                print(f"       📞 {service['phone']}")
    
    if "quick_replies" in response and response["quick_replies"]:
        print(f"  Quick Replies: {', '.join(response['quick_replies'])}")
    
    if "metadata" in response:
        print(f"  Metadata:")
        print(f"    Intent: {response['metadata'].get('intent', 'N/A')}")
        print(f"    Urgency: {response['metadata'].get('urgency', 'N/A')}")
        print(f"    Confidence: {response['metadata'].get('confidence', 'N/A')}")

def test_health_check():
    """Test health check endpoint"""
    print_test_header("Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        response.raise_for_status()
        data = response.json()
        
        print_success(f"API is {data['status']}")
        print_info(f"Service: {data['service']}")
        
        if "components" in data:
            print_info("Components Status:")
            for component, status in data['components'].items():
                print(f"    - {component}: {status}")
        
        return True
    except Exception as e:
        print_error(f"Health check failed: {str(e)}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print_test_header("Root Endpoint")
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Service: {data['service']}")
        print_info(f"Version: {data['version']}")
        print_info(f"Architecture: {data['architecture']}")
        print_info(f"Status: {data['status']}")
        
        return True
    except Exception as e:
        print_error(f"Root endpoint test failed: {str(e)}")
        return False

def test_chat_endpoint(message: str, expected_intent: str = None):
    """Test chat endpoint with a message"""
    print_test_header(f"Chat Endpoint: '{message}'")
    
    try:
        payload = {
            "message": message,
            "user_id": "test_user",
            "language": "English",
            "location": "Canberra"
        }
        
        response = requests.post(f"{API_BASE_URL}/api/v2/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            print_success("Request processed successfully")
        else:
            print_error("Request failed")
        
        print_response(data)
        
        if expected_intent and "metadata" in data:
            actual_intent = data["metadata"].get("intent")
            if actual_intent == expected_intent:
                print_success(f"Intent correctly identified as: {expected_intent}")
            else:
                print_error(f"Expected intent: {expected_intent}, Got: {actual_intent}")
        
        return data.get("success", False)
    except Exception as e:
        print_error(f"Chat endpoint test failed: {str(e)}")
        return False

def test_emergency_endpoint():
    """Test emergency endpoint"""
    print_test_header("Emergency Quick Access Endpoint")
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/v2/emergency")
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            print_success("Emergency services retrieved")
        
        print_response(data)
        
        # Check for emergency services
        if "services" in data:
            for service in data["services"]:
                if "000" in service.get("phone", ""):
                    print_success("Emergency number 000 included")
                    break
        
        return data.get("success", False)
    except Exception as e:
        print_error(f"Emergency endpoint test failed: {str(e)}")
        return False

def test_voiceflow_webhook():
    """Test Voiceflow webhook endpoint"""
    print_test_header("Voiceflow Webhook")
    
    try:
        # Simulate Voiceflow payload
        payload = {
            "query": "I need help finding a job",
            "user": {
                "id": "vf_user_123"
            },
            "language": "English",
            "context": {}
        }
        
        response = requests.post(f"{API_BASE_URL}/voiceflow/webhook", json=payload)
        response.raise_for_status()
        data = response.json()
        
        if data.get("success"):
            print_success("Webhook processed successfully")
        
        # Check for Voiceflow-specific formatting
        if "cards" in data:
            print_info(f"Cards generated: {len(data['cards'])}")
            for card in data["cards"][:2]:
                print(f"  - {card['title']}")
        
        if "quick_replies" in data:
            print_info(f"Quick replies: {', '.join(data['quick_replies'])}")
        
        return data.get("success", False)
    except Exception as e:
        print_error(f"Voiceflow webhook test failed: {str(e)}")
        return False

def test_intent_classification():
    """Test various intents"""
    print_test_header("Intent Classification Tests")
    
    test_cases = [
        ("I need emergency help!", "emergency"),
        ("My boss is not paying me", "exploitation"),
        ("Help me with MyGov website", "digital_help"),
        ("I need a job urgently", "economic"),
        ("I'm homeless and need shelter", "housing"),
        ("Where can I find free food?", "general")
    ]
    
    results = []
    for message, expected_intent in test_cases:
        print(f"\n{Colors.BOLD}Testing: '{message}'{Colors.ENDC}")
        
        payload = {
            "message": message,
            "user_id": "test_user"
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/v2/chat", json=payload)
            data = response.json()
            
            if data.get("success"):
                actual_intent = data.get("metadata", {}).get("intent")
                urgency = data.get("metadata", {}).get("urgency")
                confidence = data.get("metadata", {}).get("confidence")
                
                if actual_intent == expected_intent:
                    print_success(f"Intent: {actual_intent} (Urgency: {urgency}, Confidence: {confidence:.2f})")
                    results.append(True)
                else:
                    print_error(f"Expected: {expected_intent}, Got: {actual_intent}")
                    results.append(False)
            else:
                print_error("Request failed")
                results.append(False)
                
        except Exception as e:
            print_error(f"Test failed: {str(e)}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\n{Colors.BOLD}Intent Classification Results: {passed}/{total} passed{Colors.ENDC}")
    
    return all(results)

def test_context_analysis():
    """Test context analysis with complex messages"""
    print_test_header("Context Analysis Tests")
    
    test_messages = [
        "I just arrived in Australia with my family and need help",
        "I have no money and feel very alone",
        "My children need school and I don't speak English well",
        "It's urgent, we will be evicted tonight"
    ]
    
    for message in test_messages:
        print(f"\n{Colors.BOLD}Analyzing: '{message}'{Colors.ENDC}")
        
        payload = {
            "message": message,
            "user_id": "test_user"
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/v2/chat", json=payload)
            data = response.json()
            
            if data.get("success"):
                metadata = data.get("metadata", {})
                hidden_needs = metadata.get("hidden_needs", [])
                urgency = metadata.get("urgency")
                
                print_info(f"Urgency Level: {urgency}")
                
                if hidden_needs:
                    print_info("Hidden needs detected:")
                    for need in hidden_needs:
                        print(f"  - {need.get('label', need.get('type'))}")
                
                if data.get("next_steps"):
                    print_info("Recommended next steps:")
                    for step in data["next_steps"]:
                        print(f"  - {step}")
                        
        except Exception as e:
            print_error(f"Test failed: {str(e)}")

def test_multilingual_support():
    """Test multilingual support"""
    print_test_header("Multilingual Support")
    
    languages = ["Spanish", "Arabic", "Mandarin", "French"]
    
    for language in languages:
        print(f"\n{Colors.BOLD}Testing {language} support{Colors.ENDC}")
        
        payload = {
            "message": "I need help",
            "user_id": "test_user",
            "language": language
        }
        
        try:
            response = requests.post(f"{API_BASE_URL}/api/v2/chat", json=payload)
            data = response.json()
            
            if data.get("success"):
                # Check for language-specific call scripts
                if data.get("call_scripts"):
                    for script in data["call_scripts"]:
                        if language in script:
                            print_success(f"Language-specific script found: '{script}'")
                            break
                else:
                    print_info("No call scripts generated")
                    
        except Exception as e:
            print_error(f"Test failed: {str(e)}")

def run_performance_test():
    """Test API performance"""
    print_test_header("Performance Test")
    
    messages = [
        "I need housing assistance",
        "Help with job search",
        "Emergency medical help",
        "MyGov login problems",
        "Free food services"
    ]
    
    response_times = []
    
    for message in messages:
        payload = {
            "message": message,
            "user_id": "perf_test_user"
        }
        
        start_time = time.time()
        try:
            response = requests.post(f"{API_BASE_URL}/api/v2/chat", json=payload)
            response.raise_for_status()
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # Convert to ms
            response_times.append(response_time)
            
            print_info(f"'{message[:30]}...' - {response_time:.2f}ms")
            
        except Exception as e:
            print_error(f"Request failed: {str(e)}")
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\n{Colors.BOLD}Performance Summary:{Colors.ENDC}")
        print_info(f"Average response time: {avg_time:.2f}ms")
        print_info(f"Fastest response: {min_time:.2f}ms")
        print_info(f"Slowest response: {max_time:.2f}ms")
        
        if avg_time < 500:
            print_success("Performance is excellent (<500ms average)")
        elif avg_time < 1000:
            print_success("Performance is good (<1s average)")
        else:
            print_error("Performance needs optimization (>1s average)")

def main():
    """Run all tests"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}ACT REFUGEE SUPPORT API V2 - ORCHESTRATOR TEST SUITE{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Testing API at: {API_BASE_URL}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
    
    # Check if API is running
    print_info("\nChecking API availability...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print_success("API is running and accessible")
        else:
            print_error(f"API returned status code: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to API at {API_BASE_URL}")
        print_info("Please ensure the API is running: python api_v2_orchestrator.py")
        return
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return
    
    # Run tests
    test_results = []
    
    # Basic tests
    test_results.append(("Health Check", test_health_check()))
    test_results.append(("Root Endpoint", test_root_endpoint()))
    
    # Endpoint tests
    test_results.append(("Emergency Endpoint", test_emergency_endpoint()))
    test_results.append(("Voiceflow Webhook", test_voiceflow_webhook()))
    
    # Chat tests with different intents
    test_results.append(("General Query", test_chat_endpoint("Where can I get help?", "general")))
    test_results.append(("Housing Query", test_chat_endpoint("I need emergency accommodation", "housing")))
    test_results.append(("Economic Query", test_chat_endpoint("I'm looking for a job", "economic")))
    test_results.append(("Emergency Query", test_chat_endpoint("I need urgent help now!", "emergency")))
    
    # Advanced tests
    test_results.append(("Intent Classification", test_intent_classification()))
    test_context_analysis()  # This doesn't return pass/fail
    test_multilingual_support()  # This doesn't return pass/fail
    
    # Performance test
    run_performance_test()
    
    # Summary
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}TEST SUMMARY{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = f"{Colors.OKGREEN}PASSED{Colors.ENDC}" if result else f"{Colors.FAIL}FAILED{Colors.ENDC}"
        print(f"{test_name}: {status}")
    
    print(f"\n{Colors.BOLD}Overall: {passed}/{total} tests passed{Colors.ENDC}")
    
    if passed == total:
        print(f"{Colors.OKGREEN}{Colors.BOLD}✓ All tests passed successfully!{Colors.ENDC}")
    else:
        print(f"{Colors.WARNING}{Colors.BOLD}⚠ Some tests failed. Please review the output above.{Colors.ENDC}")
    
    print(f"\n{Colors.OKCYAN}Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")

if __name__ == "__main__":
    main()
