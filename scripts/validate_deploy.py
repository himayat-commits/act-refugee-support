"""
Railway Deployment Validation Script
Checks all requirements for successful Railway deployment
"""

import sys
import os
import json
import importlib
from pathlib import Path


def print_status(message, status="INFO"):
    """Print colored status messages"""
    colors = {"INFO": "\033[94m", "SUCCESS": "\033[92m", "WARNING": "\033[93m", "ERROR": "\033[91m", "ENDC": "\033[0m"}
    print(f"{colors.get(status, '')}{status}: {message}{colors['ENDC']}")


def check_file_exists(filepath, description):
    """Check if a required file exists"""
    if Path(filepath).exists():
        print_status(f"✓ {description} found: {filepath}", "SUCCESS")
        return True
    else:
        print_status(f"✗ {description} missing: {filepath}", "ERROR")
        return False


def check_environment_variables():
    """Check if required environment variables are set"""
    print("\n🔍 Checking Environment Variables...")

    required_vars = {
        "QDRANT_HOST": "Qdrant database host",
        "QDRANT_PORT": "Qdrant database port",
        "OPENAI_API_KEY": "OpenAI API key for embeddings",
    }

    optional_vars = {
        "QDRANT_API_KEY": "Qdrant API key (if using cloud)",
        "USE_LIGHTWEIGHT": "Lightweight mode flag",
        "PORT": "Server port",
        "ENABLE_AUTH": "API authentication flag",
    }

    all_good = True

    # Check required variables
    for var, description in required_vars.items():
        if os.getenv(var):
            print_status(f"✓ {var} is set ({description})", "SUCCESS")
        else:
            print_status(f"✗ {var} not set ({description})", "ERROR")
            all_good = False

    # Check optional variables
    for var, description in optional_vars.items():
        if os.getenv(var):
            print_status(f"✓ {var} is set ({description})", "SUCCESS")
        else:
            print_status(f"ℹ {var} not set ({description}) - using default", "WARNING")

    return all_good


def check_python_imports():
    """Check if all required Python packages can be imported"""
    print("\n🔍 Checking Python Imports...")

    required_packages = ["fastapi", "uvicorn", "pydantic", "qdrant_client", "openai", "dotenv", "numpy"]

    all_good = True

    for package in required_packages:
        try:
            importlib.import_module(package)
            print_status(f"✓ {package} can be imported", "SUCCESS")
        except ImportError as e:
            print_status(f"✗ {package} import failed: {e}", "ERROR")
            all_good = False

    return all_good


def check_server_startup():
    """Test if the server can start without errors"""
    print("\n🔍 Testing Server Startup...")

    try:
        # Import the simplified server
        from src.api.main_api import app

        print_status("✓ Server module imports successfully", "SUCCESS")

        # Check if app is created
        if app:
            print_status("✓ FastAPI app created successfully", "SUCCESS")
            return True
        else:
            print_status("✗ FastAPI app creation failed", "ERROR")
            return False

    except Exception as e:
        print_status(f"✗ Server startup test failed: {e}", "ERROR")
        return False


def check_railway_config():
    """Validate Railway configuration files"""
    print("\n🔍 Checking Railway Configuration...")

    all_good = True

    # Check railway.json
    if Path("railway.json").exists():
        try:
            with open("railway.json", "r") as f:
                config = json.load(f)

            # Validate structure
            if "build" in config and "deploy" in config:
                print_status("✓ railway.json has valid structure", "SUCCESS")

                # Check specific settings
                if config["deploy"].get("healthcheckPath") == "/health":
                    print_status("✓ Health check path configured correctly", "SUCCESS")
                else:
                    print_status("✗ Health check path not configured", "ERROR")
                    all_good = False

                if config["deploy"].get("startCommand"):
                    print_status(f"✓ Start command: {config['deploy']['startCommand']}", "SUCCESS")
                else:
                    print_status("✗ No start command specified", "ERROR")
                    all_good = False
            else:
                print_status("✗ railway.json missing required sections", "ERROR")
                all_good = False

        except json.JSONDecodeError as e:
            print_status(f"✗ railway.json is not valid JSON: {e}", "ERROR")
            all_good = False
    else:
        print_status("✗ railway.json not found", "ERROR")
        all_good = False

    return all_good


def test_health_endpoint():
    """Test if health endpoint works"""
    print("\n🔍 Testing Health Endpoint...")

    try:
        from src.api.main_api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)
        response = client.get("/health")

        if response.status_code == 200:
            print_status("✓ Health endpoint returns 200 OK", "SUCCESS")
            print_status(f"  Response: {response.json()}", "INFO")
            return True
        else:
            print_status(f"✗ Health endpoint returned {response.status_code}", "ERROR")
            return False

    except Exception as e:
        print_status(f"✗ Health endpoint test failed: {e}", "ERROR")
        return False


def check_dependencies_file():
    """Check if requirements-light.txt has all necessary packages"""
    print("\n🔍 Checking Dependencies File...")

    if not Path("requirements-light.txt").exists():
        print_status("✗ requirements-light.txt not found", "ERROR")
        return False

    with open("requirements-light.txt", "r") as f:
        deps = f.read().lower()

    required_deps = ["fastapi", "uvicorn", "qdrant-client", "openai", "pydantic"]
    all_good = True

    for dep in required_deps:
        if dep in deps:
            print_status(f"✓ {dep} in requirements", "SUCCESS")
        else:
            print_status(f"✗ {dep} missing from requirements", "ERROR")
            all_good = False

    return all_good


def main():
    """Run all validation checks"""
    print("=" * 60)
    print("🚂 RAILWAY DEPLOYMENT VALIDATION")
    print("=" * 60)

    checks = {
        "Required Files": [
            ("railway.json", "Railway configuration"),
            ("Procfile", "Process configuration"),
            ("requirements-light.txt", "Python dependencies"),
            ("src/api/main_api.py", "Main API server file"),
            ("src/core/config.py", "Configuration module"),
            (".env", "Environment variables file"),
        ]
    }

    all_passed = True

    # Check files
    print("\n🔍 Checking Required Files...")
    for filepath, description in checks["Required Files"]:
        if not check_file_exists(filepath, description):
            all_passed = False

    # Run validation functions
    validation_checks = [
        ("Environment Variables", check_environment_variables),
        ("Railway Config", check_railway_config),
        ("Dependencies", check_dependencies_file),
        ("Python Imports", check_python_imports),
        ("Server Startup", check_server_startup),
        ("Health Endpoint", test_health_endpoint),
    ]

    for name, check_func in validation_checks:
        try:
            if not check_func():
                all_passed = False
        except Exception as e:
            print_status(f"Check '{name}' failed with error: {e}", "ERROR")
            all_passed = False

    # Final summary
    print("\n" + "=" * 60)
    if all_passed:
        print_status("✅ ALL CHECKS PASSED - Ready for Railway deployment!", "SUCCESS")
        print("\nNext steps:")
        print("1. Commit and push changes to your repository")
        print("2. Connect repository to Railway")
        print("3. Set environment variables in Railway dashboard:")
        print("   - QDRANT_HOST")
        print("   - QDRANT_PORT")
        print("   - OPENAI_API_KEY")
        print("   - QDRANT_API_KEY (if using Qdrant Cloud)")
        print("4. Deploy!")
    else:
        print_status("❌ VALIDATION FAILED - Fix issues before deploying", "ERROR")
        print("\nPlease fix the errors above before deploying to Railway.")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
