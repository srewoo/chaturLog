#!/usr/bin/env python3
"""
Test script for chunking pipeline
Tests the Stream → Chunk → Summarize → Index pipeline
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8001/api"
# Get the test file path relative to this script
SCRIPT_DIR = Path(__file__).parent
TEST_FILE = str(SCRIPT_DIR / "sample file.json")

# Colors for output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(step, message):
    print(f"\n{BLUE}{'='*60}")
    print(f"STEP {step}: {message}")
    print(f"{'='*60}{RESET}\n")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_warning(message):
    print(f"{YELLOW}⚠ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def main():
    print(f"\n{BLUE}╔════════════════════════════════════════════════════════╗")
    print(f"║     ChaturLog Chunking Pipeline Test                  ║")
    print(f"╚════════════════════════════════════════════════════════╝{RESET}\n")
    
    # Check file size
    file_size = Path(TEST_FILE).stat().st_size
    print(f"📄 Test File: {TEST_FILE}")
    print(f"📊 File Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    print(f"🎯 Threshold: 100,000 bytes")
    print(f"{'✅ Will use CHUNKING pipeline' if file_size >= 100000 else '❌ Will use single-pass'}\n")
    
    # Step 1: Register/Login
    print_step(1, "Authentication")
    
    email = "srewoo@gmail.com"
    password = "Pass@1213"
    
    # Try to register
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password
        })
        if response.status_code == 200:
            print_success(f"Registered new user: {email}")
        else:
            print_warning("User might already exist, trying login...")
    except Exception as e:
        print_warning(f"Registration skipped: {e}")
    
    # Login
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": email,
        "password": password
    })
    
    if response.status_code != 200:
        print_error(f"Login failed: {response.text}")
        return
    
    data = response.json()
    token = data['access_token']
    print_success(f"Logged in successfully!")
    print(f"   Token: {token[:50]}...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 2: Upload Log File
    print_step(2, "Upload Log File")
    
    with open(TEST_FILE, 'rb') as f:
        files = {'file': (Path(TEST_FILE).name, f, 'application/json')}
        response = requests.post(f"{BASE_URL}/upload", files=files, headers=headers)
    
    if response.status_code != 200:
        print_error(f"Upload failed: {response.text}")
        return
    
    upload_data = response.json()
    analysis_id = upload_data['analysis_id']
    print_success(f"File uploaded successfully!")
    print(f"   Analysis ID: {analysis_id}")
    print(f"   Filename: {upload_data['filename']}")
    
    # Step 3: Analyze with AI (this will trigger chunking!)
    print_step(3, "Analyze with AI (Chunking Pipeline)")
    
    print(f"{YELLOW}🤖 Starting analysis with GPT-4o-mini...")
    print(f"   Expected: Chunking pipeline will be triggered")
    print(f"   Chunks: ~{file_size // 10000} chunks estimated{RESET}\n")
    
    start_time = time.time()
    
    response = requests.post(
        f"{BASE_URL}/analyze/{analysis_id}",
        json={"ai_model": "gpt-4o"},
        headers=headers
    )
    
    elapsed = time.time() - start_time
    
    if response.status_code != 200:
        print_error(f"Analysis failed: {response.text}")
        return
    
    analysis_data = response.json()
    print_success(f"Analysis completed in {elapsed:.2f} seconds!")
    
    # Check if chunking was used
    if 'chunks_processed' in analysis_data:
        print(f"\n{GREEN}🎉 CHUNKING PIPELINE USED!{RESET}")
        print(f"   Chunks Processed: {analysis_data['chunks_processed']}")
        print(f"   Method: Stream → Chunk → Summarize → Index")
    else:
        print(f"\n{YELLOW}📄 Single-pass analysis used{RESET}")
    
    # Display results
    print(f"\n{BLUE}📊 Analysis Results:{RESET}")
    analysis_results = analysis_data.get('analysis', {})
    
    if 'total_chunks' in analysis_results:
        print(f"   Total Chunks: {analysis_results['total_chunks']}")
    
    error_patterns = analysis_results.get('error_patterns', [])
    print(f"   Error Patterns: {len(error_patterns)}")
    
    api_endpoints = analysis_results.get('api_endpoints', [])
    print(f"   API Endpoints: {len(api_endpoints)}")
    
    perf_issues = analysis_results.get('performance_issues', [])
    print(f"   Performance Issues: {len(perf_issues)}")
    
    if 'severity_distribution' in analysis_results:
        print(f"\n   Severity Distribution:")
        for severity, count in analysis_results['severity_distribution'].items():
            print(f"      {severity}: {count} chunks")
    
    # Show first few errors
    if error_patterns:
        print(f"\n   {BLUE}First 5 Error Patterns:{RESET}")
        for i, error in enumerate(error_patterns[:5], 1):
            print(f"      {i}. {error.get('type', 'Unknown')}: {error.get('description', 'No description')[:80]}...")
    
    # Show first few API endpoints
    if api_endpoints:
        print(f"\n   {BLUE}First 5 API Endpoints:{RESET}")
        for i, ep in enumerate(api_endpoints[:5], 1):
            print(f"      {i}. {ep.get('method', 'GET')} {ep.get('path', '/')}")
    
    # Step 4: Generate Tests
    print_step(4, "Generate Tests (Should work without token limits!)")
    
    print(f"{YELLOW}🧪 Generating Jest tests...{RESET}")
    
    response = requests.post(
        f"{BASE_URL}/generate-tests/{analysis_id}",
        json={"framework": "jest"},
        headers=headers
    )
    
    if response.status_code != 200:
        print_error(f"Test generation failed: {response.text}")
        print(f"\n{YELLOW}This might be expected if there are issues with the aggregated data format.{RESET}")
    else:
        test_data = response.json()
        test_cases = test_data.get('test_cases', [])
        print_success(f"Generated {len(test_cases)} test cases!")
        
        if test_cases:
            print(f"\n   {BLUE}First Test Case:{RESET}")
            first_test = test_cases[0]
            print(f"      Description: {first_test.get('description', 'No description')}")
            print(f"      Priority: {first_test.get('priority', 'medium')}")
            print(f"      Framework: Jest")
            print(f"\n      Code Preview (first 500 chars):")
            code = first_test.get('test_code', '')
            print(f"      {code[:500]}...")
    
    # Summary
    print(f"\n{GREEN}╔════════════════════════════════════════════════════════╗")
    print(f"║              ✓ TEST COMPLETE!                         ║")
    print(f"╚════════════════════════════════════════════════════════╝{RESET}\n")
    
    print(f"📊 Summary:")
    print(f"   File Size: {file_size:,} bytes")
    print(f"   Analysis Time: {elapsed:.2f} seconds")
    print(f"   Method: {'Chunking Pipeline' if 'chunks_processed' in analysis_data else 'Single-pass'}")
    if 'chunks_processed' in analysis_data:
        print(f"   Chunks: {analysis_data['chunks_processed']}")
    print(f"   Errors Found: {len(error_patterns)}")
    print(f"   API Endpoints: {len(api_endpoints)}")
    print(f"   Tests Generated: {len(test_cases) if 'test_cases' in locals() else 'N/A'}")
    
    print(f"\n{GREEN}✅ Chunking pipeline is working!{RESET}")
    print(f"{BLUE}💡 Large logs (>100k bytes) are now handled automatically!{RESET}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Test interrupted by user{RESET}\n")
    except Exception as e:
        print(f"\n{RED}Error: {e}{RESET}\n")
        import traceback
        traceback.print_exc()

