---
title: "Docker Deployment Guide"
canonical_id: "DOC-DEPLOY-001"
version: "1.0.0"
updated: "2025-01-12"
owner: "Contextor Team"
status: "approved"
tags: ["deployment", "docker", "containerization"]
source_url: "https://github.com/daddia/contextor/docs/deployment/docker-guide.md"
---

# Docker Deployment Guide [ID: DOC-DEPLOY-001]

This guide covers containerized deployment of Contextor for both CLI processing and MCP server hosting.

## Summary

- Build Docker images for Contextor CLI and MCP server components
- Configure docker-compose for local and production deployments
- Set up volume mounts for persistent data and configuration
- Implement health checks and monitoring for production reliability
- Scale MCP server deployment with load balancing
- Integrate with CI/CD pipelines for automated deployments

## Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- Basic understanding of containerization concepts
- Access to source documentation repositories
- Understanding of Contextor workflow and configuration

## Building Images

### Contextor CLI Image

Create `Dockerfile.cli`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY contextor/ ./contextor/
COPY config/ ./config/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main

# Create non-root user
RUN useradd --create-home --shell /bin/bash contextor
USER contextor

# Set entrypoint
ENTRYPOINT ["poetry", "run", "contextor"]
```

Build the CLI image:

```bash
docker build -f Dockerfile.cli -t contextor-cli:latest .
```

### MCP Server Image

Create `Dockerfile.mcp`:

```dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY contextor/ ./contextor/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main

# Create directories
RUN mkdir -p /app/sourcedocs /app/logs

# Create non-root user
RUN useradd --create-home --shell /bin/bash contextor \
    && chown -R contextor:contextor /app
USER contextor

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start MCP server
CMD ["poetry", "run", "contextor-server", "--transport=sse", "--host=0.0.0.0", "--port=8080"]
```

Build the MCP server image:

```bash
docker build -f Dockerfile.mcp -t contextor-mcp:latest .
```

## Local Development Setup

### docker-compose.dev.yml

```yaml
version: '3.8'

services:
  contextor-cli:
    build:
      context: .
      dockerfile: Dockerfile.cli
    volumes:
      - ./vendor:/app/vendor:ro
      - ./sourcedocs:/app/sourcedocs
      - ./config:/app/config:ro
      - ./logs:/app/logs
    working_dir: /app
    environment:
      - CONTEXTOR_LOG_LEVEL=INFO
    profiles:
      - cli

  contextor-mcp:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    ports:
      - "8080:8080"
    volumes:
      - ./sourcedocs:/app/sourcedocs:ro
      - ./logs:/app/logs
    environment:
      - CONTEXTOR_LOG_LEVEL=INFO
      - SOURCEDOCS_PATH=/app/sourcedocs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    restart: unless-stopped

  # Optional: Add a reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - contextor-mcp
    profiles:
      - proxy
```

### Usage Examples

```bash
# Process documentation using CLI container
docker-compose -f docker-compose.dev.yml run --rm contextor-cli optimize \
  --src /app/vendor/nextjs/docs \
  --out /app/sourcedocs/nextjs \
  --project-config nextjs

# Start MCP server
docker-compose -f docker-compose.dev.yml up contextor-mcp

# Start with reverse proxy
docker-compose -f docker-compose.dev.yml --profile proxy up -d
```

## Production Deployment

### docker-compose.prod.yml

```yaml
version: '3.8'

services:
  contextor-mcp:
    image: contextor-mcp:latest
    ports:
      - "8080:8080"
    volumes:
      - sourcedocs-data:/app/sourcedocs:ro
      - logs-data:/app/logs
    environment:
      - CONTEXTOR_LOG_LEVEL=WARNING
      - SOURCEDOCS_PATH=/app/sourcedocs
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - contextor-network

  # Load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - contextor-mcp
    networks:
      - contextor-network
    deploy:
      replicas: 1

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    networks:
      - contextor-network
    profiles:
      - monitoring

volumes:
  sourcedocs-data:
  logs-data:
  prometheus-data:

networks:
  contextor-network:
    driver: bridge
```

### Nginx Configuration

Create `nginx/nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream contextor_backend {
        server contextor-mcp:8080;
    }

    server {
        listen 80;
        server_name your-domain.com;

        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;

        # Proxy settings
        location / {
            proxy_pass http://contextor_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # SSE support
            proxy_buffering off;
            proxy_cache off;
            proxy_set_header Connection '';
            proxy_http_version 1.1;
            chunked_transfer_encoding off;
        }

        # Health check endpoint
        location /health {
            proxy_pass http://contextor_backend/health;
            access_log off;
        }
    }
}
```

### Deploy Production Stack

```bash
# Deploy production stack
docker-compose -f docker-compose.prod.yml up -d

# Deploy with monitoring
docker-compose -f docker-compose.prod.yml --profile monitoring up -d

# Check deployment status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f contextor-mcp
```

## CI/CD Integration

### GitHub Actions Deployment

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy Contextor

on:
  push:
    branches: [main]
    tags: ['v*']
  workflow_dispatch:

env:
  REGISTRY: ghcr.io
  CLI_IMAGE_NAME: contextor-cli
  MCP_IMAGE_NAME: contextor-mcp

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata for CLI
        id: meta-cli
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ github.repository }}/${{ env.CLI_IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Extract metadata for MCP
        id: meta-mcp
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ github.repository }}/${{ env.MCP_IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}

      - name: Build and push CLI image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile.cli
          push: true
          tags: ${{ steps.meta-cli.outputs.tags }}
          labels: ${{ steps.meta-cli.outputs.labels }}

      - name: Build and push MCP image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: Dockerfile.mcp
          push: true
          tags: ${{ steps.meta-mcp.outputs.tags }}
          labels: ${{ steps.meta-mcp.outputs.labels }}

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - name: Deploy to production
        run: |
          # Add your deployment commands here
          # e.g., update Kubernetes manifests, trigger deployment pipeline
          echo "Deploying to production..."
```

### Kubernetes Deployment

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contextor-mcp
  labels:
    app: contextor-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: contextor-mcp
  template:
    metadata:
      labels:
        app: contextor-mcp
    spec:
      containers:
      - name: contextor-mcp
        image: ghcr.io/your-org/contextor-mcp:latest
        ports:
        - containerPort: 8080
        env:
        - name: CONTEXTOR_LOG_LEVEL
          value: "INFO"
        - name: SOURCEDOCS_PATH
          value: "/app/sourcedocs"
        volumeMounts:
        - name: sourcedocs-volume
          mountPath: /app/sourcedocs
          readOnly: true
        - name: logs-volume
          mountPath: /app/logs
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: sourcedocs-volume
        persistentVolumeClaim:
          claimName: sourcedocs-pvc
      - name: logs-volume
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: contextor-mcp-service
spec:
  selector:
    app: contextor-mcp
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: contextor-mcp-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - contextor.your-domain.com
    secretName: contextor-tls
  rules:
  - host: contextor.your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: contextor-mcp-service
            port:
              number: 80
```

Deploy to Kubernetes:

```bash
# Deploy to cluster
kubectl apply -f k8s/

# Check deployment status
kubectl get deployments
kubectl get pods
kubectl get services

# View logs
kubectl logs -l app=contextor-mcp -f
```

## Configuration Management

### Environment Variables

```bash
# Core configuration
CONTEXTOR_LOG_LEVEL=INFO
SOURCEDOCS_PATH=/app/sourcedocs

# MCP server specific
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8080
MCP_TRANSPORT=sse

# Optional authentication
BEARER_TOKEN=your-optional-token
CORS_ORIGINS=https://your-domain.com

# Performance tuning
MAX_WORKERS=4
WORKER_TIMEOUT=30
```

### Volume Mounts

**Essential Volumes:**

```yaml
volumes:
  # Read-only sourcedocs data
  - ./sourcedocs:/app/sourcedocs:ro

  # Writable logs directory
  - ./logs:/app/logs

  # Configuration files
  - ./config:/app/config:ro
```

**Development Volumes:**

```yaml
volumes:
  # Source code for development
  - ./contextor:/app/contextor

  # Vendor documentation
  - ./vendor:/app/vendor:ro

  # Output for CLI processing
  - ./output:/app/output
```

### Secrets Management

```yaml
# docker-compose.secrets.yml
services:
  contextor-mcp:
    environment:
      - BEARER_TOKEN_FILE=/run/secrets/bearer_token
    secrets:
      - bearer_token

secrets:
  bearer_token:
    file: ./secrets/bearer_token.txt
```

## Production Considerations

### Resource Requirements

**Minimum Requirements:**
- CPU: 0.25 cores
- Memory: 256MB
- Storage: 1GB (for logs and cache)

**Recommended for Production:**
- CPU: 0.5 cores
- Memory: 512MB
- Storage: 5GB (with log rotation)

**High-Load Configuration:**
- CPU: 1 core
- Memory: 1GB
- Storage: 10GB
- Multiple replicas with load balancing

### Performance Optimization

```dockerfile
# Multi-stage build for smaller images
FROM python:3.11-slim as builder

WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-dev

FROM python:3.11-slim as runtime

# Copy only necessary files
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY contextor/ ./contextor/

# Optimize Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

USER contextor
CMD ["contextor-server", "--transport=sse", "--host=0.0.0.0", "--port=8080"]
```

### Security Configuration

```yaml
# docker-compose.security.yml
services:
  contextor-mcp:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /app/logs
    user: "1000:1000"
```

### Monitoring and Logging

```yaml
# docker-compose.monitoring.yml
services:
  contextor-mcp:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    labels:
      - "prometheus.io/scrape=true"
      - "prometheus.io/port=8080"
      - "prometheus.io/path=/metrics"

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/datasources:/etc/grafana/provisioning/datasources:ro
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false

volumes:
  prometheus-data:
  grafana-data:
```

## Automated Processing Pipeline

### Documentation Update Pipeline

Create `docker-compose.pipeline.yml`:

```yaml
version: '3.8'

services:
  # Documentation processor
  doc-processor:
    build:
      context: .
      dockerfile: Dockerfile.cli
    volumes:
      - ./workspace:/app/workspace
      - ./config:/app/config:ro
    environment:
      - CONTEXTOR_LOG_LEVEL=INFO
    command: >
      sh -c "
        # Clone/update source repositories
        mkdir -p /app/workspace/vendor

        # Process each project
        for project in nextjs react tailwindcss; do
          echo \"Processing \$$project...\"

          # Update source
          if [ -d \"/app/workspace/vendor/\$$project\" ]; then
            cd \"/app/workspace/vendor/\$$project\" && git pull
          else
            case \$$project in
              nextjs) git clone https://github.com/vercel/next.js.git \"/app/workspace/vendor/\$$project\" ;;
              react) git clone https://github.com/facebook/react.git \"/app/workspace/vendor/\$$project\" ;;
              tailwindcss) git clone https://github.com/tailwindlabs/tailwindcss.git \"/app/workspace/vendor/\$$project\" ;;
            esac
          fi

          # Process documentation
          poetry run contextor optimize \
            --src \"/app/workspace/vendor/\$$project/docs\" \
            --out \"/app/workspace/sourcedocs/\$$project\" \
            --project-config \"\$$project\" \
            --metrics-output \"/app/workspace/sourcedocs/\$$project/metrics.json\"

          # Run intelligence analysis
          poetry run contextor intelligence \
            --source-dir \"/app/workspace/sourcedocs/\$$project\" \
            --features topic-extraction,cross-linking,quality-scoring
        done
      "
    profiles:
      - processing

  # Schedule processor with cron
  doc-scheduler:
    image: alpine:latest
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    command: >
      sh -c "
        apk add --no-cache docker-cli
        echo '0 6 * * 1 docker-compose -f docker-compose.pipeline.yml run --rm doc-processor' | crontab -
        crond -f
      "
    profiles:
      - scheduler
```

Run the pipeline:

```bash
# One-time processing
docker-compose -f docker-compose.pipeline.yml run --rm doc-processor

# Scheduled processing
docker-compose -f docker-compose.pipeline.yml --profile scheduler up -d
```

## Troubleshooting

### Container Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs contextor-mcp

# Check container status
docker-compose ps

# Inspect container
docker inspect contextor-mcp
```

**Permission errors:**
```bash
# Fix volume permissions
sudo chown -R 1000:1000 ./sourcedocs ./logs

# Or use bind mounts with correct ownership
docker-compose run --rm contextor-cli chown -R contextor:contextor /app/sourcedocs
```

**Health check failures:**
```bash
# Test health endpoint manually
docker-compose exec contextor-mcp curl http://localhost:8080/health

# Check server logs
docker-compose logs contextor-mcp | grep -i error
```

### Performance Issues

**High memory usage:**
```bash
# Monitor resource usage
docker stats

# Adjust memory limits
# In docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 1G
```

**Slow response times:**
```bash
# Check if sourcedocs volume is mounted correctly
docker-compose exec contextor-mcp ls -la /app/sourcedocs

# Monitor request processing
docker-compose logs contextor-mcp | grep -i "request"
```

### Network Issues

**Port conflicts:**
```bash
# Check what's using port 8080
lsof -i :8080

# Use different port
# In docker-compose.yml:
ports:
  - "8081:8080"
```

**SSL/TLS issues:**
```bash
# Test without SSL
curl -k https://localhost/health

# Check certificate
openssl x509 -in ssl/cert.pem -text -noout
```

## Maintenance

### Log Management

```bash
# Rotate logs
docker-compose exec contextor-mcp logrotate /etc/logrotate.conf

# Clean old logs
docker system prune -f

# View recent logs
docker-compose logs --tail=100 contextor-mcp
```

### Updates and Upgrades

```bash
# Update images
docker-compose pull

# Restart with new images
docker-compose up -d

# Zero-downtime deployment
docker-compose up -d --no-deps contextor-mcp
```

### Backup and Recovery

```bash
# Backup sourcedocs data
docker run --rm -v sourcedocs-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/sourcedocs-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore from backup
docker run --rm -v sourcedocs-data:/data -v $(pwd):/backup alpine \
  tar xzf /backup/sourcedocs-backup-20250112.tar.gz -C /data
```

## Change log

2025-01-12 — Initial Docker deployment guide with comprehensive containerization and production deployment strategies — (Documentation Team)
