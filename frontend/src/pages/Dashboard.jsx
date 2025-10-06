import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadLogFile, analyzeLog, generateTests, getAnalyses, getAnalysis, exportTests } from '../utils/api';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Input } from '../components/ui/input';
import { Progress } from '../components/ui/progress';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { Upload, FileText, Download, LogOut, Sparkles, Code, Settings, HelpCircle, BookOpen, ExternalLink, Search, Filter, AlertCircle, Activity, Zap, TrendingUp, AlertTriangle, Info, CheckCircle } from 'lucide-react';

export default function Dashboard() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [aiModel, setAiModel] = useState('gpt-4o');
  const [framework, setFramework] = useState('jest');
  const [analyses, setAnalyses] = useState([]);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterModel, setFilterModel] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');
  const [progressStage, setProgressStage] = useState('');
  const [progressPercent, setProgressPercent] = useState(0);
  const navigate = useNavigate();

  const userEmail = localStorage.getItem('user_email');

  useEffect(() => {
    loadAnalyses();
  }, []);

  const loadAnalyses = async () => {
    try {
      const response = await getAnalyses();
      setAnalyses(response.analyses || []);
    } catch (err) {
      console.error('Failed to load analyses:', err);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user_email');
    navigate('/login');
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadAndAnalyze = async () => {
    if (!selectedFile) {
      setUploadStatus('Please select a file first');
      return;
    }

    setLoading(true);
    setProgressPercent(0);
    
    try {
      // Step 1: Upload file
      setProgressStage('Uploading file to server...');
      setProgressPercent(10);
      setUploadStatus('📤 Uploading file...');
      
      const uploadResponse = await uploadLogFile(selectedFile);
      const analysisId = uploadResponse.analysis_id;
      setProgressPercent(25);

      // Step 2: Analyze with AI
      setProgressStage(`Analyzing logs with ${aiModel}...`);
      setProgressPercent(30);
      setUploadStatus('🤖 AI is analyzing your log file...');
      
      const analyzeResponse = await analyzeLog(analysisId, aiModel);
      setProgressPercent(60);
      setProgressStage('Analysis complete! Extracting patterns...');

      // Step 3: Generate tests
      setProgressStage(`Generating ${framework} test cases...`);
      setProgressPercent(70);
      setUploadStatus('🧪 Generating test cases...');
      
      const testsResponse = await generateTests(analysisId, framework);
      setProgressPercent(85);

      // Step 4: Load the complete analysis
      setProgressStage('Finalizing results...');
      setProgressPercent(90);
      setUploadStatus('✅ Loading results...');
      
      const fullAnalysis = await getAnalysis(analysisId);
      setCurrentAnalysis(fullAnalysis);

      // Reload analyses list
      await loadAnalyses();
      
      setProgressPercent(100);
      setProgressStage('Complete!');
      setUploadStatus(`✨ Success! Generated ${testsResponse.test_cases?.length || 0} test cases`);

      // Reset file selection after a short delay
      setTimeout(() => {
        setSelectedFile(null);
        setProgressPercent(0);
        setProgressStage('');
      }, 2000);
    } catch (err) {
      console.error('Error:', err);
      setProgressStage('');
      setProgressPercent(0);
      setUploadStatus(`❌ Error: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalysisDetails = async (analysisId) => {
    try {
      const response = await getAnalysis(analysisId);
      setCurrentAnalysis(response);
    } catch (err) {
      console.error('Failed to load analysis:', err);
    }
  };

  const downloadTestCode = (testCase) => {
    const blob = new Blob([testCase.test_code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_${testCase.framework}_${testCase.id}.${
      testCase.framework === 'junit' ? 'java' : testCase.framework === 'pytest' ? 'py' : 'js'
    }`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportAll = async () => {
    if (!currentAnalysis?.id) {
      setUploadStatus('❌ No analysis selected');
      return;
    }

    try {
      setUploadStatus('📦 Preparing export...');
      await exportTests(currentAnalysis.id);
      setUploadStatus('✅ Tests exported successfully!');
      setTimeout(() => setUploadStatus(''), 3000);
    } catch (err) {
      console.error('Export error:', err);
      setUploadStatus(`❌ Export failed: ${err.response?.data?.detail || err.message}`);
    }
  };

  const getPriorityBadge = (priority) => {
    const colors = {
      high: 'bg-red-100 text-red-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-green-100 text-green-800'
    };
    return colors[priority] || colors.medium;
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'text-slate-500',
      uploaded: 'text-blue-500',
      analyzing: 'text-blue-600',
      completed: 'text-green-600',
      failed: 'text-red-600'
    };
    return colors[status] || colors.pending;
  };

  // Filter analyses based on search and filter criteria
  const filteredAnalyses = analyses.filter(analysis => {
    // Search filter
    const matchesSearch = !searchQuery || 
      analysis.filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (analysis.ai_model && analysis.ai_model.toLowerCase().includes(searchQuery.toLowerCase()));
    
    // Model filter
    const matchesModel = filterModel === 'all' || 
      (analysis.ai_model && analysis.ai_model.toLowerCase().includes(filterModel.toLowerCase()));
    
    // Status filter
    const matchesStatus = filterStatus === 'all' || analysis.status === filterStatus;
    
    return matchesSearch && matchesModel && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Sparkles className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900">ChaturLog</h1>
                <p className="text-sm text-slate-600">AI-Powered Log Analysis</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-sm text-slate-600">{userEmail}</span>
              
              {/* Help Documentation Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    data-testid="help-button"
                  >
                    <BookOpen className="h-4 w-4 mr-2" />
                    Help
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-64">
                  <DropdownMenuLabel>Documentation</DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <a 
                      href="https://github.com/srewoo/chaturLog/blob/main/README.md" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center cursor-pointer"
                    >
                      <FileText className="h-4 w-4 mr-2" />
                      Getting Started
                      <ExternalLink className="h-3 w-3 ml-auto" />
                    </a>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <a 
                      href="https://github.com/srewoo/chaturLog/blob/main/SETUP_GUIDE.md" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center cursor-pointer"
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Setup Guide
                      <ExternalLink className="h-3 w-3 ml-auto" />
                    </a>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <a 
                      href="https://github.com/srewoo/chaturLog/blob/main/IMPROVEMENT_RECOMMENDATIONS.md" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center cursor-pointer"
                    >
                      <Sparkles className="h-4 w-4 mr-2" />
                      Feature Roadmap
                      <ExternalLink className="h-3 w-3 ml-auto" />
                    </a>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuLabel>API Documentation</DropdownMenuLabel>
                  <DropdownMenuItem asChild>
                    <a 
                      href="https://platform.openai.com/docs" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center cursor-pointer"
                    >
                      OpenAI API Docs
                      <ExternalLink className="h-3 w-3 ml-auto" />
                    </a>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <a 
                      href="https://docs.anthropic.com" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center cursor-pointer"
                    >
                      Anthropic API Docs
                      <ExternalLink className="h-3 w-3 ml-auto" />
                    </a>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <a 
                      href="https://ai.google.dev/docs" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center cursor-pointer"
                    >
                      Google AI Docs
                      <ExternalLink className="h-3 w-3 ml-auto" />
                    </a>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <a 
                      href="https://github.com/srewoo/chaturLog/issues" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="flex items-center cursor-pointer"
                    >
                      <HelpCircle className="h-4 w-4 mr-2" />
                      Report an Issue
                      <ExternalLink className="h-3 w-3 ml-auto" />
                    </a>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigate('/settings')}
                data-testid="settings-button"
              >
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleLogout}
                data-testid="logout-button"
              >
                <LogOut className="h-4 w-4 mr-2" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs defaultValue="upload" className="space-y-6">
          <TabsList className="grid w-full max-w-md grid-cols-2">
            <TabsTrigger value="upload" data-testid="upload-tab">
              <Upload className="h-4 w-4 mr-2" />
              Upload & Analyze
            </TabsTrigger>
            <TabsTrigger value="history" data-testid="history-tab">
              <FileText className="h-4 w-4 mr-2" />
              History
            </TabsTrigger>
          </TabsList>

          {/* Upload Tab */}
          <TabsContent value="upload" className="space-y-6">
            <Card data-testid="upload-card">
              <CardHeader>
                <CardTitle>Upload Log File</CardTitle>
                <CardDescription>
                  Upload your log file (.log, .txt, .json) up to 50MB for AI-powered analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* File Upload Area */}
                <div
                  className={`upload-area ${dragActive ? 'drag-active' : ''}`}
                  onDragEnter={handleDrag}
                  onDragLeave={handleDrag}
                  onDragOver={handleDrag}
                  onDrop={handleDrop}
                  onClick={() => document.getElementById('file-input')?.click()}
                  data-testid="upload-dropzone"
                  style={{ cursor: 'pointer' }}
                >
                  <Upload className="h-12 w-12 text-slate-400 mx-auto mb-4" />
                  <p className="text-lg font-medium text-slate-700 mb-2">
                    {selectedFile ? selectedFile.name : 'Drop your log file here'}
                  </p>
                  <p className="text-sm text-slate-500 mb-4">
                    or click to browse
                  </p>
                  <input
                    type="file"
                    onChange={handleFileChange}
                    accept=".log,.txt,.json"
                    className="hidden"
                    id="file-input"
                    data-testid="file-input"
                    ref={(input) => {
                      if (input) {
                        window.fileInput = input;
                      }
                    }}
                  />
                  <Button 
                    variant="outline" 
                    className="cursor-pointer" 
                    onClick={(e) => {
                      e.stopPropagation();
                      document.getElementById('file-input')?.click();
                    }}
                    type="button"
                    data-testid="select-file-button"
                  >
                    Select File
                  </Button>
                </div>

                {/* Configuration */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">AI Model</label>
                    <Select value={aiModel} onValueChange={setAiModel}>
                      <SelectTrigger data-testid="ai-model-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="gpt-4o">OpenAI GPT-4o</SelectItem>
                        <SelectItem value="gpt-4o-mini">OpenAI GPT-4o Mini</SelectItem>
                        <SelectItem value="claude-3-7-sonnet-20250219">Claude 3.7 Sonnet</SelectItem>
                        <SelectItem value="claude-4-sonnet-20250514">Claude 4 Sonnet</SelectItem>
                        <SelectItem value="gemini-2.0-flash">Gemini 2.0 Flash</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <label className="text-sm font-medium text-slate-700">Test Framework</label>
                    <Select value={framework} onValueChange={setFramework}>
                      <SelectTrigger data-testid="framework-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="jest">Jest (JavaScript)</SelectItem>
                        <SelectItem value="mocha">Mocha (JavaScript)</SelectItem>
                        <SelectItem value="cypress">Cypress (E2E)</SelectItem>
                        <SelectItem value="junit">JUnit (Java)</SelectItem>
                        <SelectItem value="pytest">pytest (Python)</SelectItem>
                        <SelectItem value="rspec">RSpec (Ruby)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Action Button */}
                <Button
                  onClick={handleUploadAndAnalyze}
                  disabled={!selectedFile || loading}
                  className="w-full"
                  data-testid="analyze-button"
                >
                  {loading ? (
                    <>
                      <span className="spinner mr-2"></span>
                      Processing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Upload & Analyze
                    </>
                  )}
                </Button>

                {/* Progress Indicator */}
                {loading && progressPercent > 0 && (
                  <Card>
                    <CardContent className="pt-6">
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium text-slate-700">
                            {progressStage}
                          </span>
                          <span className="text-slate-600">{progressPercent}%</span>
                        </div>
                        <Progress value={progressPercent} className="h-2" />
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                          <div className="flex items-center gap-1">
                            {progressPercent < 30 ? (
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                            ) : progressPercent < 70 ? (
                              <div className="w-2 h-2 bg-purple-500 rounded-full animate-pulse"></div>
                            ) : progressPercent < 100 ? (
                              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                            ) : (
                              <div className="w-2 h-2 bg-green-600 rounded-full"></div>
                            )}
                            <span>
                              {progressPercent < 30 ? 'Uploading' :
                               progressPercent < 70 ? 'Analyzing' :
                               progressPercent < 100 ? 'Generating Tests' : 'Complete'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Status Message */}
                {uploadStatus && (
                  <div
                    className={`p-4 rounded-lg ${
                      uploadStatus.includes('Error') || uploadStatus.includes('❌')
                        ? 'bg-red-50 text-red-800'
                        : uploadStatus.includes('Success') || uploadStatus.includes('✨')
                        ? 'bg-green-50 text-green-800'
                        : 'bg-blue-50 text-blue-800'
                    }`}
                    data-testid="status-message"
                  >
                    {uploadStatus}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Results Display */}
            {currentAnalysis && (
              <div className="space-y-6 fade-in">
                {/* Log Summary Section */}
                <Card className="border-blue-200 bg-gradient-to-br from-blue-50 to-indigo-50">
                  <CardHeader>
                    <div className="flex items-center gap-2">
                      <Activity className="h-5 w-5 text-blue-600" />
                      <CardTitle className="text-blue-900">Log File Summary</CardTitle>
                    </div>
                    <CardDescription className="text-blue-700">
                      AI-powered analysis of your log file
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Key Metrics Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                      {/* Total Errors */}
                      <div className="bg-white rounded-lg p-4 border border-red-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="p-2 bg-red-100 rounded-lg">
                              <AlertCircle className="h-4 w-4 text-red-600" />
                            </div>
                            <span className="text-sm font-medium text-slate-600">Errors Found</span>
                          </div>
                        </div>
                        <p className="text-3xl font-bold text-red-600">
                          {currentAnalysis.patterns?.filter(p => p.severity === 'high' || p.severity === 'critical').length || 0}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {currentAnalysis.patterns?.filter(p => p.severity === 'critical').length || 0} critical
                        </p>
                      </div>

                      {/* Warnings */}
                      <div className="bg-white rounded-lg p-4 border border-yellow-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="p-2 bg-yellow-100 rounded-lg">
                              <AlertTriangle className="h-4 w-4 text-yellow-600" />
                            </div>
                            <span className="text-sm font-medium text-slate-600">Warnings</span>
                          </div>
                        </div>
                        <p className="text-3xl font-bold text-yellow-600">
                          {currentAnalysis.patterns?.filter(p => p.severity === 'medium').length || 0}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          Medium priority
                        </p>
                      </div>

                      {/* Info Items */}
                      <div className="bg-white rounded-lg p-4 border border-blue-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="p-2 bg-blue-100 rounded-lg">
                              <Info className="h-4 w-4 text-blue-600" />
                            </div>
                            <span className="text-sm font-medium text-slate-600">Info/Low</span>
                          </div>
                        </div>
                        <p className="text-3xl font-bold text-blue-600">
                          {currentAnalysis.patterns?.filter(p => p.severity === 'low').length || 0}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          Low priority
                        </p>
                      </div>

                      {/* Test Cases */}
                      <div className="bg-white rounded-lg p-4 border border-green-200 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="p-2 bg-green-100 rounded-lg">
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            </div>
                            <span className="text-sm font-medium text-slate-600">Tests Generated</span>
                          </div>
                        </div>
                        <p className="text-3xl font-bold text-green-600">
                          {currentAnalysis.test_cases?.length || 0}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          Ready to use
                        </p>
                      </div>
                    </div>

                    {/* AI Insights */}
                    <div className="bg-white rounded-lg p-5 border border-indigo-200">
                      <div className="flex items-start gap-3">
                        <div className="p-2 bg-indigo-100 rounded-lg mt-0.5">
                          <Sparkles className="h-5 w-5 text-indigo-600" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-indigo-900 mb-2">AI Analysis Summary</h3>
                          <div className="space-y-2 text-sm text-slate-700">
                            <p>
                              <strong>File:</strong> {currentAnalysis.filename || 'N/A'}
                            </p>
                            <p>
                              <strong>Model Used:</strong> {currentAnalysis.ai_model || aiModel}
                            </p>
                            <p>
                              <strong>Analysis Date:</strong> {
                                currentAnalysis.created_at 
                                  ? new Date(currentAnalysis.created_at).toLocaleString('en-US', {
                                      year: 'numeric',
                                      month: 'short',
                                      day: 'numeric',
                                      hour: '2-digit',
                                      minute: '2-digit'
                                    })
                                  : 'Just now'
                              }
                            </p>
                            {currentAnalysis.patterns && currentAnalysis.patterns.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-200">
                                <p className="font-medium text-slate-900 mb-2">Top Issues Detected:</p>
                                <ul className="list-disc list-inside space-y-1 text-slate-600">
                                  {currentAnalysis.patterns.slice(0, 3).map((pattern, idx) => (
                                    <li key={idx} className="text-xs">
                                      <span className="font-medium">{pattern.pattern_type}:</span> {pattern.description.substring(0, 100)}{pattern.description.length > 100 ? '...' : ''}
                                    </li>
                                  ))}
                                  {currentAnalysis.patterns.length > 3 && (
                                    <li className="text-xs italic text-slate-500">
                                      + {currentAnalysis.patterns.length - 3} more issues detected
                                    </li>
                                  )}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="flex items-center gap-3 pt-2 border-t border-indigo-200">
                      <span className="text-sm font-medium text-slate-700">Quick Actions:</span>
                      <div className="flex gap-2">
                        {currentAnalysis.test_cases && currentAnalysis.test_cases.length > 0 && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleExportAll(currentAnalysis.id)}
                            className="text-xs"
                          >
                            <Download className="h-3 w-3 mr-1" />
                            Export Tests
                          </Button>
                        )}
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {
                            // Try patterns card first, then test cases card
                            const patternsCard = document.querySelector('[data-testid="patterns-card"]');
                            const testCasesCard = document.querySelector('[data-testid="test-cases-card"]');
                            const targetElement = patternsCard || testCasesCard;
                            
                            if (targetElement) {
                              targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            }
                          }}
                          className="text-xs"
                        >
                          <Activity className="h-3 w-3 mr-1" />
                          View Details
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Patterns Card */}
                {currentAnalysis.patterns && currentAnalysis.patterns.length > 0 && (
                  <Card data-testid="patterns-card">
                    <CardHeader>
                      <CardTitle>Detected Patterns</CardTitle>
                      <CardDescription>
                        {currentAnalysis.patterns.length} patterns found in the log file
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {currentAnalysis.patterns.map((pattern, idx) => (
                          <div
                            key={pattern.id || idx}
                            className="p-4 border border-slate-200 rounded-lg"
                            data-testid={`pattern-${idx}`}
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center space-x-2 mb-2">
                                  <Badge className={getPriorityBadge(pattern.severity)}>
                                    {pattern.severity}
                                  </Badge>
                                  <span className="text-sm text-slate-600">
                                    Type: {pattern.pattern_type}
                                  </span>
                                </div>
                                <p className="text-sm text-slate-700">{pattern.description}</p>
                              </div>
                              <span className="text-sm font-medium text-slate-500">
                                x{pattern.frequency}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}

                {/* Test Cases Card */}
                {currentAnalysis.test_cases && currentAnalysis.test_cases.length > 0 && (
                  <Card data-testid="test-cases-card">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle>Generated Test Cases</CardTitle>
                          <CardDescription>
                            {currentAnalysis.test_cases.length} test cases ready for download
                          </CardDescription>
                        </div>
                        <Button
                          onClick={handleExportAll}
                          variant="default"
                          className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                          data-testid="export-all-button"
                        >
                          <Download className="h-4 w-4 mr-2" />
                          Export All as ZIP
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        {currentAnalysis.test_cases.map((testCase, idx) => (
                          <div
                            key={testCase.id || idx}
                            className="border border-slate-200 rounded-lg overflow-hidden"
                            data-testid={`test-case-${idx}`}
                          >
                            <div className="p-4 bg-slate-50 border-b border-slate-200">
                              <div className="flex items-center justify-between">
                                <div>
                                  <div className="flex items-center space-x-2 mb-1">
                                    <Badge variant="outline">{testCase.framework}</Badge>
                                    <Badge className={getPriorityBadge(testCase.priority)}>
                                      {testCase.priority} priority
                                    </Badge>
                                  </div>
                                  <p className="text-sm text-slate-700">{testCase.description}</p>
                                </div>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => downloadTestCode(testCase)}
                                  data-testid={`download-test-${idx}`}
                                >
                                  <Download className="h-4 w-4 mr-2" />
                                  Download
                                </Button>
                              </div>
                            </div>
                            <div className="p-4">
                              <pre className="test-code">{testCase.test_code}</pre>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            )}
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history" data-testid="history-content">
            <Card>
              <CardHeader>
                <CardTitle>Analysis History</CardTitle>
                <CardDescription>
                  View and manage your previous log analyses ({filteredAnalyses.length})
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Search and Filter Controls */}
                <div className="space-y-4 mb-6">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search by filename or model..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                      data-testid="search-input"
                    />
                  </div>
                  
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <label className="text-sm font-medium text-slate-700 mb-2 block">
                        <Filter className="inline h-3 w-3 mr-1" />
                        AI Model
                      </label>
                      <Select value={filterModel} onValueChange={setFilterModel}>
                        <SelectTrigger data-testid="filter-model-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Models</SelectItem>
                          <SelectItem value="gpt">GPT Models</SelectItem>
                          <SelectItem value="claude">Claude Models</SelectItem>
                          <SelectItem value="gemini">Gemini Models</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="flex-1">
                      <label className="text-sm font-medium text-slate-700 mb-2 block">
                        <Filter className="inline h-3 w-3 mr-1" />
                        Status
                      </label>
                      <Select value={filterStatus} onValueChange={setFilterStatus}>
                        <SelectTrigger data-testid="filter-status-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">All Status</SelectItem>
                          <SelectItem value="completed">Completed</SelectItem>
                          <SelectItem value="pending">Pending</SelectItem>
                          <SelectItem value="failed">Failed</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  
                  {(searchQuery || filterModel !== 'all' || filterStatus !== 'all') && (
                    <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                      <span className="text-sm text-blue-700">
                        Showing {filteredAnalyses.length} of {analyses.length} analyses
                      </span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSearchQuery('');
                          setFilterModel('all');
                          setFilterStatus('all');
                        }}
                        className="text-blue-600 hover:text-blue-700"
                      >
                        Clear Filters
                      </Button>
                    </div>
                  )}
                </div>
                
                {/* Analysis List */}
                {analyses.length === 0 ? (
                  <div className="text-center py-12">
                    <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">No analyses yet. Upload a log file to get started!</p>
                  </div>
                ) : filteredAnalyses.length === 0 ? (
                  <div className="text-center py-12">
                    <Search className="h-12 w-12 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">No analyses match your filters</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setSearchQuery('');
                        setFilterModel('all');
                        setFilterStatus('all');
                      }}
                      className="mt-4"
                    >
                      Clear Filters
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {filteredAnalyses.map((analysis) => (
                      <div
                        key={analysis.id}
                        className="p-4 border border-slate-200 rounded-lg card-hover cursor-pointer"
                        onClick={() => loadAnalysisDetails(analysis.id)}
                        data-testid={`analysis-${analysis.id}`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <Code className="h-4 w-4 text-slate-400" />
                              <span className="font-medium text-slate-900">{analysis.filename}</span>
                            </div>
                            <div className="flex items-center space-x-3 text-sm text-slate-600">
                              <span>Model: {analysis.ai_model || 'N/A'}</span>
                              <span>•</span>
                              <span>
                                {new Date(analysis.created_at).toLocaleDateString()}
                              </span>
                            </div>
                          </div>
                          <Badge className={getStatusColor(analysis.status)}>
                            {analysis.status}
                          </Badge>
                        </div>
                      </div>
                    ))}
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
