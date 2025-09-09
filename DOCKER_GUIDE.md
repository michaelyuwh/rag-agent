# 🐳 Docker Deployment Guide for RAG Agent

## ✅ Docker Support Confirmation

**YES!** Your RAG Agent is fully Docker-ready with comprehensive containerization support:

- ✅ **Production Dockerfile** - Optimized multi-layer build
- ✅ **Docker Compose** - Complete orchestration setup
- ✅ **Health Checks** - Automated service monitoring
- ✅ **Volume Persistence** - Data and config preservation
- ✅ **Multi-Service Support** - RAG Agent + Ollama integration
- ✅ **Network Isolation** - Secure container networking

---

## 🚀 Quick Start with Docker

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/michaelyuwh/rag-agent.git
cd rag-agent

# Start with Docker Compose (includes Ollama)
docker-compose up -d

# Access the application
open http://localhost:8501
```

### Option 2: Docker Only

```bash
# Clone the repository
git clone https://github.com/michaelyuwh/rag-agent.git
cd rag-agent

# Build the Docker image
docker build -t rag-agent .

# Run the container
docker run -d \
  --name rag-agent \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config.json:/app/config.json \
  rag-agent

# Access the application
open http://localhost:8501
```

---

## 🛠️ Docker Configuration

### Current Dockerfile Features

```dockerfile
# Production-optimized Dockerfile
FROM python:3.11-slim

# Fast package management with uv
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Health checks and monitoring
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Production-ready server configuration
CMD ["uv", "run", "streamlit", "run", "rag_agent/main.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

### Docker Compose Services

1. **`rag-agent`** - Main application container
   - Port: 8501 (web interface)
   - Volumes: Data persistence and config
   - Health checks enabled
   
2. **`ollama`** (Optional) - Local AI models
   - Port: 11434 (API)
   - GPU support ready
   - Persistent model storage

---

## 🔧 Environment Configuration

### Basic Configuration

Create a `.env` file for sensitive data:

```env
# .env file (create this in project root)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
ADMIN_PASSWORD=your_secure_admin_password
ENCRYPTION_KEY=your_32_char_encryption_key_here
```

### Advanced Configuration

```yaml
# docker-compose.override.yml (optional customizations)
version: '3.8'
services:
  rag-agent:
    environment:
      - ENABLE_CODE_EXECUTION=false  # Disable for production
      - MAX_UPLOAD_SIZE=50MB
      - CACHE_TTL=3600
    # Add custom resource limits
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
```

---

## 🚀 Production Deployment

### 1. Cloud Deployment (AWS/GCP/Azure)

```bash
# Build and tag for registry
docker build -t your-registry/rag-agent:v1.0.0 .

# Push to container registry
docker push your-registry/rag-agent:v1.0.0

# Deploy with production compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 2. Kubernetes Deployment

```yaml
# kubernetes-deployment.yaml (basic example)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: rag-agent
  template:
    metadata:
      labels:
        app: rag-agent
    spec:
      containers:
      - name: rag-agent
        image: michaelyuwh/rag-agent:v1.0.0
        ports:
        - containerPort: 8501
        env:
        - name: STREAMLIT_SERVER_ADDRESS
          value: "0.0.0.0"
        volumeMounts:
        - name: data-storage
          mountPath: /app/data
      volumes:
      - name: data-storage
        persistentVolumeClaim:
          claimName: rag-agent-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: rag-agent-service
spec:
  selector:
    app: rag-agent
  ports:
  - port: 8501
    targetPort: 8501
  type: LoadBalancer
```

---

## 📊 Docker Performance Optimization

### Resource Requirements

| Component | Minimum | Recommended | Production |
|-----------|---------|-------------|------------|
| **CPU** | 2 cores | 4 cores | 8+ cores |
| **Memory** | 4GB | 8GB | 16GB+ |
| **Storage** | 5GB | 20GB | 50GB+ |
| **Network** | 100Mbps | 1Gbps | 10Gbps+ |

### Optimization Tips

```dockerfile
# Multi-stage build for smaller images
FROM python:3.11-slim as builder
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

FROM python:3.11-slim as runtime
COPY --from=builder /app/.venv /app/.venv
# ... rest of runtime setup
```

---

## 🔍 Monitoring & Debugging

### Health Check Endpoints

```bash
# Check application health
curl http://localhost:8501/_stcore/health

# Check container status
docker ps
docker logs rag-agent

# Check resource usage
docker stats rag-agent
```

### Debugging Commands

```bash
# View logs in real-time
docker-compose logs -f rag-agent

# Execute commands in container
docker-compose exec rag-agent bash

# Check container internals
docker-compose exec rag-agent uv run python -c "from rag_agent.main import main; print('✅ App ready')"
```

---

## 🛡️ Security Considerations

### Production Security

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  rag-agent:
    # Run as non-root user
    user: "1000:1000"
    
    # Read-only root filesystem
    read_only: true
    
    # Temporary filesystem for writable areas
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
    
    # Security options
    security_opt:
      - no-new-privileges:true
    
    # Resource limits
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
```

### Network Security

```yaml
# Reverse proxy with HTTPS (nginx example)
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - rag-agent
```

---

## 🎯 Deployment Scenarios

### 1. Development Environment
```bash
# Quick start for development
docker-compose up -d
```

### 2. Staging Environment
```bash
# With external database and monitoring
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

### 3. Production Environment
```bash
# Full production setup with security and monitoring
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

---

## ✅ Docker Deployment Checklist

Before deploying to production:

- [ ] **Environment variables** configured securely
- [ ] **Volume mounts** set up for data persistence
- [ ] **Health checks** configured and tested
- [ ] **Resource limits** appropriate for workload
- [ ] **Security settings** applied (non-root user, read-only filesystem)
- [ ] **Monitoring** and logging configured
- [ ] **Backup strategy** for persistent data
- [ ] **SSL/TLS** certificates configured for HTTPS
- [ ] **Firewall rules** configured appropriately
- [ ] **Container updates** strategy defined

---

## 🎉 Success!

Your RAG Agent is now running in Docker with:

- ✅ **Containerized Application** - Consistent deployment across environments
- ✅ **Service Orchestration** - Multi-container setup with networking
- ✅ **Data Persistence** - Volumes for chat history and documents
- ✅ **Health Monitoring** - Automated health checks and restart policies
- ✅ **Scalability** - Ready for horizontal scaling
- ✅ **Security** - Production-ready security configurations

**Access your containerized RAG Agent at:** http://localhost:8501

**Admin Panel:** http://localhost:8501 → "🔧 Admin Panel" (password: admin123)

---

**🐳 Your RAG Agent is now fully containerized and ready for any deployment environment!**
