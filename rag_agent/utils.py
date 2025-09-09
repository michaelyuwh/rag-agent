"""
Utility functions and helpers for the RAG Agent.
"""

import os
import platform
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information."""
    try:
        import psutil
        
        return {
            'platform': platform.system().lower(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'python_version': platform.python_version(),
            'total_ram_gb': round(psutil.virtual_memory().total / (1024**3), 1),
            'available_ram_gb': round(psutil.virtual_memory().available / (1024**3), 1),
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq().current if psutil.cpu_freq() else None
        }
    except ImportError:
        # Fallback without psutil
        return {
            'platform': platform.system().lower(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'python_version': platform.python_version()
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        return {}

def check_internet_connection() -> bool:
    """Check if internet connection is available."""
    try:
        import requests
        response = requests.get("https://www.google.com", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_port_availability(host: str = "localhost", port: int = 8501) -> bool:
    """Check if a port is available for use."""
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
    except Exception:
        return False

def find_available_port(start_port: int = 8501, end_port: int = 8510) -> Optional[int]:
    """Find an available port in the given range."""
    for port in range(start_port, end_port + 1):
        if check_port_availability(port=port):
            return port
    return None

def calculate_file_hash(file_path: str) -> str:
    """Calculate MD5 hash of a file."""
    hash_md5 = hashlib.md5()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return ""

def ensure_directory(path: str) -> bool:
    """Ensure a directory exists, create if it doesn't."""
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        return False

def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes."""
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except Exception:
        return 0.0

def clean_filename(filename: str) -> str:
    """Clean filename for cross-platform compatibility."""
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255-len(ext)] + ext
    
    return filename

def format_bytes(bytes_size: int) -> str:
    """Format bytes into human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} PB"

def check_ollama_status() -> Dict[str, Any]:
    """Check if Ollama is running and get available models."""
    try:
        import requests
        
        # Check if Ollama server is running
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            if 'models' in data:
                for model in data['models']:
                    models.append({
                        'name': model['name'],
                        'size': model.get('size', 0),
                        'modified_at': model.get('modified_at', '')
                    })
            
            return {
                'running': True,
                'models': models,
                'count': len(models)
            }
        else:
            return {'running': False, 'models': [], 'count': 0}
            
    except Exception as e:
        logger.debug(f"Ollama check failed: {e}")
        return {'running': False, 'models': [], 'count': 0}

def check_lm_studio_status() -> Dict[str, Any]:
    """Check if LM Studio is running and get available models."""
    try:
        import requests
        
        # Common LM Studio ports
        ports = [1234, 1235, 1236]
        
        for port in ports:
            try:
                response = requests.get(f"http://localhost:{port}/v1/models", timeout=2)
                
                if response.status_code == 200:
                    data = response.json()
                    models = []
                    
                    if 'data' in data:
                        for model in data['data']:
                            models.append({
                                'id': model['id'],
                                'object': model.get('object', ''),
                                'created': model.get('created', 0)
                            })
                    
                    return {
                        'running': True,
                        'port': port,
                        'models': models,
                        'count': len(models)
                    }
                    
            except Exception:
                continue
                
        return {'running': False, 'models': [], 'count': 0}
        
    except Exception as e:
        logger.debug(f"LM Studio check failed: {e}")
        return {'running': False, 'models': [], 'count': 0}

def validate_api_key(api_key: str, service: str) -> bool:
    """Validate API key for different services."""
    if not api_key or len(api_key) < 10:
        return False
        
    # Basic validation based on known patterns
    if service == "openai":
        return api_key.startswith("sk-") and len(api_key) > 20
    elif service == "anthropic":
        return api_key.startswith("sk-ant-") and len(api_key) > 30
    elif service == "google":
        return len(api_key) > 30  # Google API keys are typically longer
    else:
        return len(api_key) > 10  # Generic validation

def get_model_recommendations(ram_gb: float) -> Dict[str, str]:
    """Get model recommendations based on available RAM."""
    if ram_gb <= 8:
        return {
            'category': 'Low-End (8GB or less)',
            'primary': 'phi3:mini (3.8B parameters)',
            'alternative': 'gemma2:2b',
            'coding': 'codellama:7b-code (if RAM allows)',
            'note': 'Focus on lightweight models. Consider using cloud APIs for complex tasks.'
        }
    elif ram_gb <= 16:  # Your system
        return {
            'category': 'Mid-Range (16GB)',
            'primary': 'llama3.1:8b (Recommended for your system)',
            'alternative': 'mistral-nemo:12b',
            'coding': 'codellama:7b or deepseek-coder:6.7b',
            'note': 'Perfect balance of performance and resource usage. Excellent for development tasks.'
        }
    elif ram_gb <= 32:
        return {
            'category': 'High-End (32GB)',
            'primary': 'llama3.1:13b or mixtral:8x7b',
            'alternative': 'mistral-nemo:12b',
            'coding': 'deepseek-coder:13b',
            'note': 'Can run larger models with good performance.'
        }
    else:
        return {
            'category': 'Enthusiast (32GB+)',
            'primary': 'llama3.1:70b (quantized)',
            'alternative': 'mixtral:8x22b',
            'coding': 'deepseek-coder:33b',
            'note': 'Can run the largest available models.'
        }

def export_chat_session(session_data: Dict[str, Any], format: str = "markdown") -> str:
    """Export chat session to different formats."""
    try:
        if format.lower() == "markdown":
            lines = [f"# {session_data['title']}\n"]
            lines.append(f"**Created:** {session_data['created_at']}")
            lines.append(f"**Updated:** {session_data['updated_at']}")
            if session_data.get('model_used'):
                lines.append(f"**Model:** {session_data['model_used']}")
            lines.append("\n---\n")
            
            for message in session_data['messages']:
                role = message['role'].title()
                timestamp = message['timestamp']
                content = message['content']
                
                lines.append(f"## {role} ({timestamp})\n")
                lines.append(f"{content}\n")
                
            return "\n".join(lines)
            
        elif format.lower() == "json":
            import json
            return json.dumps(session_data, indent=2)
            
        else:
            return "Unsupported format"
            
    except Exception as e:
        logger.error(f"Error exporting session: {e}")
        return f"Error exporting session: {e}"

class CrossPlatformPath:
    """Helper class for cross-platform path handling."""
    
    @staticmethod
    def normalize(path: str) -> str:
        """Normalize path for current platform."""
        return str(Path(path))
    
    @staticmethod
    def join(*parts) -> str:
        """Join path parts in a cross-platform way."""
        return str(Path(*parts))
    
    @staticmethod
    def exists(path: str) -> bool:
        """Check if path exists."""
        return Path(path).exists()
    
    @staticmethod
    def is_file(path: str) -> bool:
        """Check if path is a file."""
        return Path(path).is_file()
    
    @staticmethod
    def is_dir(path: str) -> bool:
        """Check if path is a directory."""
        return Path(path).is_dir()
    
    @staticmethod
    def get_size(path: str) -> int:
        """Get file size."""
        return Path(path).stat().st_size if Path(path).exists() else 0
