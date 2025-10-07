import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Badge } from '../components/ui/badge';
import { Textarea } from '../components/ui/textarea';
import { Switch } from '../components/ui/switch';
import { ArrowLeft, Save, Key, CheckCircle, FileText, Plus, Edit2, Trash2, Star, GitBranch, Lock } from 'lucide-react';
import axios from 'axios';
import { getPrompts, createPrompt, updatePrompt, deletePrompt, getRepoMappings, deleteRepoMapping } from '../utils/api';

const API_BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Settings() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  // API Keys state
  const [openaiKey, setOpenaiKey] = useState('');
  const [anthropicKey, setAnthropicKey] = useState('');
  const [googleKey, setGoogleKey] = useState('');

  // Custom Prompts state
  const [prompts, setPrompts] = useState([]);
  const [showPromptForm, setShowPromptForm] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState(null);
  const [promptForm, setPromptForm] = useState({
    name: '',
    description: '',
    system_prompt: '',
    analysis_prompt: '',
    test_generation_prompt: '',
    is_default: false
  });

  // Git Integration state
  const [gitProvider, setGitProvider] = useState('github');
  const [gitRepository, setGitRepository] = useState('');
  const [gitToken, setGitToken] = useState('');
  const [gitBranch, setGitBranch] = useState('main');
  const [gitEnabled, setGitEnabled] = useState(false);
  const [testingConnection, setTestingConnection] = useState(false);
  const [connectionResult, setConnectionResult] = useState(null);
  
  // Repository mappings state
  const [repoMappings, setRepoMappings] = useState([]);

  // Default prompt templates
  const defaultPrompts = [
    {
      name: "Standard Analysis (Built-in Default)",
      description: "ChaturLog's default prompt - comprehensive error analysis with business impact",
      system_prompt: "You are an expert log analyzer. Analyze logs and identify errors, patterns, performance issues, and API endpoints.",
      analysis_prompt: `Analyze the following log file and provide a comprehensive analysis:

Please provide:
1. Error Patterns: List all error patterns with severity (critical/high/medium/low)
2. API Endpoints: Extract all API endpoints, HTTP methods, and status codes
3. Performance Issues: Identify slow requests, timeouts, or bottlenecks
4. Business Impact: Assess user impact and severity
5. Test Scenarios: Suggest key test scenarios based on the errors found`,
      test_generation_prompt: `Generate comprehensive test cases based on the log analysis:

Requirements:
1. Generate test cases for identified errors and API endpoints
2. Include proper imports and setup/teardown
3. Add assertions for error conditions, status codes, and response validation
4. Prioritize tests by risk score (critical errors first)
5. Make tests executable and production-ready`
    },
    {
      name: "Security-Focused Analysis",
      description: "Emphasizes authentication, authorization, and security vulnerabilities",
      system_prompt: "You are a security-focused log analyst specializing in identifying authentication failures, unauthorized access attempts, and security vulnerabilities.",
      analysis_prompt: `Analyze logs with a security focus:

Prioritize:
- Authentication and authorization errors
- Failed login attempts and suspicious patterns
- SQL injection or XSS attempts
- Rate limiting violations
- Unusual access patterns
- Data exposure risks`,
      test_generation_prompt: `Generate security-focused test cases:

Include:
- Authentication and authorization tests
- Input validation and sanitization tests
- Rate limiting tests
- Session management tests
- Security header validation`
    },
    {
      name: "Performance-Focused Analysis",
      description: "Identifies bottlenecks, slow queries, and optimization opportunities",
      system_prompt: "You are a performance optimization specialist analyzing logs for bottlenecks, slow queries, and scalability issues.",
      analysis_prompt: `Analyze logs for performance issues:

Focus on:
- Response times > 1000ms
- Database query performance
- Memory usage patterns
- Cache hit/miss ratios
- Third-party API latencies
- Resource-intensive operations`,
      test_generation_prompt: `Generate performance test cases:

Include:
- Load testing scenarios
- Response time assertions
- Query optimization tests
- Memory leak detection
- Concurrent request handling`
    },
    {
      name: "API Testing Focus",
      description: "Optimized for REST API testing with comprehensive endpoint coverage",
      system_prompt: "You are an API testing expert specializing in REST API validation, contract testing, and integration testing.",
      analysis_prompt: `Analyze logs for API-specific insights:

Extract:
- All API endpoints and methods
- Status code distributions
- Request/response patterns
- Error responses and validation failures
- API versioning issues`,
      test_generation_prompt: `Generate API test cases with:

- Comprehensive endpoint coverage
- Request/response validation
- Status code assertions
- Error handling scenarios
- Edge cases and boundary testing
- Mock data generation`
    }
  ];

  // Load saved keys and prompts on mount
  useEffect(() => {
    loadApiKeys();
    loadPrompts();
    loadGitConfig();
    loadRepoMappings();
  }, []);

  const loadApiKeys = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/settings/api-keys`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        const keys = response.data.api_keys;
        setOpenaiKey(keys.openai_key || '');
        setAnthropicKey(keys.anthropic_key || '');
        setGoogleKey(keys.google_key || '');
      }
    } catch (err) {
      console.error('Failed to load API keys:', err);
    }
  };

  const handleSaveKeys = async () => {
    setLoading(true);
    setSuccess('');
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE}/settings/api-keys`,
        {
          openai_key: openaiKey,
          anthropic_key: anthropicKey,
          google_key: googleKey
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setSuccess('API keys saved successfully!');
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save API keys');
    } finally {
      setLoading(false);
    }
  };

  // Git Configuration functions
  const loadGitConfig = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_BASE}/settings/git-config`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.success) {
        const config = response.data.git_config;
        setGitProvider(config.git_provider || 'github');
        setGitRepository(config.repository || '');
        setGitToken(config.git_token || '');
        setGitBranch(config.default_branch || 'main');
        setGitEnabled(config.enabled || false);
      }
    } catch (err) {
      console.error('Failed to load Git configuration:', err);
    }
  };

  const handleSaveGitConfig = async () => {
    setLoading(true);
    setSuccess('');
    setError('');
    setConnectionResult(null);

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE}/settings/git-config`,
        {
          git_provider: gitProvider,
          repository: gitRepository,
          git_token: gitToken,
          default_branch: gitBranch,
          enabled: gitEnabled
        },
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      if (response.data.success) {
        setSuccess('Git configuration saved successfully!');
        setTimeout(() => setSuccess(''), 3000);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save Git configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setConnectionResult(null);
    setError('');

    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_BASE}/settings/git-config/test`,
        {},
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      setConnectionResult(response.data);
    } catch (err) {
      setConnectionResult({
        success: false,
        message: err.response?.data?.detail || 'Failed to test connection'
      });
    } finally {
      setTestingConnection(false);
    }
  };

  // Repository mappings functions
  const loadRepoMappings = async () => {
    try {
      const response = await getRepoMappings();
      if (response.success) {
        setRepoMappings(response.mappings || []);
      }
    } catch (err) {
      console.error('Failed to load repository mappings:', err);
    }
  };

  const handleDeleteMapping = async (serviceName) => {
    if (!window.confirm(`Delete mapping for ${serviceName}?`)) {
      return;
    }

    try {
      await deleteRepoMapping(serviceName);
      setSuccess(`Mapping deleted for ${serviceName}`);
      setTimeout(() => setSuccess(''), 3000);
      loadRepoMappings();
    } catch (err) {
      setError('Failed to delete mapping');
      console.error('Delete mapping error:', err);
    }
  };

  // Prompts management functions
  const loadPrompts = async () => {
    try {
      const response = await getPrompts();
      if (response.success) {
        setPrompts(response.prompts);
      }
    } catch (err) {
      console.error('Failed to load prompts:', err);
    }
  };

  const handleCreatePrompt = () => {
    setEditingPrompt(null);
    setPromptForm({
      name: '',
      description: '',
      system_prompt: '',
      analysis_prompt: '',
      test_generation_prompt: '',
      is_default: false
    });
    setShowPromptForm(true);
  };

  const handleEditPrompt = (prompt) => {
    setEditingPrompt(prompt);
    setPromptForm({
      name: prompt.name,
      description: prompt.description || '',
      system_prompt: prompt.system_prompt || '',
      analysis_prompt: prompt.analysis_prompt || '',
      test_generation_prompt: prompt.test_generation_prompt || '',
      is_default: prompt.is_default
    });
    setShowPromptForm(true);
  };

  const handleSavePrompt = async () => {
    setLoading(true);
    setSuccess('');
    setError('');

    try {
      if (editingPrompt) {
        await updatePrompt(editingPrompt.id, promptForm);
        setSuccess('Prompt updated successfully!');
      } else {
        await createPrompt(promptForm);
        setSuccess('Prompt created successfully!');
      }
      
      await loadPrompts();
      setShowPromptForm(false);
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save prompt');
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePrompt = async (promptId) => {
    if (!window.confirm('Are you sure you want to delete this prompt?')) {
      return;
    }

    setLoading(true);
    setSuccess('');
    setError('');

    try {
      await deletePrompt(promptId);
      setSuccess('Prompt deleted successfully!');
      await loadPrompts();
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to delete prompt');
    } finally {
      setLoading(false);
    }
  };

  const handleUseTemplate = (template) => {
    setEditingPrompt(null);
    setPromptForm({
      name: template.name,
      description: template.description,
      system_prompt: template.system_prompt,
      analysis_prompt: template.analysis_prompt,
      test_generation_prompt: template.test_generation_prompt,
      is_default: false
    });
    setShowPromptForm(true);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/dashboard')}
                data-testid="back-button"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Dashboard
              </Button>
              <div className="h-6 w-px bg-slate-300"></div>
              <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="api-keys" className="space-y-6">
          <TabsList className="grid w-full max-w-3xl grid-cols-3">
            <TabsTrigger value="api-keys" data-testid="api-keys-tab">
              <Key className="h-4 w-4 mr-2" />
              API Keys
            </TabsTrigger>
            <TabsTrigger value="git-integration" data-testid="git-integration-tab">
              <GitBranch className="h-4 w-4 mr-2" />
              Git Integration
            </TabsTrigger>
            <TabsTrigger value="prompts" data-testid="prompts-tab">
              <FileText className="h-4 w-4 mr-2" />
              Custom Prompts
            </TabsTrigger>
          </TabsList>

          {/* API Keys Tab */}
          <TabsContent value="api-keys">
            <Card>
              <CardHeader>
                <CardTitle>Configure AI Model API Keys</CardTitle>
                <CardDescription>
                  Add your API keys to enable AI-powered log analysis and test generation.
                  Your keys are encrypted and stored securely.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* OpenAI API Key */}
                <div className="space-y-2">
                  <Label htmlFor="openai-key">
                    OpenAI API Key
                    <span className="text-sm text-slate-500 ml-2">(for GPT-4o models)</span>
                  </Label>
                  <Input
                    id="openai-key"
                    type="password"
                    placeholder="sk-..."
                    value={openaiKey}
                    onChange={(e) => setOpenaiKey(e.target.value)}
                    data-testid="openai-key-input"
                  />
                  <p className="text-xs text-slate-500">
                    Get your API key from:{' '}
                    <a
                      href="https://platform.openai.com/api-keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      https://platform.openai.com/api-keys
                    </a>
                  </p>
                </div>

                {/* Anthropic API Key */}
                <div className="space-y-2">
                  <Label htmlFor="anthropic-key">
                    Anthropic API Key
                    <span className="text-sm text-slate-500 ml-2">(for Claude models)</span>
                  </Label>
                  <Input
                    id="anthropic-key"
                    type="password"
                    placeholder="sk-ant-..."
                    value={anthropicKey}
                    onChange={(e) => setAnthropicKey(e.target.value)}
                    data-testid="anthropic-key-input"
                  />
                  <p className="text-xs text-slate-500">
                    Get your API key from:{' '}
                    <a
                      href="https://console.anthropic.com/settings/keys"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      https://console.anthropic.com/settings/keys
                    </a>
                  </p>
                </div>

                {/* Google API Key */}
                <div className="space-y-2">
                  <Label htmlFor="google-key">
                    Google AI API Key
                    <span className="text-sm text-slate-500 ml-2">(for Gemini models)</span>
                  </Label>
                  <Input
                    id="google-key"
                    type="password"
                    placeholder="AIza..."
                    value={googleKey}
                    onChange={(e) => setGoogleKey(e.target.value)}
                    data-testid="google-key-input"
                  />
                  <p className="text-xs text-slate-500">
                    Get your API key from:{' '}
                    <a
                      href="https://makersuite.google.com/app/apikey"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      https://makersuite.google.com/app/apikey
                    </a>
                  </p>
                </div>

                {/* Success Message */}
                {success && (
                  <Alert className="bg-green-50 border-green-200" data-testid="success-message">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <AlertDescription className="text-green-800">
                      {success}
                    </AlertDescription>
                  </Alert>
                )}

                {/* Error Message */}
                {error && (
                  <Alert className="bg-red-50 border-red-200" data-testid="error-message">
                    <AlertDescription className="text-red-800">
                      {error}
                    </AlertDescription>
                  </Alert>
                )}

                {/* Save Button */}
                <Button
                  onClick={handleSaveKeys}
                  disabled={loading}
                  className="w-full"
                  data-testid="save-keys-button"
                >
                  {loading ? (
                    <>
                      <span className="spinner mr-2"></span>
                      Saving...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Save API Keys
                    </>
                  )}
                </Button>

                {/* Info Box */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <p className="text-sm text-blue-900 font-medium mb-2">
                    🔒 Security Note
                  </p>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• Your API keys are encrypted before storage</li>
                    <li>• Keys are never logged or exposed in responses</li>
                    <li>• Each user's keys are isolated and secure</li>
                    <li>• You can update or remove keys anytime</li>
                  </ul>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Git Integration Tab */}
          <TabsContent value="git-integration">
            <Card>
              <CardHeader>
                <CardTitle>Git Repository Integration</CardTitle>
                <CardDescription>
                  Connect ChaturLog to your Git repository for enhanced analysis and context-aware test generation.
                  ChaturLog will have READ-ONLY access to your repository.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Enable Git Integration */}
                <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <div className="flex items-center space-x-3">
                    <Lock className="h-5 w-5 text-slate-600" />
                    <div>
                      <h3 className="font-medium text-slate-900">Enable Git Integration</h3>
                      <p className="text-sm text-slate-500">Connect to your repository for better analysis</p>
                    </div>
                  </div>
                  <Switch
                    checked={gitEnabled}
                    onCheckedChange={setGitEnabled}
                    data-testid="git-enabled-switch"
                  />
                </div>

                {/* Git Provider Selection */}
                <div className="space-y-2">
                  <Label htmlFor="git-provider">Git Provider</Label>
                  <select
                    id="git-provider"
                    value={gitProvider}
                    onChange={(e) => setGitProvider(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    data-testid="git-provider-select"
                  >
                    <option value="github">GitHub</option>
                    <option value="gitlab">GitLab</option>
                    <option value="bitbucket">Bitbucket</option>
                  </select>
                  <p className="text-xs text-slate-500">
                    Select your Git hosting provider
                  </p>
                </div>

                {/* Repository Name */}
                <div className="space-y-2">
                  <Label htmlFor="git-repository">
                    Repository
                    <span className="text-sm text-slate-500 ml-2">(org/repo format)</span>
                  </Label>
                  <Input
                    id="git-repository"
                    type="text"
                    placeholder="e.g., myorg/myapp"
                    value={gitRepository}
                    onChange={(e) => setGitRepository(e.target.value)}
                    data-testid="git-repository-input"
                  />
                  <p className="text-xs text-slate-500">
                    The repository will be auto-detected from logs if not specified
                  </p>
                </div>

                {/* Personal Access Token */}
                <div className="space-y-2">
                  <Label htmlFor="git-token">
                    Personal Access Token (READ-ONLY)
                  </Label>
                  <Input
                    id="git-token"
                    type="password"
                    placeholder="ghp_... or glpat-... or ..."
                    value={gitToken}
                    onChange={(e) => setGitToken(e.target.value)}
                    data-testid="git-token-input"
                  />
                  <p className="text-xs text-slate-500">
                    Get your token from:{' '}
                    {gitProvider === 'github' && (
                      <a
                        href="https://github.com/settings/tokens"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        GitHub Settings → Developer settings → Personal access tokens
                      </a>
                    )}
                    {gitProvider === 'gitlab' && (
                      <a
                        href="https://gitlab.com/-/profile/personal_access_tokens"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        GitLab Profile → Access Tokens
                      </a>
                    )}
                    {gitProvider === 'bitbucket' && (
                      <a
                        href="https://bitbucket.org/account/settings/app-passwords/"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        Bitbucket Personal Settings → App passwords
                      </a>
                    )}
                  </p>
                </div>

                {/* Default Branch */}
                <div className="space-y-2">
                  <Label htmlFor="git-branch">Default Branch</Label>
                  <Input
                    id="git-branch"
                    type="text"
                    placeholder="main"
                    value={gitBranch}
                    onChange={(e) => setGitBranch(e.target.value)}
                    data-testid="git-branch-input"
                  />
                  <p className="text-xs text-slate-500">
                    The default branch to read code from (usually 'main' or 'master')
                  </p>
                </div>

                {/* Required Permissions Notice */}
                <Alert>
                  <Lock className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Required Token Permissions:</strong>
                    <ul className="mt-2 ml-4 list-disc text-sm space-y-1">
                      <li><strong>GitHub:</strong> <code>repo:read</code> (read repository contents)</li>
                      <li><strong>GitLab:</strong> <code>read_repository</code></li>
                      <li><strong>Bitbucket:</strong> <code>repository:read</code></li>
                    </ul>
                    <p className="mt-2 text-sm">
                      ⚠️ ChaturLog only requires READ access. Never grant write permissions.
                    </p>
                  </AlertDescription>
                </Alert>

                {/* Test Connection Button */}
                <div className="flex items-center gap-3">
                  <Button
                    onClick={handleTestConnection}
                    variant="outline"
                    disabled={testingConnection || !gitToken || !gitRepository}
                    data-testid="test-connection-button"
                  >
                    {testingConnection ? 'Testing...' : 'Test Connection'}
                  </Button>
                  <Button
                    onClick={handleSaveGitConfig}
                    disabled={loading}
                    data-testid="save-git-config-button"
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {loading ? 'Saving...' : 'Save Configuration'}
                  </Button>
                </div>

                {/* Connection Test Result */}
                {connectionResult && (
                  <Alert variant={connectionResult.success ? "default" : "destructive"}>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      <strong>{connectionResult.success ? 'Success!' : 'Error:'}</strong>
                      <p className="mt-1">{connectionResult.message}</p>
                      {connectionResult.success && connectionResult.repository_info && (
                        <div className="mt-3 text-sm space-y-1">
                          <p><strong>Repository:</strong> {connectionResult.repository_info.name}</p>
                          <p><strong>Default Branch:</strong> {connectionResult.repository_info.default_branch}</p>
                          <p><strong>Language:</strong> {connectionResult.repository_info.language || 'N/A'}</p>
                          <p><strong>Private:</strong> {connectionResult.repository_info.private ? 'Yes' : 'No'}</p>
                        </div>
                      )}
                    </AlertDescription>
                  </Alert>
                )}

                {/* Success/Error Messages */}
                {success && (
                  <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>{success}</AlertDescription>
                  </Alert>
                )}
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
            
            {/* Repository Mappings Card */}
            <Card>
              <CardHeader>
                <CardTitle>Repository Mappings</CardTitle>
                <CardDescription>
                  Saved mappings between service names and Git repositories. These are automatically applied during log analysis.
                </CardDescription>
              </CardHeader>
              <CardContent>
                {repoMappings.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <GitBranch className="h-12 w-12 mx-auto mb-3 opacity-50" />
                    <p>No repository mappings yet</p>
                    <p className="text-sm mt-1">
                      Mappings will be created automatically when ChaturLog detects service names in your logs
                    </p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {repoMappings.map((mapping) => (
                      <div
                        key={mapping.service_name}
                        className="flex items-center justify-between p-4 border border-slate-200 rounded-lg hover:bg-slate-50"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-3">
                            <GitBranch className="h-4 w-4 text-slate-400" />
                            <div>
                              <p className="font-medium text-slate-900">
                                <code className="bg-slate-100 px-2 py-1 rounded text-sm">
                                  {mapping.service_name}
                                </code>
                              </p>
                              <p className="text-sm text-slate-600 mt-1">
                                → <span className="font-mono">{mapping.repository}</span>
                              </p>
                              <p className="text-xs text-slate-400 mt-1">
                                Created: {new Date(mapping.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteMapping(mapping.service_name)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Custom Prompts Tab */}
          <TabsContent value="prompts">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Custom AI Prompts</CardTitle>
                    <CardDescription>
                      Customize how AI analyzes logs and generates tests. Create prompt templates for different use cases.
                    </CardDescription>
                  </div>
                  {!showPromptForm && (
                    <Button onClick={handleCreatePrompt} size="sm">
                      <Plus className="h-4 w-4 mr-2" />
                      New Prompt
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {showPromptForm ? (
                  /* Prompt Form */
                  <div className="space-y-6">
                    <div className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="prompt-name">Prompt Name *</Label>
                        <Input
                          id="prompt-name"
                          placeholder="e.g., Detailed Error Analysis"
                          value={promptForm.name}
                          onChange={(e) => setPromptForm({...promptForm, name: e.target.value})}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="prompt-description">Description</Label>
                        <Input
                          id="prompt-description"
                          placeholder="Brief description of this prompt's purpose"
                          value={promptForm.description}
                          onChange={(e) => setPromptForm({...promptForm, description: e.target.value})}
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="system-prompt">System Prompt</Label>
                        <Textarea
                          id="system-prompt"
                          placeholder="Define AI's role and behavior (e.g., 'You are an expert log analyst...')"
                          value={promptForm.system_prompt}
                          onChange={(e) => setPromptForm({...promptForm, system_prompt: e.target.value})}
                          rows={3}
                        />
                        <p className="text-xs text-slate-500">
                          Optional: Defines the AI's expertise and approach
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="analysis-prompt">Analysis Prompt</Label>
                        <Textarea
                          id="analysis-prompt"
                          placeholder="Custom instructions for log analysis (e.g., 'Focus on authentication errors...')"
                          value={promptForm.analysis_prompt}
                          onChange={(e) => setPromptForm({...promptForm, analysis_prompt: e.target.value})}
                          rows={4}
                        />
                        <p className="text-xs text-slate-500">
                          Optional: Specific guidance for analyzing logs
                        </p>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="test-prompt">Test Generation Prompt</Label>
                        <Textarea
                          id="test-prompt"
                          placeholder="Custom instructions for test generation (e.g., 'Include edge cases and mocking...')"
                          value={promptForm.test_generation_prompt}
                          onChange={(e) => setPromptForm({...promptForm, test_generation_prompt: e.target.value})}
                          rows={4}
                        />
                        <p className="text-xs text-slate-500">
                          Optional: Specific guidance for generating tests
                        </p>
                      </div>

                      <div className="flex items-center space-x-2 p-4 bg-amber-50 border border-amber-200 rounded-lg">
                        <Switch
                          id="is-default"
                          checked={promptForm.is_default}
                          onCheckedChange={(checked) => setPromptForm({...promptForm, is_default: checked})}
                        />
                        <div className="flex-1">
                          <Label htmlFor="is-default" className="cursor-pointer flex items-center">
                            <Star className="h-4 w-4 mr-2 text-amber-600" />
                            Set as Default Prompt
                          </Label>
                          <p className="text-xs text-slate-600 mt-1">
                            This prompt will be used automatically for all analyses
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Success/Error Messages */}
                    {success && (
                      <Alert className="bg-green-50 border-green-200">
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <AlertDescription className="text-green-800">
                          {success}
                        </AlertDescription>
                      </Alert>
                    )}

                    {error && (
                      <Alert className="bg-red-50 border-red-200">
                        <AlertDescription className="text-red-800">
                          {error}
                        </AlertDescription>
                      </Alert>
                    )}

                    {/* Form Actions */}
                    <div className="flex gap-3">
                      <Button
                        onClick={handleSavePrompt}
                        disabled={loading || !promptForm.name}
                        className="flex-1"
                      >
                        {loading ? (
                          <>
                            <span className="spinner mr-2"></span>
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="h-4 w-4 mr-2" />
                            {editingPrompt ? 'Update Prompt' : 'Create Prompt'}
                          </>
                        )}
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setShowPromptForm(false);
                          setEditingPrompt(null);
                        }}
                      >
                        Cancel
                      </Button>
                    </div>
                  </div>
                ) : (
                  /* Prompts List */
                  <div className="space-y-6">
                    {/* Default Templates Section */}
                    <div>
                      <h3 className="text-sm font-semibold text-slate-700 mb-3">📋 Default Templates</h3>
                      <p className="text-xs text-slate-600 mb-4">
                        Use these as starting points for your custom prompts. Click "Use as Template" to copy and modify.
                      </p>
                      <div className="space-y-3">
                        {defaultPrompts.map((template, idx) => (
                          <Card key={idx} className="bg-slate-50 border-slate-200">
                            <CardContent className="pt-4">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <h4 className="font-medium text-slate-900 text-sm mb-1">{template.name}</h4>
                                  <p className="text-xs text-slate-600 mb-2">{template.description}</p>
                                  <div className="flex gap-2">
                                    <Badge variant="outline" className="text-xs">System</Badge>
                                    <Badge variant="outline" className="text-xs">Analysis</Badge>
                                    <Badge variant="outline" className="text-xs">Test Gen</Badge>
                                  </div>
                                </div>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => handleUseTemplate(template)}
                                  className="ml-4"
                                >
                                  <FileText className="h-3 w-3 mr-1" />
                                  Use as Template
                                </Button>
                              </div>
                            </CardContent>
                          </Card>
                        ))}
                      </div>
                    </div>

                    {/* User's Custom Prompts Section */}
                    <div>
                      <h3 className="text-sm font-semibold text-slate-700 mb-3">✨ Your Custom Prompts</h3>
                      {prompts.length === 0 ? (
                        <div className="text-center py-8 border-2 border-dashed border-slate-200 rounded-lg">
                          <FileText className="h-10 w-10 text-slate-300 mx-auto mb-3" />
                          <p className="text-slate-500 text-sm mb-3">No custom prompts yet</p>
                          <Button onClick={handleCreatePrompt} variant="outline" size="sm">
                            <Plus className="h-4 w-4 mr-2" />
                            Create Your First Prompt
                          </Button>
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {prompts.map((prompt) => (
                            <Card key={prompt.id} className="hover:shadow-md transition-shadow">
                              <CardContent className="pt-6">
                                <div className="flex items-start justify-between">
                                  <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-2">
                                      <h3 className="font-semibold text-slate-900">{prompt.name}</h3>
                                      {prompt.is_default && (
                                        <Badge className="bg-amber-100 text-amber-800 border-amber-300">
                                          <Star className="h-3 w-3 mr-1" />
                                          Default
                                        </Badge>
                                      )}
                                    </div>
                                    {prompt.description && (
                                      <p className="text-sm text-slate-600 mb-3">{prompt.description}</p>
                                    )}
                                    <div className="flex gap-2 text-xs text-slate-500">
                                      {prompt.system_prompt && (
                                        <Badge variant="outline">System</Badge>
                                      )}
                                      {prompt.analysis_prompt && (
                                        <Badge variant="outline">Analysis</Badge>
                                      )}
                                      {prompt.test_generation_prompt && (
                                        <Badge variant="outline">Test Gen</Badge>
                                      )}
                                    </div>
                                  </div>
                                  <div className="flex gap-2">
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => handleEditPrompt(prompt)}
                                    >
                                      <Edit2 className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => handleDeletePrompt(prompt.id)}
                                      className="text-red-600 hover:text-red-700"
                                    >
                                      <Trash2 className="h-4 w-4" />
                                    </Button>
                                  </div>
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Info Box */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                      <p className="text-sm text-blue-900 font-medium mb-2">
                        💡 Tips for Creating Effective Prompts
                      </p>
                      <ul className="text-sm text-blue-800 space-y-1">
                        <li>• Start with a default template and customize it</li>
                        <li>• Be specific about what you want the AI to focus on</li>
                        <li>• Use examples to guide the AI's output format</li>
                        <li>• Set one prompt as default for consistent results</li>
                        <li>• Create different prompts for different types of logs</li>
                      </ul>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

