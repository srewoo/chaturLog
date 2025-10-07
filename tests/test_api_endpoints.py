"""
ChaturLog API Endpoints Test Suite

Comprehensive unit tests for all API endpoints and features.

Test Coverage:
- Authentication (register, login)
- File upload and validation
- Log analysis
- Test generation (all frameworks)
- Settings and API key management
- Git configuration and repository mappings
- Custom prompts
- Analysis history (CRUD operations)
"""

import pytest
import requests
import json
import time
from pathlib import Path
from typing import Dict, Optional

# Configuration
BASE_URL = "http://localhost:8001"
API_PREFIX = "/api"

# Test data
TEST_USERS = [
    {"email": "srewoo@gmail.com", "password": "Pass@1213"},
    {"email": "test2@chaturlog.com", "password": "SecurePass456!"}
]

SAMPLE_LOG_FILE = Path(__file__).parent / "sample file.json"
FRAMEWORKS = ["jest", "junit", "pytest", "mocha", "cypress", "rspec"]


class TestAuth:
    """Test authentication endpoints"""
    
    def test_register_new_user(self):
        """Test user registration with valid data"""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json={"email": "newuser@test.com", "password": "NewPass123!"}
        )
        assert response.status_code in [200, 400]  # 400 if user exists
        if response.status_code == 200:
            data = response.json()
            assert "message" in data
    
    def test_register_invalid_email(self):
        """Test registration with invalid email format"""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json={"email": "invalid-email", "password": "Pass123!"}
        )
        assert response.status_code == 422
    
    def test_register_weak_password(self):
        """Test registration with weak password"""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json={"email": "test@test.com", "password": "123"}
        )
        assert response.status_code == 422
    
    def test_register_missing_fields(self):
        """Test registration with missing required fields"""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            json={"email": "test@test.com"}
        )
        assert response.status_code == 422
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials"""
        # Register first
        requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USERS[0])
        
        # Login
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json=TEST_USERS[0]
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 0
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"email": "nonexistent@test.com", "password": "WrongPass123!"}
        )
        assert response.status_code == 401
    
    def test_login_missing_fields(self):
        """Test login with missing fields"""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/login",
            json={"email": "test@test.com"}
        )
        assert response.status_code == 422


class TestFileUpload:
    """Test file upload endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token for tests"""
        requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USERS[0])
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=TEST_USERS[0])
        return response.json()["access_token"]
    
    def test_upload_valid_log_file(self, auth_token):
        """Test uploading a valid log file"""
        if not SAMPLE_LOG_FILE.exists():
            pytest.skip("Sample log file not found")
        
        with open(SAMPLE_LOG_FILE, 'rb') as f:
            files = {'file': f}
            headers = {'Authorization': f'Bearer {auth_token}'}
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/upload",
                files=files,
                headers=headers
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "filename" in data
        assert "message" in data
    
    def test_upload_without_auth(self):
        """Test uploading without authentication"""
        if not SAMPLE_LOG_FILE.exists():
            pytest.skip("Sample log file not found")
        
        with open(SAMPLE_LOG_FILE, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/upload",
                files=files
            )
        
        assert response.status_code == 401
    
    def test_upload_invalid_file_type(self, auth_token):
        """Test uploading invalid file type"""
        # Create a fake image file
        fake_file = b"fake image content"
        files = {'file': ('test.png', fake_file, 'image/png')}
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/upload",
            files=files,
            headers=headers
        )
        
        # Should reject non-log files
        assert response.status_code in [400, 422]
    
    def test_upload_empty_file(self, auth_token):
        """Test uploading empty file"""
        files = {'file': ('empty.log', b'', 'text/plain')}
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/upload",
            files=files,
            headers=headers
        )
        
        assert response.status_code in [400, 422]


class TestLogAnalysis:
    """Test log analysis endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USERS[0])
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=TEST_USERS[0])
        return response.json()["access_token"]
    
    @pytest.fixture
    def uploaded_filename(self, auth_token):
        """Upload a file and return filename"""
        if not SAMPLE_LOG_FILE.exists():
            pytest.skip("Sample log file not found")
        
        with open(SAMPLE_LOG_FILE, 'rb') as f:
            files = {'file': f}
            headers = {'Authorization': f'Bearer {auth_token}'}
            response = requests.post(
                f"{BASE_URL}{API_PREFIX}/upload",
                files=files,
                headers=headers
            )
        return response.json()["filename"]
    
    def test_analyze_log_file(self, auth_token, uploaded_filename):
        """Test analyzing a log file"""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/analyze",
            json={"filename": uploaded_filename},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis_id" in data
        assert "message" in data
    
    def test_analyze_without_auth(self, uploaded_filename):
        """Test analyzing without authentication"""
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/analyze",
            json={"filename": uploaded_filename}
        )
        assert response.status_code == 401
    
    def test_analyze_nonexistent_file(self, auth_token):
        """Test analyzing nonexistent file"""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/analyze",
            json={"filename": "nonexistent.log"},
            headers=headers
        )
        assert response.status_code in [404, 500]
    
    def test_get_analysis_by_id(self, auth_token, uploaded_filename):
        """Test retrieving analysis by ID"""
        # First analyze
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        analyze_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/analyze",
            json={"filename": uploaded_filename},
            headers=headers
        )
        analysis_id = analyze_response.json()["analysis_id"]
        
        # Wait for analysis
        time.sleep(2)
        
        # Get analysis
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/analyze/{analysis_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "analysis" in data
        assert "patterns" in data
    
    def test_get_all_analyses(self, auth_token):
        """Test getting all analyses for user"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/analyses",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_delete_analysis(self, auth_token, uploaded_filename):
        """Test deleting an analysis"""
        # First analyze
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        analyze_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/analyze",
            json={"filename": uploaded_filename},
            headers=headers
        )
        analysis_id = analyze_response.json()["analysis_id"]
        
        # Delete analysis
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/analyses/{analysis_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True


class TestTestGeneration:
    """Test test generation endpoints"""
    
    @pytest.fixture
    def analysis_id(self):
        """Create an analysis and return its ID"""
        # Register and login
        requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USERS[0])
        login_response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=TEST_USERS[0])
        token = login_response.json()["access_token"]
        
        # Upload file
        if not SAMPLE_LOG_FILE.exists():
            pytest.skip("Sample log file not found")
        
        with open(SAMPLE_LOG_FILE, 'rb') as f:
            files = {'file': f}
            headers = {'Authorization': f'Bearer {token}'}
            upload_response = requests.post(
                f"{BASE_URL}{API_PREFIX}/upload",
                files=files,
                headers=headers
            )
        
        filename = upload_response.json()["filename"]
        
        # Analyze
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        analyze_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/analyze",
            json={"filename": filename},
            headers=headers
        )
        
        time.sleep(2)  # Wait for analysis
        return analyze_response.json()["analysis_id"], token
    
    @pytest.mark.parametrize("framework", FRAMEWORKS)
    def test_generate_tests_all_frameworks(self, analysis_id, framework):
        """Test generating tests for each framework"""
        aid, token = analysis_id
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/generate-tests/{aid}",
            json={"framework": framework},
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "tests" in data
        assert len(data["tests"]) > 0
        
        # Validate test structure
        for test in data["tests"]:
            assert "description" in test
            assert "test_code" in test
            assert len(test["test_code"]) > 100  # Should not be empty/minimal
    
    def test_generate_tests_invalid_framework(self, analysis_id):
        """Test generating tests with invalid framework"""
        aid, token = analysis_id
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/generate-tests/{aid}",
            json={"framework": "invalid_framework"},
            headers=headers
        )
        
        # Should either reject or fall back to default
        assert response.status_code in [200, 400, 422]
    
    def test_generate_tests_without_auth(self, analysis_id):
        """Test generating tests without authentication"""
        aid, _ = analysis_id
        
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/generate-tests/{aid}",
            json={"framework": "jest"}
        )
        
        assert response.status_code == 401
    
    def test_export_tests(self, analysis_id):
        """Test exporting generated tests"""
        aid, token = analysis_id
        
        # First generate tests
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        requests.post(
            f"{BASE_URL}{API_PREFIX}/generate-tests/{aid}",
            json={"framework": "jest"},
            headers=headers
        )
        
        # Export tests
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/export-tests/{aid}",
            headers=headers
        )
        
        assert response.status_code == 200
        assert response.headers['Content-Type'] == 'application/zip'


class TestSettings:
    """Test settings and API key management"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USERS[0])
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=TEST_USERS[0])
        return response.json()["access_token"]
    
    def test_get_api_keys(self, auth_token):
        """Test getting API keys"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/settings/api-keys",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "api_keys" in data
    
    def test_save_api_key(self, auth_token):
        """Test saving an API key"""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/settings/api-keys",
            json={
                "provider": "openai",
                "api_key": "sk-test-key-123",
                "model": "gpt-4o"
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
    
    def test_save_api_key_invalid_provider(self, auth_token):
        """Test saving API key with invalid provider"""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/settings/api-keys",
            json={
                "provider": "invalid_provider",
                "api_key": "test-key",
                "model": "test-model"
            },
            headers=headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_delete_api_key(self, auth_token):
        """Test deleting an API key"""
        # First save a key
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        requests.post(
            f"{BASE_URL}{API_PREFIX}/settings/api-keys",
            json={
                "provider": "openai",
                "api_key": "sk-test-key-123",
                "model": "gpt-4o"
            },
            headers=headers
        )
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/settings/api-keys/openai",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True


class TestGitIntegration:
    """Test Git configuration and repository mappings"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USERS[0])
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=TEST_USERS[0])
        return response.json()["access_token"]
    
    def test_get_git_config(self, auth_token):
        """Test getting Git configuration"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/settings/git-config",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    def test_save_git_config(self, auth_token):
        """Test saving Git configuration"""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/settings/git-config",
            json={
                "git_provider": "github",
                "repository": "test-org/test-repo",
                "git_token": "test-token-123",
                "default_branch": "main",
                "enabled": True
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
    
    def test_save_git_config_invalid_provider(self, auth_token):
        """Test saving Git config with invalid provider"""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/settings/git-config",
            json={
                "git_provider": "invalid",
                "repository": "test/repo",
                "git_token": "token",
                "default_branch": "main",
                "enabled": True
            },
            headers=headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_get_repo_mappings(self, auth_token):
        """Test getting repository mappings"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/repo-mappings",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "mappings" in data
    
    def test_save_repo_mapping(self, auth_token):
        """Test saving a repository mapping"""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/repo-mappings",
            json={
                "service_name": "test-service",
                "repository": "org/repo"
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
    
    def test_delete_repo_mapping(self, auth_token):
        """Test deleting a repository mapping"""
        # First create a mapping
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        requests.post(
            f"{BASE_URL}{API_PREFIX}/repo-mappings",
            json={
                "service_name": "test-service",
                "repository": "org/repo"
            },
            headers=headers
        )
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/repo-mappings/test-service",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True


class TestCustomPrompts:
    """Test custom prompts management"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        requests.post(f"{BASE_URL}{API_PREFIX}/auth/register", json=TEST_USERS[0])
        response = requests.post(f"{BASE_URL}{API_PREFIX}/auth/login", json=TEST_USERS[0])
        return response.json()["access_token"]
    
    def test_get_custom_prompts(self, auth_token):
        """Test getting custom prompts"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/settings/custom-prompts",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "prompts" in data
    
    def test_save_custom_prompt(self, auth_token):
        """Test saving a custom prompt"""
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/settings/custom-prompts",
            json={
                "name": "Test Prompt",
                "prompt_type": "system",
                "prompt_text": "You are a helpful assistant.",
                "is_default": False
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "prompt_id" in data
    
    def test_update_custom_prompt(self, auth_token):
        """Test updating a custom prompt"""
        # First create a prompt
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/settings/custom-prompts",
            json={
                "name": "Test Prompt",
                "prompt_type": "system",
                "prompt_text": "Original text",
                "is_default": False
            },
            headers=headers
        )
        prompt_id = create_response.json()["prompt_id"]
        
        # Update it
        response = requests.put(
            f"{BASE_URL}{API_PREFIX}/settings/custom-prompts/{prompt_id}",
            json={
                "name": "Updated Prompt",
                "prompt_text": "Updated text"
            },
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True
    
    def test_delete_custom_prompt(self, auth_token):
        """Test deleting a custom prompt"""
        # First create a prompt
        headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        create_response = requests.post(
            f"{BASE_URL}{API_PREFIX}/settings/custom-prompts",
            json={
                "name": "Test Prompt",
                "prompt_type": "system",
                "prompt_text": "Test text",
                "is_default": False
            },
            headers=headers
        )
        prompt_id = create_response.json()["prompt_id"]
        
        # Delete it
        response = requests.delete(
            f"{BASE_URL}{API_PREFIX}/settings/custom-prompts/{prompt_id}",
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data.get("success") is True


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_endpoint(self):
        """Test accessing invalid endpoint"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/invalid-endpoint")
        assert response.status_code == 404
    
    def test_missing_auth_token(self):
        """Test accessing protected endpoint without token"""
        response = requests.get(f"{BASE_URL}{API_PREFIX}/analyses")
        assert response.status_code == 401
    
    def test_invalid_auth_token(self):
        """Test accessing protected endpoint with invalid token"""
        headers = {'Authorization': 'Bearer invalid-token-123'}
        response = requests.get(
            f"{BASE_URL}{API_PREFIX}/analyses",
            headers=headers
        )
        assert response.status_code == 401
    
    def test_malformed_json(self):
        """Test sending malformed JSON"""
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/auth/register",
            data="invalid json{",
            headers=headers
        )
        assert response.status_code == 422


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
