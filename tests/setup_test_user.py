#!/usr/bin/env python3
"""
Setup Test User for ChaturLog Tests

This script registers the test user and configures API keys.
Run this before running the test suites.
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:8001/api"
TEST_USER = {
    "email": "srewoo@gmail.com",
    "password": "Pass@1213"
}

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def print_step(message):
    print(f"\n{BLUE}▶ {message}{RESET}")


def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message):
    print(f"{RED}✗ {message}{RESET}")


def print_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")


def setup_test_user():
    """Register and configure test user"""
    print(f"\n{BLUE}{'='*60}")
    print(f"  ChaturLog Test User Setup")
    print(f"{'='*60}{RESET}\n")
    
    print_step("Registering test user...")
    
    # Try to register
    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=TEST_USER,
            timeout=10
        )
        
        if response.status_code == 200:
            print_success("User registered successfully!")
        elif response.status_code == 400:
            print_warning("User already exists (this is fine)")
        else:
            print_error(f"Registration failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to backend server!")
        print_error("Please start the backend server first:")
        print(f"  cd backend")
        print(f"  python3 server.py")
        return None
    except Exception as e:
        print_error(f"Error during registration: {str(e)}")
        return None
    
    # Login to get token
    print_step("Logging in...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=TEST_USER,
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json()["access_token"]
            print_success("Login successful!")
            return token
        else:
            print_error(f"Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print_error(f"Error during login: {str(e)}")
        return None


def check_api_keys(token):
    """Check if API keys are configured"""
    print_step("Checking API keys...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/settings/api-keys",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if response.status_code == 200:
            api_keys = response.json().get("api_keys", {})
            
            # Check which keys are configured (not empty)
            configured_keys = []
            if api_keys.get("openai_key"):
                configured_keys.append("OpenAI")
            if api_keys.get("anthropic_key"):
                configured_keys.append("Anthropic")
            if api_keys.get("google_key"):
                configured_keys.append("Google AI")
            
            if configured_keys:
                print_success(f"Found {len(configured_keys)} API key(s) configured:")
                for provider in configured_keys:
                    print(f"  - {provider}")
                return True
            else:
                print_warning("No API keys configured!")
                print("\nYou need to configure at least one API key:")
                print("  Option 1: Via UI - Go to Settings → API Keys")
                print("  Option 2: Via script - Run setup_api_keys.py")
                return False
                
    except Exception as e:
        print_error(f"Error checking API keys: {str(e)}")
        return False


def main():
    # Setup user
    token = setup_test_user()
    
    if not token:
        print(f"\n{RED}{'='*60}")
        print(f"  Setup failed!")
        print(f"{'='*60}{RESET}\n")
        return 1
    
    # Check API keys
    has_keys = check_api_keys(token)
    
    # Summary
    print(f"\n{BLUE}{'='*60}")
    print(f"  Setup Summary")
    print(f"{'='*60}{RESET}\n")
    
    print_success(f"User: {TEST_USER['email']}")
    print_success("Authentication: Ready ✓")
    
    if has_keys:
        print_success("API Keys: Configured ✓")
        print(f"\n{GREEN}{'='*60}")
        print(f"  All tests are ready to run! 🚀")
        print(f"{'='*60}{RESET}\n")
        return 0
    else:
        print_warning("API Keys: Not configured")
        print(f"\n{YELLOW}{'='*60}")
        print(f"  Please configure API keys before running tests")
        print(f"{'='*60}{RESET}\n")
        return 1


if __name__ == "__main__":
    exit(main())
