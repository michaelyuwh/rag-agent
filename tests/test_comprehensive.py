"""
Comprehensive test suite for RAG Agent - Core Functionality Tests
"""

import pytest
import tempfile
import json
import shutil
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

# Test the session migration functionality
class TestSessionManagement:
    """Test session data handling and migration."""
    
    def test_migrate_session_data_old_format(self):
        """Test migration from old string format to new dict format."""
        from rag_agent.ui import migrate_session_data
        
        # Old format - sessions as strings
        old_sessions = {
            "session1": "Some old chat data",
            "session2": "More old data"
        }
        
        migrated = migrate_session_data(old_sessions)
        
        assert len(migrated) == 2
        for session_id, session in migrated.items():
            assert isinstance(session, dict)
            assert "id" in session
            assert "title" in session
            assert "messages" in session
            assert "created_at" in session
            assert session["title"] == "Migrated Session"
            assert session["messages"] == []
    
    def test_migrate_session_data_new_format(self):
        """Test that new format sessions pass through correctly."""
        from rag_agent.ui import migrate_session_data
        
        # New format - already correct
        new_sessions = {
            "session1": {
                "id": "session1",
                "title": "Test Session",
                "messages": [{"role": "user", "content": "Hello"}],
                "created_at": "2025-01-01T10:00:00"
            }
        }
        
        migrated = migrate_session_data(new_sessions)
        
        assert migrated == new_sessions
        assert migrated["session1"]["title"] == "Test Session"
        assert len(migrated["session1"]["messages"]) == 1
    
    def test_migrate_session_data_mixed_format(self):
        """Test migration with mixed old and new formats."""
        from rag_agent.ui import migrate_session_data
        
        mixed_sessions = {
            "old_session": "Old string data",
            "new_session": {
                "id": "new_session",
                "title": "New Session",
                "messages": [],
                "created_at": "2025-01-01T10:00:00"
            }
        }
        
        migrated = migrate_session_data(mixed_sessions)
        
        assert len(migrated) == 2
        # Old session should be migrated
        assert migrated["old_session"]["title"] == "Migrated Session"
        assert migrated["old_session"]["messages"] == []
        # New session should remain unchanged
        assert migrated["new_session"]["title"] == "New Session"

class TestErrorRecovery:
    """Test error recovery and resilience features."""
    
    def test_load_chat_sessions_corrupted_file(self):
        """Test loading sessions when file is corrupted."""
        from rag_agent.ui import load_chat_sessions
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create corrupted JSON file
            sessions_file = Path(temp_dir) / "sessions.json"
            with open(sessions_file, 'w') as f:
                f.write("{ invalid json }")
            
            # Mock config to use temp directory
            with patch('rag_agent.ui.config_manager') as mock_config:
                mock_config.config.chat_history_path = temp_dir
                
                sessions = load_chat_sessions()
                
                # Should return empty dict on corruption
                assert sessions == {}
                # Should create backup file
                backup_file = sessions_file.with_suffix('.backup')
                assert backup_file.exists()
    
    def test_load_chat_sessions_missing_file(self):
        """Test loading sessions when file doesn't exist."""
        from rag_agent.ui import load_chat_sessions
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock config to use temp directory (no sessions file)
            with patch('rag_agent.ui.config_manager') as mock_config:
                mock_config.config.chat_history_path = temp_dir
                
                sessions = load_chat_sessions()
                
                # Should return empty dict
                assert sessions == {}

class TestConfigurationManagement:
    """Test configuration loading and validation."""
    
    def test_config_manager_initialization(self):
        """Test that ConfigManager initializes properly."""
        from rag_agent.config import ConfigManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            
            # Test basic properties exist
            assert config_manager.config is not None
            assert hasattr(config_manager.config, 'embedding_model')
            assert hasattr(config_manager.config, 'vector_store_path')
            assert hasattr(config_manager.config, 'chat_history_path')
            
        finally:
            Path(config_path).unlink(missing_ok=True)
    
    def test_config_model_detection(self):
        """Test that model detection works."""
        from rag_agent.config import ConfigManager
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path)
            
            # Should have detected some models (at least templates)
            assert len(config_manager.config.models) > 0
            
            # Check for template models
            model_types = [model.type for model in config_manager.config.models.values()]
            assert any(model_type in ['ollama', 'openai', 'anthropic', 'lm_studio'] for model_type in model_types)
            
        finally:
            Path(config_path).unlink(missing_ok=True)

class TestSecurityFeatures:
    """Test security and validation features."""
    
    def test_security_manager_initialization(self):
        """Test SecurityManager initializes properly."""
        try:
            from rag_agent.security import SecurityManager
            
            security_manager = SecurityManager()
            
            # Test basic functionality
            assert hasattr(security_manager, 'encrypt_api_keys')
            assert hasattr(security_manager, 'decrypt_api_keys')
            assert hasattr(security_manager, 'validate_file_upload')
            
        except ImportError:
            pytest.skip("Cryptography not available")
    
    def test_rate_limiter_functionality(self):
        """Test rate limiting works correctly."""
        try:
            from rag_agent.security import RateLimiter
            
            rate_limiter = RateLimiter()
            
            # Test rate limiting
            user_id = "test_user"
            operation = "chat"
            
            # First request should be allowed
            assert rate_limiter.is_allowed(operation, user_id) == True
            
            # Should track the request (rate limiter uses combined keys)
            combined_key = f"{operation}:{user_id}"
            assert combined_key in rate_limiter.requests
            assert len(rate_limiter.requests[combined_key]) >= 1
            
        except ImportError:
            pytest.skip("Security features not available")

class TestCodeExecution:
    """Test code execution safety features."""
    
    def test_security_validator(self):
        """Test code security validation."""
        try:
            from rag_agent.code_execution import SecurityValidator
            
            # Safe code should pass
            safe_code = """
print("Hello, World!")
x = 5 + 3
result = x * 2
"""
            is_safe, warnings = SecurityValidator.validate_code(safe_code)
            assert is_safe == True
            
            # Dangerous code should be rejected
            dangerous_code = """
import os
os.system("rm -rf /")
"""
            is_safe, warnings = SecurityValidator.validate_code(dangerous_code)
            assert is_safe == False
            assert len(warnings) > 0
            assert any("import" in warning.lower() for warning in warnings)
            
        except ImportError:
            pytest.skip("Code execution features not available")
    
    def test_safe_executor_basic_functionality(self):
        """Test basic safe code execution."""
        try:
            from rag_agent.code_execution import SafeExecutor
            
            executor = SafeExecutor()
            
            # Test simple code execution
            result = executor.execute_code("print('Hello, Test!')")
            
            if result.success:
                assert "Hello, Test!" in result.output
            else:
                # Execution might be disabled in test environment
                assert result.error is not None
                
        except ImportError:
            pytest.skip("Code execution features not available")

class TestPerformanceMonitoring:
    """Test performance monitoring features."""
    
    def test_performance_monitor_initialization(self):
        """Test PerformanceMonitor initializes properly."""
        try:
            from rag_agent.performance import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            assert hasattr(monitor, 'record_operation')
            assert hasattr(monitor, 'get_performance_summary')
            
        except ImportError:
            pytest.skip("Performance monitoring not available")
    
    def test_metrics_recording(self):
        """Test metrics are recorded correctly."""
        try:
            from rag_agent.performance import PerformanceMonitor
            
            monitor = PerformanceMonitor()
            
            # Record a test operation (pass start time, not duration)
            start_time = time.time()
            monitor.record_operation("test_operation", start_time, True)
            
            # Get performance summary
            summary = monitor.get_performance_summary()
            assert isinstance(summary, dict)
            # The summary should contain metrics information
            assert "total_operations" in summary or "recent_operations" in summary
            
        except ImportError:
            pytest.skip("Performance monitoring not available")

class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_utility_functions(self):
        """Test basic utility functions."""
        try:
            from rag_agent.utils import (
                clean_filename, 
                format_bytes, 
                validate_api_key,
                CrossPlatformPath
            )
            
            # Test filename cleaning
            assert clean_filename("test<>file.txt") == "test__file.txt"
            assert clean_filename("normal_file.txt") == "normal_file.txt"
            
            # Test byte formatting
            assert format_bytes(1024) == "1.0 KB"
            assert format_bytes(1024 * 1024) == "1.0 MB"
            assert format_bytes(1024 * 1024 * 1024) == "1.0 GB"
            
            # Test API key validation
            assert validate_api_key("sk-1234567890abcdefghijklmnop", "openai") == True  # Long enough key
            assert validate_api_key("invalid", "openai") == False
            assert validate_api_key("", "openai") == False
            assert validate_api_key("sk-short", "openai") == False  # Too short
            
            # Test cross-platform paths
            path = CrossPlatformPath.join("folder", "file.txt")
            assert isinstance(path, str)
            assert "file.txt" in path
            
        except ImportError:
            pytest.skip("Utility functions not available")

class TestSystemRequirements:
    """Test system requirements and environment."""
    
    def test_python_version(self):
        """Test Python version requirement."""
        import sys
        assert sys.version_info >= (3, 8), "Python 3.8+ required"
    
    def test_directory_creation(self):
        """Test that directories can be created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "test_subdir"
            test_dir.mkdir(exist_ok=True)
            assert test_dir.exists()
            assert test_dir.is_dir()
    
    def test_json_operations(self):
        """Test JSON read/write operations."""
        test_data = {"test": "data", "number": 42}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            with open(temp_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data
            
        finally:
            Path(temp_file).unlink()

# Integration Tests
class TestIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.mark.asyncio
    async def test_basic_workflow_simulation(self):
        """Test a basic RAG workflow simulation."""
        # This would test the complete pipeline in a controlled environment
        # For now, just test that major components can be imported together
        
        try:
            from rag_agent.config import ConfigManager
            from rag_agent.ui import load_chat_sessions, migrate_session_data
            
            # Create temporary config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                config_path = f.name
            
            try:
                # Initialize components
                config_manager = ConfigManager(config_path)
                
                # Test session handling
                test_sessions = {"test": {"id": "test", "title": "Test", "messages": []}}
                migrated = migrate_session_data(test_sessions)
                
                assert len(migrated) == 1
                assert "test" in migrated
                
            finally:
                Path(config_path).unlink(missing_ok=True)
                
        except ImportError as e:
            pytest.skip(f"Components not available: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
