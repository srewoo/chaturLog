import os
import re
import json
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class TestGenerator:
    """Generate test cases from log analysis using direct API calls"""
    
    def __init__(self, ai_model: str = "gpt-4o", api_key: str = None):
        self.ai_model = ai_model
        self.api_key = api_key
        
        # Determine provider and model
        if "gpt" in ai_model or "openai" in ai_model:
            self.provider = "openai"
            self.model_name = ai_model if "gpt" in ai_model else "gpt-4o"
        elif "claude" in ai_model or "anthropic" in ai_model:
            self.provider = "anthropic"
            self.model_name = ai_model if "claude" in ai_model else "claude-3-7-sonnet-20250219"
        elif "gemini" in ai_model:
            self.provider = "google"
            self.model_name = ai_model if "gemini" in ai_model else "gemini-2.0-flash-exp"
        else:
            self.provider = "openai"
            self.model_name = "gpt-4o"
    
    async def generate_tests(self, analysis_data: Dict[str, Any], framework: str, custom_prompt: str = None, system_prompt: str = None) -> List[Dict[str, Any]]:
        """
        Generate test cases based on analysis data
        
        Args:
            analysis_data: Analysis results from log analysis
            framework: Test framework ('jest', 'junit', 'pytest', 'mocha', 'cypress', 'rspec')
            custom_prompt: Optional custom test generation prompt
            system_prompt: Optional system prompt to define AI's role
        """
        # Create test generation prompt
        framework_templates = {
            "jest": self._get_jest_template(),
            "junit": self._get_junit_template(),
            "pytest": self._get_pytest_template(),
            "mocha": self._get_mocha_template(),
            "cypress": self._get_cypress_template(),
            "rspec": self._get_rspec_template()
        }
        
        template = framework_templates.get(framework, framework_templates["jest"])
        
        if custom_prompt:
            # Use custom prompt
            prompt = f"""
{custom_prompt}

ANALYSIS DATA:
{str(analysis_data)}

FRAMEWORK: {framework.upper()}

{template}

Respond with a JSON array of test cases:
[
  {{
    "description": "Test description",
    "priority": "high|medium|low",
    "risk_score": 0.0-1.0,
    "test_code": "Complete executable test code"
  }}
]
"""
        else:
            # Use default prompt
            prompt = f"""
Based on the following log analysis, generate comprehensive test cases using {framework.upper()}:

ANALYSIS DATA:
{str(analysis_data)}

Requirements:
1. Generate {framework.upper()} test cases for identified errors and API endpoints
2. Include proper imports and setup/teardown
3. Add assertions for error conditions, status codes, and response validation
4. Prioritize tests by risk score (critical errors first)
5. Make tests executable and production-ready

{template}

Generate at least 3-5 test cases covering:
- Error scenarios from logs
- API endpoint testing
- Performance validation
- Edge cases

Respond with a JSON array of test cases:
[
  {{
    "description": "Test description",
    "priority": "high|medium|low",
    "risk_score": 0.0-1.0,
    "test_code": "Complete executable test code"
  }}
]
"""
        
        try:
            # Use custom or default system prompt
            if not system_prompt:
                system_prompt = f"You are an expert test automation engineer specializing in {framework}."
            
            if self.provider == "openai":
                response = await self._call_openai(prompt, system_prompt)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(prompt, system_prompt)
            elif self.provider == "google":
                response = await self._call_google(prompt, system_prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Parse test cases from response
            test_cases = self._parse_test_response(response, framework)
            
            return test_cases
        except Exception as e:
            # Return a sample test case on error
            return [{
                "description": f"Sample {framework} test - Error during generation: {str(e)}",
                "priority": "low",
                "risk_score": 0.1,
                "test_code": self._get_sample_test(framework)
            }]
    
    async def _call_openai(self, prompt: str, system_prompt: str) -> str:
        """Call OpenAI API directly"""
        import openai
        
        client = openai.AsyncOpenAI(api_key=self.api_key)
        
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str, system_prompt: str) -> str:
        """Call Anthropic API directly"""
        import anthropic
        
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        response = await client.messages.create(
            model=self.model_name,
            max_tokens=4000,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    async def _call_google(self, prompt: str, system_prompt: str) -> str:
        """Call Google Gemini API directly"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_prompt
        )
        
        response = await model.generate_content_async(prompt)
        return response.text
    
    def _parse_test_response(self, response: str, framework: str) -> List[Dict[str, Any]]:
        """Parse AI response into test cases"""
        try:
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                test_cases = json.loads(json_match.group())
                return test_cases if isinstance(test_cases, list) else [test_cases]
            else:
                # Fallback: create sample test
                return [{
                    "description": f"Generated {framework} test from analysis",
                    "priority": "medium",
                    "risk_score": 0.5,
                    "test_code": self._extract_code_blocks(response, framework)
                }]
        except json.JSONDecodeError:
            return [{
                "description": f"Generated {framework} test",
                "priority": "medium",
                "risk_score": 0.5,
                "test_code": self._extract_code_blocks(response, framework)
            }]
    
    def _extract_code_blocks(self, text: str, framework: str) -> str:
        """Extract code blocks from markdown response"""
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', text, re.DOTALL)
        if code_blocks:
            return code_blocks[0]
        return self._get_sample_test(framework)
    
    def _get_jest_template(self) -> str:
        return """
JEST Template Example:
```javascript
import request from 'supertest';
import { app } from '../src/app';

describe('API Tests', () => {
  it('should handle error scenario', async () => {
    const response = await request(app).get('/api/endpoint');
    expect(response.status).toBe(200);
  });
});
```
"""
    
    def _get_junit_template(self) -> str:
        return """
JUNIT Template Example:
```java
import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;
import org.junit.Test;

public class ApiTests {
  @Test
  public void testErrorScenario() {
    given()
      .when().get("/api/endpoint")
      .then().statusCode(200);
  }
}
```
"""
    
    def _get_pytest_template(self) -> str:
        return """
PYTEST Template Example:
```python
import pytest
import requests

def test_error_scenario():
    response = requests.get('http://localhost:8000/api/endpoint')
    assert response.status_code == 200
```
"""
    
    def _get_mocha_template(self) -> str:
        return """
MOCHA Template Example:
```javascript
const chai = require('chai');
const request = require('supertest');
const expect = chai.expect;
const app = require('../src/app');

describe('API Tests', function() {
  it('should handle error scenario', function(done) {
    request(app)
      .get('/api/endpoint')
      .expect(200)
      .end(function(err, res) {
        expect(res.status).to.equal(200);
        done();
      });
  });
});
```
"""
    
    def _get_cypress_template(self) -> str:
        return """
CYPRESS Template Example:
```javascript
describe('API E2E Tests', () => {
  beforeEach(() => {
    cy.visit('/');
  });

  it('should handle error scenario', () => {
    cy.request('GET', '/api/endpoint')
      .its('status')
      .should('eq', 200);
  });

  it('should display error message on failure', () => {
    cy.intercept('GET', '/api/endpoint', { statusCode: 500 }).as('apiFailure');
    cy.visit('/dashboard');
    cy.wait('@apiFailure');
    cy.contains('Error').should('be.visible');
  });
});
```
"""
    
    def _get_rspec_template(self) -> str:
        return """
RSPEC Template Example:
```ruby
require 'rails_helper'
require 'net/http'

RSpec.describe 'API Tests', type: :request do
  describe 'GET /api/endpoint' do
    it 'handles error scenario' do
      get '/api/endpoint'
      expect(response).to have_http_status(:ok)
      expect(response.content_type).to match(/json/)
    end

    it 'returns proper error on invalid request' do
      get '/api/endpoint', params: { invalid: 'data' }
      expect(response).to have_http_status(:unprocessable_entity)
    end
  end
end
```
"""
    
    def _get_sample_test(self, framework: str) -> str:
        """Return a sample test case"""
        samples = {
            "jest": """import request from 'supertest';

describe('Sample Test', () => {
  it('should return 200', async () => {
    // Add your test logic here
    expect(true).toBe(true);
  });
});""",
            "junit": """import org.junit.Test;
import static org.junit.Assert.*;

public class SampleTest {
  @Test
  public void testSample() {
    assertTrue(true);
  }
}""",
            "pytest": """import pytest

def test_sample():
    assert True
""",
            "mocha": """const chai = require('chai');
const expect = chai.expect;

describe('Sample Test', function() {
  it('should return true', function() {
    expect(true).to.be.true;
  });
});""",
            "cypress": """describe('Sample E2E Test', () => {
  it('should load the page', () => {
    cy.visit('/');
    cy.contains('Welcome').should('be.visible');
  });
});""",
            "rspec": """require 'rails_helper'

RSpec.describe 'Sample Test' do
  it 'should return true' do
    expect(true).to be true
  end
end
"""
        }
        return samples.get(framework, samples["jest"])
