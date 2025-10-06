"""
Test validation service to ensure generated tests are syntactically correct
"""
import ast
import re
from typing import Dict, List, Any


class TestValidator:
    """Validate generated test code for syntax and quality"""
    
    def validate_test_code(
        self,
        test_code: str,
        framework: str
    ) -> Dict[str, Any]:
        """
        Validate test code syntax and structure
        
        Returns:
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str],
            "suggestions": List[str]
        }
        """
        if framework in ["pytest"]:
            return self._validate_python(test_code)
        elif framework in ["jest", "mocha", "cypress"]:
            return self._validate_javascript(test_code)
        elif framework == "junit":
            return self._validate_java(test_code)
        elif framework == "rspec":
            return self._validate_ruby(test_code)
        else:
            # Default: basic validation
            return self._validate_generic(test_code)
    
    def _validate_python(self, code: str) -> Dict[str, Any]:
        """Validate Python test syntax"""
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Parse the code with AST
            ast.parse(code)
            
            # Check for best practices
            if "import pytest" not in code:
                warnings.append("Missing 'import pytest' statement")
            
            if "def test_" not in code:
                warnings.append("No test functions found (should start with 'test_')")
            
            if "assert" not in code:
                warnings.append("No assertions found in test code")
            
            # Check for common issues
            if "print(" in code:
                suggestions.append("Consider using logging instead of print statements")
            
            return {
                "valid": True,
                "errors": errors,
                "warnings": warnings,
                "suggestions": suggestions
            }
            
        except SyntaxError as e:
            errors.append(f"Syntax error at line {e.lineno}: {e.msg}")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
                "suggestions": ["Fix syntax errors before using this test"]
            }
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return {
                "valid": False,
                "errors": errors,
                "warnings": warnings,
                "suggestions": []
            }
    
    def _validate_javascript(self, code: str) -> Dict[str, Any]:
        """Validate JavaScript test syntax (basic checks)"""
        errors = []
        warnings = []
        suggestions = []
        
        # Basic syntax checks
        # Check for balanced braces
        if code.count('{') != code.count('}'):
            errors.append("Unbalanced curly braces")
        
        if code.count('(') != code.count(')'):
            errors.append("Unbalanced parentheses")
        
        # Check for test structure
        has_describe = 'describe(' in code
        has_it = 'it(' in code or 'test(' in code
        
        if not (has_describe or has_it):
            warnings.append("No test blocks found (describe/it or test)")
        
        # Check for assertions
        has_assertion = any(assertion in code for assertion in [
            'expect(', 'assert', 'should', 'cy.'
        ])
        
        if not has_assertion:
            warnings.append("No assertions found in test code")
        
        # Check for common issues
        if 'console.log(' in code:
            suggestions.append("Remove console.log statements before production use")
        
        # Check for async/await patterns
        if 'async' in code and 'await' not in code:
            warnings.append("Async function found without await - might be missing await statements")
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _validate_java(self, code: str) -> Dict[str, Any]:
        """Validate Java test syntax (basic checks)"""
        errors = []
        warnings = []
        suggestions = []
        
        # Check for balanced braces
        if code.count('{') != code.count('}'):
            errors.append("Unbalanced curly braces")
        
        if code.count('(') != code.count(')'):
            errors.append("Unbalanced parentheses")
        
        # Check for test annotations
        if '@Test' not in code:
            warnings.append("No @Test annotations found")
        
        # Check for assertions
        has_assertion = any(assertion in code for assertion in [
            'assert', 'assertEquals', 'assertTrue', 'assertFalse',
            'assertNotNull', 'expect('
        ])
        
        if not has_assertion:
            warnings.append("No assertions found in test code")
        
        # Check for proper class structure
        if 'public class' not in code and 'class' in code:
            warnings.append("Class should be public")
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _validate_ruby(self, code: str) -> Dict[str, Any]:
        """Validate Ruby test syntax (basic checks)"""
        errors = []
        warnings = []
        suggestions = []
        
        # Check for RSpec structure
        has_describe = 'describe' in code or 'RSpec.describe' in code
        has_it = 'it ' in code or "it '" in code or 'it "' in code
        
        if not has_describe:
            warnings.append("No describe blocks found")
        
        if not has_it:
            warnings.append("No 'it' blocks found")
        
        # Check for expectations
        if 'expect(' not in code:
            warnings.append("No expectations found (expect)")
        
        # Check for balanced blocks
        if code.count('do') != code.count('end'):
            errors.append("Unbalanced do...end blocks")
        
        valid = len(errors) == 0
        
        return {
            "valid": valid,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions
        }
    
    def _validate_generic(self, code: str) -> Dict[str, Any]:
        """Generic validation for unknown frameworks"""
        warnings = []
        
        if not code or len(code.strip()) < 10:
            warnings.append("Test code seems too short")
        
        return {
            "valid": True,
            "errors": [],
            "warnings": warnings,
            "suggestions": ["Manual review recommended for this framework"]
        }
    
    def calculate_quality_score(self, validation_result: Dict[str, Any]) -> float:
        """
        Calculate quality score (0-1) based on validation results
        
        Score calculation:
        - Valid syntax: 0.5 base
        - No errors: +0.3
        - No warnings: +0.15
        - No suggestions: +0.05
        """
        score = 0.0
        
        if validation_result["valid"]:
            score += 0.5
        
        if len(validation_result["errors"]) == 0:
            score += 0.3
        
        if len(validation_result["warnings"]) == 0:
            score += 0.15
        else:
            # Partial credit for few warnings
            score += max(0, 0.15 - (len(validation_result["warnings"]) * 0.05))
        
        if len(validation_result["suggestions"]) == 0:
            score += 0.05
        
        return min(score, 1.0)

