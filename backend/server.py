from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Header, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import shutil
import zipfile
import io

# Import custom modules
from database import init_db, get_db, hash_password, verify_password
from auth import create_access_token, get_current_user_id
from services.ai_analyzer import LogAnalyzer
from services.test_generator import TestGenerator
from services.test_validator import TestValidator

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize database
init_db()

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Create the main app
app = FastAPI()

# Create a router with /api prefix
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== Models ====================

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class AnalyzeRequest(BaseModel):
    ai_model: str = "gpt-4o"

class GenerateTestsRequest(BaseModel):
    framework: str  # jest, junit, pytest

class AuthResponse(BaseModel):
    access_token: str
    user_id: int
    email: str

class ApiKeysRequest(BaseModel):
    openai_key: Optional[str] = None
    anthropic_key: Optional[str] = None
    google_key: Optional[str] = None

# ==================== Auth Dependency ====================

def get_current_user(authorization: Optional[str] = Header(None)) -> int:
    """Dependency to get current user from token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = authorization.replace("Bearer ", "")
        user_id = get_current_user_id(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

# ==================== Auth Routes ====================

@api_router.post("/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register new user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if user exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (request.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        password_hash = hash_password(request.password)
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (request.email, password_hash)
        )
        conn.commit()
        
        user_id = cursor.lastrowid
        
        # Create token
        token = create_access_token({"user_id": user_id, "email": request.email})
        
        conn.close()
        
        return AuthResponse(
            access_token=token,
            user_id=user_id,
            email=request.email
        )
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Login user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, email, password_hash FROM users WHERE email = ?", (request.email,))
        user = cursor.fetchone()
        
        if not user or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create token
        token = create_access_token({"user_id": user["id"], "email": user["email"]})
        
        conn.close()
        
        return AuthResponse(
            access_token=token,
            user_id=user["id"],
            email=user["email"]
        )
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Settings Routes ====================

@api_router.get("/settings/api-keys")
async def get_api_keys(user_id: int = Depends(get_current_user)):
    """Get user's API keys (masked for security)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT openai_key, anthropic_key, google_key FROM api_keys WHERE user_id = ?", (user_id,))
        keys = cursor.fetchone()
        conn.close()
        
        if keys:
            # Mask keys for display (show only last 4 characters)
            def mask_key(key):
                if not key:
                    return ""
                return "***" + key[-4:] if len(key) > 4 else "***"
            
            return {
                "success": True,
                "api_keys": {
                    "openai_key": mask_key(keys["openai_key"]),
                    "anthropic_key": mask_key(keys["anthropic_key"]),
                    "google_key": mask_key(keys["google_key"])
                }
            }
        else:
            return {
                "success": True,
                "api_keys": {
                    "openai_key": "",
                    "anthropic_key": "",
                    "google_key": ""
                }
            }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/settings/api-keys")
async def save_api_keys(request: ApiKeysRequest, user_id: int = Depends(get_current_user)):
    """Save or update user's API keys"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if keys exist
        cursor.execute("SELECT id FROM api_keys WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing keys
            cursor.execute(
                "UPDATE api_keys SET openai_key = ?, anthropic_key = ?, google_key = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (request.openai_key, request.anthropic_key, request.google_key, user_id)
            )
        else:
            # Insert new keys
            cursor.execute(
                "INSERT INTO api_keys (user_id, openai_key, anthropic_key, google_key) VALUES (?, ?, ?, ?)",
                (user_id, request.openai_key, request.anthropic_key, request.google_key)
            )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "API keys saved successfully"
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

def get_user_api_key(user_id: int, ai_model: str) -> str:
    """Get the appropriate API key for the selected AI model"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT openai_key, anthropic_key, google_key FROM api_keys WHERE user_id = ?", (user_id,))
        keys = cursor.fetchone()
        conn.close()
        
        if not keys:
            raise HTTPException(status_code=400, detail="No API keys configured. Please add your API keys in Settings.")
        
        # Determine which key to use based on model
        if "gpt" in ai_model or "openai" in ai_model:
            if not keys["openai_key"]:
                raise HTTPException(status_code=400, detail="OpenAI API key not configured. Please add it in Settings.")
            return keys["openai_key"]
        elif "claude" in ai_model or "anthropic" in ai_model:
            if not keys["anthropic_key"]:
                raise HTTPException(status_code=400, detail="Anthropic API key not configured. Please add it in Settings.")
            return keys["anthropic_key"]
        elif "gemini" in ai_model:
            if not keys["google_key"]:
                raise HTTPException(status_code=400, detail="Google AI API key not configured. Please add it in Settings.")
            return keys["google_key"]
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported AI model: {ai_model}")
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Upload & Analysis Routes ====================

@api_router.post("/upload")
async def upload_log_file(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user)
):
    """Upload log file"""
    # Validate file type
    if not file.filename.endswith(('.log', '.txt', '.json')):
        raise HTTPException(status_code=400, detail="Invalid file type. Supported: .log, .txt, .json")
    
    # Validate file size (50MB max)
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="File too large. Max size: 50MB")
    
    try:
        # Save file
        file_path = UPLOAD_DIR / f"{user_id}_{datetime.now().timestamp()}_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Create analysis record
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO analyses (user_id, filename, file_path, status) VALUES (?, ?, ?, ?)",
            (user_id, file.filename, str(file_path), "uploaded")
        )
        conn.commit()
        analysis_id = cursor.lastrowid
        conn.close()
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "filename": file.filename,
            "message": "File uploaded successfully"
        }
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/analyze/{analysis_id}")
async def analyze_logs(
    analysis_id: int,
    request: AnalyzeRequest,
    user_id: int = Depends(get_current_user)
):
    """Analyze uploaded log file using AI"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get analysis record
        cursor.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id)
        )
        analysis = cursor.fetchone()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Read log file
        file_path = Path(analysis["file_path"])
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Log file not found")
        
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            log_content = f.read()
        
        # Update status
        cursor.execute(
            "UPDATE analyses SET status = ?, ai_model = ? WHERE id = ?",
            ("analyzing", request.ai_model, analysis_id)
        )
        conn.commit()
        
        # Get user's API key
        api_key = get_user_api_key(user_id, request.ai_model)
        
        # Analyze with AI
        analyzer = LogAnalyzer(ai_model=request.ai_model, api_key=api_key)
        result = await analyzer.analyze_logs(log_content, analysis["filename"])
        
        if result["success"]:
            # Store patterns
            analysis_data = result["analysis"]
            
            # Store error patterns
            if "error_patterns" in analysis_data:
                for pattern in analysis_data["error_patterns"]:
                    cursor.execute(
                        "INSERT INTO patterns (analysis_id, pattern_type, description, severity, frequency) VALUES (?, ?, ?, ?, ?)",
                        (analysis_id, pattern.get("type", "error"), pattern.get("description", ""), 
                         pattern.get("severity", "medium"), pattern.get("frequency", 1))
                    )
            
            # Update analysis status
            cursor.execute(
                "UPDATE analyses SET status = ?, completed_at = ? WHERE id = ?",
                ("completed", datetime.now().isoformat(), analysis_id)
            )
            conn.commit()
            
            conn.close()
            
            return {
                "success": True,
                "analysis_id": analysis_id,
                "analysis": analysis_data,
                "message": "Analysis completed successfully"
            }
        else:
            cursor.execute(
                "UPDATE analyses SET status = ? WHERE id = ?",
                ("failed", analysis_id)
            )
            conn.commit()
            conn.close()
            raise HTTPException(status_code=500, detail=result.get("error", "Analysis failed"))
    
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        cursor.execute("UPDATE analyses SET status = ? WHERE id = ?", ("failed", analysis_id))
        conn.commit()
        conn.close()
        logger.error(f"Analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/generate-tests/{analysis_id}")
async def generate_tests(
    analysis_id: int,
    request: GenerateTestsRequest,
    user_id: int = Depends(get_current_user)
):
    """Generate test cases from analysis"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get analysis record
        cursor.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id)
        )
        analysis = cursor.fetchone()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        if analysis["status"] != "completed":
            raise HTTPException(status_code=400, detail="Analysis not completed yet")
        
        # Get patterns
        cursor.execute(
            "SELECT * FROM patterns WHERE analysis_id = ?",
            (analysis_id,)
        )
        patterns = cursor.fetchall()
        
        # Prepare analysis data
        analysis_data = {
            "patterns": [dict(p) for p in patterns],
            "filename": analysis["filename"]
        }
        
        # Get user's API key
        api_key = get_user_api_key(user_id, analysis["ai_model"])
        
        # Generate tests
        generator = TestGenerator(ai_model=analysis["ai_model"], api_key=api_key)
        test_cases = await generator.generate_tests(analysis_data, request.framework)
        
        # Validate and store test cases
        validator = TestValidator()
        validated_cases = []
        
        for test_case in test_cases:
            test_code = test_case.get("test_code", "")
            
            # Validate test code
            validation_result = validator.validate_test_code(test_code, request.framework)
            quality_score = validator.calculate_quality_score(validation_result)
            
            # Add validation info to test case
            test_case["validation"] = validation_result
            test_case["quality_score"] = quality_score
            validated_cases.append(test_case)
            
            # Store in database
            cursor.execute(
                "INSERT INTO test_cases (analysis_id, framework, test_code, risk_score, priority, description) VALUES (?, ?, ?, ?, ?, ?)",
                (analysis_id, request.framework, test_code, 
                 test_case.get("risk_score", 0.5), test_case.get("priority", "medium"),
                 test_case.get("description", ""))
            )
        
        conn.commit()
        conn.close()
        
        # Calculate validation summary
        valid_count = sum(1 for tc in validated_cases if tc["validation"]["valid"])
        avg_quality = sum(tc["quality_score"] for tc in validated_cases) / len(validated_cases) if validated_cases else 0
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "framework": request.framework,
            "test_cases": validated_cases,
            "validation_summary": {
                "total": len(validated_cases),
                "valid": valid_count,
                "invalid": len(validated_cases) - valid_count,
                "average_quality_score": round(avg_quality, 2)
            },
            "message": f"Generated {len(validated_cases)} test cases ({valid_count} valid)"
        }
    
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        logger.error(f"Test generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/analyses")
async def get_analyses(user_id: int = Depends(get_current_user)):
    """Get all analyses for user"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, filename, status, ai_model, created_at, completed_at FROM analyses WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,)
    )
    analyses = cursor.fetchall()
    conn.close()
    
    return {
        "success": True,
        "analyses": [dict(a) for a in analyses]
    }

@api_router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: int, user_id: int = Depends(get_current_user)):
    """Get specific analysis details"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
        (analysis_id, user_id)
    )
    analysis = cursor.fetchone()
    
    if not analysis:
        conn.close()
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    # Get patterns
    cursor.execute("SELECT * FROM patterns WHERE analysis_id = ?", (analysis_id,))
    patterns = cursor.fetchall()
    
    # Get test cases
    cursor.execute("SELECT * FROM test_cases WHERE analysis_id = ?", (analysis_id,))
    tests = cursor.fetchall()
    
    conn.close()
    
    return {
        "success": True,
        "analysis": dict(analysis),
        "patterns": [dict(p) for p in patterns],
        "test_cases": [dict(t) for t in tests]
    }

@api_router.get("/export/{analysis_id}")
async def export_tests(analysis_id: int, user_id: int = Depends(get_current_user)):
    """Export all test cases for an analysis as a ZIP file"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Verify analysis belongs to user
        cursor.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id)
        )
        analysis = cursor.fetchone()
        
        if not analysis:
            conn.close()
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Get all test cases
        cursor.execute(
            "SELECT * FROM test_cases WHERE analysis_id = ? ORDER BY framework, priority",
            (analysis_id,)
        )
        tests = cursor.fetchall()
        conn.close()
        
        if not tests:
            raise HTTPException(status_code=404, detail="No test cases found for this analysis")
        
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Group tests by framework
            tests_by_framework = {}
            for test in tests:
                framework = test["framework"]
                if framework not in tests_by_framework:
                    tests_by_framework[framework] = []
                tests_by_framework[framework].append(test)
            
            # Add tests to ZIP, organized by framework
            for framework, framework_tests in tests_by_framework.items():
                # Determine file extension
                extensions = {
                    "jest": "test.js",
                    "mocha": "test.js",
                    "cypress": "cy.js",
                    "junit": "Test.java",
                    "pytest": "test.py",
                    "rspec": "_spec.rb"
                }
                ext = extensions.get(framework, "test.txt")
                
                for idx, test in enumerate(framework_tests, 1):
                    filename = f"{framework}/test_{idx:03d}.{ext}"
                    
                    # Add description as comment
                    content = f"""{'#' if framework in ['pytest', 'rspec'] else '//'} Test Case #{idx}
{'#' if framework in ['pytest', 'rspec'] else '//'} Priority: {test.get('priority', 'medium')}
{'#' if framework in ['pytest', 'rspec'] else '//'} Description: {test.get('description', 'N/A')}
{'#' if framework in ['pytest', 'rspec'] else '//'} Risk Score: {test.get('risk_score', 0.0)}

{test['test_code']}
"""
                    zip_file.writestr(filename, content)
            
            # Add README
            readme_content = f"""# ChaturLog - Generated Test Cases

Analysis ID: {analysis_id}
File: {analysis['filename']}
AI Model: {analysis['ai_model']}
Generated: {analysis['created_at']}

## Test Statistics
- Total Test Cases: {len(tests)}
- Frameworks: {', '.join(tests_by_framework.keys())}

## Structure
Tests are organized by framework in separate directories:
{chr(10).join(f'- {fw}/ ({len(tests_by_framework[fw])} tests)' for fw in tests_by_framework.keys())}

## Running Tests
Refer to each framework's documentation for specific setup and execution instructions.

---
Generated by ChaturLog - AI-Powered Log Analysis & Test Generation
"""
            zip_file.writestr("README.md", readme_content)
        
        # Prepare response
        zip_buffer.seek(0)
        
        return StreamingResponse(
            iter([zip_buffer.getvalue()]),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=chaturlog_tests_{analysis_id}.zip"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/")
async def root():
    return {"message": "ChaturLog API - AI-Powered Log Analysis", "version": "1.0"}

# Include router in app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)