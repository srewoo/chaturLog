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
import { ArrowLeft, Save, Key, CheckCircle, FileText, Plus, Edit2, Trash2, Star } from 'lucide-react';
import axios from 'axios';
import { getPrompts, createPrompt, updatePrompt, deletePrompt } from '../utils/api';

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
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="api-keys" data-testid="api-keys-tab">
              <Key className="h-4 w-4 mr-2" />
              API Keys
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

