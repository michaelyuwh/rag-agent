"""
Main entry point for the RAG Agent application.
"""

import sys
import logging
from pathlib import Path

# Add the package to Python path
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('rag_agent.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Check if running in Streamlit
        import streamlit as st
        
        # Import and run the UI
        from rag_agent.ui import main as ui_main
        ui_main()
        
    except ImportError as e:
        logger.error(f"Required packages not installed: {e}")
        print("\n🚫 Error: Required packages not installed.")
        print("\nPlease install dependencies with uv:")
        print("uv sync")
        print("\nThen run the application:")
        print("uv run streamlit run rag_agent/main.py")
        print("# or")
        print("uv run rag-agent")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        print(f"\n🚫 Error starting application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
