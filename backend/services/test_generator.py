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
        
        # Extract context information
        project_context = analysis_data.get('project_context', '')
        detected_framework = analysis_data.get('testing_framework_detected')
        
        context_instructions = ""
        if project_context:
            context_instructions = f"""
IMPORTANT - Use the following project context to generate tests that match the project structure:

{project_context}

Generate tests that:
- Follow the project's existing patterns and conventions
- Use the correct import style for the project
- Match the project's testing framework ({detected_framework or framework})
- Use appropriate file paths based on project structure
- Include proper mocking for dependencies
"""
        
        if custom_prompt:
            # Use custom prompt
            prompt = f"""
⚠️ CRITICAL: Generate test cases EXCLUSIVELY for {framework.upper()} framework! ⚠️

TARGET FRAMEWORK: {framework.upper()}
LANGUAGE: {"JavaScript/TypeScript" if framework.lower() in ['jest', 'mocha', 'cypress'] else "Python" if framework.lower() == 'pytest' else "Java" if framework.lower() == 'junit' else "Ruby" if framework.lower() == 'rspec' else "Unknown"}

IMPORTANT INSTRUCTIONS:
❌ DO NOT return template code with placeholders like "Add your test logic here"
❌ DO NOT return generic examples with "expect(true).toBe(true)"
✅ DO generate REAL, EXECUTABLE tests based on the actual log analysis data below
✅ DO write tests that validate the specific errors, patterns, and issues found in the logs
✅ DO create meaningful assertions that test actual conditions from the log file

{custom_prompt}

{context_instructions}

ANALYSIS DATA:
Log File: {analysis_data.get('filename', 'unknown')}
Log Size: {analysis_data.get('log_size_full', 0)} characters

ERROR PATTERNS: {self._format_patterns(analysis_data.get('error_patterns', []))}
API ENDPOINTS: {self._format_api_endpoints(analysis_data.get('api_endpoints', []))}
PERFORMANCE ISSUES: {self._format_performance_issues(analysis_data.get('performance_issues', []))}
TEST SCENARIOS: {self._format_test_scenarios(analysis_data.get('test_scenarios', []))}

LOG EXCERPT: ```
{analysis_data.get('log_excerpt', 'No log excerpt')[:2000]}
```

FRAMEWORK: {framework.upper()}

REFERENCE TEMPLATE (use structure but fill with REAL test logic):
{template}

⚠️ FINAL CHECKS:
1. Are tests based on ACTUAL log data, not generic examples?
2. Is code valid {framework.upper()} syntax?
3. Would these catch the REAL issues from logs?

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
            # Use default prompt with STRONG framework emphasis
            prompt = f"""
⚠️ CRITICAL: Generate test cases EXCLUSIVELY for {framework.upper()} framework! ⚠️

TARGET FRAMEWORK: {framework.upper()}
LANGUAGE: {"JavaScript/TypeScript" if framework.lower() in ['jest', 'mocha', 'cypress'] else "Python" if framework.lower() == 'pytest' else "Java" if framework.lower() == 'junit' else "Ruby" if framework.lower() == 'rspec' else "Unknown"}

IMPORTANT INSTRUCTIONS:
❌ DO NOT return template code with placeholders like "Add your test logic here"
❌ DO NOT return generic examples with "expect(true).toBe(true)"
✅ DO generate REAL, EXECUTABLE tests based on the actual log analysis data below
✅ DO write tests that validate the specific errors, patterns, and issues found in the logs
✅ DO create meaningful assertions that test actual conditions from the log file

Based on the following log analysis, generate comprehensive test cases using {framework.upper()}:

{context_instructions}

ANALYSIS DATA:
Log File: {analysis_data.get('filename', 'unknown')}
Log Size: {analysis_data.get('log_size_full', 0)} characters

ERROR PATTERNS FOUND:
{self._format_patterns(analysis_data.get('error_patterns', []))}

API ENDPOINTS FOUND:
{self._format_api_endpoints(analysis_data.get('api_endpoints', []))}

PERFORMANCE ISSUES:
{self._format_performance_issues(analysis_data.get('performance_issues', []))}

SUGGESTED TEST SCENARIOS:
{self._format_test_scenarios(analysis_data.get('test_scenarios', []))}

LOG EXCERPT (Representative Sample):
```
{analysis_data.get('log_excerpt', 'No log excerpt available')[:2000]}
```

Requirements:
1. Generate {framework.upper()} test cases for identified errors and API endpoints FROM THE ANALYSIS DATA
2. Include proper imports and setup/teardown (matching project structure if context provided)
3. Add assertions for ACTUAL error conditions found in logs, NOT generic examples
4. Prioritize tests by risk score (critical errors first)
5. Make tests executable and production-ready with REAL test logic
6. Use project-specific patterns and conventions if context is available
7. EVERY test MUST validate something SPECIFIC from the log analysis

CODE FORMATTING STANDARDS (CRITICAL):
- Add comprehensive docstrings explaining purpose, parameters, and expected behavior
- Use Arrange-Act-Assert pattern with clear comment sections
- Include inline comments explaining WHY decisions are made
- Organize tests into logical classes/groups
- Use descriptive variable names (no single letters except loops)
- Add helper functions for reusable logic
- Include detailed assertion messages that aid debugging
- Use Path library for file handling (cross-platform compatibility)
- Add type hints where applicable (Python) or JSDoc (JavaScript)
- Follow PEP 8 (Python) or Airbnb style guide (JavaScript)
- Structure: Imports → Constants → Fixtures/Setup → Test Classes → Helper Functions

REFERENCE TEMPLATE (use this structure but fill with REAL test logic):
{template}

Generate at least 3-5 test cases covering:
- Specific error scenarios from logs (e.g., if log shows circular reference, test for that)
- Specific API endpoints mentioned in logs (not generic /api/endpoint)
- Specific performance issues found (not generic performance tests)
- Edge cases related to the actual errors found

⚠️ FINAL CHECKS BEFORE RESPONDING:
1. Does each test validate something SPECIFIC from the analysis data?
2. Are assertions based on ACTUAL log patterns, not generic examples?
3. Is the code valid {framework.upper()} syntax in {"JavaScript" if framework.lower() in ['jest', 'mocha', 'cypress'] else "Python" if framework.lower() == 'pytest' else "Java" if framework.lower() == 'junit' else "Ruby" if framework.lower() == 'rspec' else "appropriate language"}?
4. Would these tests catch the ACTUAL issues found in the logs?

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
            # Use custom or default system prompt with EXPLICIT framework specification
            if not system_prompt:
                system_prompt = f"""You are an expert test automation engineer specializing EXCLUSIVELY in {framework.upper()}.

CRITICAL REQUIREMENTS:
- You MUST generate {framework.upper()} tests ONLY
- DO NOT use Python/pytest syntax if framework is Jest/Mocha/Cypress (JavaScript)
- DO NOT use JavaScript syntax if framework is pytest (Python)
- DO NOT use Java syntax if framework is not JUnit
- DO NOT mix frameworks or languages
- The test code MUST be executable in the {framework.upper()} framework

If the framework is:
- jest/mocha/cypress: Use JavaScript/TypeScript with appropriate testing library
- pytest: Use Python with pytest syntax
- junit: Use Java with JUnit annotations
- rspec: Use Ruby with RSpec syntax

VERIFY before responding: Does your test code match the {framework.upper()} framework?"""
            
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
            
            # Reject template code - try regeneration once if detected
            if self._contains_template_code(test_cases):
                print("⚠️ Template code detected in first attempt, regenerating with stricter prompt...")
                
                # Add even stricter instruction
                strict_prompt = f"""
CRITICAL ERROR DETECTED: You returned template code in your previous attempt.

{prompt}

ABSOLUTELY FORBIDDEN PHRASES IN YOUR RESPONSE:
- "Add your test logic here"
- "expect(true).toBe(true)"
- "Add your logic"
- "TODO"
- "FIXME"
- "placeholder"

EVERY LINE OF TEST CODE MUST BE FUNCTIONAL AND BASED ON THE ANALYSIS DATA.
DO NOT USE ANY PLACEHOLDER TEXT OR GENERIC ASSERTIONS.
"""
                
                if self.provider == "openai":
                    response = await self._call_openai(strict_prompt, system_prompt)
                elif self.provider == "anthropic":
                    response = await self._call_anthropic(strict_prompt, system_prompt)
                elif self.provider == "google":
                    response = await self._call_google(strict_prompt, system_prompt)
                
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
            temperature=0.7,  # Increased for more creative, specific responses
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
            temperature=0.7,  # Increased for more creative, specific responses
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
        
        generation_config = genai.GenerationConfig(
            temperature=0.7,  # Increased for more creative, specific responses
            max_output_tokens=4000
        )
        
        response = await model.generate_content_async(
            prompt,
            generation_config=generation_config
        )
        return response.text
    
    def _contains_template_code(self, test_cases: List[Dict[str, Any]]) -> bool:
        """Check if test cases contain template/placeholder code"""
        template_indicators = [
            'add your test logic here',
            'add your logic',
            'expect(true).tobe(true)',
            'assert true',
            'todo',
            'fixme',
            'placeholder',
            'sample test',
            'your code here',
            'implement this'
        ]
        
        for test_case in test_cases:
            test_code = test_case.get('test_code', '').lower()
            for indicator in template_indicators:
                if indicator in test_code:
                    print(f"⚠️ Found template indicator: '{indicator}'")
                    return True
        
        return False
    
    def _validate_framework_match(self, test_code: str, framework: str) -> bool:
        """Validate that the test code matches the expected framework"""
        framework_lower = framework.lower()
        
        # Framework-specific validation patterns
        validation_patterns = {
            'jest': [
                (r'import.*from.*[\'"]jest[\'"]', True),  # Jest imports
                (r'describe\s*\(', True),  # Describe blocks
                (r'(test|it)\s*\(', True),  # Test blocks
                (r'expect\s*\(', True),  # Assertions
                (r'import\s+pytest', False),  # Should NOT have pytest
                (r'@pytest', False),  # Should NOT have pytest decorators
            ],
            'mocha': [
                (r'describe\s*\(', True),
                (r'it\s*\(', True),
                (r'(expect|assert)', True),
                (r'import\s+pytest', False),
                (r'@pytest', False),
            ],
            'cypress': [
                (r'cy\.', True),  # Cypress commands
                (r'describe\s*\(', True),
                (r'it\s*\(', True),
                (r'import\s+pytest', False),
                (r'@pytest', False),
            ],
            'pytest': [
                (r'import\s+pytest', True),  # Pytest imports
                (r'def\s+test_', True),  # Test functions
                (r'@pytest', True),  # Pytest decorators (optional but common)
                (r'describe\s*\(', False),  # Should NOT have JS describe
                (r'it\s*\(', False),  # Should NOT have JS it
            ],
            'junit': [
                (r'@Test', True),  # JUnit annotations
                (r'import.*org\.junit', True),  # JUnit imports
                (r'public\s+(void|class)', True),  # Java syntax
                (r'import\s+pytest', False),
                (r'describe\s*\(', False),
            ],
            'rspec': [
                (r'describe\s+[\'"]', True),  # RSpec describe
                (r'it\s+[\'"]', True),  # RSpec it
                (r'expect\s*\(', True),  # RSpec expectations
                (r'import\s+pytest', False),
                (r'import.*from', False),  # Should NOT have JS imports
            ]
        }
        
        if framework_lower not in validation_patterns:
            return True  # Unknown framework, skip validation
        
        patterns = validation_patterns[framework_lower]
        for pattern, should_match in patterns:
            has_match = bool(re.search(pattern, test_code, re.MULTILINE | re.IGNORECASE))
            if should_match and not has_match:
                # Required pattern not found
                return False
            if not should_match and has_match:
                # Forbidden pattern found (wrong framework)
                print(f"⚠️ WARNING: Found wrong framework pattern '{pattern}' in {framework} test code")
                return False
        
        return True
    
    def _parse_test_response(self, response: str, framework: str) -> List[Dict[str, Any]]:
        """Parse AI response into test cases"""
        try:
            # Try to extract JSON array from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                test_cases = json.loads(json_match.group())
                test_cases = test_cases if isinstance(test_cases, list) else [test_cases]
                
                # Validate each test case matches the framework
                validated_cases = []
                for tc in test_cases:
                    test_code = tc.get('test_code', '')
                    if self._validate_framework_match(test_code, framework):
                        validated_cases.append(tc)
                    else:
                        print(f"⚠️ Rejected test case: Framework mismatch (expected {framework})")
                        # Try to add a warning to the test case
                        tc['description'] = f"⚠️ FRAMEWORK MISMATCH - {tc.get('description', 'Test')}"
                        tc['test_code'] = f"// ERROR: Generated code does not match {framework} framework\n// Please regenerate tests\n\n{test_code}"
                        validated_cases.append(tc)
                
                return validated_cases if validated_cases else test_cases
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
JEST Template - Generate PRODUCTION-READY tests with this structure:

```javascript
/**
 * Test Suite: [Descriptive Name]
 * 
 * Purpose: [What this test suite validates]
 * Priority: [high/medium/low]
 * Risk Score: [0.0-1.0]
 */

import request from 'supertest';
import { app } from '../src/app';

describe('[Feature/Component] Tests', () => {
  // Setup: Configure test environment
  beforeAll(async () => {
    // Initialize test database, mocks, etc.
  });

  // Cleanup: Reset state after tests
  afterAll(async () => {
    // Close connections, clear mocks
  });

  describe('[Specific Scenario]', () => {
    it('should [expected behavior] when [condition]', async () => {
      // Arrange: Set up test data
      const testData = { /* ... */ };

      // Act: Execute the test
      const response = await request(app)
        .post('/api/endpoint')
        .send(testData);

      // Assert: Verify results
    expect(response.status).toBe(200);
      expect(response.body).toHaveProperty('data');
    });

    it('should handle error when [error condition]', async () => {
      // Test error scenarios with clear assertions
      const response = await request(app)
        .post('/api/endpoint')
        .send({ invalid: 'data' });

      expect(response.status).toBe(400);
      expect(response.body.error).toBeDefined();
    });
  });
});
```

IMPORTANT FORMATTING RULES:
- Use descriptive test names with "should [action] when [condition]"
- Add JSDoc comments for test suites
- Follow Arrange-Act-Assert pattern
- Include setup/teardown hooks
- Group related tests with nested describe blocks
- Add inline comments explaining complex logic
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
PYTEST Template - Generate PRODUCTION-READY tests with this structure:

```python
\"\"\"
Test Suite: [Descriptive Name]

Purpose: [What this test suite validates]
Priority: [high/medium/low]
Risk Score: [0.0-1.0]

Author: ChaturLog Auto-Generated
Framework: pytest
\"\"\"

import pytest
import json
import re
from pathlib import Path
from typing import Dict, List, Any


# ============================================================================
# Fixtures: Reusable test data and setup
# ============================================================================

@pytest.fixture(scope='module')
def log_file_path():
    \"\"\"Return path to log file for testing.\"\"\"
    return Path(__file__).parent / 'logs' / 'test-log.json'


@pytest.fixture(scope='module')
def log_data(log_file_path):
    \"\"\"Load and parse log file content.\"\"\"
    with open(log_file_path, 'r', encoding='utf-8') as file:
        return file.read()


@pytest.fixture(scope='module')
def parsed_logs(log_data):
    \"\"\"Parse log data into structured format.\"\"\"
    try:
        return json.loads(log_data)
    except json.JSONDecodeError:
        return log_data.split('\\n')


# ============================================================================
# Test Cases: Organized by functionality
# ============================================================================

class TestErrorPatterns:
    \"\"\"Test suite for validating error patterns in logs.\"\"\"
    
    def test_no_critical_errors(self, log_data):
        \"\"\"
        Verify no critical errors exist in logs.
        
        Critical errors indicate severe issues that may cause
        system failures or data corruption.
        \"\"\"
        # Arrange: Define critical error patterns
        critical_patterns = [
            r'CRITICAL',
            r'FATAL',
            r'\\[Circular\\]',
            r'OutOfMemory',
            r'StackOverflow'
        ]
        
        # Act: Search for critical patterns
        found_errors = []
        for pattern in critical_patterns:
            matches = re.findall(pattern, log_data, re.IGNORECASE)
            if matches:
                found_errors.append((pattern, len(matches)))
        
        # Assert: No critical errors should exist
        assert len(found_errors) == 0, (
            f'Found {len(found_errors)} critical error patterns:\\n' +
            '\\n'.join(f'  - {pat}: {count} occurrences' 
                      for pat, count in found_errors)
        )
    
    def test_error_rate_within_threshold(self, parsed_logs):
        \"\"\"
        Verify error rate is within acceptable threshold.
        
        Error rate should be < 5% of total log entries.
        \"\"\"
        # Arrange
        if isinstance(parsed_logs, list):
            total_entries = len(parsed_logs)
            error_entries = sum(1 for log in parsed_logs 
                              if 'error' in str(log).lower())
        else:
            total_entries = 1
            error_entries = 0
        
        # Calculate error rate
        error_rate = (error_entries / total_entries * 100) if total_entries > 0 else 0
        threshold = 5.0
        
        # Assert: Error rate below threshold
        assert error_rate < threshold, (
            f'Error rate {error_rate:.2f}% exceeds threshold {threshold}%. '
            f'Found {error_entries} errors in {total_entries} log entries.'
        )


class TestAPIEndpoints:
    \"\"\"Test suite for API endpoint validation from logs.\"\"\"
    
    def test_no_500_errors(self, log_data):
        \"\"\"Verify no HTTP 500 errors in API calls.\"\"\"
        # Arrange: Pattern for HTTP 500 errors
        pattern = re.compile(r'HTTP\\s*500|status[:\\s]*500', re.IGNORECASE)
        
        # Act: Find all matches
        matches = pattern.findall(log_data)
        
        # Assert: No 500 errors
        assert len(matches) == 0, (
            f'Found {len(matches)} HTTP 500 errors. '
            f'This indicates server-side failures that need investigation.'
        )
    
    @pytest.mark.parametrize('status_code', [400, 401, 403, 404])
    def test_client_error_codes(self, log_data, status_code):
        \"\"\"Test handling of client error codes (4xx).\"\"\"
        pattern = re.compile(
            rf'HTTP\\s*{status_code}|status[:\\s]*{status_code}',
            re.IGNORECASE
        )
        matches = pattern.findall(log_data)
        
        # Note: Client errors are acceptable but should be monitored
        if matches:
            print(f'INFO: Found {len(matches)} HTTP {status_code} responses')


class TestPerformance:
    \"\"\"Test suite for performance issues in logs.\"\"\"
    
    def test_no_timeout_errors(self, log_data):
        \"\"\"Verify no timeout errors in logs.\"\"\"
        # Arrange: Timeout patterns
        timeout_patterns = [
            r'timeout',
            r'timed out',
            r'ETIMEDOUT',
            r'request timeout'
        ]
        
        # Act: Search for timeout patterns
        found_timeouts = []
        for pattern in timeout_patterns:
            matches = re.findall(pattern, log_data, re.IGNORECASE)
            if matches:
                found_timeouts.extend(matches)
        
        # Assert: No timeouts
        assert len(found_timeouts) == 0, (
            f'Found {len(found_timeouts)} timeout occurrences. '
            f'This indicates performance issues or network problems.'
        )


# ============================================================================
# Helper Functions
# ============================================================================

def extract_timestamps(log_data: str) -> List[str]:
    \"\"\"Extract timestamps from log entries.\"\"\"
    timestamp_pattern = r'\\d{4}-\\d{2}-\\d{2}[T ]\\d{2}:\\d{2}:\\d{2}'
    return re.findall(timestamp_pattern, log_data)


def count_pattern_occurrences(log_data: str, pattern: str) -> int:
    \"\"\"Count occurrences of a pattern in log data.\"\"\"
    return len(re.findall(pattern, log_data, re.IGNORECASE))
```

IMPORTANT FORMATTING RULES:
- Use triple-quoted docstrings for all classes and functions
- Organize tests into logical classes
- Follow Arrange-Act-Assert pattern with clear comments
- Use descriptive test names: test_[what]_[condition]
- Include helper functions for reusable logic
- Use @pytest.mark.parametrize for testing multiple scenarios
- Add inline comments explaining WHY, not just WHAT
- Include assertion messages that help debugging
- Use Path for file handling (cross-platform)
- Handle exceptions gracefully
- Group related fixtures together
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
    
    def _format_patterns(self, patterns: List[Dict]) -> str:
        """Format error patterns for prompt"""
        if not patterns:
            return "No specific error patterns identified"
        
        formatted = []
        for i, pattern in enumerate(patterns[:10], 1):  # Limit to 10
            formatted.append(f"{i}. {pattern.get('type', 'Unknown')}: {pattern.get('description', 'No description')}")
            formatted.append(f"   Severity: {pattern.get('severity', 'medium')}, Frequency: {pattern.get('frequency', 1)}")
        
        if len(patterns) > 10:
            formatted.append(f"... and {len(patterns) - 10} more patterns")
        
        return '\n'.join(formatted)
    
    def _format_api_endpoints(self, endpoints: List[Dict]) -> str:
        """Format API endpoints for prompt"""
        if not endpoints:
            return "No API endpoints identified"
        
        formatted = []
        for i, ep in enumerate(endpoints[:15], 1):  # Limit to 15
            method = ep.get('method', 'GET')
            path = ep.get('path', '/')
            status = ep.get('status_codes', [])
            issues = ep.get('issues', '')
            formatted.append(f"{i}. {method} {path} → Status: {status}")
            if issues:
                formatted.append(f"   Issues: {issues}")
        
        if len(endpoints) > 15:
            formatted.append(f"... and {len(endpoints) - 15} more endpoints")
        
        return '\n'.join(formatted)
    
    def _format_performance_issues(self, issues: List[Dict]) -> str:
        """Format performance issues for prompt"""
        if not issues:
            return "No performance issues identified"
        
        formatted = []
        for i, issue in enumerate(issues[:10], 1):  # Limit to 10
            formatted.append(f"{i}. {issue.get('issue', 'Unknown issue')}")
            formatted.append(f"   Impact: {issue.get('impact', 'Unknown')}, Frequency: {issue.get('frequency', 'Unknown')}")
        
        if len(issues) > 10:
            formatted.append(f"... and {len(issues) - 10} more issues")
        
        return '\n'.join(formatted)
    
    def _format_test_scenarios(self, scenarios: List[Dict]) -> str:
        """Format test scenarios for prompt"""
        if not scenarios:
            return "No specific test scenarios suggested"
        
        formatted = []
        for i, scenario in enumerate(scenarios[:10], 1):  # Limit to 10
            formatted.append(f"{i}. {scenario.get('scenario', 'Unknown scenario')}")
            formatted.append(f"   Priority: {scenario.get('priority', 'medium')}")
        
        if len(scenarios) > 10:
            formatted.append(f"... and {len(scenarios) - 10} more scenarios")
        
        return '\n'.join(formatted)
    
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
