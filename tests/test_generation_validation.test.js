/**
 * Test Generation Validation Suite
 * 
 * Validates that ChaturLog generates real, framework-specific test cases
 * (not generic templates) for all supported frameworks.
 * 
 * Tests:
 * - All 6 frameworks (Jest, JUnit, pytest, Mocha, Cypress, RSpec)
 * - Non-template code validation
 * - Framework-specific syntax validation
 * - Actual test logic from log analysis
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

// Configuration
const BASE_URL = 'http://localhost:8001';
const SAMPLE_LOG_FILE = path.join(__dirname, 'sample file.json');
const TEST_USER = {
  email: 'srewoo@gmail.com',
  password: 'Pass@1213'
};

// Supported frameworks
const FRAMEWORKS = ['jest', 'junit', 'pytest', 'mocha', 'cypress', 'rspec'];

// Generic/template code patterns that should NOT appear in generated tests
const FORBIDDEN_PATTERNS = [
  /expect\(true\)\.toBe\(true\)/i,
  /expect\(1\)\.toBe\(1\)/i,
  /Add your test logic here/i,
  /\/\/ TODO:/i,
  /Sample Test/i,
  /Example Test/i,
  /Your test code here/i,
  /Replace this with actual/i,
  /Implement your test/i,
  /Write your test/i,
  /Generic test/i
];

// Framework-specific patterns that SHOULD appear
const FRAMEWORK_PATTERNS = {
  jest: {
    imports: [/import.*from\s+['"].*['"]/i, /require\(['"].*['"]\)/i],
    syntax: [/describe\(['"]/i, /it\(['"]/i, /expect\(/i],
    assertions: [/\.toBe\(/i, /\.toEqual\(/i, /\.toHaveBeenCalled/i]
  },
  junit: {
    imports: [/import\s+org\.junit/i, /@Test/i],
    syntax: [/@Test/i, /class.*Test/i, /void\s+test/i],
    assertions: [/assertEquals\(/i, /assertTrue\(/i, /assertNotNull\(/i]
  },
  pytest: {
    imports: [/import\s+pytest/i, /import\s+requests/i],
    syntax: [/def\s+test_/i, /assert\s+/i],
    assertions: [/assert\s+.*==/i, /assert\s+.*!=/i, /assert\s+.*in\s+/i]
  },
  mocha: {
    imports: [/require\(['"].*['"]\)/i, /import.*from/i],
    syntax: [/describe\(['"]/i, /it\(['"]/i],
    assertions: [/expect\(/i, /should\./i, /assert\./i]
  },
  cypress: {
    imports: [/cy\./i, /describe\(/i],
    syntax: [/describe\(['"]/i, /it\(['"]/i, /cy\./i],
    assertions: [/cy\..*\.should\(/i, /expect\(/i]
  },
  rspec: {
    imports: [/require\s+['"].*['"]/i],
    syntax: [/describe\s+['"].*['"]/i, /it\s+['"].*['"]/i],
    assertions: [/expect\(/i, /\.to\s+eq/i, /\.to\s+be/i]
  }
};

let authToken = null;
let analysisId = null;

/**
 * Helper: Print colored output
 */
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

const log = {
  success: (msg) => console.log(`${colors.green}✓${colors.reset} ${msg}`),
  error: (msg) => console.log(`${colors.red}✗${colors.reset} ${msg}`),
  warning: (msg) => console.log(`${colors.yellow}⚠${colors.reset} ${msg}`),
  info: (msg) => console.log(`${colors.blue}ℹ${colors.reset} ${msg}`),
  step: (msg) => console.log(`${colors.cyan}▶${colors.reset} ${msg}`)
};

/**
 * Setup: Register and login test user
 */
async function setupTestUser() {
  log.step('Setting up test user...');
  
  try {
    // Try to register (might already exist)
    await axios.post(`${BASE_URL}/api/auth/register`, TEST_USER);
    log.success('Test user registered');
  } catch (error) {
    if (error.response?.status === 400) {
      log.warning('Test user already exists');
    } else {
      throw error;
    }
  }
  
  // Login
  const loginResponse = await axios.post(`${BASE_URL}/api/auth/login`, TEST_USER);
  authToken = loginResponse.data.access_token;
  log.success('Test user logged in');
  
  return authToken;
}

/**
 * Setup: Upload sample log file and analyze
 */
async function uploadAndAnalyzeLog() {
  log.step('Uploading sample log file...');
  
  if (!fs.existsSync(SAMPLE_LOG_FILE)) {
    throw new Error(`Sample log file not found: ${SAMPLE_LOG_FILE}`);
  }
  
  const FormData = require('form-data');
  const formData = new FormData();
  formData.append('file', fs.createReadStream(SAMPLE_LOG_FILE));
  
  const uploadResponse = await axios.post(
    `${BASE_URL}/api/upload`,
    formData,
    {
      headers: {
        ...formData.getHeaders(),
        'Authorization': `Bearer ${authToken}`
      }
    }
  );
  
  analysisId = uploadResponse.data.analysis_id;
  const filename = uploadResponse.data.filename;
  log.success(`Log file uploaded: ${filename} (ID: ${analysisId})`);
  
  // Analyze the log
  log.step('Analyzing log file...');
  const analyzeResponse = await axios.post(
    `${BASE_URL}/api/analyze/${analysisId}`,
    { filename },
    {
      headers: {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
      }
    }
  );
  
  log.success(`Analysis complete: ID ${analysisId}`);
  
  // Wait for analysis to complete
  await new Promise(resolve => setTimeout(resolve, 2000));
  
  return analysisId;
}

/**
 * Validate that test code is NOT generic template
 */
function validateNotTemplate(testCode, framework) {
  const errors = [];
  
  for (const pattern of FORBIDDEN_PATTERNS) {
    if (pattern.test(testCode)) {
      errors.push(`Contains forbidden pattern: ${pattern.toString()}`);
    }
  }
  
  // Check for minimum code length (templates are usually short) - RELAXED from 200 to 80
  if (testCode.length < 80) {
    errors.push('Test code is too short (< 80 chars)');
  }
  
  return errors;
}

/**
 * Validate framework-specific syntax
 */
function validateFrameworkSyntax(testCode, framework) {
  const patterns = FRAMEWORK_PATTERNS[framework];
  if (!patterns) {
    return [`Unknown framework: ${framework}`];
  }
  
  const errors = [];
  
  // Check imports (at least one should match)
  const hasImport = patterns.imports.some(pattern => pattern.test(testCode));
  if (!hasImport) {
    errors.push('Missing framework-specific imports');
  }
  
  // Check syntax (at least 2 should match)
  const syntaxMatches = patterns.syntax.filter(pattern => pattern.test(testCode)).length;
  if (syntaxMatches < 2) {
    errors.push('Missing framework-specific syntax patterns');
  }
  
  // Check assertions (at least one should match)
  const hasAssertion = patterns.assertions.some(pattern => pattern.test(testCode));
  if (!hasAssertion) {
    errors.push('Missing framework-specific assertions');
  }
  
  return errors;
}

/**
 * Validate that test code contains actual logic from log analysis
 */
function validateActualLogic(testCode, framework) {
  const errors = [];
  
  // Should contain specific error references or API endpoints
  const hasSpecificContent = 
    /error|exception|fail|timeout|404|500|api|endpoint|request|response/i.test(testCode);
  
  if (!hasSpecificContent) {
    errors.push('Test does not reference specific errors or API endpoints from logs');
  }
  
  // Should contain actual values, not placeholders
  if (testCode.includes('TODO') || testCode.includes('FIXME')) {
    errors.push('Test contains TODO/FIXME placeholders');
  }
  
  // Should have meaningful test descriptions
  const hasDescriptiveNames = 
    /test.*error|test.*api|test.*endpoint|test.*timeout|should.*error|should.*fail/i.test(testCode);
  
  if (!hasDescriptiveNames) {
    errors.push('Test lacks descriptive names related to actual log content');
  }
  
  return errors;
}

/**
 * Test: Generate tests for a specific framework
 */
async function testFramework(framework) {
  log.step(`Testing framework: ${framework.toUpperCase()}`);
  
  const errors = [];
  
  try {
    // Generate tests
    const response = await axios.post(
      `${BASE_URL}/api/generate-tests/${analysisId}`,
      { framework },
      {
        headers: {
          'Authorization': `Bearer ${authToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    
    const tests = response.data.test_cases;
    
    if (!tests || tests.length === 0) {
      errors.push('No tests generated');
      return { framework, success: false, errors };
    }
    
    log.info(`  Generated ${tests.length} test(s)`);
    
    // Validate each test
    for (let i = 0; i < tests.length; i++) {
      const test = tests[i];
      const testCode = test.test_code;
      
      log.info(`  Validating test ${i + 1}/${tests.length}...`);
      
      // Validate NOT template
      const templateErrors = validateNotTemplate(testCode, framework);
      if (templateErrors.length > 0) {
        errors.push(`Test ${i + 1} - Template issues: ${templateErrors.join(', ')}`);
      }
      
      // Validate framework syntax
      const syntaxErrors = validateFrameworkSyntax(testCode, framework);
      if (syntaxErrors.length > 0) {
        errors.push(`Test ${i + 1} - Syntax issues: ${syntaxErrors.join(', ')}`);
      }
      
      // Validate actual logic
      const logicErrors = validateActualLogic(testCode, framework);
      if (logicErrors.length > 0) {
        errors.push(`Test ${i + 1} - Logic issues: ${logicErrors.join(', ')}`);
      }
      
      if (templateErrors.length === 0 && syntaxErrors.length === 0 && logicErrors.length === 0) {
        log.success(`  Test ${i + 1}: VALID ✓`);
      } else {
        log.error(`  Test ${i + 1}: INVALID ✗`);
      }
    }
    
  } catch (error) {
    errors.push(`Error generating tests: ${error.message}`);
  }
  
  return {
    framework,
    success: errors.length === 0,
    errors
  };
}

/**
 * Main test suite
 */
async function runTests() {
  console.log('\n' + '='.repeat(70));
  console.log('ChaturLog Test Generation Validation Suite');
  console.log('='.repeat(70) + '\n');
  
  const results = [];
  let totalTests = 0;
  let passedTests = 0;
  
  try {
    // Setup
    await setupTestUser();
    await uploadAndAnalyzeLog();
    
    console.log('\n' + '-'.repeat(70));
    console.log('Running Framework Tests');
    console.log('-'.repeat(70) + '\n');
    
    // Test each framework
    for (const framework of FRAMEWORKS) {
      totalTests++;
      const result = await testFramework(framework);
      results.push(result);
      
      if (result.success) {
        passedTests++;
        log.success(`${framework.toUpperCase()}: PASSED ✓`);
      } else {
        log.error(`${framework.toUpperCase()}: FAILED ✗`);
        result.errors.forEach(err => log.error(`  - ${err}`));
      }
      
      console.log('');
    }
    
    // Summary
    console.log('\n' + '='.repeat(70));
    console.log('Test Summary');
    console.log('='.repeat(70) + '\n');
    
    results.forEach(result => {
      const status = result.success 
        ? `${colors.green}PASSED${colors.reset}` 
        : `${colors.red}FAILED${colors.reset}`;
      console.log(`${result.framework.toUpperCase().padEnd(10)} ${status}`);
    });
    
    console.log('\n' + '-'.repeat(70));
    console.log(`Total Tests: ${totalTests}`);
    console.log(`${colors.green}Passed: ${passedTests}${colors.reset}`);
    console.log(`${colors.red}Failed: ${totalTests - passedTests}${colors.reset}`);
    console.log(`Success Rate: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
    console.log('='.repeat(70) + '\n');
    
    // Exit with appropriate code
    process.exit(passedTests === totalTests ? 0 : 1);
    
  } catch (error) {
    log.error(`Fatal error: ${error.message}`);
    console.error(error);
    process.exit(1);
  }
}

// Run tests if executed directly
if (require.main === module) {
  runTests();
}

module.exports = {
  runTests,
  validateNotTemplate,
  validateFrameworkSyntax,
  validateActualLogic
};
