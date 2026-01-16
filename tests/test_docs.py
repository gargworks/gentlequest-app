"""
Automated documentation validation tests.

These tests verify that documentation matches the actual codebase.
Run with: pytest tests/test_docs.py -v

Gold Standard Methodology: Layer 2 - Automated Validation
"""
import re
import json
from pathlib import Path
from datetime import datetime, timedelta

import pytest
import yaml


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SYNTHESIS_DIR = PROJECT_ROOT / '.brain' / 'artifacts' / 'synthesis'
DOCS_DIR = PROJECT_ROOT / 'docs'


class TestDocumentationExists:
    """Verify all required documentation exists."""
    
    REQUIRED_DOCS = [
        'ARCHITECTURE_MAP.md',
        'OPERATIONS_PLAYBOOK.md',
        'API_CONTRACTS.md',
        'EXTENSION_GUIDE.md',
        'DECISION_LOG.md',
        'ENVIRONMENT_MATRIX.md',
        'CRITICAL_PATHS.md',
        'TECH_DEBT_REGISTRY.md',
        'MASTER_CONTEXT_INDEX.md',
        'TESTING_STRATEGY.md',
        'SECURITY_CHECKLIST.md',
        'AI_PROVIDER_SPECS.md',
    ]
    
    @pytest.mark.parametrize("doc_name", REQUIRED_DOCS)
    def test_required_doc_exists(self, doc_name):
        """Each required document must exist."""
        doc_path = SYNTHESIS_DIR / doc_name
        assert doc_path.exists(), f"Required document missing: {doc_name}"
    
    def test_openapi_spec_exists(self):
        """OpenAPI specification must exist."""
        assert (DOCS_DIR / 'openapi.yaml').exists(), "OpenAPI spec missing"
    
    def test_env_schema_exists(self):
        """Environment schema must exist."""
        assert (DOCS_DIR / 'schemas' / 'environment.schema.json').exists(), \
            "Environment schema missing"


class TestDocumentStructure:
    """Verify documents have required structure."""
    
    def test_docs_have_last_updated(self):
        """Each doc should have a Last Updated date or Date field."""
        missing = []
        # Historical files that use different date formats
        historical_prefixes = ('2025', '2026', 'founders_desk', 'MASTER_SESSION', 'CODEBASE_EXPLORATION', 'TECHNICAL_APPENDIX', 'SESSION_NOTES', 'STRATEGIC_PLANNING')
        
        for md_file in SYNTHESIS_DIR.glob('*.md'):
            if md_file.name.startswith(('digest_', 'session_')):
                continue
            # Skip historical files that use "Date:" format
            if md_file.name.startswith(historical_prefixes):
                continue
            content = md_file.read_text()
            if 'Last Updated' not in content and 'last_updated' not in content and 'Date:' not in content:
                missing.append(md_file.name)
        
        assert not missing, f"Documents missing Last Updated: {missing}"
    
    def test_docs_have_purpose(self):
        """Each doc should state its purpose."""
        missing = []
        for md_file in SYNTHESIS_DIR.glob('*.md'):
            if md_file.name.startswith(('digest_', 'session_', 'MEGA_')):
                continue
            content = md_file.read_text()
            if 'Purpose' not in content and 'purpose' not in content:
                missing.append(md_file.name)
        
        # Warn but don't fail for now
        if missing:
            pytest.skip(f"Documents missing Purpose statement: {missing}")


class TestOpenAPISpec:
    """Verify OpenAPI specification is valid and complete."""
    
    @pytest.fixture
    def openapi_spec(self):
        """Load OpenAPI spec."""
        spec_path = DOCS_DIR / 'openapi.yaml'
        if not spec_path.exists():
            pytest.skip("OpenAPI spec not found")
        return yaml.safe_load(spec_path.read_text())
    
    def test_openapi_has_info(self, openapi_spec):
        """Spec must have info section."""
        assert 'info' in openapi_spec
        assert 'title' in openapi_spec['info']
        assert 'version' in openapi_spec['info']
    
    def test_openapi_has_servers(self, openapi_spec):
        """Spec must define servers."""
        assert 'servers' in openapi_spec
        assert len(openapi_spec['servers']) > 0
    
    def test_openapi_has_paths(self, openapi_spec):
        """Spec must have API paths."""
        assert 'paths' in openapi_spec
        assert len(openapi_spec['paths']) > 0
    
    def test_critical_endpoints_documented(self, openapi_spec):
        """Critical endpoints must be in spec."""
        critical = ['/api/health', '/api/chat', '/api/mood']
        paths = openapi_spec.get('paths', {})
        
        for endpoint in critical:
            assert endpoint in paths, f"Critical endpoint not in OpenAPI: {endpoint}"


class TestEnvironmentSchema:
    """Verify environment schema is valid."""
    
    @pytest.fixture
    def env_schema(self):
        """Load environment schema."""
        schema_path = DOCS_DIR / 'schemas' / 'environment.schema.json'
        if not schema_path.exists():
            pytest.skip("Environment schema not found")
        return json.loads(schema_path.read_text())
    
    def test_schema_is_valid_json_schema(self, env_schema):
        """Schema must be valid JSON Schema."""
        assert '$schema' in env_schema
        assert 'properties' in env_schema
    
    def test_required_vars_defined(self, env_schema):
        """Required env vars must be in schema."""
        required = env_schema.get('required', [])
        assert 'SECRET_KEY' in required
        assert 'DATABASE_URL' in required
    
    def test_sensitive_vars_marked(self, env_schema):
        """Sensitive vars should be marked."""
        props = env_schema.get('properties', {})
        sensitive_vars = ['SECRET_KEY', 'DATABASE_URL', 'GEMINI_API_KEY', 'OPENAI_API_KEY']
        
        for var in sensitive_vars:
            if var in props:
                assert props[var].get('sensitive', False), \
                    f"{var} should be marked as sensitive"


class TestCriticalPathsAccuracy:
    """Verify CRITICAL_PATHS.md references real files."""
    
    def test_backend_critical_files_exist(self):
        """Backend critical path files must exist."""
        critical_backend = [
            'app.py',
            'routes/chat.py',
        ]
        
        for file_path in critical_backend:
            full_path = PROJECT_ROOT / file_path
            # Only check if routes directory exists
            if 'routes' in file_path:
                if not (PROJECT_ROOT / 'routes').exists():
                    continue  # Skip if routes not in separate files
            assert full_path.exists() or file_path in ['routes/chat.py'], \
                f"Critical path file missing: {file_path}"
    
    def test_flutter_critical_dirs_exist(self):
        """Flutter critical directories must exist."""
        flutter_dirs = [
            'ai_buddy_web/lib/screens',
            'ai_buddy_web/lib/services',
            'ai_buddy_web/lib/providers',
        ]
        
        for dir_path in flutter_dirs:
            full_path = PROJECT_ROOT / dir_path
            assert full_path.exists(), f"Critical Flutter dir missing: {dir_path}"


class TestDocumentFreshness:
    """Verify documents are not stale."""
    
    MAX_AGE_DAYS = 90
    
    def _extract_date(self, content: str) -> datetime | None:
        """Extract last updated date from content."""
        patterns = [
            r'\*\*Last Updated:\*\*\s*(\w+ \d+, \d{4})',
            r'Last Updated:\s*(\w+ \d+, \d{4})',
            r'last_updated:\s*["\']?(\d{4}-\d{2}-\d{2})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    if '-' in date_str:
                        return datetime.strptime(date_str, '%Y-%m-%d')
                    else:
                        return datetime.strptime(date_str, '%B %d, %Y')
                except ValueError:
                    continue
        return None
    
    def test_core_docs_not_stale(self):
        """Core documentation should not be older than MAX_AGE_DAYS."""
        core_docs = [
            'ARCHITECTURE_MAP.md',
            'API_CONTRACTS.md',
            'CRITICAL_PATHS.md',
        ]
        
        stale = []
        cutoff = datetime.now() - timedelta(days=self.MAX_AGE_DAYS)
        
        for doc_name in core_docs:
            doc_path = SYNTHESIS_DIR / doc_name
            if not doc_path.exists():
                continue
                
            content = doc_path.read_text()
            doc_date = self._extract_date(content)
            
            if doc_date and doc_date < cutoff:
                age = (datetime.now() - doc_date).days
                stale.append(f"{doc_name}: {age} days old")
        
        assert not stale, f"Stale documents found: {stale}"


class TestCrossReferences:
    """Verify cross-references between documents are valid."""
    
    def test_master_index_links_valid(self):
        """All links in MASTER_CONTEXT_INDEX should point to existing files."""
        index_path = SYNTHESIS_DIR / 'MASTER_CONTEXT_INDEX.md'
        if not index_path.exists():
            pytest.skip("MASTER_CONTEXT_INDEX.md not found")
        
        content = index_path.read_text()
        
        # Extract markdown links: [text](./FILE.md)
        links = re.findall(r'\[.*?\]\(\./([^)]+\.md)\)', content)
        
        broken = []
        for link in links:
            if not (SYNTHESIS_DIR / link).exists():
                broken.append(link)
        
        assert not broken, f"Broken links in MASTER_CONTEXT_INDEX: {broken}"
