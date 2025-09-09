"""
Basic tests for the RAG Agent components.
"""

import pytest
import tempfile
import os
from pathlib import Path

# Test configuration management
def test_config_manager():
    """Test basic configuration functionality."""
    try:
        from rag_agent.config import ConfigManager
        
        # Create temporary config
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = f.name
            
        config_manager = ConfigManager(config_path)
        
        # Test basic properties
        assert config_manager.config is not None
        assert hasattr(config_manager.config, 'embedding_model')
        assert hasattr(config_manager.config, 'vector_store_path')
        
        # Cleanup
        os.unlink(config_path)
        
    except ImportError:
        pytest.skip("Dependencies not installed")

def test_document_ingestion():
    """Test document ingestion functionality."""
    try:
        from rag_agent.ingestion import DocumentIngestion
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            ingestion = DocumentIngestion(vector_store_path=temp_dir)
            
            # Test file type detection
            assert ingestion.is_supported("test.txt")
            assert ingestion.is_supported("test.py")
            assert ingestion.is_supported("test.pdf")
            assert not ingestion.is_supported("test.unknown")
            
            # Test text parsing
            test_text = "This is a test document."
            chunks = ingestion.chunk_text(test_text, "test.txt")
            assert len(chunks) > 0
            assert chunks[0].page_content == test_text
            
    except ImportError:
        pytest.skip("Dependencies not installed")

def test_utils():
    """Test utility functions."""
    try:
        from rag_agent.utils import (
            clean_filename, 
            format_bytes, 
            validate_api_key,
            CrossPlatformPath
        )
        
        # Test filename cleaning
        assert clean_filename("test<>file.txt") == "test__file.txt"
        
        # Test byte formatting
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1024 * 1024) == "1.0 MB"
        
        # Test API key validation
        assert validate_api_key("sk-1234567890abcdef", "openai")
        assert not validate_api_key("invalid", "openai")
        
        # Test cross-platform paths
        path = CrossPlatformPath.join("folder", "file.txt")
        assert isinstance(path, str)
        
    except ImportError:
        pytest.skip("Dependencies not installed")

def test_system_requirements():
    """Test that the system meets basic requirements."""
    import sys
    
    # Check Python version
    assert sys.version_info >= (3, 8), "Python 3.8+ required"
    
    # Check that required directories can be created
    test_dir = Path("test_temp_dir")
    test_dir.mkdir(exist_ok=True)
    assert test_dir.exists()
    test_dir.rmdir()

if __name__ == "__main__":
    pytest.main([__file__])
