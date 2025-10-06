# Environment Variables Setup Guide

## Backend Environment Variables

Create a `.env` file in the `backend/` directory with the following variables:

```env
# JWT Secret Key - CHANGE THIS IN PRODUCTION
JWT_SECRET_KEY=your-secret-key-change-in-production-to-a-secure-random-string

# CORS Origins (comma-separated list of allowed origins)
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Server Configuration
HOST=0.0.0.0
PORT=8001

# File Upload Configuration
MAX_FILE_SIZE_MB=50
```

## Frontend Environment Variables

Create a `.env` file in the `frontend/` directory with the following variables:

```env
# Backend API URL
REACT_APP_BACKEND_URL=http://localhost:8001

# App Configuration
REACT_APP_NAME=ChaturLog
REACT_APP_VERSION=1.0.0

# API Configuration
REACT_APP_MAX_FILE_SIZE_MB=50
REACT_APP_ALLOWED_FILE_TYPES=.log,.txt,.json
```

## API Keys Configuration

**IMPORTANT**: API keys are now configured per-user through the Settings page in the application UI for better security and flexibility.

Each user must add their own API keys:
1. **OpenAI API Key**: For GPT-4o and GPT-4o-mini models
   - Get your key from: https://platform.openai.com/api-keys

2. **Anthropic API Key**: For Claude 3.7 and Claude 4 Sonnet models
   - Get your key from: https://console.anthropic.com/settings/keys

3. **Google AI API Key**: For Gemini 2.0 Flash models
   - Get your key from: https://makersuite.google.com/app/apikey

### How to Add API Keys:
1. Register/Login to ChaturLog
2. Click "Settings" in the dashboard header
3. Go to "API Keys" tab
4. Enter your API keys
5. Click "Save API Keys"

## Quick Setup

### Backend
```bash
cd backend
# Create .env file
cat > .env << EOF
JWT_SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=http://localhost:3000
HOST=0.0.0.0
PORT=8001
EOF

pip install -r requirements.txt
python server.py
```

### Frontend
```bash
cd frontend
# Create .env file
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

yarn install
yarn start
```

## Security Notes

⚠️ **IMPORTANT**: Never commit `.env` files to version control!

✅ Always use strong, random JWT secrets in production

✅ Keep API keys secure - they are now stored per-user in encrypted form

✅ Each user manages their own API keys

✅ API keys are never exposed in API responses (masked for security)
