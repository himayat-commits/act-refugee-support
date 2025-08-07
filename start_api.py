#!/usr/bin/env python3
"""
Quick Start Script for ACT Refugee Support API
Initializes the database and starts the API server
"""

import os
import sys
import subprocess
import time

def check_requirements():
    """Check if required services are running"""
    print("🔍 Checking requirements...")
    
    # Check for Qdrant
    try:
        import requests
        response = requests.get("http://localhost:6333/dashboard/")
        if response.status_code == 200:
            print("✅ Qdrant is running")
        else:
            print("❌ Qdrant is not responding properly")
            return False
    except:
        print("❌ Qdrant is not running. Please start it with:")
        print("   docker run -p 6333:6333 qdrant/qdrant")
        return False
    
    # Check for dependencies
    try:
        import qdrant_client
        import fastapi
        import sentence_transformers
        print("✅ Python dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    return True

def initialize_database():
    """Initialize the Qdrant database with resources"""
    print("\n📊 Initializing database...")
    try:
        result = subprocess.run([sys.executable, "main.py"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database initialized successfully")
            return True
        else:
            print(f"❌ Database initialization failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def start_api_server():
    """Start the FastAPI server"""
    print("\n🚀 Starting API server...")
    print("   API will be available at: http://localhost:8000")
    print("   Documentation: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([sys.executable, "api_server.py"])
    except KeyboardInterrupt:
        print("\n\n👋 API server stopped")

def main():
    print("=" * 50)
    print("ACT Refugee Support API - Quick Start")
    print("=" * 50)
    
    # Check environment
    if not os.path.exists(".env"):
        print("\n⚠️  No .env file found. Creating from template...")
        try:
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ Created .env file. Please edit it with your configuration.")
        except:
            print("❌ Could not create .env file. Please copy .env.example manually.")
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Please fix the above issues before continuing.")
        sys.exit(1)
    
    # Initialize database
    if initialize_database():
        # Start server
        start_api_server()
    else:
        print("\n❌ Failed to initialize database. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
