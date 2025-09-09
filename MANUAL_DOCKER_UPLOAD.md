# 🚀 Manual Docker Image Upload

If you want to upload the Docker image manually right now (without waiting for GitHub Actions), follow these steps:

## 1. Create GitHub Personal Access Token

Visit: https://github.com/settings/tokens/new

**Required scopes:**
- ✅ `write:packages`
- ✅ `read:packages`  
- ✅ `repo` (if private repository)

## 2. Login and Push

```bash
# Login with your token
echo "YOUR_GITHUB_TOKEN" | docker login ghcr.io -u michaelyuwh --password-stdin

# Build and tag the image
docker build -t ghcr.io/michaelyuwh/rag-agent:latest -t ghcr.io/michaelyuwh/rag-agent:v1.0.0 .

# Push both tags
docker push ghcr.io/michaelyuwh/rag-agent:latest
docker push ghcr.io/michaelyuwh/rag-agent:v1.0.0
```

## 3. Verify Upload

Visit: https://github.com/michaelyuwh/rag-agent/pkgs/container/rag-agent

---

**Note:** The GitHub Actions workflow will automatically build and upload on every commit to main, so manual upload is optional!
