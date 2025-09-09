"""
RAG Agent - A Python-based Retrieval-Augmented Generation agent for development tasks.
"""

__version__ = "1.0.0"
__author__ = "RAG Agent Project"
__description__ = "A modular RAG agent for development assistance with local and cloud AI models"

from .config import config_manager
from .agent import rag_agent

__all__ = ["config_manager", "rag_agent"]
