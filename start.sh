#!/bin/bash

# RAG Agent Startup Script - Using UV for fast Python package management

echo "🤖 Starting RAG Agent..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install it first:"
    echo "curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "or"
    echo "brew install uv"
    exit 1
fi

# Check if virtual environment exists, create if not
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment with uv..."
    uv venv
fi

# Install/sync dependencies
echo "📚 Installing dependencies..."
uv sync

# Check if successful
if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "🚀 Starting RAG Agent with Streamlit..."

# Run the application
uv run streamlit run rag_agent/main.py --server.port=8501 --server.address=localhost

echo "✅ RAG Agent stopped"
