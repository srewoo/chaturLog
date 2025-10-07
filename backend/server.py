from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Header, Depends
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
import shutil
import zipfile
import io

# Import custom modules
from database import init_db, migrate_database, get_db, hash_password, verify_password, encrypt_token, decrypt_token
from auth import create_access_token, get_current_user_id
from services.ai_analyzer import LogAnalyzer
from services.test_generator import TestGenerator
from services.test_validator import TestValidator
from services.context_analyzer import ContextAnalyzer
from services.log_chunker import LogChunker, ChunkSummarizer, ChunkIndex
from services.git_client import GitClient
from services.git_detector import GitRepositoryDetector

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Initialize database
init_db()
migrate_database()

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

# 🆕 ANALYSIS CONTEXT CACHE - Saves 70% tokens on multi-framework generation!
class AnalysisContextCache:
    """
    Simple in-memory cache for analysis context
    Reuses analysis data across multiple test framework generations
    """
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        from datetime import timedelta
        self.ttl = timedelta(seconds=ttl_seconds)
    
    def get(self, analysis_id: int) -> Optional[Dict]:
        """Get cached context if exists and not expired"""
        if analysis_id in self.cache:
            data, timestamp = self.cache[analysis_id]
            if datetime.now() - timestamp < self.ttl:
                logger.info(f"✅ Cache HIT for analysis {analysis_id} - Saving tokens!")
                return data
            else:
                del self.cache[analysis_id]  # Expired
        return None
    
    def set(self, analysis_id: int, data: Dict):
        """Cache analysis context"""
        self.cache[analysis_id] = (data, datetime.now())
        logger.info(f"💾 Cached analysis {analysis_id} context ({len(self.cache)} in cache)")
    
    def clear(self, analysis_id: int = None):
        """Clear cache for specific analysis or all"""
        if analysis_id:
            self.cache.pop(analysis_id, None)
        else:
            self.cache.clear()
    
    def size(self):
        return len(self.cache)

# Global cache instance (1 hour TTL)
analysis_cache = AnalysisContextCache(ttl_seconds=3600)

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

class CustomPromptRequest(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    analysis_prompt: Optional[str] = None
    test_generation_prompt: Optional[str] = None
    is_default: bool = False

class GitConfigRequest(BaseModel):
    git_provider: str  # github, gitlab, bitbucket
    repository: Optional[str] = None
    git_token: str
    default_branch: str = 'main'
    enabled: bool = True

class RepoMappingRequest(BaseModel):
    service_name: str
    repository: str  # org/repo format

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

# ==================== Git Configuration Routes ====================

@api_router.get("/settings/git-config")
async def get_git_config(user_id: int = Depends(get_current_user)):
    """Get user's Git configuration (token is masked for security)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT git_provider, repository, git_token_encrypted, default_branch, enabled FROM git_configs WHERE user_id = ?",
            (user_id,)
        )
        config = cursor.fetchone()
        conn.close()
        
        if config:
            # Mask token for display
            token = decrypt_token(config["git_token_encrypted"])
            masked_token = "***" + token[-4:] if token and len(token) > 4 else "***"
            
            return {
                "success": True,
                "git_config": {
                    "git_provider": config["git_provider"],
                    "repository": config["repository"],
                    "git_token": masked_token,
                    "default_branch": config["default_branch"],
                    "enabled": bool(config["enabled"])
                }
            }
        else:
            return {
                "success": True,
                "git_config": {
                    "git_provider": "",
                    "repository": "",
                    "git_token": "",
                    "default_branch": "main",
                    "enabled": False
                }
            }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/settings/git-config")
async def save_git_config(request: GitConfigRequest, user_id: int = Depends(get_current_user)):
    """Save or update user's Git configuration"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Validate provider
        if request.git_provider not in ['github', 'gitlab', 'bitbucket']:
            raise HTTPException(status_code=400, detail="Invalid Git provider. Use 'github', 'gitlab', or 'bitbucket'")
        
        # Encrypt token
        encrypted_token = encrypt_token(request.git_token)
        
        # Check if config exists
        cursor.execute("SELECT id FROM git_configs WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()
        
        if existing:
            # Update existing config
            cursor.execute(
                """UPDATE git_configs 
                   SET git_provider = ?, repository = ?, git_token_encrypted = ?, 
                       default_branch = ?, enabled = ?, updated_at = CURRENT_TIMESTAMP 
                   WHERE user_id = ?""",
                (request.git_provider, request.repository, encrypted_token, 
                 request.default_branch, request.enabled, user_id)
            )
        else:
            # Insert new config
            cursor.execute(
                """INSERT INTO git_configs 
                   (user_id, git_provider, repository, git_token_encrypted, default_branch, enabled) 
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, request.git_provider, request.repository, encrypted_token, 
                 request.default_branch, request.enabled)
            )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Git configuration saved successfully"
        }
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/settings/git-config/test")
async def test_git_connection(user_id: int = Depends(get_current_user)):
    """Test Git token validity using user API (more reliable)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT git_provider, repository, git_token_encrypted FROM git_configs WHERE user_id = ? AND enabled = 1",
            (user_id,)
        )
        config = cursor.fetchone()
        conn.close()
        
        if not config:
            return {
                "success": False,
                "message": "No Git configuration found. Please configure Git integration first."
            }
        
        # Decrypt token
        token = decrypt_token(config["git_token_encrypted"])
        if not token:
            return {
                "success": False,
                "message": "Invalid token configuration"
            }
        
        # Test token using /user API (no repository required - more reliable!)
        git_client = GitClient(
            provider=config["git_provider"],
            token=token,
            repository="dummy/dummy"  # Not used for token test
        )
        
        result = git_client.test_token()
        
        # If token is valid and repository is configured, also test repository access
        if result['success'] and config["repository"]:
            git_client.repository = config["repository"]
            repo_test = git_client.test_connection()
            result['repository_access'] = repo_test['success']
            if repo_test['success']:
                result['repository_info'] = repo_test['repository_info']
        
        return result
        
    except Exception as e:
        conn.close()
        return {
            "success": False,
            "message": f"Error testing connection: {str(e)}"
        }

# ==================== Repository Mapping Routes ====================

@api_router.get("/repo-mappings")
async def get_repo_mappings(user_id: int = Depends(get_current_user)):
    """Get all repository mappings for the user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT service_name, repository, created_at FROM repo_mappings WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        )
        mappings = cursor.fetchall()
        conn.close()
        
        return {
            "success": True,
            "mappings": [
                {
                    "service_name": m["service_name"],
                    "repository": m["repository"],
                    "created_at": m["created_at"]
                }
                for m in mappings
            ]
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/repo-mappings")
async def save_repo_mapping(request: RepoMappingRequest, user_id: int = Depends(get_current_user)):
    """Save a repository mapping (service name → repository)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Validate repository format (should be org/repo)
        if '/' not in request.repository:
            raise HTTPException(status_code=400, detail="Repository must be in 'org/repo' format")
        
        # Insert or replace mapping
        cursor.execute(
            """INSERT OR REPLACE INTO repo_mappings (user_id, service_name, repository, created_at) 
               VALUES (?, ?, ?, CURRENT_TIMESTAMP)""",
            (user_id, request.service_name, request.repository)
        )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Repository mapping saved: {request.service_name} → {request.repository}"
        }
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/repo-mappings/{service_name}")
async def delete_repo_mapping(service_name: str, user_id: int = Depends(get_current_user)):
    """Delete a repository mapping"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM repo_mappings WHERE user_id = ? AND service_name = ?",
            (user_id, service_name)
        )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Repository mapping deleted for {service_name}"
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

# ==================== Custom Prompts Routes ====================

@api_router.get("/prompts")
async def get_prompts(user_id: int = Depends(get_current_user)):
    """Get all custom prompts for user"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM custom_prompts WHERE user_id = ? ORDER BY is_default DESC, created_at DESC",
            (user_id,)
        )
        prompts = cursor.fetchall()
        conn.close()
        
        return {
            "success": True,
            "prompts": [dict(p) for p in prompts]
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: int, user_id: int = Depends(get_current_user)):
    """Get specific custom prompt"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM custom_prompts WHERE id = ? AND user_id = ?",
            (prompt_id, user_id)
        )
        prompt = cursor.fetchone()
        conn.close()
        
        if not prompt:
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        return {
            "success": True,
            "prompt": dict(prompt)
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/prompts")
async def create_prompt(request: CustomPromptRequest, user_id: int = Depends(get_current_user)):
    """Create new custom prompt"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # If setting as default, unset other defaults
        if request.is_default:
            cursor.execute(
                "UPDATE custom_prompts SET is_default = 0 WHERE user_id = ?",
                (user_id,)
            )
        
        # Insert new prompt
        cursor.execute(
            """INSERT INTO custom_prompts 
            (user_id, name, description, system_prompt, analysis_prompt, test_generation_prompt, is_default) 
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (user_id, request.name, request.description, request.system_prompt,
             request.analysis_prompt, request.test_generation_prompt, request.is_default)
        )
        
        prompt_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "prompt_id": prompt_id,
            "message": "Custom prompt created successfully"
        }
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.put("/prompts/{prompt_id}")
async def update_prompt(
    prompt_id: int,
    request: CustomPromptRequest,
    user_id: int = Depends(get_current_user)
):
    """Update custom prompt"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Verify ownership
        cursor.execute(
            "SELECT id FROM custom_prompts WHERE id = ? AND user_id = ?",
            (prompt_id, user_id)
        )
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        # If setting as default, unset other defaults
        if request.is_default:
            cursor.execute(
                "UPDATE custom_prompts SET is_default = 0 WHERE user_id = ? AND id != ?",
                (user_id, prompt_id)
            )
        
        # Update prompt
        cursor.execute(
            """UPDATE custom_prompts 
            SET name = ?, description = ?, system_prompt = ?, analysis_prompt = ?, 
                test_generation_prompt = ?, is_default = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?""",
            (request.name, request.description, request.system_prompt,
             request.analysis_prompt, request.test_generation_prompt,
             request.is_default, prompt_id, user_id)
        )
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Custom prompt updated successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: int, user_id: int = Depends(get_current_user)):
    """Delete custom prompt"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM custom_prompts WHERE id = ? AND user_id = ?",
            (prompt_id, user_id)
        )
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Prompt not found")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "Custom prompt deleted successfully"
        }
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

async def process_with_chunking(
    analysis_id: int,
    file_path: str,
    filename: str,
    user_id: int,
    ai_model: str,
    api_key: str,
    cursor,
    conn
) -> Dict[str, Any]:
    """
    Process large log files using chunking pipeline
    
    Stream → Chunk → Summarize → Index → Aggregate
    Handles logs of ANY size without token limits!
    """
    import json
    
    print(f"🚀 Starting chunking pipeline for {filename}...")
    
    try:
        # Initialize chunking services
        chunker = LogChunker(chunk_size=10000)  # 10k chars = ~2.5k tokens
        summarizer = ChunkSummarizer(ai_model="gpt-4o-mini", api_key=api_key)  # Use mini for cost efficiency!
        chunk_index = ChunkIndex(conn)
        
        # Stream and summarize chunks
        chunk_count = 0
        total_errors = []
        total_api_calls = []
        total_perf_issues = []
        all_patterns = set()
        
        for chunk in chunker.stream_chunks(file_path):
            chunk_count += 1
            print(f"  📦 Processing chunk {chunk_count} (lines {chunk['start_line']}-{chunk['end_line']})...")
            
            try:
                # Summarize chunk
                summary = await summarizer.summarize_chunk(chunk)
                
                # Store in database
                chunk_index.store_chunk_summary(analysis_id, summary)
                
                # Aggregate data
                total_errors.extend(summary.get('errors_found', []))
                total_api_calls.extend(summary.get('api_calls', []))
                total_perf_issues.extend(summary.get('performance_issues', []))
                all_patterns.update(summary.get('key_patterns', []))
                
            except Exception as e:
                print(f"  ⚠️ Error processing chunk {chunk_count}: {e}")
                # Continue with next chunk
                continue
        
        print(f"✅ Processed {chunk_count} chunks successfully!")
        
        # Aggregate all summaries from database
        aggregated = chunk_index.aggregate_summaries(analysis_id)
        
        # Store aggregated analysis
        cursor.execute(
            "UPDATE analyses SET status = ?, completed_at = ?, analysis_data = ? WHERE id = ?",
            ("completed", datetime.now().isoformat(), json.dumps(aggregated), analysis_id)
        )
        
        # Store patterns (for backward compatibility)
        for error in aggregated.get('error_patterns', []):
            cursor.execute(
                "INSERT INTO patterns (analysis_id, pattern_type, description, severity) VALUES (?, ?, ?, ?)",
                (analysis_id, error.get('type', 'error'), error.get('description', ''), error.get('severity', 'medium'))
            )
        
        conn.commit()
        
        return {
            "success": True,
            "analysis_id": analysis_id,
            "chunks_processed": chunk_count,
            "analysis": aggregated,
            "message": f"Analysis completed using chunking pipeline ({chunk_count} chunks processed)"
        }
        
    except Exception as e:
        print(f"❌ Chunking pipeline error: {e}")
        cursor.execute("UPDATE analyses SET status = ? WHERE id = ?", ("failed", analysis_id))
        conn.commit()
        raise HTTPException(status_code=500, detail=f"Chunking pipeline error: {str(e)}")


@api_router.post("/analyze/{analysis_id}")
async def analyze_logs(
    analysis_id: int,
    request: AnalyzeRequest,
    user_id: int = Depends(get_current_user)
):
    """
    Analyze uploaded log file using AI
    
    Uses intelligent routing:
    - Small logs (< 100k chars): Single-pass analysis
    - Large logs (>= 100k chars): Chunking pipeline (scalable!)
    """
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
        
        # Check file size to determine processing strategy
        file_size = file_path.stat().st_size
        
        # Update status
        cursor.execute(
            "UPDATE analyses SET status = ?, ai_model = ? WHERE id = ?",
            ("analyzing", request.ai_model, analysis_id)
        )
        conn.commit()
        
        # Get user's API key
        api_key = get_user_api_key(user_id, request.ai_model)
        
        # Route to appropriate processing method
        CHUNK_THRESHOLD = 100000  # 100k chars (~25k tokens)
        
        if file_size >= CHUNK_THRESHOLD:
            # Use chunking pipeline for large files
            print(f"📊 Large log detected ({file_size} bytes), using chunking pipeline...")
            result = await process_with_chunking(
                analysis_id=analysis_id,
                file_path=str(file_path),
                filename=analysis["filename"],
                user_id=user_id,
                ai_model=request.ai_model,
                api_key=api_key,
                cursor=cursor,
                conn=conn
            )
            return result
        else:
            # Use single-pass for small files
            print(f"📄 Small log detected ({file_size} bytes), using single-pass analysis...")
        
        # Single-pass analysis (existing code)
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            log_content = f.read()
        
        # Detect Git repository from log content
        git_detector = GitRepositoryDetector()
        git_detection = git_detector.detect_repository(log_content, analysis["filename"])
        
        # Check for user-provided repository mappings
        detected_repo = git_detection.get('repository')
        if not detected_repo and git_detection.get('service_name'):
            # Check if user has a mapping for this service
            cursor.execute(
                "SELECT repository FROM repo_mappings WHERE user_id = ? AND service_name = ?",
                (user_id, git_detection['service_name'])
            )
            mapping = cursor.fetchone()
            if mapping:
                detected_repo = mapping['repository']
                git_detection['repository'] = detected_repo
                git_detection['confidence'] = 'high'  # User confirmed
                git_detection['detection_methods'].append('user_mapping')
        
        # Store Git detection info
        git_info = {
            'detected_repository': detected_repo,
            'git_service': git_detection.get('git_service'),
            'commit_hash': git_detection.get('commit_hash'),
            'branch': git_detection.get('branch'),
            'service_name': git_detection.get('service_name'),
            'repository_suggestions': git_detection.get('repository_suggestions', []),
            'confidence': git_detection.get('confidence'),
            'detection_methods': git_detection.get('detection_methods', [])
        }
        logger.info(f"Git detection result: {git_info}")
        
        # Get user's default custom prompt if exists
        cursor.execute(
            "SELECT system_prompt, analysis_prompt FROM custom_prompts WHERE user_id = ? AND is_default = 1",
            (user_id,)
        )
        custom_prompt_row = cursor.fetchone()
        
        system_prompt = None
        analysis_prompt = None
        if custom_prompt_row:
            system_prompt = custom_prompt_row["system_prompt"]
            analysis_prompt = custom_prompt_row["analysis_prompt"]
        
        # Analyze with AI
        analyzer = LogAnalyzer(ai_model=request.ai_model, api_key=api_key)
        result = await analyzer.analyze_logs(
            log_content, 
            analysis["filename"],
            custom_prompt=analysis_prompt,
            system_prompt=system_prompt
        )
        
        if result["success"]:
            # Store patterns
            analysis_data = result["analysis"]
            
            # Add Git detection info to analysis data
            analysis_data['git_info'] = git_info
            
            # Store error patterns
            if "error_patterns" in analysis_data:
                for pattern in analysis_data["error_patterns"]:
                    cursor.execute(
                        "INSERT INTO patterns (analysis_id, pattern_type, description, severity, frequency) VALUES (?, ?, ?, ?, ?)",
                        (analysis_id, pattern.get("type", "error"), pattern.get("description", ""), 
                         pattern.get("severity", "medium"), pattern.get("frequency", 1))
                    )
            
            # Update analysis status and store complete analysis JSON
            import json
            cursor.execute(
                "UPDATE analyses SET status = ?, completed_at = ?, analysis_data = ? WHERE id = ?",
                ("completed", datetime.now().isoformat(), json.dumps(analysis_data), analysis_id)
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
        
        # Get patterns (for backward compatibility)
        cursor.execute(
            "SELECT * FROM patterns WHERE analysis_id = ?",
            (analysis_id,)
        )
        patterns = cursor.fetchall()
        
        # Load complete analysis JSON if available (NEW!)
        import json
        complete_analysis = {}
        if analysis["analysis_data"]:
            try:
                complete_analysis = json.loads(analysis["analysis_data"])
            except json.JSONDecodeError:
                print("⚠️ Warning: Could not parse stored analysis_data JSON")
                complete_analysis = {}
        
        # 🆕 CHECK CACHE FIRST - Reuse analysis context if available
        cached_context = analysis_cache.get(analysis_id)
        if cached_context:
            # Use cached analysis data
            analysis_data = cached_context
            logger.info(f"🚀 Using cached context for analysis {analysis_id} - Saving ~5k tokens!")
        else:
            # Read and prepare analysis context (will be cached)
            logger.info(f"📖 Reading log file for analysis {analysis_id} - First generation")
            
        # Read log file content with smart sampling (CRITICAL FIX!)
        log_content = ""
        log_excerpt = ""
        log_sample_for_testing = ""
        
        if not cached_context:  # Only read if not cached
            try:
                with open(analysis["file_path"], 'r', encoding='utf-8') as f:
                    log_content = f.read()
                    
                    # 🆕 SMART ERROR-AWARE EXCERPT (10k chars - 5x improvement!)
                    def smart_error_excerpt(content: str, max_chars: int = 10000) -> str:
                        """Extract log excerpt prioritizing error sections"""
                        if len(content) <= max_chars:
                            return content
                        
                        # Find error keywords
                        error_patterns = [
                            r'\berror\b', r'\bfail(ed|ure)?\b', r'\bexception\b', r'\bcrash(ed)?\b',
                            r'\bwarn(ing)?\b', r'\bcritical\b', r'\b4\d{2}\b', r'\b5\d{2}\b'
                        ]
                        
                        # Find first error position
                        import re
                        first_error_pos = len(content)
                        for pattern in error_patterns:
                            match = re.search(pattern, content, re.IGNORECASE)
                            if match:
                                first_error_pos = min(first_error_pos, match.start())
                        
                        # Extract context around first error
                        if first_error_pos < len(content):
                            start = max(0, first_error_pos - 2000)
                            return content[start:start + max_chars]
                        
                        # Fallback: first 10k
                        return content[:max_chars]
                    
                    log_excerpt = smart_error_excerpt(log_content, 10000)  # 🆕 10k chars, error-aware!
                    
                    # Smart sampling for test generation (avoid token limits!)
                    # For test generation, we only need representative samples
                    max_test_chars = 15000  # ~4k tokens (safe limit)
                    
                    if len(log_content) <= max_test_chars:
                        log_sample_for_testing = log_content
                    else:
                        # Sample from beginning, middle, and end
                        chunk_size = max_test_chars // 3
                        start = log_content[:chunk_size]
                        middle_pos = len(log_content) // 2 - chunk_size // 2
                        middle = log_content[middle_pos:middle_pos + chunk_size]
                        end = log_content[-chunk_size:]
                        
                        log_sample_for_testing = f"""{start}

... [Log continues - {len(log_content) - 2*chunk_size} chars omitted] ...

{middle}

... [Showing end of log] ...

{end}"""
                    
                    print(f"📊 Log size: {len(log_content)} chars → Excerpt: {len(log_excerpt)} | Sample: {len(log_sample_for_testing)}")
            except Exception as e:
                print(f"⚠️ Warning: Could not read log file: {e}")
            
            # Prepare comprehensive analysis data (only if not cached)
            analysis_data = {
                # Patterns (backward compatibility)
                "patterns": [dict(p) for p in patterns],
                
                # Complete AI analysis results (NEW!)
                "error_patterns": complete_analysis.get("error_patterns", []),
                "api_endpoints": complete_analysis.get("api_endpoints", []),
                "performance_issues": complete_analysis.get("performance_issues", []),
                "business_impact": complete_analysis.get("business_impact", {}),
                "test_scenarios": complete_analysis.get("test_scenarios", []),
                
                # Log file information (NEW!)
                "filename": analysis["filename"],
                "log_file_path": analysis["file_path"],
                "log_content": log_sample_for_testing,  # SAMPLED log content (token-safe!)
                "log_excerpt": log_excerpt,  # Error-aware 10k excerpt!
                "log_size_full": len(log_content),  # Total size for context
            }
            
            # 🆕 CACHE THE ANALYSIS DATA for future test generations
            analysis_cache.set(analysis_id, analysis_data)
            logger.info(f"💾 Cached analysis data for {analysis_id} (reusable for all frameworks!)")
        
        # Get user's API key
        api_key = get_user_api_key(user_id, analysis["ai_model"])
        
        # Get user's default custom prompt if exists
        cursor.execute(
            "SELECT system_prompt, test_generation_prompt FROM custom_prompts WHERE user_id = ? AND is_default = 1",
            (user_id,)
        )
        custom_prompt_row = cursor.fetchone()
        
        system_prompt = None
        test_gen_prompt = None
        if custom_prompt_row:
            system_prompt = custom_prompt_row["system_prompt"]
            test_gen_prompt = custom_prompt_row["test_generation_prompt"]
        
        # Analyze project context for context-aware test generation
        context_analyzer = ContextAnalyzer()
        project_context = context_analyzer.analyze_project_context(analysis["file_path"])
        context_summary = context_analyzer.format_context_for_prompt(project_context)
        
        # Add context to analysis data
        analysis_data['project_context'] = context_summary
        analysis_data['testing_framework_detected'] = project_context.get('testing_framework')
        
        # Generate tests with context awareness
        generator = TestGenerator(ai_model=analysis["ai_model"], api_key=api_key)
        test_cases = await generator.generate_tests(
            analysis_data, 
            request.framework,
            custom_prompt=test_gen_prompt,
            system_prompt=system_prompt
        )
        
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

@api_router.delete("/analyses/{analysis_id}")
async def delete_analysis(analysis_id: int, user_id: int = Depends(get_current_user)):
    """Delete a specific analysis (non-recoverable)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get analysis to check ownership and get file path
        cursor.execute(
            "SELECT * FROM analyses WHERE id = ? AND user_id = ?",
            (analysis_id, user_id)
        )
        analysis = cursor.fetchone()
        
        if not analysis:
            conn.close()
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Delete associated records (cascade)
        cursor.execute("DELETE FROM patterns WHERE analysis_id = ?", (analysis_id,))
        cursor.execute("DELETE FROM test_cases WHERE analysis_id = ?", (analysis_id,))
        cursor.execute("DELETE FROM chunk_summaries WHERE analysis_id = ?", (analysis_id,))
        
        # Delete analysis record
        cursor.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        
        # Delete log file if it exists
        import os
        file_path = analysis["file_path"]
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Analysis deleted successfully"
        }
    except HTTPException:
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Error deleting analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/analyses")
async def delete_all_analyses(user_id: int = Depends(get_current_user)):
    """Delete all analyses for the current user (non-recoverable)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get all analyses for user to delete files
        cursor.execute(
            "SELECT id, file_path FROM analyses WHERE user_id = ?",
            (user_id,)
        )
        analyses = cursor.fetchall()
        
        if not analyses:
            conn.close()
            return {
                "success": True,
                "message": "No analyses to delete",
                "deleted_count": 0
            }
        
        analysis_ids = [a["id"] for a in analyses]
        
        # Delete associated records for all analyses
        for analysis_id in analysis_ids:
            cursor.execute("DELETE FROM patterns WHERE analysis_id = ?", (analysis_id,))
            cursor.execute("DELETE FROM test_cases WHERE analysis_id = ?", (analysis_id,))
            cursor.execute("DELETE FROM chunk_summaries WHERE analysis_id = ?", (analysis_id,))
        
        # Delete all analysis records
        cursor.execute("DELETE FROM analyses WHERE user_id = ?", (user_id,))
        
        # Delete all log files
        import os
        deleted_files = 0
        for analysis in analyses:
            file_path = analysis["file_path"]
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    deleted_files += 1
                except Exception as e:
                    logger.warning(f"Failed to delete file {file_path}: {e}")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"All analyses deleted successfully",
            "deleted_count": len(analyses),
            "deleted_files": deleted_files
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        logger.error(f"Error deleting all analyses: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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