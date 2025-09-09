# 🤝 Contributing to RAG Agent

Thank you for your interest in contributing to RAG Agent! This document provides guidelines for contributing to this project.

## 🚀 Quick Start for Contributors

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/rag-agent.git
cd rag-agent

# Install dependencies with development tools
uv sync --extra dev --extra test

# Run tests to ensure everything works
uv run python -m pytest tests/ -v
```

## 📋 How to Contribute

### 1. Types of Contributions

We welcome:
- 🐛 **Bug fixes**
- ✨ **New features**
- 📝 **Documentation improvements**
- 🧪 **Test coverage improvements**
- 🔧 **Performance optimizations**
- 🛡️ **Security enhancements**

### 2. Development Workflow

1. **Create an Issue** (for bugs/features)
2. **Fork the Repository**
3. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. **Make Changes** following our coding standards
5. **Add Tests** for new functionality
6. **Run Quality Checks**
   ```bash
   # Run tests
   uv run python -m pytest tests/ -v
   
   # Format code
   uv run black rag_agent/
   uv run isort rag_agent/
   
   # Type checking
   uv run mypy rag_agent/
   
   # Linting
   uv run flake8 rag_agent/
   ```
7. **Commit Changes** with descriptive messages
8. **Push and Create Pull Request**

### 3. Coding Standards

- **Code Style**: Use Black for formatting
- **Type Hints**: Add type hints for all functions
- **Documentation**: Include docstrings for new functions/classes
- **Testing**: Write tests for new features
- **Security**: Follow security best practices

### 4. Pull Request Guidelines

- **Clear Title**: Describe what the PR does
- **Description**: Explain the changes and why they're needed
- **Tests**: Ensure all tests pass
- **Documentation**: Update docs if needed
- **Small PRs**: Keep changes focused and manageable

## 🧪 Testing

```bash
# Run all tests
uv run python -m pytest tests/ -v

# Run specific test file
uv run python -m pytest tests/test_comprehensive.py -v

# Run with coverage
uv run python -m pytest tests/ --cov=rag_agent --cov-report=html
```

## 📝 Documentation

- Update README.md for significant changes
- Add docstrings to new functions/classes
- Update QUICK_START.md if setup changes
- Include examples for new features

## 🐛 Reporting Issues

When reporting issues, please include:
- **Environment**: OS, Python version, uv/pip version
- **Steps to Reproduce**: Clear step-by-step instructions
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Error Messages**: Full error traces if applicable
- **Screenshots**: If relevant for UI issues

## 💬 Getting Help

- **GitHub Discussions**: For questions and ideas
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check README and QUICK_START guides first

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to RAG Agent! 🚀**
