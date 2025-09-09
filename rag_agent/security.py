"""
Security utilities for RAG Agent.
Handles API key encryption, user authentication, and secure data handling.
"""

import os
import json
import hashlib
import secrets
from typing import Dict, Optional, Any
from cryptography.fernet import Fernet
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Manages API key encryption and basic security features."""
    
    def __init__(self, config_dir: str = "data"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.key_file = self.config_dir / ".security_key"
        self.encrypted_file = self.config_dir / ".encrypted_config"
        self._cipher = None
        self._init_encryption()
    
    def _init_encryption(self):
        """Initialize encryption key."""
        if self.key_file.exists():
            # Load existing key
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Set secure permissions
            os.chmod(self.key_file, 0o600)
        
        self._cipher = Fernet(key)
    
    def encrypt_api_keys(self, api_keys: Dict[str, str]) -> bool:
        """Encrypt and store API keys securely."""
        try:
            # Convert to JSON and encrypt
            json_data = json.dumps(api_keys).encode()
            encrypted_data = self._cipher.encrypt(json_data)
            
            # Save encrypted data
            with open(self.encrypted_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set secure permissions
            os.chmod(self.encrypted_file, 0o600)
            logger.info("API keys encrypted and stored securely")
            return True
            
        except Exception as e:
            logger.error(f"Failed to encrypt API keys: {e}")
            return False
    
    def decrypt_api_keys(self) -> Dict[str, str]:
        """Decrypt and retrieve API keys."""
        try:
            if not self.encrypted_file.exists():
                return {}
            
            # Load and decrypt data
            with open(self.encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = self._cipher.decrypt(encrypted_data)
            api_keys = json.loads(decrypted_data.decode())
            
            logger.info("API keys decrypted successfully")
            return api_keys
            
        except Exception as e:
            logger.error(f"Failed to decrypt API keys: {e}")
            return {}
    
    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input to prevent injection attacks."""
        # Remove potential harmful characters
        dangerous_chars = ['<', '>', '&', '"', "'", '\\', ';', '|', '`']
        sanitized = user_input
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limit length
        return sanitized[:5000]  # Max 5000 characters
    
    def validate_file_upload(self, filename: str, file_size: int) -> tuple[bool, str]:
        """Validate uploaded files for security."""
        # Check file extension
        allowed_extensions = {
            '.pdf', '.docx', '.xlsx', '.csv', '.txt', '.md', 
            '.py', '.js', '.html', '.json', '.xml', '.yaml', '.yml'
        }
        
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            return False, f"File type {file_ext} not allowed"
        
        # Check file size (50MB limit)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            return False, f"File too large. Maximum size: {max_size//1024//1024}MB"
        
        # Check filename for dangerous patterns
        dangerous_patterns = ['..', '/', '\\', '<', '>', '|', ':', '*', '?', '"']
        for pattern in dangerous_patterns:
            if pattern in filename:
                return False, "Invalid characters in filename"
        
        return True, "File validation passed"
    
    def hash_session_id(self, session_data: str) -> str:
        """Create secure hash for session identification."""
        salt = secrets.token_hex(16)
        hash_obj = hashlib.sha256((session_data + salt).encode())
        return hash_obj.hexdigest()
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_urlsafe(length)

class RateLimiter:
    """Simple rate limiting for API calls."""
    
    def __init__(self):
        self.requests = {}
        self.limits = {
            'chat': {'count': 60, 'window': 3600},  # 60 requests per hour
            'upload': {'count': 10, 'window': 3600},  # 10 uploads per hour
            'api': {'count': 100, 'window': 3600}  # 100 API calls per hour
        }
    
    def is_allowed(self, action: str, identifier: str) -> bool:
        """Check if action is allowed based on rate limits."""
        import time
        current_time = time.time()
        
        if action not in self.limits:
            return True
        
        limit_config = self.limits[action]
        key = f"{action}:{identifier}"
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < limit_config['window']
        ]
        
        # Check if under limit
        if len(self.requests[key]) < limit_config['count']:
            self.requests[key].append(current_time)
            return True
        
        return False

# Global security manager
security_manager = SecurityManager()
rate_limiter = RateLimiter()
