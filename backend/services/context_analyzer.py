"""
Context Analyzer Service - Extracts project structure and patterns
for generating better, context-aware tests.
"""
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional


class ContextAnalyzer:
    """Analyzes project structure to provide context for test generation"""
    
    def __init__(self):
        self.supported_config_files = [
            'package.json',
            'requirements.txt',
            'Gemfile',
            'pom.xml',
            'build.gradle',
            'Cargo.toml',
            'go.mod'
        ]
        
        self.test_file_patterns = {
            'javascript': [r'\.test\.(js|ts|jsx|tsx)$', r'\.spec\.(js|ts|jsx|tsx)$', r'__tests__'],
            'python': [r'test_.*\.py$', r'.*_test\.py$', r'tests/'],
            'java': [r'.*Test\.java$', r'src/test/'],
            'ruby': [r'.*_spec\.rb$', r'spec/'],
            'go': [r'.*_test\.go$']
        }
    
    def analyze_project_context(self, log_file_path: str) -> Dict[str, Any]:
        """
        Analyze project structure from log file location
        
        Returns context including:
        - Project type (Node.js, Python, Java, etc.)
        - Dependencies
        - Testing framework
        - File structure
        - Import patterns
        - Naming conventions
        """
        # Get project root from log file path
        project_root = self._find_project_root(log_file_path)
        
        if not project_root:
            return self._get_default_context()
        
        context = {
            'project_root': str(project_root),
            'project_type': None,
            'language': None,
            'testing_framework': None,
            'dependencies': {},
            'test_patterns': [],
            'import_style': None,
            'file_structure': {},
            'conventions': {}
        }
        
        # Detect project type and language
        context.update(self._detect_project_type(project_root))
        
        # Extract dependencies
        context['dependencies'] = self._extract_dependencies(project_root, context['project_type'])
        
        # Detect testing framework
        context['testing_framework'] = self._detect_testing_framework(
            project_root, 
            context['dependencies'], 
            context['language']
        )
        
        # Analyze test patterns
        context['test_patterns'] = self._analyze_test_patterns(project_root, context['language'])
        
        # Detect import style
        context['import_style'] = self._detect_import_style(project_root, context['language'])
        
        # Get file structure
        context['file_structure'] = self._get_file_structure(project_root, context['language'])
        
        # Extract naming conventions
        context['conventions'] = self._extract_conventions(project_root, context['language'])
        
        return context
    
    def _find_project_root(self, log_file_path: str) -> Optional[Path]:
        """Find project root by looking for config files"""
        current_path = Path(log_file_path).parent
        
        # Traverse up to find project root (max 5 levels)
        for _ in range(5):
            # Check for common project indicators
            for config_file in self.supported_config_files:
                if (current_path / config_file).exists():
                    return current_path
            
            # Check for .git directory
            if (current_path / '.git').exists():
                return current_path
            
            parent = current_path.parent
            if parent == current_path:  # Reached root
                break
            current_path = parent
        
        return None
    
    def _detect_project_type(self, project_root: Path) -> Dict[str, Any]:
        """Detect project type from config files"""
        result = {'project_type': None, 'language': None}
        
        if (project_root / 'package.json').exists():
            result['project_type'] = 'nodejs'
            result['language'] = 'javascript'
            
            # Check if TypeScript
            if (project_root / 'tsconfig.json').exists():
                result['language'] = 'typescript'
        
        elif (project_root / 'requirements.txt').exists() or (project_root / 'setup.py').exists():
            result['project_type'] = 'python'
            result['language'] = 'python'
        
        elif (project_root / 'pom.xml').exists() or (project_root / 'build.gradle').exists():
            result['project_type'] = 'java'
            result['language'] = 'java'
        
        elif (project_root / 'Gemfile').exists():
            result['project_type'] = 'ruby'
            result['language'] = 'ruby'
        
        elif (project_root / 'go.mod').exists():
            result['project_type'] = 'go'
            result['language'] = 'go'
        
        elif (project_root / 'Cargo.toml').exists():
            result['project_type'] = 'rust'
            result['language'] = 'rust'
        
        return result
    
    def _extract_dependencies(self, project_root: Path, project_type: str) -> Dict[str, str]:
        """Extract project dependencies"""
        dependencies = {}
        
        try:
            if project_type == 'nodejs':
                package_json = project_root / 'package.json'
                if package_json.exists():
                    with open(package_json, 'r') as f:
                        data = json.load(f)
                        dependencies = {
                            **data.get('dependencies', {}),
                            **data.get('devDependencies', {})
                        }
            
            elif project_type == 'python':
                requirements = project_root / 'requirements.txt'
                if requirements.exists():
                    with open(requirements, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # Parse package==version format
                                parts = re.split(r'[=<>]', line)
                                if parts:
                                    dependencies[parts[0].strip()] = line
        
        except Exception as e:
            print(f"Error extracting dependencies: {e}")
        
        return dependencies
    
    def _detect_testing_framework(self, project_root: Path, dependencies: Dict, language: str) -> Optional[str]:
        """Detect testing framework from dependencies"""
        if language == 'javascript' or language == 'typescript':
            if 'jest' in dependencies:
                return 'jest'
            elif 'mocha' in dependencies:
                return 'mocha'
            elif 'cypress' in dependencies:
                return 'cypress'
            elif 'vitest' in dependencies:
                return 'vitest'
        
        elif language == 'python':
            if 'pytest' in dependencies:
                return 'pytest'
            elif 'unittest' in dependencies or (project_root / 'tests').exists():
                return 'unittest'
        
        elif language == 'java':
            if (project_root / 'pom.xml').exists():
                return 'junit'
        
        elif language == 'ruby':
            if 'rspec' in dependencies:
                return 'rspec'
        
        return None
    
    def _analyze_test_patterns(self, project_root: Path, language: str) -> List[Dict[str, Any]]:
        """Analyze existing test patterns"""
        patterns = []
        
        test_dirs = ['test', 'tests', '__tests__', 'spec']
        
        for test_dir in test_dirs:
            test_path = project_root / test_dir
            if test_path.exists() and test_path.is_dir():
                # Count test files
                test_files = list(test_path.rglob('*'))
                test_files = [f for f in test_files if f.is_file()]
                
                patterns.append({
                    'directory': test_dir,
                    'file_count': len(test_files),
                    'structure': 'found'
                })
        
        return patterns
    
    def _detect_import_style(self, project_root: Path, language: str) -> Optional[str]:
        """Detect import style (ESM, CommonJS, etc.)"""
        if language in ['javascript', 'typescript']:
            package_json = project_root / 'package.json'
            if package_json.exists():
                try:
                    with open(package_json, 'r') as f:
                        data = json.load(f)
                        if data.get('type') == 'module':
                            return 'esm'
                        return 'commonjs'
                except:
                    pass
        
        return None
    
    def _get_file_structure(self, project_root: Path, language: str) -> Dict[str, Any]:
        """Get basic file structure"""
        structure = {
            'src_directory': None,
            'test_directory': None,
            'common_directories': []
        }
        
        # Common source directories
        src_dirs = ['src', 'lib', 'app', 'source']
        for src_dir in src_dirs:
            if (project_root / src_dir).exists():
                structure['src_directory'] = src_dir
                break
        
        # Common test directories
        test_dirs = ['test', 'tests', '__tests__', 'spec']
        for test_dir in test_dirs:
            if (project_root / test_dir).exists():
                structure['test_directory'] = test_dir
                break
        
        # List all top-level directories
        try:
            dirs = [d.name for d in project_root.iterdir() if d.is_dir() and not d.name.startswith('.')]
            structure['common_directories'] = dirs[:10]  # Limit to 10
        except:
            pass
        
        return structure
    
    def _extract_conventions(self, project_root: Path, language: str) -> Dict[str, Any]:
        """Extract naming and structure conventions"""
        conventions = {
            'naming': None,
            'test_naming': None,
            'indentation': None
        }
        
        # Detect test naming convention
        test_dirs = ['test', 'tests', '__tests__', 'spec']
        for test_dir in test_dirs:
            test_path = project_root / test_dir
            if test_path.exists():
                try:
                    test_files = list(test_path.rglob('*'))[:5]  # Sample 5 files
                    for f in test_files:
                        if f.is_file():
                            if '_test' in f.name or '.test.' in f.name:
                                conventions['test_naming'] = 'suffix'
                            elif 'test_' in f.name or f.name.startswith('test'):
                                conventions['test_naming'] = 'prefix'
                            elif '_spec' in f.name or '.spec.' in f.name:
                                conventions['test_naming'] = 'spec'
                            break
                except:
                    pass
        
        return conventions
    
    def _get_default_context(self) -> Dict[str, Any]:
        """Return default context when project root can't be found"""
        return {
            'project_root': None,
            'project_type': 'unknown',
            'language': 'javascript',
            'testing_framework': None,
            'dependencies': {},
            'test_patterns': [],
            'import_style': None,
            'file_structure': {},
            'conventions': {}
        }
    
    def format_context_for_prompt(self, context: Dict[str, Any]) -> str:
        """Format context as a string for AI prompt"""
        lines = []
        
        lines.append("PROJECT CONTEXT:")
        
        if context.get('project_type'):
            lines.append(f"- Type: {context['project_type']}")
        
        if context.get('language'):
            lines.append(f"- Language: {context['language']}")
        
        if context.get('testing_framework'):
            lines.append(f"- Testing Framework: {context['testing_framework']}")
        
        if context.get('import_style'):
            lines.append(f"- Import Style: {context['import_style']}")
        
        if context.get('file_structure', {}).get('src_directory'):
            lines.append(f"- Source Directory: {context['file_structure']['src_directory']}")
        
        if context.get('file_structure', {}).get('test_directory'):
            lines.append(f"- Test Directory: {context['file_structure']['test_directory']}")
        
        if context.get('dependencies'):
            key_deps = list(context['dependencies'].keys())[:10]
            lines.append(f"- Key Dependencies: {', '.join(key_deps)}")
        
        if context.get('conventions', {}).get('test_naming'):
            lines.append(f"- Test Naming: {context['conventions']['test_naming']}")
        
        return '\n'.join(lines)

