# 🧪 ChaturLog Test Suite

Comprehensive test suite to validate ChaturLog's test generation capabilities across all supported frameworks.

---

## 📋 Overview

This test suite validates that ChaturLog:
- ✅ Generates tests for **all 6 frameworks** (Jest, JUnit, pytest, Mocha, Cypress, RSpec)
- ✅ Produces **real, executable test code** (not generic templates)
- ✅ Includes **framework-specific syntax** and assertions
- ✅ Contains **actual logic** derived from log analysis

---

## 📁 Test Files

### **test_generation_validation.test.js** (JavaScript/Node.js)
Comprehensive validation suite for all frameworks using Node.js.

### **test_generation_validation.py** (Python)
Python version of the validation suite with identical functionality.

### **test_chunking.py**
Tests the log chunking and summarization pipeline for large log files.

### **sample file.json**
Sample log file used for testing.

### **test-apollo-server.json**
Sample log file for testing Git repository detection.

---

## 🚀 Running Tests

### **Prerequisites**

1. **Backend server must be running**:
   ```bash
   cd backend
   python3 server.py
   ```

2. **API keys must be configured** (via UI or database):
   - OpenAI API key
   - OR Anthropic API key
   - OR Google AI API key

### **JavaScript Tests**

```bash
# Install dependencies (if not already installed)
cd tests
npm install axios form-data

# Run tests
node test_generation_validation.test.js
```

### **Python Tests**

```bash
# Install dependencies
pip install requests

# Run tests
cd tests
python3 test_generation_validation.py
```

### **Chunking Tests**

```bash
cd tests
python3 test_chunking.py
```

---

## 🎯 What Gets Tested

### **1. All Frameworks**
Tests are generated and validated for:
- ✅ **Jest** (JavaScript/TypeScript)
- ✅ **JUnit** (Java)
- ✅ **pytest** (Python)
- ✅ **Mocha** (JavaScript/TypeScript)
- ✅ **Cypress** (E2E JavaScript)
- ✅ **RSpec** (Ruby)

### **2. Template Detection**
Validates that generated tests **DO NOT** contain:
- ❌ `expect(true).toBe(true)` (generic assertions)
- ❌ `// TODO: Add your test logic here` (placeholders)
- ❌ "Sample Test" or "Example Test" (template names)
- ❌ Suspiciously short code (< 200 characters)

### **3. Framework-Specific Syntax**
Validates that generated tests **DO** contain:

**Jest/Mocha**:
- ✅ `describe()` and `it()` blocks
- ✅ `expect()` assertions
- ✅ Proper imports (`import`/`require`)

**JUnit**:
- ✅ `@Test` annotations
- ✅ `assertEquals()`, `assertTrue()` assertions
- ✅ `import org.junit.*`

**pytest**:
- ✅ `def test_*` function names
- ✅ `assert` statements
- ✅ Proper imports

**Cypress**:
- ✅ `cy.*` commands
- ✅ `.should()` assertions
- ✅ `describe()` and `it()` blocks

**RSpec**:
- ✅ `describe` and `it` blocks
- ✅ `expect().to` syntax
- ✅ Proper `require` statements

### **4. Actual Logic Validation**
Validates that tests contain:
- ✅ References to actual errors from logs
- ✅ API endpoint names
- ✅ HTTP status codes (404, 500, etc.)
- ✅ Descriptive test names (not generic)
- ❌ NO TODO/FIXME placeholders

---

## 📊 Test Output

### **Example Success Output**

```
======================================================================
ChaturLog Test Generation Validation Suite
======================================================================

▶ Setting up test user...
✓ Test user logged in
▶ Uploading sample log file...
✓ Log file uploaded: sample file.json
▶ Analyzing log file...
✓ Analysis complete: ID 42

----------------------------------------------------------------------
Running Framework Tests
----------------------------------------------------------------------

▶ Testing framework: JEST
ℹ   Generated 5 test(s)
ℹ   Validating test 1/5...
✓   Test 1: VALID ✓
ℹ   Validating test 2/5...
✓   Test 2: VALID ✓
...
✓ JEST: PASSED ✓

▶ Testing framework: JUNIT
...
✓ JUNIT: PASSED ✓

▶ Testing framework: PYTEST
...
✓ PYTEST: PASSED ✓

▶ Testing framework: MOCHA
...
✓ MOCHA: PASSED ✓

▶ Testing framework: CYPRESS
...
✓ CYPRESS: PASSED ✓

▶ Testing framework: RSPEC
...
✓ RSPEC: PASSED ✓

======================================================================
Test Summary
======================================================================

JEST       PASSED
JUNIT      PASSED
PYTEST     PASSED
MOCHA      PASSED
CYPRESS    PASSED
RSPEC      PASSED

----------------------------------------------------------------------
Total Tests: 6
Passed: 6
Failed: 0
Success Rate: 100.0%
======================================================================
```

### **Example Failure Output**

```
▶ Testing framework: JEST
ℹ   Generated 3 test(s)
ℹ   Validating test 1/3...
✗   Test 1: INVALID ✗
✗ JEST: FAILED ✗
  - Test 1 - Template issues: Contains forbidden pattern: expect(true).toBe(true)
  - Test 1 - Logic issues: Test does not reference specific errors or API endpoints from logs
```

---

## 🔧 Troubleshooting

### **"No API keys configured"**

**Solution**: Configure API keys via Settings UI or run `setup_api_keys.py`:
```bash
cd tests
python3 setup_api_keys.py
```

### **"Sample log file not found"**

**Solution**: Ensure `sample file.json` exists in the `tests/` directory.

### **"Connection refused"**

**Solution**: Start the backend server:
```bash
cd backend
python3 server.py
```

### **Tests fail with "Template issues"**

**Root Cause**: AI is generating generic template code instead of actual tests.

**Solutions**:
1. Check AI API key is valid
2. Ensure log file contains meaningful errors/patterns
3. Try a different AI model (OpenAI, Claude, or Gemini)
4. Increase log file size (more context = better tests)

### **Tests fail with "Syntax issues"**

**Root Cause**: AI is generating wrong framework syntax.

**Solutions**:
1. Check `test_generator.py` prompts are framework-specific
2. Verify AI model is not mixing frameworks
3. Try regenerating with custom prompts

---

## 📝 Adding New Tests

### **Template for Framework Tests**

```javascript
// JavaScript
async function testNewFeature() {
  log.step('Testing new feature...');
  
  const errors = [];
  
  try {
    // Your test logic here
    
    // Validate response
    if (!validationPassed) {
      errors.push('Validation failed');
    }
    
  } catch (error) {
    errors.push(`Error: ${error.message}`);
  }
  
  return {
    feature: 'new_feature',
    success: errors.length === 0,
    errors
  };
}
```

```python
# Python
def test_new_feature() -> Dict:
    """Test new feature"""
    log.step("Testing new feature...")
    
    errors = []
    
    try:
        # Your test logic here
        
        # Validate response
        if not validation_passed:
            errors.append("Validation failed")
    
    except Exception as e:
        errors.append(f"Error: {str(e)}")
    
    return {
        "feature": "new_feature",
        "success": len(errors) == 0,
        "errors": errors
    }
```

---

## 🎯 Best Practices

### **1. Test Isolation**
Each test should be independent and not rely on previous test state.

### **2. Meaningful Assertions**
Validate actual behavior, not just "test passes".

### **3. Error Messages**
Provide clear, actionable error messages when tests fail.

### **4. Test Data**
Use realistic sample log files that contain:
- Actual errors
- API endpoints
- HTTP status codes
- Stack traces
- Timestamps

### **5. Cleanup**
Tests should clean up resources (files, database entries) after completion.

---

## 📊 Test Coverage

| Category | Coverage |
|----------|----------|
| **Frameworks** | 6/6 (100%) |
| **Template Detection** | ✅ Comprehensive |
| **Syntax Validation** | ✅ All frameworks |
| **Logic Validation** | ✅ Error context |
| **Edge Cases** | ✅ Empty logs, large files |

---

## 🚀 CI/CD Integration

### **GitHub Actions Example**

```yaml
name: ChaturLog Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Setup Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '18'
    
    - name: Install dependencies
      run: |
        pip install -r backend/requirements.txt
        cd tests && npm install
    
    - name: Start backend
      run: |
        cd backend
        python3 server.py &
        sleep 5
    
    - name: Run tests
      env:
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
      run: |
        cd tests
        python3 test_generation_validation.py
```

---

## 📚 Related Documentation

- **Test Generation Analysis**: `TEST_GENERATION_ANALYSIS.md`
- **Implementation Guide**: `IMPLEMENTATION_COMPLETE_PHASE1.md`
- **Setup Guide**: `docs/index.html`

---

## 🆘 Support

If tests are failing consistently:

1. Check backend logs: `backend.log`
2. Verify API keys in Settings UI
3. Review generated test output for patterns
4. Open an issue with test output and logs

---

**Happy Testing!** 🧪✨
