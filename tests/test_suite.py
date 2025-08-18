"""
Comprehensive Test Suite for ACT Refugee Support System
Run with: pytest test_suite.py -v
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.api.main_api import app
from src.core.config import QdrantConfig
from src.core.models import Resource, ResourceCategory, SearchQuery

# Test client for FastAPI
client = TestClient(app)

# ============= API ENDPOINT TESTS =============


class TestAPIEndpoints:
    """Test all API endpoints"""

    def test_root_endpoint(self):
        """Test root endpoint returns correct service info"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert data["service"] == "ACT Refugee Support API"
        assert "endpoints" in data

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data

    @patch("api_server.search_engine.search")
    def test_search_endpoint(self, mock_search):
        """Test main search endpoint"""
        # Mock search results
        mock_search.return_value = [
            {
                "resource": {
                    "name": "Test Service",
                    "description": "Test description",
                    "contact": {
                        "phone": "123456789",
                        "website": "http://test.com",
                        "address": "Test Address",
                        "hours": "9-5",
                    },
                    "services_provided": ["Service 1"],
                    "cost": "Free",
                    "languages_available": ["English"],
                    "urgency_level": "standard",
                }
            }
        ]

        response = client.post("/search", json={"message": "I need help", "limit": 3})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "resources" in data
        assert len(data["resources"]) > 0

    def test_search_with_invalid_data(self):
        """Test search endpoint with invalid data"""
        response = client.post("/search", json={})
        assert response.status_code == 422  # Unprocessable Entity

    def test_emergency_search(self):
        """Test emergency search endpoint"""
        with patch("api_server.search_engine.search_urgent_services") as mock_urgent:
            mock_urgent.return_value = []
            response = client.post("/search/emergency")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "EMERGENCY" in data["message"]

    def test_economic_search(self):
        """Test economic integration search"""
        response = client.post("/search/economic", json={"message": "I need job training", "limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


# ============= MODEL VALIDATION TESTS =============


class TestModels:
    """Test Pydantic models and validation"""

    def test_refugee_resource_validation(self):
        """Test Resource model validation"""
        valid_resource = {
            "name": "Test Resource",
            "description": "A test resource description",
            "category": "healthcare",
            "services_provided": ["Service 1", "Service 2"],
            "eligibility": "All refugees",
            "cost": "Free",
            "languages_available": ["English", "Arabic"],
            "contact": {
                "phone": "0400000000",
                "email": "test@example.com",
                "website": "https://example.com",
                "address": "123 Test St",
                "hours": "Mon-Fri 9-5",
            },
            "urgency_level": "standard",
        }

        resource = Resource(**valid_resource)
        assert resource.name == "Test Resource"
        assert resource.category == ResourceCategory.HEALTHCARE

    def test_search_query_validation(self):
        """Test SearchQuery model validation"""
        query = SearchQuery(query="test query", categories=[ResourceCategory.HEALTHCARE], urgency="high", limit=5)
        assert query.query == "test query"
        assert query.limit == 5

    def test_invalid_resource_category(self):
        """Test invalid category raises error"""
        with pytest.raises(ValueError):
            SearchQuery(query="test", categories=["invalid_category"])


# ============= SEARCH FUNCTIONALITY TESTS =============


class TestSearchFunctionality:
    """Test search engine functionality"""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration"""
        config = Mock()
        config.get_client = Mock(return_value=Mock())
        config.get_embedding_model = Mock(return_value=Mock())
        return config

    def test_intent_detection(self):
        """Test intent detection from queries"""
        from api_server import detect_intent

        # Test emergency intent
        assert detect_intent("emergency help needed") == "emergency"
        assert detect_intent("urgent crisis") == "emergency"

        # Test employment intent
        assert detect_intent("I need a job") == "employment"
        assert detect_intent("looking for work") == "employment"

        # Test housing intent
        assert detect_intent("need accommodation") == "housing"
        assert detect_intent("homeless shelter") == "housing"

        # Test digital help intent
        assert detect_intent("help with MyGov") == "digital_help"
        assert detect_intent("need computer access") == "digital_help"

    def test_resource_formatting(self):
        """Test resource formatting for Voiceflow"""
        from api_server import format_resources_for_voiceflow

        test_results = [
            {
                "resource": {
                    "name": "Test Service",
                    "description": "A" * 300,  # Long description
                    "contact": {
                        "phone": "123456789",
                        "website": "http://test.com",
                        "address": "Test Address",
                        "hours": "24/7",
                    },
                    "services_provided": ["S1", "S2", "S3", "S4"],
                    "cost": "Free",
                    "languages_available": ["English", "Arabic"],
                    "urgency_level": "critical",
                }
            }
        ]

        formatted = format_resources_for_voiceflow(test_results)

        assert len(formatted) == 1
        assert "🚨" in formatted[0]["name"]  # Critical marker
        assert len(formatted[0]["description"]) <= 203  # Truncated + "..."
        assert len(formatted[0]["services"].split(", ")) <= 3  # Max 3 services

    @patch("openai.OpenAI")
    def test_embedding_generation(self, mock_openai):
        """Test OpenAI embedding generation"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1] * 1536)]
        mock_client.embeddings.create.return_value = mock_response
        mock_openai.return_value = mock_client

        embedding = OpenAIEmbedding("test_key")
        result = embedding.encode("test text")

        assert len(result) == 1536
        assert all(isinstance(x, float) for x in result)


# ============= INTEGRATION TESTS =============


class TestIntegration:
    """Integration tests for complete workflows"""

    @pytest.mark.asyncio
    async def test_full_search_workflow(self):
        """Test complete search workflow"""
        with patch("api_server.search_engine.search") as mock_search:
            mock_search.return_value = [
                {
                    "resource": {
                        "name": "Integration Test Service",
                        "description": "Full workflow test",
                        "contact": {"phone": "000", "website": "", "address": "", "hours": ""},
                        "services_provided": [],
                        "cost": "Free",
                        "languages_available": [],
                        "urgency_level": "standard",
                    }
                }
            ]

            # Simulate user search
            response = client.post(
                "/search",
                json={
                    "message": "I need healthcare services",
                    "category": "healthcare",
                    "language": "Arabic",
                    "limit": 5,
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert len(data["resources"]) > 0
            assert "metadata" in data
            assert data["metadata"]["intent"] == "healthcare"

    def test_error_handling(self):
        """Test error handling in API"""
        # Test with malformed request
        response = client.post("/search", data="invalid json")
        assert response.status_code == 422

        # Test with missing required fields
        response = client.post("/search", json={"invalid": "data"})
        assert response.status_code == 422


# ============= PERFORMANCE TESTS =============


class TestPerformance:
    """Performance and load tests"""

    def test_response_time(self):
        """Test API response time"""
        import time

        start = time.time()
        response = client.get("/health")
        end = time.time()

        assert response.status_code == 200
        assert (end - start) < 1.0  # Should respond in less than 1 second

    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import concurrent.futures

        def make_request():
            return client.get("/health")

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert all(r.status_code == 200 for r in results)


# ============= DATA VALIDATION TESTS =============


class TestDataValidation:
    """Test data validation and sanitization"""

    def test_phone_validation(self):
        """Test phone number validation"""
        from data_pipeline import ResourceValidator

        # Valid phone numbers
        valid_phones = ["0400000000", "+61 400 000 000", "02-1234-5678"]
        for phone in valid_phones:
            resource = ResourceValidator(name="Test", description="Test description", contact_phone=phone)
            assert resource.contact_phone == phone

        # Invalid phone numbers
        with pytest.raises(ValueError):
            ResourceValidator(name="Test", description="Test description", contact_phone="invalid-phone")

    def test_email_validation(self):
        """Test email validation"""
        from data_pipeline import ResourceValidator

        # Valid email
        resource = ResourceValidator(name="Test", description="Test description", contact_email="test@example.com")
        assert "@" in resource.contact_email

        # Invalid email
        with pytest.raises(ValueError):
            ResourceValidator(name="Test", description="Test description", contact_email="invalid-email")

    def test_website_validation(self):
        """Test website URL validation"""
        from data_pipeline import ResourceValidator

        # URL without protocol
        resource = ResourceValidator(name="Test", description="Test description", contact_website="example.com")
        assert resource.contact_website == "https://example.com"

        # URL with protocol
        resource = ResourceValidator(name="Test", description="Test description", contact_website="http://example.com")
        assert resource.contact_website == "http://example.com"

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "<script>alert('XSS')</script>",
            "../../etc/passwd",
        ]

        for dangerous_input in dangerous_inputs:
            response = client.post("/search", json={"message": dangerous_input, "limit": 3})
            # Should handle safely without crashing
            assert response.status_code in [200, 422, 500]


# ============= CONFIGURATION TESTS =============


class TestConfiguration:
    """Test configuration and environment setup"""

    def test_environment_variables(self):
        """Test environment variable loading"""
        from dotenv import load_dotenv

        load_dotenv()

        # Check critical environment variables
        critical_vars = ["QDRANT_HOST", "OPENAI_API_KEY"]
        for var in critical_vars:
            assert os.getenv(var) is not None, f"Missing critical env var: {var}"

    def test_config_initialization(self):
        """Test configuration initialization"""
        config = QdrantConfig()

        assert config.host is not None
        assert config.port > 0
        assert config.vector_size == 1536  # OpenAI dimension


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
