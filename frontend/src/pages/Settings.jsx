import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Alert, AlertDescription } from '../components/ui/alert';
import { ArrowLeft, Save, Key, HelpCircle, CheckCircle } from 'lucide-react';
import axios from 'axios';

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

  // Load saved keys on mount
  useEffect(() => {
    loadApiKeys();
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
            <TabsTrigger value="help" data-testid="help-tab">
              <HelpCircle className="h-4 w-4 mr-2" />
              Help
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

          {/* Help Tab */}
          <TabsContent value="help">
            <Card>
              <CardHeader>
                <CardTitle>Help & Documentation</CardTitle>
                <CardDescription>
                  Resources to help you get the most out of ChaturLog
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Documentation Links */}
                <div className="space-y-4">
                  <div className="border border-slate-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                    <h3 className="font-medium text-slate-900 mb-2">📖 Setup Guide</h3>
                    <p className="text-sm text-slate-600 mb-3">
                      Complete installation and configuration instructions
                    </p>
                    <a
                      href="https://github.com/yourusername/chaturlog/blob/main/SETUP_GUIDE.md"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm font-medium"
                    >
                      View Setup Guide →
                    </a>
                  </div>

                  <div className="border border-slate-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                    <h3 className="font-medium text-slate-900 mb-2">🔍 Application Analysis</h3>
                    <p className="text-sm text-slate-600 mb-3">
                      Comprehensive overview of features and architecture
                    </p>
                    <a
                      href="https://github.com/yourusername/chaturlog/blob/main/COMPLETE_APPLICATION_ANALYSIS.md"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm font-medium"
                    >
                      View Analysis →
                    </a>
                  </div>

                  <div className="border border-slate-200 rounded-lg p-4 hover:border-blue-300 transition-colors">
                    <h3 className="font-medium text-slate-900 mb-2">⚙️ Environment Configuration</h3>
                    <p className="text-sm text-slate-600 mb-3">
                      Environment variables and configuration options
                    </p>
                    <a
                      href="https://github.com/yourusername/chaturlog/blob/main/ENV_SETUP.md"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-sm font-medium"
                    >
                      View Configuration Guide →
                    </a>
                  </div>
                </div>

                {/* Quick Links */}
                <div className="border-t border-slate-200 pt-6">
                  <h3 className="font-medium text-slate-900 mb-4">Quick Links</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <a
                      href="https://platform.openai.com/docs"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      OpenAI Documentation →
                    </a>
                    <a
                      href="https://docs.anthropic.com"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      Anthropic Documentation →
                    </a>
                    <a
                      href="https://ai.google.dev/docs"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      Google AI Documentation →
                    </a>
                    <a
                      href="https://github.com/yourusername/chaturlog"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm text-blue-600 hover:underline"
                    >
                      GitHub Repository →
                    </a>
                  </div>
                </div>

                {/* Version Info */}
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-center">
                  <p className="text-sm text-slate-600">
                    ChaturLog v1.0.0
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    AI-Powered Log Analysis & Test Generation
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

