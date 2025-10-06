"""
Log Chunker Service - Stream, Chunk, Summarize, and Index Pipeline

This service processes large log files by:
1. STREAM: Read log file in chunks (memory efficient)
2. CHUNK: Break into logical segments (by time, size, or pattern)
3. SUMMARIZE: AI summarizes each chunk independently
4. INDEX: Store summaries with metadata for fast retrieval
5. QUERY: Retrieve relevant chunks for test generation

Handles logs of ANY size without token limits!
"""

import re
import json
import hashlib
from typing import List, Dict, Any, Iterator, Optional
from datetime import datetime
from pathlib import Path


class LogChunker:
    """
    Intelligent log file chunking and summarization system
    
    Key Features:
    - Memory-efficient streaming (never loads entire file)
    - Smart chunking (by time, size, or log patterns)
    - Parallel-ready (can process chunks independently)
    - Incremental processing (resume from last chunk)
    """
    
    def __init__(self, chunk_size: int = 10000):
        """
        Args:
            chunk_size: Characters per chunk (~2.5k tokens, safe for AI)
        """
        self.chunk_size = chunk_size
        self.timestamp_patterns = [
            r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}',
            r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}',
            r'\[.*?\d{4}.*?\]',
        ]
    
    def stream_chunks(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """
        Stream log file in chunks (memory efficient)
        
        Yields:
            {
                'chunk_id': int,
                'content': str,
                'start_line': int,
                'end_line': int,
                'size': int,
                'timestamp_range': (start, end),
                'hash': str
            }
        """
        chunk_id = 0
        buffer = []
        buffer_size = 0
        line_number = 0
        start_line = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line_number += 1
                buffer.append(line)
                buffer_size += len(line)
                
                # Yield chunk when size limit reached
                if buffer_size >= self.chunk_size:
                    content = ''.join(buffer)
                    
                    yield {
                        'chunk_id': chunk_id,
                        'content': content,
                        'start_line': start_line,
                        'end_line': line_number,
                        'size': buffer_size,
                        'timestamp_range': self._extract_time_range(content),
                        'hash': self._hash_content(content)
                    }
                    
                    chunk_id += 1
                    buffer = []
                    buffer_size = 0
                    start_line = line_number
            
            # Yield remaining content
            if buffer:
                content = ''.join(buffer)
                yield {
                    'chunk_id': chunk_id,
                    'content': content,
                    'start_line': start_line,
                    'end_line': line_number,
                    'size': buffer_size,
                    'timestamp_range': self._extract_time_range(content),
                    'hash': self._hash_content(content)
                }
    
    def smart_chunk_by_time(self, file_path: str, time_window_seconds: int = 300) -> Iterator[Dict[str, Any]]:
        """
        Chunk logs by time windows (e.g., every 5 minutes)
        
        Better for time-series analysis and finding patterns
        """
        current_chunk = []
        current_chunk_start_time = None
        chunk_id = 0
        line_number = 0
        start_line = 0
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line_number += 1
                timestamp = self._extract_timestamp(line)
                
                if timestamp:
                    if current_chunk_start_time is None:
                        current_chunk_start_time = timestamp
                    
                    # Check if we should start a new chunk
                    time_diff = (timestamp - current_chunk_start_time).total_seconds()
                    
                    if time_diff > time_window_seconds and current_chunk:
                        # Yield current chunk
                        content = ''.join(current_chunk)
                        yield {
                            'chunk_id': chunk_id,
                            'content': content,
                            'start_line': start_line,
                            'end_line': line_number - 1,
                            'size': len(content),
                            'timestamp_range': (current_chunk_start_time, timestamp),
                            'hash': self._hash_content(content)
                        }
                        
                        chunk_id += 1
                        current_chunk = []
                        current_chunk_start_time = timestamp
                        start_line = line_number
                
                current_chunk.append(line)
            
            # Yield remaining
            if current_chunk:
                content = ''.join(current_chunk)
                yield {
                    'chunk_id': chunk_id,
                    'content': content,
                    'start_line': start_line,
                    'end_line': line_number,
                    'size': len(content),
                    'timestamp_range': (current_chunk_start_time, None),
                    'hash': self._hash_content(content)
                }
    
    def smart_chunk_by_pattern(self, file_path: str, pattern: str = r'^={3,}|^-{3,}') -> Iterator[Dict[str, Any]]:
        """
        Chunk logs by delimiter patterns (e.g., ===, ---, section headers)
        
        Good for structured logs with clear sections
        """
        current_chunk = []
        chunk_id = 0
        line_number = 0
        start_line = 0
        delimiter_pattern = re.compile(pattern)
        
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                line_number += 1
                
                # Check if this is a delimiter
                if delimiter_pattern.match(line) and current_chunk:
                    # Yield current chunk
                    content = ''.join(current_chunk)
                    yield {
                        'chunk_id': chunk_id,
                        'content': content,
                        'start_line': start_line,
                        'end_line': line_number - 1,
                        'size': len(content),
                        'timestamp_range': self._extract_time_range(content),
                        'hash': self._hash_content(content)
                    }
                    
                    chunk_id += 1
                    current_chunk = []
                    start_line = line_number
                
                current_chunk.append(line)
            
            # Yield remaining
            if current_chunk:
                content = ''.join(current_chunk)
                yield {
                    'chunk_id': chunk_id,
                    'content': content,
                    'start_line': start_line,
                    'end_line': line_number,
                    'size': len(content),
                    'timestamp_range': self._extract_time_range(content),
                    'hash': self._hash_content(content)
                }
    
    def get_chunk_statistics(self, file_path: str) -> Dict[str, Any]:
        """Get statistics about how a file would be chunked"""
        chunks = list(self.stream_chunks(file_path))
        
        return {
            'total_chunks': len(chunks),
            'total_size': sum(c['size'] for c in chunks),
            'avg_chunk_size': sum(c['size'] for c in chunks) / len(chunks) if chunks else 0,
            'min_chunk_size': min(c['size'] for c in chunks) if chunks else 0,
            'max_chunk_size': max(c['size'] for c in chunks) if chunks else 0,
            'estimated_tokens': sum(c['size'] for c in chunks) // 4,  # ~4 chars per token
            'estimated_cost_usd': (sum(c['size'] for c in chunks) // 4) * 0.000005,  # Rough estimate
        }
    
    def _extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract timestamp from log line"""
        for pattern in self.timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                try:
                    # Try common formats
                    timestamp_str = match.group()
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%m/%d/%Y %H:%M:%S']:
                        try:
                            return datetime.strptime(timestamp_str[:19], fmt)
                        except ValueError:
                            continue
                except Exception:
                    pass
        return None
    
    def _extract_time_range(self, content: str) -> tuple:
        """Extract start and end timestamps from content"""
        lines = content.split('\n')
        start_time = None
        end_time = None
        
        # Find first timestamp
        for line in lines[:min(10, len(lines))]:
            start_time = self._extract_timestamp(line)
            if start_time:
                break
        
        # Find last timestamp
        for line in reversed(lines[-min(10, len(lines)):]):
            end_time = self._extract_timestamp(line)
            if end_time:
                break
        
        return (start_time, end_time)
    
    def _hash_content(self, content: str) -> str:
        """Generate hash for chunk content (for deduplication)"""
        return hashlib.md5(content.encode()).hexdigest()[:16]


class ChunkSummarizer:
    """
    Summarize log chunks using AI
    
    Each chunk gets summarized independently, then summaries are aggregated
    """
    
    def __init__(self, ai_model: str = "gpt-4o-mini", api_key: str = None):
        """Use mini model for cost efficiency on large logs"""
        self.ai_model = ai_model
        self.api_key = api_key
        
        # Determine provider
        if "gpt" in ai_model or "openai" in ai_model:
            self.provider = "openai"
            self.model_name = ai_model if "gpt" in ai_model else "gpt-4o-mini"
        elif "claude" in ai_model:
            self.provider = "anthropic"
            self.model_name = ai_model if "claude" in ai_model else "claude-3-haiku-20240307"
        elif "gemini" in ai_model:
            self.provider = "google"
            self.model_name = ai_model if "gemini" in ai_model else "gemini-1.5-flash"
        else:
            self.provider = "openai"
            self.model_name = "gpt-4o-mini"
    
    async def summarize_chunk(self, chunk: Dict[str, Any]) -> Dict[str, Any]:
        """
        Summarize a single chunk
        
        Returns:
            {
                'chunk_id': int,
                'summary': str,
                'errors_found': List[Dict],
                'api_calls': List[Dict],
                'performance_issues': List[Dict],
                'key_patterns': List[str],
                'severity': str,
                'line_range': (int, int)
            }
        """
        prompt = f"""
Analyze this log chunk and provide a concise summary:

CHUNK ID: {chunk['chunk_id']}
LINES: {chunk['start_line']}-{chunk['end_line']}
TIME RANGE: {chunk['timestamp_range'][0]} to {chunk['timestamp_range'][1]}

LOG CONTENT:
```
{chunk['content']}
```

Provide a JSON response with:
{{
  "summary": "Brief overview of what happened in this chunk",
  "errors_found": [{{"type": "error type", "description": "what happened", "severity": "high/medium/low", "line": 123}}],
  "api_calls": [{{"method": "GET", "endpoint": "/api/users", "status": 200, "count": 5}}],
  "performance_issues": [{{"issue": "slow query", "impact": "2s delay", "line": 456}}],
  "key_patterns": ["pattern 1", "pattern 2"],
  "severity": "critical/high/medium/low/info"
}}

Focus on: errors, API endpoints, performance issues, unusual patterns.
Be concise - this is one chunk of many.
"""
        
        try:
            if self.provider == "openai":
                response = await self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = await self._call_anthropic(prompt)
            elif self.provider == "google":
                response = await self._call_google(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Parse response
            summary_data = json.loads(self._extract_json(response))
            summary_data['chunk_id'] = chunk['chunk_id']
            summary_data['line_range'] = (chunk['start_line'], chunk['end_line'])
            summary_data['timestamp_range'] = chunk['timestamp_range']
            
            return summary_data
            
        except Exception as e:
            return {
                'chunk_id': chunk['chunk_id'],
                'summary': f"Error summarizing chunk: {str(e)}",
                'errors_found': [],
                'api_calls': [],
                'performance_issues': [],
                'key_patterns': [],
                'severity': 'unknown',
                'line_range': (chunk['start_line'], chunk['end_line'])
            }
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        import openai
        client = openai.AsyncOpenAI(api_key=self.api_key)
        
        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a log analysis expert. Provide concise, structured summaries."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000  # Keep summaries concise!
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str) -> str:
        """Call Anthropic API"""
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=self.api_key)
        
        response = await client.messages.create(
            model=self.model_name,
            max_tokens=1000,
            temperature=0.3,
            system="You are a log analysis expert. Provide concise, structured summaries.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    async def _call_google(self, prompt: str) -> str:
        """Call Google Gemini API"""
        import google.generativeai as genai
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction="You are a log analysis expert. Provide concise, structured summaries."
        )
        
        generation_config = genai.GenerationConfig(
            temperature=0.3,
            max_output_tokens=1000
        )
        
        response = await model.generate_content_async(prompt, generation_config=generation_config)
        return response.text
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from markdown or plain text"""
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\n?(\{.*?\})\n?```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find raw JSON
        json_match = re.search(r'(\{.*\})', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        return text


class ChunkIndex:
    """
    Index chunk summaries for fast retrieval
    
    Enables quick querying of relevant chunks for test generation
    """
    
    def __init__(self, db_connection):
        """Initialize with database connection"""
        self.conn = db_connection
        self._ensure_table()
    
    def _ensure_table(self):
        """Create chunk_summaries table if not exists"""
        cursor = self.conn.cursor()
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
        
        # Index for fast retrieval
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_chunk_summaries_analysis 
            ON chunk_summaries(analysis_id, severity)
        ''')
        
        self.conn.commit()
    
    def store_chunk_summary(self, analysis_id: int, summary: Dict[str, Any]):
        """Store a chunk summary"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO chunk_summaries (
                analysis_id, chunk_id, summary, errors_json, api_calls_json,
                performance_issues_json, key_patterns_json, severity,
                start_line, end_line, timestamp_start, timestamp_end
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            analysis_id,
            summary['chunk_id'],
            summary.get('summary', ''),
            json.dumps(summary.get('errors_found', [])),
            json.dumps(summary.get('api_calls', [])),
            json.dumps(summary.get('performance_issues', [])),
            json.dumps(summary.get('key_patterns', [])),
            summary.get('severity', 'info'),
            summary['line_range'][0],
            summary['line_range'][1],
            str(summary['timestamp_range'][0]) if summary['timestamp_range'][0] else None,
            str(summary['timestamp_range'][1]) if summary['timestamp_range'][1] else None
        ))
        
        self.conn.commit()
    
    def get_summaries_by_severity(self, analysis_id: int, min_severity: str = 'medium') -> List[Dict]:
        """Get chunk summaries filtered by severity"""
        severity_levels = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1, 'info': 0}
        min_level = severity_levels.get(min_severity, 2)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM chunk_summaries 
            WHERE analysis_id = ?
            ORDER BY severity DESC, chunk_id ASC
        ''', (analysis_id,))
        
        results = []
        for row in cursor.fetchall():
            if severity_levels.get(row['severity'], 0) >= min_level:
                results.append(dict(row))
        
        return results
    
    def get_all_summaries(self, analysis_id: int) -> List[Dict]:
        """Get all chunk summaries for an analysis"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM chunk_summaries 
            WHERE analysis_id = ?
            ORDER BY chunk_id ASC
        ''', (analysis_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def aggregate_summaries(self, analysis_id: int) -> Dict[str, Any]:
        """Aggregate all chunk summaries into final analysis"""
        summaries = self.get_all_summaries(analysis_id)
        
        all_errors = []
        all_api_calls = []
        all_perf_issues = []
        all_patterns = set()
        
        for summary in summaries:
            all_errors.extend(json.loads(summary['errors_json']))
            all_api_calls.extend(json.loads(summary['api_calls_json']))
            all_perf_issues.extend(json.loads(summary['performance_issues_json']))
            all_patterns.update(json.loads(summary['key_patterns_json']))
        
        return {
            'total_chunks': len(summaries),
            'error_patterns': all_errors,
            'api_endpoints': all_api_calls,
            'performance_issues': all_perf_issues,
            'key_patterns': list(all_patterns),
            'severity_distribution': self._get_severity_distribution(summaries),
            'timeline': self._build_timeline(summaries)
        }
    
    def _get_severity_distribution(self, summaries: List[Dict]) -> Dict[str, int]:
        """Count chunks by severity"""
        distribution = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0}
        for summary in summaries:
            severity = summary.get('severity', 'info')
            distribution[severity] = distribution.get(severity, 0) + 1
        return distribution
    
    def _build_timeline(self, summaries: List[Dict]) -> List[Dict]:
        """Build timeline of events from chunks"""
        timeline = []
        for summary in summaries:
            if summary.get('timestamp_start'):
                timeline.append({
                    'timestamp': summary['timestamp_start'],
                    'chunk_id': summary['chunk_id'],
                    'severity': summary['severity'],
                    'summary': summary['summary'][:100]
                })
        return sorted(timeline, key=lambda x: x['timestamp'])

