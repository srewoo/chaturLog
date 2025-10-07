"""
Git Client Service for ChaturLog
Provides READ-ONLY access to Git repositories (GitHub, GitLab, Bitbucket)
"""

import re
import json
from typing import Optional, Dict, List, Any
import requests
from pathlib import Path


class GitClient:
    """
    Unified Git client for multiple providers
    IMPORTANT: Only provides READ-ONLY access to repositories
    """
    
    def __init__(self, provider: str, token: str, repository: str):
        """
        Initialize Git client
        
        Args:
            provider: Git provider ('github', 'gitlab', 'bitbucket')
            token: Personal access token (READ-ONLY permissions)
            repository: Repository in format 'org/repo'
        """
        self.provider = provider.lower()
        self.token = token
        self.repository = repository
        
        # Validate provider
        if self.provider not in ['github', 'gitlab', 'bitbucket']:
            raise ValueError(f"Unsupported provider: {provider}. Use 'github', 'gitlab', or 'bitbucket'")
        
        # Set up API base URLs
        self.api_urls = {
            'github': 'https://api.github.com',
            'gitlab': 'https://gitlab.com/api/v4',
            'bitbucket': 'https://api.bitbucket.org/2.0'
        }
        
        self.base_url = self.api_urls[self.provider]
        
    def _get_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests"""
        if self.provider == 'github':
            return {
                'Authorization': f'token {self.token}',
                'Accept': 'application/vnd.github.v3+json'
            }
        elif self.provider == 'gitlab':
            return {
                'PRIVATE-TOKEN': self.token,
                'Content-Type': 'application/json'
            }
        elif self.provider == 'bitbucket':
            return {
                'Authorization': f'Bearer {self.token}',
                'Accept': 'application/json'
            }
    
    def test_token(self) -> Dict[str, Any]:
        """
        Test Git token validity using user API (doesn't require repository access)
        
        Returns:
            {
                'success': bool,
                'message': str,
                'user_info': dict or None
            }
        """
        try:
            if self.provider == 'github':
                url = f"{self.base_url}/user"
            elif self.provider == 'gitlab':
                url = f"{self.base_url}/user"
            elif self.provider == 'bitbucket':
                url = f"{self.base_url}/user"
            
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                user_info = response.json()
                return {
                    'success': True,
                    'message': 'Token is valid',
                    'user_info': {
                        'username': user_info.get('login') or user_info.get('username') or user_info.get('display_name'),
                        'name': user_info.get('name') or user_info.get('display_name'),
                        'email': user_info.get('email'),
                    }
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': 'Invalid token or insufficient permissions',
                    'user_info': None
                }
            else:
                return {
                    'success': False,
                    'message': f'Error: HTTP {response.status_code}',
                    'user_info': None
                }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'Connection timeout',
                'user_info': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'user_info': None
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Git provider and repository
        
        Returns:
            {
                'success': bool,
                'message': str,
                'repository_info': dict or None
            }
        """
        try:
            if self.provider == 'github':
                url = f"{self.base_url}/repos/{self.repository}"
            elif self.provider == 'gitlab':
                # Encode repository path for GitLab
                repo_path = self.repository.replace('/', '%2F')
                url = f"{self.base_url}/projects/{repo_path}"
            elif self.provider == 'bitbucket':
                url = f"{self.base_url}/repositories/{self.repository}"
            
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                repo_info = response.json()
                return {
                    'success': True,
                    'message': 'Connection successful',
                    'repository_info': {
                        'name': repo_info.get('name') or repo_info.get('path'),
                        'description': repo_info.get('description'),
                        'default_branch': repo_info.get('default_branch') or repo_info.get('mainbranch', {}).get('name', 'main'),
                        'language': repo_info.get('language'),
                        'private': repo_info.get('private') or repo_info.get('visibility') == 'private'
                    }
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': 'Invalid token or insufficient permissions',
                    'repository_info': None
                }
            elif response.status_code == 404:
                return {
                    'success': False,
                    'message': 'Repository not found or no access',
                    'repository_info': None
                }
            else:
                return {
                    'success': False,
                    'message': f'Error: HTTP {response.status_code}',
                    'repository_info': None
                }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'Connection timeout',
                'repository_info': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error: {str(e)}',
                'repository_info': None
            }
    
    def get_file_content(self, file_path: str, ref: str = 'main') -> Optional[str]:
        """
        Read file content from repository (READ-ONLY)
        
        Args:
            file_path: Path to file in repository (e.g., 'src/main/java/UserService.java')
            ref: Branch, tag, or commit to read from (default: 'main')
        
        Returns:
            File content as string or None if not found
        """
        try:
            if self.provider == 'github':
                url = f"{self.base_url}/repos/{self.repository}/contents/{file_path}"
                params = {'ref': ref}
                response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
                
                if response.status_code == 200:
                    content_data = response.json()
                    # GitHub returns base64 encoded content
                    import base64
                    content = base64.b64decode(content_data['content']).decode('utf-8')
                    return content
            
            elif self.provider == 'gitlab':
                repo_path = self.repository.replace('/', '%2F')
                file_path_encoded = file_path.replace('/', '%2F')
                url = f"{self.base_url}/projects/{repo_path}/repository/files/{file_path_encoded}/raw"
                params = {'ref': ref}
                response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
                
                if response.status_code == 200:
                    return response.text
            
            elif self.provider == 'bitbucket':
                url = f"{self.base_url}/repositories/{self.repository}/src/{ref}/{file_path}"
                response = requests.get(url, headers=self._get_headers(), timeout=10)
                
                if response.status_code == 200:
                    return response.text
            
            return None
        except Exception as e:
            print(f"Error reading file {file_path}: {str(e)}")
            return None
    
    def list_files(self, path: str = '', ref: str = 'main', recursive: bool = False) -> List[Dict[str, Any]]:
        """
        List files in repository directory (READ-ONLY)
        
        Args:
            path: Directory path (empty for root)
            ref: Branch, tag, or commit
            recursive: If True, list all files recursively
        
        Returns:
            List of file objects with 'path', 'type', 'name'
        """
        try:
            if self.provider == 'github':
                url = f"{self.base_url}/repos/{self.repository}/contents/{path}"
                params = {'ref': ref}
                response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
                
                if response.status_code == 200:
                    contents = response.json()
                    files = []
                    for item in contents:
                        files.append({
                            'path': item['path'],
                            'name': item['name'],
                            'type': item['type']  # 'file' or 'dir'
                        })
                        
                        # Recursively get files in subdirectories
                        if recursive and item['type'] == 'dir':
                            files.extend(self.list_files(item['path'], ref, recursive=True))
                    
                    return files
            
            elif self.provider == 'gitlab':
                repo_path = self.repository.replace('/', '%2F')
                url = f"{self.base_url}/projects/{repo_path}/repository/tree"
                params = {'ref': ref, 'path': path, 'recursive': recursive}
                response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
                
                if response.status_code == 200:
                    tree = response.json()
                    return [{
                        'path': item['path'],
                        'name': item['name'],
                        'type': item['type']  # 'blob' (file) or 'tree' (dir)
                    } for item in tree]
            
            elif self.provider == 'bitbucket':
                url = f"{self.base_url}/repositories/{self.repository}/src/{ref}/{path}"
                response = requests.get(url, headers=self._get_headers(), timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    files = []
                    for item in data.get('values', []):
                        files.append({
                            'path': item['path'],
                            'name': item['path'].split('/')[-1],
                            'type': item['type']  # 'commit_file' or 'commit_directory'
                        })
                    return files
            
            return []
        except Exception as e:
            print(f"Error listing files in {path}: {str(e)}")
            return []
    
    def get_commit_info(self, commit_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get commit information (READ-ONLY)
        
        Args:
            commit_hash: Full or short commit hash
        
        Returns:
            Commit info dict or None
        """
        try:
            if self.provider == 'github':
                url = f"{self.base_url}/repos/{self.repository}/commits/{commit_hash}"
                response = requests.get(url, headers=self._get_headers(), timeout=10)
                
                if response.status_code == 200:
                    commit = response.json()
                    return {
                        'hash': commit['sha'],
                        'short_hash': commit['sha'][:7],
                        'message': commit['commit']['message'],
                        'author': commit['commit']['author']['name'],
                        'author_email': commit['commit']['author']['email'],
                        'date': commit['commit']['author']['date'],
                        'files_changed': [f['filename'] for f in commit.get('files', [])]
                    }
            
            elif self.provider == 'gitlab':
                repo_path = self.repository.replace('/', '%2F')
                url = f"{self.base_url}/projects/{repo_path}/repository/commits/{commit_hash}"
                response = requests.get(url, headers=self._get_headers(), timeout=10)
                
                if response.status_code == 200:
                    commit = response.json()
                    return {
                        'hash': commit['id'],
                        'short_hash': commit['short_id'],
                        'message': commit['message'],
                        'author': commit['author_name'],
                        'author_email': commit['author_email'],
                        'date': commit['created_at'],
                        'files_changed': []  # GitLab requires separate API call for diffs
                    }
            
            elif self.provider == 'bitbucket':
                url = f"{self.base_url}/repositories/{self.repository}/commit/{commit_hash}"
                response = requests.get(url, headers=self._get_headers(), timeout=10)
                
                if response.status_code == 200:
                    commit = response.json()
                    return {
                        'hash': commit['hash'],
                        'short_hash': commit['hash'][:7],
                        'message': commit['message'],
                        'author': commit['author']['user']['display_name'],
                        'author_email': commit['author']['user'].get('email'),
                        'date': commit['date'],
                        'files_changed': []
                    }
            
            return None
        except Exception as e:
            print(f"Error getting commit info for {commit_hash}: {str(e)}")
            return None
    
    def search_files(self, query: str, extension: str = None) -> List[Dict[str, Any]]:
        """
        Search for files in repository (READ-ONLY)
        
        Args:
            query: Search query (file name or content)
            extension: Optional file extension filter (e.g., '.java', '.py')
        
        Returns:
            List of matching files
        """
        try:
            # Simple implementation: list all files and filter
            # For production, use provider-specific search APIs
            all_files = self.list_files(recursive=True)
            
            matching_files = []
            for file in all_files:
                if file['type'] in ['file', 'blob', 'commit_file']:
                    # Filter by extension if specified
                    if extension and not file['path'].endswith(extension):
                        continue
                    
                    # Filter by query (case-insensitive)
                    if query.lower() in file['name'].lower() or query.lower() in file['path'].lower():
                        matching_files.append(file)
            
            return matching_files
        except Exception as e:
            print(f"Error searching files: {str(e)}")
            return []
    
    def get_repository_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed repository information (READ-ONLY)
        
        Returns:
            Repository info dict or None
        """
        connection_result = self.test_connection()
        if connection_result['success']:
            return connection_result['repository_info']
        return None


# Example usage and testing
if __name__ == "__main__":
    # Test with GitHub (requires token)
    # token = "your_github_token_here"
    # client = GitClient('github', token, 'facebook/react')
    # 
    # # Test connection
    # result = client.test_connection()
    # print(f"Connection test: {result}")
    # 
    # # Get file content
    # content = client.get_file_content('README.md')
    # if content:
    #     print(f"README.md (first 200 chars): {content[:200]}")
    # 
    # # List files
    # files = client.list_files('src', recursive=False)
    # print(f"Files in src/: {[f['name'] for f in files[:10]]}")
    
    print("GitClient service ready for use")
    print("Providers supported: GitHub, GitLab, Bitbucket")
    print("Access: READ-ONLY")
