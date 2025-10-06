import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_BASE = `${BACKEND_URL}/api`;

// Create axios instance
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth APIs
export const register = async (email, password) => {
  const response = await api.post('/auth/register', { email, password });
  return response.data;
};

export const login = async (email, password) => {
  const response = await api.post('/auth/login', { email, password });
  return response.data;
};

// File upload API
export const uploadLogFile = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  });
  return response.data;
};

// Analysis APIs
export const analyzeLog = async (analysisId, aiModel) => {
  const response = await api.post(`/analyze/${analysisId}`, { ai_model: aiModel });
  return response.data;
};

export const generateTests = async (analysisId, framework) => {
  const response = await api.post(`/generate-tests/${analysisId}`, { framework });
  return response.data;
};

export const getAnalyses = async () => {
  const response = await api.get('/analyses');
  return response.data;
};

export const getAnalysis = async (analysisId) => {
  const response = await api.get(`/analyses/${analysisId}`);
  return response.data;
};

export const exportTests = async (analysisId) => {
  const response = await api.get(`/export/${analysisId}`, {
    responseType: 'blob'
  });
  
  // Create download link
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', `chaturlog_tests_${analysisId}.zip`);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
  
  return { success: true };
};

// Custom Prompts APIs
export const getPrompts = async () => {
  const response = await api.get('/prompts');
  return response.data;
};

export const getPrompt = async (promptId) => {
  const response = await api.get(`/prompts/${promptId}`);
  return response.data;
};

export const createPrompt = async (promptData) => {
  const response = await api.post('/prompts', promptData);
  return response.data;
};

export const updatePrompt = async (promptId, promptData) => {
  const response = await api.put(`/prompts/${promptId}`, promptData);
  return response.data;
};

export const deletePrompt = async (promptId) => {
  const response = await api.delete(`/prompts/${promptId}`);
  return response.data;
};

export default api;