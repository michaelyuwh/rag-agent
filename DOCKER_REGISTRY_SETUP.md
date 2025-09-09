# 📦 GitHub Container Registry Setup Guide

## Quick Start - Push Docker Image to GitHub

Your Docker image has been built and tagged for GitHub Container Registry (GHCR). Follow these steps to upload it:

### 1. Create GitHub Personal Access Token

1. Go to GitHub Settings: https://github.com/settings/tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Set these permissions:
   - ✅ `write:packages` - Upload packages to GitHub Container Registry
   - ✅ `read:packages` - Download packages from GitHub Container Registry
   - ✅ `delete:packages` - Delete packages (optional)
4. Copy the generated token (save it securely)

### 2. Login to GitHub Container Registry

```bash
# Replace YOUR_TOKEN with your actual token
echo "YOUR_TOKEN" | docker login ghcr.io -u michaelyuwh --password-stdin
```

### 3. Push the Docker Image

```bash
cd /Users/michaelyu/Project/rag-agent

# Push both latest and version tags
docker push ghcr.io/michaelyuwh/rag-agent:latest
docker push ghcr.io/michaelyuwh/rag-agent:v1.0.0
```

### 4. Verify Upload

- Visit: https://github.com/michaelyuwh/rag-agent/pkgs/container/rag-agent
- Your image should appear in the packages section

## ✨ What You'll Get

Once uploaded, anyone can pull your image:

```bash
# Pull and run your RAG Agent from GitHub
docker pull ghcr.io/michaelyuwh/rag-agent:latest
docker run -p 8501:8501 ghcr.io/michaelyuwh/rag-agent:latest
```

## 🔧 Alternative: Automated GitHub Actions

I can also create a GitHub Actions workflow to automatically build and push images on every commit. Would you like that setup too?

## 📋 Image Information

- **Registry**: GitHub Container Registry (ghcr.io)
- **Repository**: ghcr.io/michaelyuwh/rag-agent
- **Tags**: 
  - `latest` - Always points to newest version
  - `v1.0.0` - Specific version tag
- **Size**: ~800MB (includes Python 3.11 + all dependencies)
- **Architecture**: linux/amd64

## 🛡️ Security Notes

- The image will be public by default
- You can make it private in GitHub package settings
- Uses multi-stage builds for optimization
- Includes health checks and security best practices
