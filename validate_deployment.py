#!/usr/bin/env python3
"""
Railway Deployment Validation Script
Checks all requirements and configurations for successful Railway deployment
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import List, Tuple, Dict

class DeploymentValidator:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.successes = []
        
    def add_error(self, message: str):
        self.errors.append(f"❌ ERROR: {message}")
    
    def add_warning(self, message: str):
        self.warnings.append(f"⚠️  WARNING: {message}")
    
    def add_success(self, message: str):
        self.successes.append(f"✅ SUCCESS: {message}")
    
    def check_file_exists(self, filename: str, required: bool = True) -> bool:
        """Check if a file exists"""
        if Path(filename).exists():
            self.add_success(f"Found {filename}")
            return True
        else:
            if required:
                self.add_error(f"Missing required file: {filename}")
            else:
                self.add_warning(f"Optional file missing: {filename}")
            return False
    
    def check_python_imports(self) -> bool:
        """Check if all required Python packages can be imported"""
        required_packages = [
            "fastapi",
            "uvicorn",
            "pydantic",
            "qdrant_client",
            "openai",
            "dotenv",
            "numpy"
        ]
        
        optional_packages = [
            "redis",
            "pytest",
            "locust"
        ]
        
        all_ok = True
        
        # Check required packages
        for package in required_packages:
            spec = importlib.util.find_spec(package)
            if spec is None:
                self.add_error(f"Required package '{package}' not installed")
                all_ok = False
            else:
                self.add_success(f"Package '{package}' is available")
        
        # Check optional packages
        for package in optional_packages:
            spec = importlib.util.find_spec(package)
            if spec is None:
                self.add_warning(f"Optional package '{package}' not installed")
        
        return all_ok
    
    def check_environment_variables(self) -> bool:
        """Check if required environment variables are set"""
        required_vars = [
            "QDRANT_HOST",
            "QDRANT_API_KEY",
            "OPENAI_API_KEY"
        ]
        
        optional_vars = [
            "PORT",
            "REDIS_HOST",
            "ENABLE_AUTH",
            "API_KEY"
        ]
        
        all_ok = True
        
        # Check required environment variables
        for var in required_vars:
            if os.getenv(var):
                self.add_success(f"Environment variable '{var}' is set")
            else:
                self.add_error(f"Required environment variable '{var}' is not set")
                all_ok = False
        
        # Check optional environment variables
        for var in optional_vars:
            if not os.getenv(var):
                self.add_warning(f"Optional environment variable '{var}' is not set")
        
        return all_ok
    
    def check_railway_config(self) -> bool:
        """Check Railway configuration files"""
        all_ok = True
        
        # Check railway.json
        if self.check_file_exists("railway.json"):
            try:
                with open("railway.json", "r") as f:
                    config = json.load(f)
                
                # Validate structure
                if "build" in config:
                    self.add_success("railway.json has build configuration")
                else:
                    self.add_error("railway.json missing build configuration")
                    all_ok = False
                
                if "deploy" in config:
                    self.add_success("railway.json has deploy configuration")
                    
                    # Check start command
                    if "startCommand" in config["deploy"]:
                        start_cmd = config["deploy"]["startCommand"]
                        if "api_server" in start_cmd or "uvicorn" in start_cmd:
                            self.add_success(f"Start command configured: {start_cmd}")
                        else:
                            self.add_warning(f"Unusual start command: {start_cmd}")
                else:
                    self.add_error("railway.json missing deploy configuration")
                    all_ok = False
                    
            except json.JSONDecodeError as e:
                self.add_error(f"railway.json is not valid JSON: {e}")
                all_ok = False
        else:
            all_ok = False
        
        return all_ok
    
    def check_procfile(self) -> bool:
        """Check Procfile configuration"""
        if self.check_file_exists("Procfile"):
            with open("Procfile", "r") as f:
                content = f.read()
            
            if "web:" in content:
                self.add_success("Procfile has web process defined")
                if "uvicorn" in content:
                    self.add_success("Procfile uses uvicorn")
                if "$PORT" in content:
                    self.add_success("Procfile uses $PORT variable")
                else:
                    self.add_warning("Procfile doesn't reference $PORT")
                return True
            else:
                self.add_error("Procfile missing web process")
                return False
        return False
    
    def check_requirements(self) -> bool:
        """Check requirements files"""
        all_ok = True
        
        # Check for requirements files
        if self.check_file_exists("requirements-light.txt"):
            with open("requirements-light.txt", "r") as f:
                reqs = f.read()
            
            critical_packages = ["fastapi", "uvicorn", "qdrant-client", "openai"]
            for package in critical_packages:
                if package in reqs:
                    self.add_success(f"requirements-light.txt includes {package}")
                else:
                    self.add_error(f"requirements-light.txt missing {package}")
                    all_ok = False
        else:
            if self.check_file_exists("requirements.txt"):
                self.add_warning("Using requirements.txt instead of requirements-light.txt")
            else:
                self.add_error("No requirements file found")
                all_ok = False
        
        return all_ok
    
    def check_api_server(self) -> bool:
        """Check if API server files exist and are valid"""
        all_ok = True
        
        # Check for API server files
        api_files = [
            ("api_server_railway.py", True),
            ("api_server.py", False),
            ("config_light.py", True),
            ("config.py", False),
            ("models.py", True),
            ("search_engine.py", True)
        ]
        
        for filename, required in api_files:
            if not self.check_file_exists(filename, required) and required:
                all_ok = False
        
        return all_ok
    
    def check_python_version(self) -> bool:
        """Check Python version compatibility"""
        version = sys.version_info
        if version.major == 3 and version.minor >= 10:
            self.add_success(f"Python version {version.major}.{version.minor} is compatible")
            return True
        else:
            self.add_error(f"Python version {version.major}.{version.minor} may not be compatible (need 3.10+)")
            return False
    
    def validate(self) -> bool:
        """Run all validation checks"""
        print("🚀 Railway Deployment Validation")
        print("=" * 50)
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Railway Configuration", self.check_railway_config),
            ("Procfile", self.check_procfile),
            ("Requirements", self.check_requirements),
            ("API Server Files", self.check_api_server),
            ("Python Imports", self.check_python_imports),
            ("Environment Variables", self.check_environment_variables)
        ]
        
        all_passed = True
        
        for check_name, check_func in checks:
            print(f"\n📋 Checking {check_name}...")
            if not check_func():
                all_passed = False
        
        # Print summary
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        if self.successes:
            print("\n✅ Successes:")
            for success in self.successes:
                print(f"  {success}")
        
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  {error}")
        
        print("\n" + "=" * 50)
        
        if all_passed and not self.errors:
            print("✅ VALIDATION PASSED - Ready for Railway deployment!")
            return True
        else:
            print("❌ VALIDATION FAILED - Please fix the errors above")
            return False

def main():
    """Main validation function"""
    validator = DeploymentValidator()
    
    # Load .env file if it exists
    if Path(".env").exists():
        from dotenv import load_dotenv
        load_dotenv()
        print("📁 Loaded .env file")
    
    success = validator.validate()
    
    if not success:
        print("\n💡 Quick fixes:")
        print("  1. Install missing packages: pip install -r requirements-light.txt")
        print("  2. Set environment variables in Railway dashboard")
        print("  3. Ensure all required files are committed to git")
        print("  4. Check railway.json and Procfile syntax")
        
        sys.exit(1)
    else:
        print("\n🎉 Your application is ready for Railway deployment!")
        print("\n📝 Next steps:")
        print("  1. Commit all changes: git add . && git commit -m 'Ready for deployment'")
        print("  2. Push to GitHub: git push")
        print("  3. Connect your GitHub repo to Railway")
        print("  4. Set environment variables in Railway dashboard")
        print("  5. Deploy!")
        
        sys.exit(0)

if __name__ == "__main__":
    main()
