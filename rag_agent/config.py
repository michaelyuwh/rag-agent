"""
Configuration management for the RAG Agent.
Handles settings persistence, model detection, and system optimization.
"""

import json
import os
import platform
import psutil
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class ModelConfig:
    """Configuration for a single AI model."""
    name: str
    type: str  # "ollama", "openai", "anthropic", "lm_studio", etc.
    endpoint: str
    api_key: Optional[str] = None
    model_id: Optional[str] = None
    is_available: bool = False
    recommended: bool = False

@dataclass
class AppConfig:
    """Main application configuration."""
    # Model settings
    selected_model: Optional[str] = None
    models: Dict[str, ModelConfig] = None
    
    # Vector store settings
    vector_store_path: str = "data/vector_store"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # Chat settings
    max_context_length: int = 4000
    max_response_length: int = 2000
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # UI settings
    theme: str = "light"
    chat_history_path: str = "data/chat_history"
    
    # System info (auto-detected)
    system_ram_gb: Optional[float] = None
    system_platform: Optional[str] = None
    
    def __post_init__(self):
        if self.models is None:
            self.models = {}

class ConfigManager:
    """Manages application configuration and model detection."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self.config = AppConfig()
        self._ensure_data_directories()
        self.load_config()
        self._detect_system_info()
        
    def _ensure_data_directories(self):
        """Create necessary data directories."""
        os.makedirs("data", exist_ok=True)
        os.makedirs("data/vector_store", exist_ok=True)
        os.makedirs("data/chat_history", exist_ok=True)
        
    def load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_dict = json.load(f)
                    
                # Convert models dict to ModelConfig objects
                models = {}
                if 'models' in config_dict:
                    for name, model_data in config_dict['models'].items():
                        models[name] = ModelConfig(**model_data)
                    config_dict['models'] = models
                    
                # Update config with loaded data
                for key, value in config_dict.items():
                    if hasattr(self.config, key):
                        setattr(self.config, key, value)
                        
                logger.info(f"Configuration loaded from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()
            
        return self.config
        
    def save_config(self):
        """Save current configuration to file."""
        try:
            config_dict = asdict(self.config)
            # Convert ModelConfig objects to dicts
            if 'models' in config_dict and config_dict['models']:
                models_dict = {}
                for name, model in config_dict['models'].items():
                    if isinstance(model, ModelConfig):
                        models_dict[name] = asdict(model)
                    else:
                        models_dict[name] = model
                config_dict['models'] = models_dict
                
            with open(self.config_path, 'w') as f:
                json.dump(config_dict, f, indent=2)
            logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            
    def _create_default_config(self):
        """Create default configuration with detected models."""
        self.config = AppConfig()
        self._detect_available_models()
        self._set_recommended_model()
        self.save_config()
        
    def _detect_system_info(self):
        """Detect system RAM and platform information."""
        try:
            # Get system RAM in GB
            ram_bytes = psutil.virtual_memory().total
            self.config.system_ram_gb = round(ram_bytes / (1024**3), 1)
            
            # Get platform
            self.config.system_platform = platform.system().lower()
            
            logger.info(f"System: {self.config.system_platform}, RAM: {self.config.system_ram_gb}GB")
        except Exception as e:
            logger.error(f"Error detecting system info: {e}")
            
    def _detect_available_models(self):
        """Detect available AI models (local and cloud)."""
        self.config.models = {}
        
        # Check Ollama
        self._check_ollama()
        
        # Check LM Studio
        self._check_lm_studio()
        
        # Add cloud model templates (user needs to add API keys)
        self._add_cloud_model_templates()
        
    def _check_ollama(self):
        """Check if Ollama is available and get models."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'models' in data:
                    for model in data['models']:
                        model_name = f"ollama_{model['name']}"
                        self.config.models[model_name] = ModelConfig(
                            name=model['name'],
                            type="ollama",
                            endpoint="http://localhost:11434",
                            model_id=model['name'],
                            is_available=True
                        )
                    logger.info(f"Found {len(data['models'])} Ollama models")
                else:
                    # Ollama is running but no models
                    self._add_ollama_template()
            else:
                self._add_ollama_template()
        except:
            self._add_ollama_template()
            
    def _add_ollama_template(self):
        """Add Ollama template for manual configuration."""
        self.config.models["ollama_template"] = ModelConfig(
            name="Ollama (Not Running)",
            type="ollama",
            endpoint="http://localhost:11434",
            is_available=False
        )
        
    def _check_lm_studio(self):
        """Check if LM Studio is available."""
        try:
            # Common LM Studio ports
            ports = [1234, 1235, 1236]
            for port in ports:
                try:
                    response = requests.get(f"http://localhost:{port}/v1/models", timeout=2)
                    if response.status_code == 200:
                        data = response.json()
                        if 'data' in data:
                            for model in data['data']:
                                model_name = f"lm_studio_{model['id']}"
                                self.config.models[model_name] = ModelConfig(
                                    name=model['id'],
                                    type="lm_studio",
                                    endpoint=f"http://localhost:{port}/v1",
                                    model_id=model['id'],
                                    is_available=True
                                )
                            logger.info(f"Found LM Studio on port {port}")
                            return
                except:
                    continue
        except:
            pass
            
        # Add template if not found
        self.config.models["lm_studio_template"] = ModelConfig(
            name="LM Studio (Not Running)",
            type="lm_studio",
            endpoint="http://localhost:1234/v1",
            is_available=False
        )
        
    def _add_cloud_model_templates(self):
        """Add cloud model templates."""
        cloud_models = [
            {
                "key": "openai_gpt4",
                "name": "OpenAI GPT-4",
                "type": "openai",
                "endpoint": "https://api.openai.com/v1",
                "model_id": "gpt-4"
            },
            {
                "key": "openai_gpt4o",
                "name": "OpenAI GPT-4o",
                "type": "openai", 
                "endpoint": "https://api.openai.com/v1",
                "model_id": "gpt-4o"
            },
            {
                "key": "anthropic_claude",
                "name": "Anthropic Claude 3.5 Sonnet",
                "type": "anthropic",
                "endpoint": "https://api.anthropic.com/v1",
                "model_id": "claude-3-5-sonnet-20241022"
            }
        ]
        
        for model in cloud_models:
            self.config.models[model["key"]] = ModelConfig(
                name=model["name"],
                type=model["type"],
                endpoint=model["endpoint"],
                model_id=model["model_id"],
                is_available=False  # Will be True when API key is added
            )
            
    def _set_recommended_model(self):
        """Set recommended model based on system specs."""
        if not self.config.system_ram_gb:
            return
            
        ram_gb = self.config.system_ram_gb
        
        # Find the best available model for the system
        available_models = [m for m in self.config.models.values() if m.is_available]
        
        if not available_models:
            logger.warning("No available models found")
            return
            
        # Prefer local models, especially for mid-range systems like yours (16GB)
        for model in available_models:
            if model.type == "ollama":
                # For 16GB system, recommend efficient models
                if any(name in model.name.lower() for name in ["llama3.1:8b", "mistral", "codellama:7b"]):
                    model.recommended = True
                    self.config.selected_model = next(k for k, v in self.config.models.items() if v == model)
                    logger.info(f"Recommended model for {ram_gb}GB system: {model.name}")
                    return
                    
        # Fallback to first available model
        first_model = available_models[0]
        first_model.recommended = True
        self.config.selected_model = next(k for k, v in self.config.models.items() if v == first_model)
        logger.info(f"Using fallback model: {first_model.name}")
        
    def get_available_models(self) -> List[ModelConfig]:
        """Get list of available models."""
        return [model for model in self.config.models.values() if model.is_available]
        
    def get_recommended_models_for_system(self) -> Dict[str, str]:
        """Get model recommendations based on system RAM."""
        if not self.config.system_ram_gb:
            return {}
            
        ram_gb = self.config.system_ram_gb
        
        if ram_gb <= 16:  # Your system
            return {
                "primary": "llama3.1:8b (via Ollama)",
                "alternative": "phi3:mini (lightweight)",
                "coding": "codellama:7b or deepseek-coder:6.7b",
                "note": "Perfect for your 16GB M3 MacBook Air. Ollama recommended for local privacy."
            }
        elif ram_gb <= 32:
            return {
                "primary": "llama3.1:13b or mistral-nemo:12b",
                "alternative": "mixtral:8x7b",
                "coding": "deepseek-coder:13b",
                "note": "Good performance with larger models"
            }
        else:
            return {
                "primary": "llama3.1:70b (quantized)",
                "alternative": "mixtral:8x22b", 
                "coding": "deepseek-coder:33b",
                "note": "High-end setup, can run large models"
            }
            
    def add_api_key(self, model_key: str, api_key: str) -> bool:
        """Add API key for a cloud model."""
        if model_key in self.config.models:
            self.config.models[model_key].api_key = api_key
            self.config.models[model_key].is_available = True
            self.save_config()
            logger.info(f"API key added for {model_key}")
            return True
        return False
        
    def refresh_model_availability(self):
        """Refresh availability status of all models."""
        self._detect_available_models()
        self.save_config()

# Global config manager instance
config_manager = ConfigManager()
