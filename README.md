# 🚀 ChaturLog - AI-Powered Log Analysis & Test Generation

<div align="center">

![ChaturLog](https://img.shields.io/badge/ChaturLog-AI%20Powered-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![React](https://img.shields.io/badge/React-19.0-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-teal)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Analyze application logs with AI and generate test cases automatically**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture)

</div>

---

## 📋 Overview

**ChaturLog** is an intelligent platform that uses advanced AI models to analyze application logs and automatically generate comprehensive test cases. It helps developers quickly identify issues, understand error patterns, and create production-ready tests in multiple frameworks.

### 🎯 What It Does

- 🔍 **Analyze Logs**: Upload log files and get AI-powered analysis
- 🤖 **Multiple AI Models**: OpenAI GPT-4o, Claude 4 Sonnet, Gemini 2.0 Flash
- 🧪 **Generate Tests**: Automatic test case generation in Jest, JUnit, and pytest
- 📊 **Error Patterns**: Detect and classify errors by severity and frequency
- 🎨 **Modern UI**: Beautiful, responsive interface with drag-and-drop
- 📈 **History Tracking**: View and access all previous analyses

---

## ✨ Features

### Core Functionality
- ✅ **User Authentication** - Secure JWT-based auth
- ✅ **File Upload** - Drag-and-drop interface with validation
- ✅ **AI Analysis** - Powered by OpenAI, Claude, and Gemini
- ✅ **Test Generation** - Jest, JUnit, pytest, Mocha, Cypress, RSpec support
- ✅ **Pattern Detection** - Error classification and severity assessment
- ✅ **API Extraction** - Identify endpoints and status codes
- ✅ **Git Integration** 🆕 - Smart repository detection from logs
- ✅ **Repository Mappings** 🆕 - Automatic service-to-repo mapping
- ✅ **History Management** 🆕 - Track all analyses, delete individual or all (non-recoverable)
- ✅ **Download Tests** - Get production-ready test code
- ✅ **Custom AI Prompts** - Personalize analysis behavior
- ✅ **Scalable Processing** - Handle large log files efficiently

### Technical Features
- ✅ **Modern Stack** - FastAPI + React 19
- ✅ **Beautiful UI** - shadcn/ui components + Tailwind CSS
- ✅ **Error Handling** - Error boundaries and graceful failures
- ✅ **Loading States** - Skeleton screens for better UX
- ✅ **File Validation** - Client and server-side validation
- ✅ **Responsive Design** - Works on all screen sizes

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm/yarn
- API keys from OpenAI, Anthropic, and/or Google AI (at least one required)

### 1. Clone Repository
```bash
git clone <repository-url>
cd chaturLog
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
JWT_SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000
EOF

# Start server
python server.py
```

**Note**: API keys are now configured per-user in the Settings page for security and flexibility.

### 3. Frontend Setup
```bash
cd frontend
yarn install

# Create .env file
echo "REACT_APP_BACKEND_URL=http://localhost:8001" > .env

# Start dev server
yarn start
```

### 4. Open Application
Navigate to: `http://localhost:3000`

---

## 📖 Documentation

### 📘 **[Complete Documentation (HTML)](./docs/index.html)** ⭐ **RECOMMENDED**

Open `docs/index.html` in your browser for comprehensive, beautifully formatted documentation including:
- ✅ Overview & Features
- ✅ Quick Start Guide
- ✅ Git Integration Guide
- ✅ Test Frameworks
- ✅ API Reference
- ✅ Troubleshooting
- ✅ Security Information

**Quick Access:** Simply open the file in your browser:
```bash
open docs/index.html  # macOS
start docs/index.html  # Windows
xdg-open docs/index.html  # Linux
```

Or access it via: `http://localhost:3000/docs/` (when frontend is running)

### 🚀 **Optimization & Performance Guides** 🆕

- **[Optimization Complete Summary](./OPTIMIZATION_COMPLETE_SUMMARY.md)** - Implementation results & ROI
- **[Phase 1 Complete](./IMPLEMENTATION_COMPLETE_PHASE1.md)** - Detailed feature breakdown ✅
- **[Test Generation Analysis](./TEST_GENERATION_ANALYSIS.md)** - Technical deep dive
- **[LLM Data Flow](./CURRENT_LLM_DATA_FLOW.md)** - Visual diagrams & token analysis
- **[Phase 2 Guide](./PHASE2_IMPLEMENTATION_GUIDE.md)** - Advanced features (future)
- **[Phase 3 Guide](./PHASE3_IMPLEMENTATION_GUIDE.md)** - AI-powered enhancements (future)

**Recent Optimizations** ⚡:
- ✅ Error-aware sampling (+40% test coverage)
- ✅ Smart log excerpts (5x more context)
- ✅ Optimized formatting (-40% tokens)
- ✅ Analysis caching (-70% multi-framework tokens)
- **Result**: -30% cost, +40% quality!

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/register` | POST | User registration |
| `/api/auth/login` | POST | User login |
| `/api/upload` | POST | Upload log file |
| `/api/analyze/{id}` | POST | Analyze log with AI (includes Git detection) |
| `/api/generate-tests/{id}` | POST | Generate test cases |
| `/api/analyses` | GET | Get all analyses |
| `/api/analyses/{id}` | GET | Get specific analysis |
| `/api/analyses/{id}` | DELETE | Delete analysis 🆕 |
| `/api/analyses` | DELETE | Delete all 🆕 |
| `/api/export/{id}` | GET | Export tests as ZIP |
| `/api/settings/api-keys` | GET/POST | Manage AI API keys |
| `/api/prompts` | GET/POST | Manage custom prompts |
| `/api/settings/git-config` | GET/POST | Git configuration 🆕 |
| `/api/settings/git-config/test` | POST | Test Git connection 🆕 |
| `/api/repo-mappings` | GET/POST | Repository mappings 🆕 |
| `/api/repo-mappings/{name}` | DELETE | Delete mapping 🆕 |

---

## 🏗️ Architecture

### Technology Stack

#### Backend
- **FastAPI** - Modern Python web framework
- **SQLite** - Lightweight database
- **JWT** - Authentication
- **OpenAI API** - GPT models
- **Anthropic API** - Claude models
- **Google AI API** - Gemini models
- **Python 3.8+** - Backend language

#### Frontend
- **React 19** - UI library
- **shadcn/ui** - Component library
- **Tailwind CSS** - Styling
- **React Router v7** - Routing
- **Axios** - HTTP client

#### AI Models
- **OpenAI GPT-4o** / GPT-4o-mini
- **Anthropic Claude 3.7** / Claude 4 Sonnet
- **Google Gemini 2.0 Flash**

### Project Structure
```
chaturLog/
├── backend/
│   ├── server.py              # Main API server
│   ├── database.py            # Database management (with repo_mappings)
│   ├── auth.py                # Authentication
│   ├── services/
│   │   ├── ai_analyzer.py     # AI analysis service
│   │   ├── test_generator.py  # Test generation
│   │   ├── git_detector.py    # Git repository detection 🆕
│   │   ├── git_client.py      # Git provider API client 🆕
│   │   ├── context_analyzer.py # Project context analysis
│   │   └── log_chunker.py     # Large file processing
│   └── uploads/               # Uploaded files
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/            # shadcn/ui components
│   │   │   ├── ErrorBoundary.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   └── LoadingStates.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx  # With repo mapping dialog 🆕
│   │   │   ├── Settings.jsx   # Git integration + mappings 🆕
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   └── utils/
│   │       ├── api.js         # With repo mapping APIs 🆕
│   │       └── fileValidation.js
│   └── package.json
│
├── tests/
│   └── test-apollo-server.json # Sample log file
│
└── Documentation (12+ guides)
```

---

## 🎨 Screenshots

### Dashboard - Upload & Analyze
- Drag-and-drop file upload
- AI model selection (OpenAI, Claude, Gemini)
- Test framework selection (Jest, JUnit, pytest, Mocha, Cypress, RSpec)
- Real-time analysis progress
- **Git repository detection** 🆕

### Repository Confirmation Dialog 🆕
- Detected service name display
- Smart repository suggestions (multiple variants)
- Custom repository input option
- Organization name input
- Live preview of final repository
- One-time setup per service

### Results Display
- Error patterns with severity badges
- Frequency tracking
- API endpoint extraction
- Generated test cases with download
- **Git context information** 🆕
- Export tests as ZIP

### Settings - Git Integration 🆕
- Git provider configuration (GitHub, GitLab, Bitbucket)
- Personal access token setup
- Repository mappings management
- View/delete saved mappings
- Test connection functionality

### History
- All past analyses
- Status tracking
- Quick access to results
- Search and filter capabilities

---

## 🔐 Security

- ✅ JWT token authentication
- ✅ Password hashing (SHA-256)
- ✅ File type validation
- ✅ File size limits (50MB)
- ✅ CORS protection
- ✅ Input sanitization
- ✅ Secure file storage

---

## 🧪 Testing

### Supported Test Frameworks

#### Jest (JavaScript/TypeScript)
```javascript
import request from 'supertest';

describe('API Tests', () => {
  it('should handle error scenario', async () => {
    const response = await request(app).get('/api/endpoint');
    expect(response.status).toBe(200);
  });
});
```

#### JUnit (Java)
```java
import org.junit.Test;
import static org.junit.Assert.*;

public class ApiTest {
  @Test
  public void testErrorScenario() {
    assertTrue(true);
  }
}
```

#### pytest (Python)
```python
import pytest

def test_error_scenario():
    assert True
```

---

## 📊 Use Cases

### Development Teams
- Analyze production logs after deployments
- Generate regression tests from real errors
- Track error patterns over time

### QA Engineers
- Generate comprehensive test suites
- Cover edge cases from production logs
- Automate test case creation

### DevOps
- Monitor application health
- Identify recurring issues
- Track system performance

---

## 🚧 Roadmap

### ✅ Recently Completed
- [x] **Git Integration** - Smart repository detection from logs
- [x] **Repository Mappings** - Service-to-repo automatic mapping
- [x] **Custom AI Prompts** - Personalize analysis behavior
- [x] **More Test Frameworks** - Added Mocha, Cypress, RSpec
- [x] **Export Tests** - Download as ZIP file
- [x] **Large File Support** - Chunking & summarization pipeline
- [x] **Search & Filter** - History search and filtering

### Short-term
- [ ] Batch file analysis
- [ ] Export reports (PDF/Excel)
- [ ] Team collaboration features
- [ ] Git-enhanced test generation (using repo context)

### Medium-term
- [ ] Real-time analysis with WebSockets
- [ ] Dashboard analytics with charts
- [ ] CI/CD pipeline integration
- [ ] Integration with log providers (Datadog, Splunk)

### Long-term
- [ ] ML training from user feedback
- [ ] Shared pattern library
- [ ] Auto-fix code generation
- [ ] Enterprise features (SSO, RBAC)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **shadcn/ui** - Beautiful UI components
- **FastAPI** - Modern Python web framework
- **OpenAI, Anthropic, Google** - AI model providers
- Open source community for amazing tools and libraries

---

## 📞 Support

For issues or questions:
1. Check the [Setup Guide](./SETUP_GUIDE.md)
2. Review [Complete Analysis](./COMPLETE_APPLICATION_ANALYSIS.md)
3. Open an issue on GitHub

---

## 🎉 Get Started

Ready to analyze your logs? Follow the [Quick Start](#-quick-start) guide and start generating tests in minutes!

**Happy coding!** 🚀

---

<div align="center">

Made with ❤️ by developers, for developers

</div>
