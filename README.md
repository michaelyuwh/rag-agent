# 🚀 RAG Agent - Enterprise AI Development Assistant

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-18%20passed-green.svg)](tests/)
[![GitHub release](https://img.shields.io/github/v/release/michaelyuwh/rag-agent?label=latest%20release)](https://github.com/michaelyuwh/rag-agent/releases)
[![GitHub stars](https://img.shields.io/github/stars/michaelyuwh/rag-agent?style=social)](https://github.com/michaelyuwh/rag-agent/stargazers)

<div align="center">
  
**🏆 Production-Ready Enterprise RAG Platform**

*Built with Python, Streamlit, LangChain, and cutting-edge AI models*

[🚀 Quick Start](#quick-start) • [📚 Documentation](#documentation) • [🎮 Demo](#demo--features) • [🔧 Installation](#installation) • [⭐ Features](#enterprise-features)

</div>

A **production-ready** Retrieval-Augmented Generation (RAG) platform designed for development teams. Upload your documentation, code, and project files to create an AI assistant with deep context about your specific projects.

## ✨ Enterprise Features

### 🧠 **Advanced AI Integration**
- **Multi-Model Support**: Ollama, OpenAI, Anthropic, LM Studio
- **Smart Context**: Vector-based document retrieval with semantic search
- **Session Management**: Persistent chat history with multi-user support
- **Admin Dashboard**: Complete system monitoring and management

### 🛡️ **Enterprise Security**
- **API Key Encryption**: Secure storage using Fernet encryption
- **Input Validation**: Comprehensive sanitization and security checks
- **Rate Limiting**: Configurable request limits per user/operation
- **Session Isolation**: Complete data separation between users

### 🚀 **Developer Tools**
- **Code Execution**: Safe Python code execution with sandboxing
- **Code Analysis**: Structure analysis and improvement suggestions
- **Prompt Templates**: Custom prompt engineering with analytics
- **Performance Monitoring**: Real-time metrics and optimization

### 📊 **Monitoring & Analytics**
- **System Metrics**: CPU, memory, response time tracking
- **Usage Analytics**: Query patterns and optimization insights
- **Performance Dashboard**: Real-time monitoring interface
- **Health Checks**: Automated system validation

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+** (required)
- **16GB+ RAM** (recommended for local models)
- **[uv](https://docs.astral.sh/uv/)** (recommended package manager)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/michaelyuwh/rag-agent.git
cd rag-agent

# Install with uv (recommended)
uv sync

# Or with pip
pip install -e .
```

### 2. Launch Application

```bash
# Start the RAG Agent
uv run streamlit run rag_agent/main.py

# Or with pip
streamlit run rag_agent/main.py
```

### 3. Access Interface

Open your browser to **http://localhost:8501**

## 🤖 AI Model Setup

### 🏠 Local Models (Privacy-First)

**Ollama** (Recommended):
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download models (choose based on your RAM)
ollama pull llama3.1:8b      # Best for 16GB+ RAM
ollama pull qwen2.5:7b       # Good coding model
ollama pull phi3:mini        # Lightweight for 8GB RAM
```

**LM Studio** (GUI Option):
1. Download from [lmstudio.ai](https://lmstudio.ai/)
2. Install and download a model through the GUI
3. Start local server (default port 1234)

### ☁️ Cloud Models

**OpenAI Setup**:
1. Get API key: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Configure in app: Settings → Models → Add OpenAI Key

**Anthropic (Claude) Setup**:
1. Get API key: [console.anthropic.com](https://console.anthropic.com/)
2. Configure in app: Settings → Models → Add Anthropic Key

## 🎯 Usage Guide

### Basic Workflow

1. **📤 Upload Documents**: Drag-and-drop files (PDF, code, docs)
2. **🤖 Select Model**: Choose from auto-detected local/cloud models
3. **💬 Start Chatting**: Ask questions with full project context
4. **🔧 Use Tools**: Access admin panel, code playground, templates

### Power User Features

#### **🔧 Admin Panel** (Password: `admin123`)
- **System Monitor**: Real-time CPU, memory, performance metrics
- **User Management**: Create users, manage sessions, view activity
- **Performance Analytics**: Response times, cache statistics, optimization
- **Security Controls**: Rate limiting, encryption, audit logs

#### **🧪 Code Playground**
- **Safe Execution**: Run Python code in sandboxed environment
- **Code Analysis**: Get structure analysis and improvement suggestions
- **Security Validation**: AST-based dangerous pattern detection

#### **🎛️ Prompt Templates**
- **Custom Templates**: Create reusable prompt templates
- **Variable Substitution**: Dynamic prompt generation
- **Usage Analytics**: Track template performance and usage

### Example Use Cases

```markdown
🔍 **Code Review**: "Review this function for security issues and performance"
🐛 **Debugging**: "Help debug this error: [paste traceback]"
📝 **Documentation**: "Generate API documentation for this module"
🏗️ **Architecture**: "Design a microservices architecture for this system"
🧪 **Testing**: "Create comprehensive unit tests for this class"
```

## 📁 Project Structure

```
rag-agent/
├── rag_agent/               # 🎯 Core application
│   ├── main.py             # Application entry point
│   ├── ui.py               # Streamlit interface
│   ├── agent.py            # RAG logic and AI integration
│   ├── admin.py            # Admin dashboard
│   ├── security.py         # Security and encryption
│   ├── performance.py      # Monitoring and caching
│   ├── session_management.py # Multi-user sessions
│   ├── prompt_engineering.py # Template system
│   ├── code_execution.py   # Safe code execution
│   ├── config.py           # Configuration management
│   ├── ingestion.py        # Document processing
│   ├── retrieval.py        # Vector search
│   └── utils.py            # Utilities
├── tests/                   # 🧪 Test suite (18 tests)
├── data/                    # 📊 Application data (auto-created)
│   ├── vector_store/       # Document embeddings
│   ├── chat_history/       # User sessions
│   └── prompts/            # Custom templates
├── pyproject.toml          # 📦 Project config & dependencies
├── Dockerfile              # 🐳 Container deployment
├── docker-compose.yml      # 🐳 Multi-service deployment
└── README.md               # 📖 This file
```

## 🐳 Production Deployment

### Docker (Recommended)

```bash
# Build and run
docker build -t rag-agent .
docker run -p 8501:8501 -v ./data:/app/data rag-agent

# Or use docker-compose
docker-compose up -d
```

### Environment Variables

```bash
# Production configuration
export ADMIN_PASSWORD="your_secure_password"
export ENCRYPTION_KEY="your_32_char_encryption_key"
export ENABLE_CODE_EXECUTION="false"  # Disable in production
export LOG_LEVEL="INFO"
```

### Health Checks

```bash
# Check application health
curl http://localhost:8501/_stcore/health

# Monitor system metrics via admin panel
# http://localhost:8501 → Admin Panel → System Monitor
```

## 🧪 Development

### Running Tests

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run with coverage
uv run python -m pytest tests/ --cov=rag_agent --cov-report=html
```

### Code Quality

```bash
# Format code
uv run black rag_agent/
uv run isort rag_agent/

# Type checking
uv run mypy rag_agent/

# Linting
uv run flake8 rag_agent/
```

### Performance Testing

```bash
# Load test the application
uv run python -c "
from rag_agent.performance import PerformanceMonitor
monitor = PerformanceMonitor()
print(monitor.get_performance_summary())
"
```

## 🛡️ Security

### Security Features
- **🔐 Encryption**: All API keys encrypted with Fernet
- **🛡️ Input Validation**: Comprehensive sanitization
- **⚡ Rate Limiting**: Configurable per operation/user
- **🔒 Session Security**: Isolated user sessions
- **🧪 Safe Execution**: Sandboxed code execution

### Security Best Practices
```bash
# Change admin password
export ADMIN_PASSWORD="your_secure_password"

# Use environment variables for API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Disable code execution in production
export ENABLE_CODE_EXECUTION="false"
```

## 📊 Performance

### System Requirements
- **Minimum**: 8GB RAM, 4GB disk space
- **Recommended**: 16GB+ RAM, 10GB+ disk space
- **Optimal**: 32GB RAM, SSD storage

### Performance Optimization
- **Smart Caching**: TTL-based result caching
- **Vector Optimization**: Efficient similarity search
- **Resource Monitoring**: Real-time system metrics
- **Model Optimization**: Context window management

## 🆘 Troubleshooting

### Common Issues

**❌ "No models detected"**
```bash
# Check Ollama
ollama serve
ollama list

# Restart application
pkill -f streamlit
uv run streamlit run rag_agent/main.py
```

**❌ "Import/dependency errors"**
```bash
# Reinstall dependencies
uv sync --reinstall
# or
pip install -e . --force-reinstall
```

**❌ "Vector store errors"**
```bash
# Clear and reinitialize
rm -rf data/vector_store
# Restart app - will auto-recreate
```

**❌ "Performance issues"**
```bash
# Check system resources
uv run python -c "
import psutil
print(f'CPU: {psutil.cpu_percent()}%')
print(f'RAM: {psutil.virtual_memory().percent}%')
"
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Test** your changes: `uv run python -m pytest`
4. **Commit**: `git commit -m 'Add amazing feature'`
5. **Push**: `git push origin feature/amazing-feature`
6. **Submit** a Pull Request

### Development Setup
```bash
# Install dev dependencies
uv sync --extra dev --extra test

# Set up pre-commit hooks
pre-commit install
```

## 📄 License

This project is licensed under the **MIT License** - see [LICENSE](LICENSE) for details.

## 🎯 Roadmap

- [ ] **🔌 Plugin System**: Extensible tool architecture
- [ ] **👥 Team Features**: Collaborative workspaces
- [ ] **📱 Mobile UI**: Responsive mobile interface
- [ ] **🌐 Multi-language**: i18n support
- [ ] **☁️ Cloud Native**: Kubernetes deployment
- [ ] **🧠 Advanced AI**: Multi-modal capabilities

## 🏆 Why RAG Agent?

✅ **Production Ready**: Enterprise security, monitoring, testing  
✅ **Developer Focused**: Built by developers, for developers  
✅ **Privacy First**: Local models, encrypted storage  
✅ **Highly Extensible**: Plugin architecture, custom templates  
✅ **Performance Optimized**: Smart caching, resource monitoring  
✅ **Multi-User**: Session isolation, user management  

---

**🚀 Transform your development workflow with AI-powered assistance that understands your codebase!**

*Built with ❤️ by developers who believe in the power of context-aware AI assistance.*
