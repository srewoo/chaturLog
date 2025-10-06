import sqlite3
import os
from pathlib import Path
from datetime import datetime
import hashlib

DATABASE_PATH = Path(__file__).parent / "chaturlog.db"

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with required tables"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Analyses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            ai_model TEXT,
            analysis_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Test cases table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS test_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            framework TEXT NOT NULL,
            test_code TEXT NOT NULL,
            risk_score REAL DEFAULT 0,
            priority TEXT DEFAULT 'medium',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        )
    ''')
    
    # Patterns table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            pattern_type TEXT NOT NULL,
            description TEXT,
            severity TEXT DEFAULT 'medium',
            frequency INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        )
    ''')
    
    # API Keys table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            openai_key TEXT,
            anthropic_key TEXT,
            google_key TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Custom Prompts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS custom_prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            system_prompt TEXT,
            analysis_prompt TEXT,
            test_generation_prompt TEXT,
            is_default BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    # Chunk Summaries table (for scalable log processing)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chunk_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER NOT NULL,
            chunk_id INTEGER NOT NULL,
            summary TEXT,
            errors_json TEXT,
            api_calls_json TEXT,
            performance_issues_json TEXT,
            key_patterns_json TEXT,
            severity TEXT,
            start_line INTEGER,
            end_line INTEGER,
            timestamp_start TEXT,
            timestamp_end TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (analysis_id) REFERENCES analyses(id)
        )
    ''')
    
    # Create indexes for performance optimization
    print("📊 Creating database indexes...")
    
    # Index for frequent user queries (analyses by user, sorted by date)
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_analyses_user_created 
        ON analyses(user_id, created_at DESC)
    ''')
    
    # Index for analysis status queries
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_analyses_status 
        ON analyses(status)
    ''')
    
    # Index for pattern lookups by analysis
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_patterns_analysis 
        ON patterns(analysis_id, severity)
    ''')
    
    # Index for test case queries by analysis
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_test_cases_analysis 
        ON test_cases(analysis_id, priority)
    ''')
    
    # Index for test framework filtering
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_test_cases_framework 
        ON test_cases(framework)
    ''')
    
    # Index for filename searches
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_analyses_filename 
        ON analyses(filename)
    ''')
    
    # Index for custom prompts by user
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_custom_prompts_user 
        ON custom_prompts(user_id, is_default)
    ''')
    
    # Index for chunk summaries (scalable log processing)
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chunk_summaries_analysis 
        ON chunk_summaries(analysis_id, severity)
    ''')
    
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_chunk_summaries_chunk 
        ON chunk_summaries(analysis_id, chunk_id)
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully with indexes")

def migrate_database():
    """Apply database migrations for schema updates"""
    conn = get_db()
    cursor = conn.cursor()
    
    print("🔄 Checking for database migrations...")
    
    # Migration 1: Add analysis_data column if it doesn't exist
    try:
        cursor.execute("SELECT analysis_data FROM analyses LIMIT 1")
        print("✅ analysis_data column already exists")
    except sqlite3.OperationalError:
        print("📝 Adding analysis_data column to analyses table...")
        cursor.execute("ALTER TABLE analyses ADD COLUMN analysis_data TEXT")
        conn.commit()
        print("✅ Added analysis_data column")
    
    conn.close()
    print("✅ Database migrations complete")

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed