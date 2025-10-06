import os
import re
import json
from typing import Dict, List, Any
from dotenv import load_dotenv

load_dotenv()

class LogAnalyzer:
    """AI-powered log analysis service using direct API calls"""
    
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
    
    async def analyze_logs(self, log_content: str, filename: str) -> Dict[str, Any]:
        """
        Analyze log file and extract patterns, errors, and insights
        """
        # Create analysis prompt
        prompt = f"""
Analyze the following log file and provide a comprehensive analysis:

LOG FILE: {filename}
===
{log_content[:10000]}  # Limit to first 10k characters for analysis
===

Please provide:
1. **Error Patterns**: List all error patterns with severity (critical/high/medium/low)
2. **API Endpoints**: Extract all API endpoints, HTTP methods, and status codes
3. **Performance Issues**: Identify slow requests, timeouts, or bottlenecks
4. **Business Impact**: Assess user impact and severity
5. **Test Scenarios**: Suggest key test scenarios based on the errors found
6. **Error Fix**: Suggest a fix for the error
7. **Error Prevention**: Suggest a prevention for the error
8. **Error Detection**: Suggest a detection for the error
9. **Error Recovery**: Suggest a recovery for the error
10. **Error Logging**: Suggest a logging for the error
11. **Error Monitoring**: Suggest a monitoring for the error
12. **Error Alerting**: Suggest a alerting for the error
13. **Error Reporting**: Suggest a reporting for the error

Format your response as a structured JSON with these keys:
- error_patterns: [{{type, description, severity, frequency}}]
- api_endpoints: [{{method, path, status_codes, issues}}]
- performance_issues: [{{issue, impact, frequency}}]
- business_impact: {{severity, affected_users, description}}
- test_scenarios: [{{scenario, priority, framework_hint}}]
"""
        
        try:
            if self.provider == "openai":
                response = await self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(prompt)
            elif self.provider == "google":
                response = await self._call_google(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Parse AI response
            analysis_result = self._parse_ai_response(response)
            
            return {
                "success": True,
                "analysis": analysis_result,
                "ai_model": self.ai_model
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ai_model": self.ai_model
            }
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API directly"""
        import openai
        
        client = openai.AsyncOpenAI(api_key=self.api_key)
        
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert log analyzer. Analyze logs and identify errors, patterns, performance issues, and API endpoints."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API directly"""
        import anthropic
        
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        response = await client.messages.create(
            model=self.model_name,
            max_tokens=4000,
            system="You are an expert log analyzer. Analyze logs and identify errors, patterns, performance issues, and API endpoints.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    async def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API directly"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction="You are an expert log analyzer. Analyze logs and identify errors, patterns, performance issues, and API endpoints."
        )
        
        response = await model.generate_content_async(prompt)
        return response.text
    
    def _parse_ai_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response into structured format"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback: create structured response from text
                return {
                    "error_patterns": self._extract_patterns(response),
                    "api_endpoints": self._extract_endpoints(response),
                    "performance_issues": [],
                    "business_impact": {"severity": "medium", "description": "Analysis in progress"},
                    "test_scenarios": [],
                    "raw_analysis": response
                }
        except json.JSONDecodeError:
            return {
                "error_patterns": [],
                "api_endpoints": [],
                "performance_issues": [],
                "business_impact": {},
                "test_scenarios": [],
                "raw_analysis": response
            }
    
    def _extract_patterns(self, text: str) -> List[Dict]:
        """Extract error patterns from text"""
        patterns = []
        # Simple regex to find error mentions
        error_lines = re.findall(r'(?i)(error|exception|failure|timeout).*', text)
        for line in error_lines[:5]:  # Limit to 5 patterns
            patterns.append({
                "type": "error",
                "description": line[:100],
                "severity": "high",
                "frequency": 1
            })
        return patterns
    
    def _extract_endpoints(self, text: str) -> List[Dict]:
        """Extract API endpoints from text"""
        endpoints = []
        # Simple regex for API paths
        api_patterns = re.findall(r'(GET|POST|PUT|DELETE|PATCH)\s+(/[^\s]+)', text)
        for method, path in api_patterns[:10]:  # Limit to 10 endpoints
            endpoints.append({
                "method": method,
                "path": path,
                "status_codes": [200, 500],
                "issues": []
            })
        return endpoints
