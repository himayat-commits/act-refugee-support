#!/usr/bin/env python
"""
ACT Refugee Support API - Main Entry Point
Run with: python run_api.py
"""

import os
import sys
import uvicorn

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api.main_api import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security
    
    print(f"Starting ACT Refugee Support API on {host}:{port}")
    print(f"Documentation available at: http://{host}:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)