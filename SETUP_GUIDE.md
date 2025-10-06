# 🚀 ChaturLog - Complete Setup Guide

## 📋 Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Usage Guide](#usage-guide)
- [Architecture](#architecture)
- [API Documentation](#api-documentation)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

**ChaturLog** is an AI-powered log analysis and test generation platform that:
- Analyzes application logs using advanced AI models (OpenAI, Claude, Gemini)
- Automatically generates test cases in multiple frameworks (Jest, JUnit, pytest)
- Provides error pattern detection and severity analysis
- Tracks analysis history and results

---

## 📦 Prerequisites

### Required Software
- **Python**: 3.8 or higher
- **Node.js**: 16.x or higher
- **npm/yarn**: Package manager
- **Git**: Version control

### API Keys Required
- **Emergent LLM API Key**: For AI analysis and test generation
  - Sign up at: https://emergentintegrations.com
  - Get your API key from the dashboard

---

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd chaturLog
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Create Environment File
Create a `.env` file in the `backend/` directory:
```env
# JWT Secret Key - CHANGE THIS IN PRODUCTION
JWT_SECRET_KEY=your-secret-key-change-in-production-to-a-secure-random-string

# Emergent LLM API Key
EMERGENT_LLM_KEY=your-emergent-llm-api-key-here

# CORS Origins
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Server Configuration
HOST=0.0.0.0
PORT=8001
```

### 3. Frontend Setup

#### Install Node Dependencies
```bash
cd frontend
yarn install
# or
npm install
```

#### Create Environment File
Create a `.env` file in the `frontend/` directory:
```env
REACT_APP_BACKEND_URL=http://localhost:8001
REACT_APP_MAX_FILE_SIZE_MB=50
REACT_APP_ALLOWED_FILE_TYPES=.log,.txt,.json
```

---

## ⚙️ Configuration

### Backend Configuration

#### Database
- **Type**: SQLite
- **Location**: `backend/chaturlog.db`
- **Auto-initialization**: Database tables are created automatically on first run

#### File Uploads
- **Directory**: `backend/uploads/`
- **Max Size**: 50MB (configurable)
- **Allowed Types**: `.log`, `.txt`, `.json`

#### AI Models Supported
1. **OpenAI**:
   - `gpt-4o`
   - `gpt-4o-mini`

2. **Anthropic Claude**:
   - `claude-3-7-sonnet-20250219`
   - `claude-4-sonnet-20250514`

3. **Google Gemini**:
   - `gemini-2.0-flash`

### Frontend Configuration

#### API Client
- Base URL: Configured via `REACT_APP_BACKEND_URL`
- Authentication: JWT Bearer token in Authorization header
- Timeout: 30 seconds (default)

---

## 🏃 Running the Application

### Start Backend Server
```bash
cd backend
python server.py
```
Server will start at: `http://localhost:8001`

### Start Frontend Development Server
```bash
cd frontend
yarn start
# or
npm start
```
Application will open at: `http://localhost:3000`

### Production Build
```bash
cd frontend
yarn build
# or
npm run build
```

---

## 📖 Usage Guide

### 1. User Registration
1. Navigate to `http://localhost:3000`
2. Click "Register"
3. Enter email and password
4. Submit to create account

### 2. Login
1. Enter registered credentials
2. Click "Login"
3. Redirects to Dashboard

### 3. Upload and Analyze Logs

#### Step-by-Step:
1. **Upload File**:
   - Drag and drop log file onto upload area
   - OR click "Browse Files" to select file
   - Supported: `.log`, `.txt`, `.json` (up to 50MB)

2. **Configure Analysis**:
   - **AI Model**: Select from OpenAI, Claude, or Gemini
   - **Test Framework**: Choose Jest, JUnit, or pytest

3. **Start Analysis**:
   - Click "Upload & Analyze"
   - Wait for processing (typically 30-60 seconds)

4. **View Results**:
   - **Error Patterns**: See detected issues with severity levels
   - **API Endpoints**: View extracted endpoints and status codes
   - **Test Cases**: Download generated test code

### 4. View History
1. Click "History" tab
2. View all past analyses
3. Click on any analysis to view details

---

## 🏗️ Architecture

### Technology Stack

#### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite
- **Authentication**: JWT (JSON Web Tokens)
- **AI Integration**: Emergent Integrations library
- **File Handling**: Python multipart/form-data

#### Frontend
- **Framework**: React 19
- **UI Library**: shadcn/ui (Radix UI primitives)
- **Styling**: Tailwind CSS
- **Routing**: React Router v7
- **HTTP Client**: Axios
- **State Management**: React Hooks (useState, useEffect)

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Analyses Table
```sql
CREATE TABLE analyses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  filename TEXT NOT NULL,
  file_path TEXT NOT NULL,
  status TEXT DEFAULT 'pending',
  ai_model TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  completed_at TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Patterns Table
```sql
CREATE TABLE patterns (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  analysis_id INTEGER NOT NULL,
  pattern_type TEXT NOT NULL,
  description TEXT,
  severity TEXT DEFAULT 'medium',
  frequency INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

#### Test Cases Table
```sql
CREATE TABLE test_cases (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  analysis_id INTEGER NOT NULL,
  framework TEXT NOT NULL,
  test_code TEXT NOT NULL,
  risk_score REAL DEFAULT 0,
  priority TEXT DEFAULT 'medium',
  description TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (analysis_id) REFERENCES analyses(id)
);
```

---

## 🔌 API Documentation

### Authentication Endpoints

#### POST `/api/auth/register`
Register a new user.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "access_token": "jwt-token-here",
  "user_id": 1,
  "email": "user@example.com"
}
```

#### POST `/api/auth/login`
Login existing user.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response**: Same as register

### Analysis Endpoints

#### POST `/api/upload`
Upload log file for analysis.

**Headers**:
```
Authorization: Bearer <jwt-token>
Content-Type: multipart/form-data
```

**Form Data**:
- `file`: Log file (.log, .txt, .json)

**Response**:
```json
{
  "success": true,
  "analysis_id": 1,
  "filename": "app.log",
  "message": "File uploaded successfully"
}
```

#### POST `/api/analyze/{analysis_id}`
Analyze uploaded log file with AI.

**Request Body**:
```json
{
  "ai_model": "gpt-4o"
}
```

**Response**:
```json
{
  "success": true,
  "analysis_id": 1,
  "analysis": {
    "error_patterns": [...],
    "api_endpoints": [...],
    "performance_issues": [...],
    "business_impact": {...}
  },
  "message": "Analysis completed successfully"
}
```

#### POST `/api/generate-tests/{analysis_id}`
Generate test cases from analysis.

**Request Body**:
```json
{
  "framework": "jest"
}
```

**Response**:
```json
{
  "success": true,
  "analysis_id": 1,
  "framework": "jest",
  "test_cases": [...],
  "message": "Generated 5 test cases"
}
```

#### GET `/api/analyses`
Get all analyses for current user.

**Response**:
```json
{
  "success": true,
  "analyses": [...]
}
```

#### GET `/api/analyses/{analysis_id}`
Get specific analysis details.

**Response**:
```json
{
  "success": true,
  "analysis": {...},
  "patterns": [...],
  "test_cases": [...]
}
```

---

## 🐛 Troubleshooting

### Common Issues

#### Backend Issues

**Problem**: `ModuleNotFoundError: No module named 'emergentintegrations'`
```bash
# Solution:
pip install emergentintegrations
```

**Problem**: `sqlite3.OperationalError: unable to open database file`
```bash
# Solution: Check write permissions
chmod 755 backend/
```

**Problem**: `CORS Error when calling API`
```bash
# Solution: Check CORS_ORIGINS in .env
CORS_ORIGINS=http://localhost:3000
```

#### Frontend Issues

**Problem**: `Error: process.env.REACT_APP_BACKEND_URL is undefined`
```bash
# Solution: Create .env file with:
REACT_APP_BACKEND_URL=http://localhost:8001
```

**Problem**: `Cannot find module 'axios'`
```bash
# Solution:
yarn add axios
# or
npm install axios
```

#### API Key Issues

**Problem**: `Invalid API key` or `Authentication failed`
```bash
# Solution:
1. Check EMERGENT_LLM_KEY in backend/.env
2. Verify key is valid at emergentintegrations.com
3. Ensure no extra spaces in .env file
```

### Debug Mode

Enable debug logging in backend:
```python
# backend/server.py
logging.basicConfig(level=logging.DEBUG)
```

Enable React debug mode:
```env
# frontend/.env
REACT_APP_ENABLE_DEBUG=true
```

### Log Locations

- **Backend Logs**: Console output
- **Frontend Console**: Browser DevTools
- **Uploaded Files**: `backend/uploads/`
- **Database**: `backend/chaturlog.db`

---

## 🔒 Security Best Practices

1. **JWT Secret**: Use a strong, random secret in production
2. **API Keys**: Never commit `.env` files to version control
3. **HTTPS**: Use HTTPS in production environments
4. **Input Validation**: All file uploads are validated
5. **Rate Limiting**: Consider adding rate limiting in production
6. **Password Hashing**: Uses SHA-256 (consider bcrypt for production)

---

## 📝 Development Notes

### Component Structure
```
frontend/src/
├── components/
│   ├── ui/              # shadcn/ui components
│   ├── ErrorBoundary.jsx
│   ├── FileUpload.jsx
│   └── LoadingStates.jsx
├── pages/
│   ├── Dashboard.jsx
│   ├── Login.jsx
│   └── Register.jsx
├── utils/
│   ├── api.js
│   └── fileValidation.js
└── App.js
```

### New Components Added

1. **FileUpload.jsx**: Enhanced file upload with drag-and-drop and progress
2. **ErrorBoundary.jsx**: Catches and displays React errors gracefully
3. **LoadingStates.jsx**: Skeleton screens and loading indicators
4. **fileValidation.js**: Utility functions for file validation

### Code Quality
- Follow ES6+ standards
- Use `const` and `let` (no `var`)
- Always use `async/await` (no `.then()` chains)
- Add `data-testid` attributes for testing
- Handle errors explicitly

---

## 🚀 Deployment

### Backend Deployment
```bash
# Using gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker server:app
```

### Frontend Deployment
```bash
# Build for production
yarn build

# Serve with nginx or deploy to:
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
```

---

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review error logs
3. Verify environment configuration
4. Check API key validity

---

## 📄 License

[Add your license information here]

---

## 🎉 Success!

You're all set! ChaturLog should now be running successfully. Start analyzing your logs and generating tests! 🚀

