"""
Git Repository Detector for ChaturLog
Automatically detects Git repository information from log files
"""

import re
from typing import Optional, Dict, List


class GitRepositoryDetector:
    """
    Detects Git repository information from log content
    Uses multiple pattern matching strategies
    """
    
    def __init__(self):
        # Patterns for detecting Git repositories
        self.patterns = {
            # Direct URLs - Updated to handle multi-level paths like mindtickle/migrated-call-ai/apollo-server
            'https_url': re.compile(r'https?://(?:github\.com|gitlab\.com|bitbucket\.org|dev\.azure\.com)/([\w-]+(?:/[\w-]+)+?)(?:\.git|\s|$)', re.IGNORECASE),
            'ssh_url': re.compile(r'git@(?:github\.com|gitlab\.com|bitbucket\.org):([\w-]+(?:/[\w-]+)+?)(?:\.git|\s|$)', re.IGNORECASE),
            
            # Repository names
            'org_repo': re.compile(r'(?:github|gitlab|bitbucket|repository|repo|project):\s*([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', re.IGNORECASE),
            'repo_name': re.compile(r'(?:deploying|building|repository:|repo:)\s+([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', re.IGNORECASE),
            
            # Service names (e.g., {"name":"APOLLO_SERVER"})
            'service_name_json': re.compile(r'["\']name["\']\s*:\s*["\']([A-Z_]+)["\']', re.IGNORECASE),
            'service_name_env': re.compile(r'SERVICE_NAME[=\s]+([A-Z_-]+)', re.IGNORECASE),
            'service_name_log': re.compile(r'(?:Service|App|Application):\s*([A-Z_-]+)', re.IGNORECASE),
            
            # CI/CD Environment Variables
            'github_repo_env': re.compile(r'GITHUB_REPOSITORY[=\s]+([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', re.IGNORECASE),
            'gitlab_project': re.compile(r'CI_PROJECT_PATH[=\s]+([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', re.IGNORECASE),
            'gitlab_url': re.compile(r'CI_PROJECT_URL[=\s]+https?://gitlab\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', re.IGNORECASE),
            'circle_ci': re.compile(r'CIRCLE_PROJECT_USERNAME[=\s]+([a-zA-Z0-9_-]+).*?CIRCLE_PROJECT_REPONAME[=\s]+([a-zA-Z0-9_.-]+)', re.IGNORECASE | re.DOTALL),
            'travis_ci': re.compile(r'TRAVIS_REPO_SLUG[=\s]+([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', re.IGNORECASE),
            
            # Commit hashes
            'commit_hash': re.compile(r'(?:commit|sha|revision)[:\s]+([a-f0-9]{7,40})', re.IGNORECASE),
            
            # Branch names
            'branch': re.compile(r'(?:branch|ref)[:\s]+([\w/-]+)', re.IGNORECASE),
            
            # Docker images
            'docker_image': re.compile(r'(?:image|pulling|built from)[:\s]+([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+):([a-zA-Z0-9_.-]+)', re.IGNORECASE),
            
            # Package names (Java, Python, etc.)
            'java_package': re.compile(r'(?:com|org|io)\.([a-zA-Z0-9]+)\.([a-zA-Z0-9]+)', re.IGNORECASE)
        }
    
    def detect_repository(self, log_content: str, filename: str = '') -> Dict:
        """
        Detect Git repository from log content
        
        Args:
            log_content: Full log file content
            filename: Log filename (optional, for context)
        
        Returns:
            {
                'repository': 'org/repo' or None,
                'repository_url': Full URL or None,
                'git_service': 'github', 'gitlab', 'bitbucket', or None,
                'commit_hash': 'abc123...' or None,
                'branch': 'main' or None,
                'confidence': 'very_high', 'high', 'medium', 'low', or 'none',
                'detection_methods': List of methods that found matches
            }
        """
        result = {
            'repository': None,
            'repository_url': None,
            'git_service': None,
            'commit_hash': None,
            'branch': None,
            'confidence': 'none',
            'detection_methods': []
        }
        
        # Priority 1: Direct URLs (highest confidence)
        match = self.patterns['https_url'].search(log_content)
        if match:
            repo_path = match.group(1)  # Full path: mindtickle/migrated-call-ai/apollo-server
            result['repository'] = repo_path
            result['repository_url'] = match.group(0)
            result['git_service'] = self._detect_service_from_url(match.group(0))
            result['confidence'] = 'very_high'
            result['detection_methods'].append('https_url')
            
            # Extract service name from path (last component)
            path_parts = repo_path.split('/')
            if len(path_parts) >= 2:
                result['service_name'] = path_parts[-1]
            
            # Try to find commit and branch
            self._detect_commit_and_branch(log_content, result)
            return result
        
        match = self.patterns['ssh_url'].search(log_content)
        if match:
            repo_path = match.group(1)  # Full path
            result['repository'] = repo_path
            result['git_service'] = self._detect_service_from_url(match.group(0))
            result['confidence'] = 'very_high'
            result['detection_methods'].append('ssh_url')
            
            # Extract service name from path (last component)
            path_parts = repo_path.split('/')
            if len(path_parts) >= 2:
                result['service_name'] = path_parts[-1]
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        # Priority 2: CI/CD Environment Variables (very high confidence)
        match = self.patterns['github_repo_env'].search(log_content)
        if match:
            org, repo = match.groups()
            result['repository'] = f"{org}/{repo}"
            result['git_service'] = 'github'
            result['confidence'] = 'very_high'
            result['detection_methods'].append('github_env_var')
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        match = self.patterns['gitlab_project'].search(log_content)
        if match:
            org, repo = match.groups()
            result['repository'] = f"{org}/{repo}"
            result['git_service'] = 'gitlab'
            result['confidence'] = 'very_high'
            result['detection_methods'].append('gitlab_env_var')
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        match = self.patterns['travis_ci'].search(log_content)
        if match:
            org, repo = match.groups()
            result['repository'] = f"{org}/{repo}"
            result['confidence'] = 'very_high'
            result['detection_methods'].append('travis_ci_env')
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        # Priority 3: Explicit repository references (high confidence)
        match = self.patterns['org_repo'].search(log_content)
        if match:
            org, repo = match.groups()
            result['repository'] = f"{org}/{repo}"
            result['confidence'] = 'high'
            result['detection_methods'].append('explicit_repo_ref')
            result['git_service'] = self._infer_service_from_log(log_content)
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        match = self.patterns['repo_name'].search(log_content)
        if match:
            org, repo = match.groups()
            result['repository'] = f"{org}/{repo}"
            result['confidence'] = 'high'
            result['detection_methods'].append('repo_name_pattern')
            result['git_service'] = self._infer_service_from_log(log_content)
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        # Priority 4: Docker image tags (high confidence)
        match = self.patterns['docker_image'].search(log_content)
        if match:
            org, repo, tag = match.groups()
            result['repository'] = f"{org}/{repo}"
            result['confidence'] = 'high'
            result['detection_methods'].append('docker_image_tag')
            
            # Tag might be a commit hash
            if re.match(r'[a-f0-9]{7,40}', tag):
                result['commit_hash'] = tag
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        # Priority 5: Package names (medium confidence - educated guess)
        match = self.patterns['java_package'].search(log_content)
        if match:
            domain, org_or_app = match.groups()
            # This is a guess based on Java package naming conventions
            result['repository'] = f"{org_or_app}/{domain}"
            result['confidence'] = 'medium'
            result['detection_methods'].append('package_name_inference')
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        # Priority 6: Service names (low-medium confidence)
        service_name = self._detect_service_name(log_content)
        if service_name:
            # Generate repository name variants
            variants = self._service_name_to_repo_variants(service_name)
            
            # Use the most common variant (lowercase with dashes)
            result['repository'] = None  # Will be set by user or Git config
            result['service_name'] = service_name
            result['repository_suggestions'] = variants  # Suggest these to user
            result['confidence'] = 'low'
            result['detection_methods'].append('service_name_inference')
            
            self._detect_commit_and_branch(log_content, result)
            return result
        
        # If nothing found, try to extract at least commit and branch
        self._detect_commit_and_branch(log_content, result)
        
        if result['commit_hash'] or result['branch']:
            result['confidence'] = 'low'
            result['detection_methods'].append('partial_git_info')
        
        return result
    
    def _detect_service_name(self, log_content: str) -> Optional[str]:
        """Detect service name from log content"""
        # Try JSON format: {"name":"APOLLO_SERVER"}
        match = self.patterns['service_name_json'].search(log_content)
        if match:
            return match.group(1)
        
        # Try environment variable: SERVICE_NAME=APOLLO_SERVER
        match = self.patterns['service_name_env'].search(log_content)
        if match:
            return match.group(1)
        
        # Try log format: Service: APOLLO_SERVER
        match = self.patterns['service_name_log'].search(log_content)
        if match:
            return match.group(1)
        
        return None
    
    def _detect_service_from_url(self, url: str) -> str:
        """Detect Git service from URL"""
        url_lower = url.lower()
        if 'github.com' in url_lower:
            return 'github'
        elif 'gitlab.com' in url_lower:
            return 'gitlab'
        elif 'bitbucket.org' in url_lower:
            return 'bitbucket'
        return None
    
    def _infer_service_from_log(self, log_content: str) -> Optional[str]:
        """Infer Git service from log context"""
        log_lower = log_content.lower()
        
        # Count mentions of each service
        github_count = log_lower.count('github')
        gitlab_count = log_lower.count('gitlab')
        bitbucket_count = log_lower.count('bitbucket')
        
        if github_count > gitlab_count and github_count > bitbucket_count:
            return 'github'
        elif gitlab_count > github_count and gitlab_count > bitbucket_count:
            return 'gitlab'
        elif bitbucket_count > 0:
            return 'bitbucket'
        
        return None
    
    def _detect_commit_and_branch(self, log_content: str, result: Dict):
        """Detect commit hash and branch name"""
        # Find commit hash
        commit_match = self.patterns['commit_hash'].search(log_content)
        if commit_match:
            result['commit_hash'] = commit_match.group(1)
        
        # Find branch name
        branch_match = self.patterns['branch'].search(log_content)
        if branch_match:
            branch = branch_match.group(1)
            # Clean up branch name (remove refs/heads/ prefix)
            if branch.startswith('refs/heads/'):
                branch = branch.replace('refs/heads/', '')
            result['branch'] = branch
    
    def _service_name_to_repo_variants(self, service_name: str) -> List[str]:
        """
        Convert service name to possible repository name variants
        
        Example: APOLLO_SERVER → ['apollo-server', 'apollo_server', 'apollo', 'APOLLO-SERVER']
        """
        if not service_name:
            return []
        
        variants = set()
        
        # Original
        variants.add(service_name)
        
        # Lowercase with dashes
        variants.add(service_name.lower().replace('_', '-'))
        
        # Lowercase with underscores
        variants.add(service_name.lower())
        
        # Uppercase with dashes
        variants.add(service_name.upper().replace('_', '-'))
        
        # Just the first part (before underscore)
        if '_' in service_name:
            first_part = service_name.split('_')[0]
            variants.add(first_part.lower())
            variants.add(first_part.upper())
        
        # Remove common suffixes
        for suffix in ['_SERVER', '_SERVICE', '_API', '_APP', '-SERVER', '-SERVICE', '-API', '-APP']:
            if service_name.upper().endswith(suffix):
                base = service_name[:-len(suffix)]
                variants.add(base.lower())
                variants.add(base.lower().replace('_', '-'))
        
        return list(variants)
    
    def detect_multiple_repositories(self, log_content: str) -> List[Dict]:
        """
        Detect multiple repositories in log (for microservices)
        
        Returns:
            List of repository detection results
        """
        repositories = []
        seen_repos = set()
        
        # Find all HTTPS URLs
        for match in self.patterns['https_url'].finditer(log_content):
            org, repo = match.groups()
            repo_name = f"{org}/{repo}"
            if repo_name not in seen_repos:
                seen_repos.add(repo_name)
                repositories.append({
                    'repository': repo_name,
                    'repository_url': match.group(0),
                    'git_service': self._detect_service_from_url(match.group(0)),
                    'confidence': 'very_high'
                })
        
        # Find all SSH URLs
        for match in self.patterns['ssh_url'].finditer(log_content):
            org, repo = match.groups()
            repo_name = f"{org}/{repo}"
            if repo_name not in seen_repos:
                seen_repos.add(repo_name)
                repositories.append({
                    'repository': repo_name,
                    'git_service': self._detect_service_from_url(match.group(0)),
                    'confidence': 'very_high'
                })
        
        # Find all Docker images
        for match in self.patterns['docker_image'].finditer(log_content):
            org, repo, tag = match.groups()
            repo_name = f"{org}/{repo}"
            if repo_name not in seen_repos:
                seen_repos.add(repo_name)
                repositories.append({
                    'repository': repo_name,
                    'confidence': 'high'
                })
        
        return repositories if repositories else [self.detect_repository(log_content)]


# Example usage
if __name__ == "__main__":
    # Test detection
    test_log = """
    [INFO] GitHub Actions workflow started
    [INFO] Repository: https://github.com/myorg/myapp
    [INFO] Commit: abc123def456789
    [INFO] Branch: feature/user-auth
    [ERROR] NullPointerException in UserService
    """
    
    detector = GitRepositoryDetector()
    result = detector.detect_repository(test_log)
    
    print("Detection result:")
    print(f"  Repository: {result['repository']}")
    print(f"  Service: {result['git_service']}")
    print(f"  Commit: {result['commit_hash']}")
    print(f"  Branch: {result['branch']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Methods: {result['detection_methods']}")
