#!/usr/bin/env python3
"""
Health check script for Docker container
"""
import sys
import httpx

def check_health():
    try:
        response = httpx.get('http://localhost:8000/health', timeout=5.0)
        if response.status_code == 200:
            return 0
        else:
            return 1
    except Exception:
        return 1

if __name__ == "__main__":
    sys.exit(check_health())