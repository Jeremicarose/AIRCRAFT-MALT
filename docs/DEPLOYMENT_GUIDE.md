# Production Deployment Guide

This guide covers deploying the MLAT system to production.

## 📋 Prerequisites

- Docker and Docker Compose installed
- CKB RPC access or testnet credentials
- Receiver registry type hash
- 4DSky API access
- Server with minimum 2GB RAM, 2 CPU cores
- Open ports: 5000 (API), 8080 (Dashboard)

## 🚀 Quick Start - Local Deployment

### 1. Clone and Setup

```bash
# Clone repository
git clone <your-repo>
cd mlat-system

# Create environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

### 2. Configure Environment Variables

Edit `.env`:

```bash
# CKB Configuration
CKB_NETWORK=testnet
CKB_RPC_URL=https://testnet.ckb.dev/rpc
CKB_INDEXER_URL=https://testnet.ckb.dev/indexer
RECEIVER_REGISTRY_TYPE_HASH=0xYOUR_TYPE_HASH
SIMULATE_IF_UNAVAILABLE=false

# 4DSky Configuration
FOURDSKYAPIKEY=your_api_key_here
FOURDSKYENDPOINT=wss://api.4dsky.com/stream

# System Configuration
MAX_RECEIVERS=10
LOG_LEVEL=INFO
DATABASE_PATH=/app/data/mlat_data.db
```

### 3. Build and Run

```bash
# Build Docker images
docker-compose build

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 4. Verify Deployment

```bash
# Check API health
curl http://localhost:5000/api/health

# Access dashboard
open http://localhost:8080

# View logs
docker-compose logs mlat-processor
docker-compose logs mlat-api
```

## 🏗️ Production Deployment

### Option 1: AWS Deployment

#### Using EC2

```bash
# Launch EC2 instance (t3.medium recommended)
# Amazon Linux 2 or Ubuntu 22.04

# SSH into instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install Docker
sudo yum update -y
sudo yum install docker -y
sudo service docker start
sudo usermod -a -G docker ec2-user

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Clone and deploy
git clone <your-repo>
cd mlat-system
cp .env.example .env
nano .env  # Add credentials

# Deploy
docker-compose up -d

# Setup systemd service for auto-restart
sudo nano /etc/systemd/system/mlat.service
```

`/etc/systemd/system/mlat.service`:

```ini
[Unit]
Description=MLAT Aircraft Tracking System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ec2-user/mlat-system
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Enable service
sudo systemctl enable mlat.service
sudo systemctl start mlat.service
```

#### Using ECS (Elastic Container Service)

1. Create ECR repositories
2. Push Docker images
3. Create ECS task definitions
4. Deploy to ECS cluster
5. Setup Load Balancer

### Option 2: Google Cloud Platform

```bash
# Create GCE instance
gcloud compute instances create mlat-server \
    --machine-type=e2-medium \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=20GB

# SSH and deploy
gcloud compute ssh mlat-server

# Install Docker and deploy (same as AWS)
```

### Option 3: DigitalOcean

```bash
# Create Droplet (2GB RAM, 1 vCPU minimum)
# Select Docker marketplace image

# SSH into droplet
ssh root@your-droplet-ip

# Deploy
git clone <your-repo>
cd mlat-system
cp .env.example .env
nano .env

docker-compose up -d
```

### Option 4: Kubernetes Deployment

Create Kubernetes manifests:

`k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlat-processor
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mlat-processor
  template:
    metadata:
      labels:
        app: mlat-processor
    spec:
      containers:
      - name: mlat-processor
        image: your-registry/mlat-system:latest
        env:
        - name: CKB_RPC_URL
          valueFrom:
            secretKeyRef:
              name: mlat-secrets
              key: ckb-rpc-url
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: mlat-data-pvc
```

Deploy:

```bash
kubectl apply -f k8s/
kubectl get pods
kubectl logs -f mlat-processor-xxxxx
```

## 🔒 Security Configuration

### 1. Firewall Rules

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 5000/tcp # API
sudo ufw allow 8080/tcp # Dashboard
sudo ufw enable
```

### 2. SSL/TLS Setup

Using Let's Encrypt with nginx:

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

Update nginx.conf:

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # ... rest of config
}
```

### 3. API Authentication

Add API key authentication:

```python
# In rest_api.py
from functools import wraps
from flask import request

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != os.getenv('API_KEY'):
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/aircraft')
@require_api_key
def get_aircraft():
    # ...
```

## 📊 Monitoring Setup

### 1. Application Monitoring

Add Prometheus metrics:

```python
from prometheus_client import Counter, Histogram, generate_latest

positions_calculated = Counter('mlat_positions_total', 'Total positions calculated')
solve_duration = Histogram('mlat_solve_duration_seconds', 'Time to solve position')

@app.route('/metrics')
def metrics():
    return generate_latest()
```

### 2. Log Aggregation

Using Loki and Grafana:

```yaml
# docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
```

### 3. Health Checks

Setup monitoring with Uptime Kuma or UptimeRobot:

- Monitor: `http://your-domain/api/health`
- Alert on failure
- Check every 60 seconds

## 🔄 Backup Strategy

### Database Backups

```bash
# Create backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec mlat-api sqlite3 /app/data/mlat_data.db ".backup '/app/data/backup_${DATE}.db'"

# Sync to S3
aws s3 cp /app/data/backup_${DATE}.db s3://your-bucket/backups/

# Keep only last 30 days
find /app/data/backup_*.db -mtime +30 -delete
```

Add to cron:

```bash
# Backup daily at 2 AM
0 2 * * * /path/to/backup.sh
```

## 📈 Scaling

### Horizontal Scaling

Run multiple MLAT processors:

```yaml
# docker-compose.yml
services:
  mlat-processor:
    deploy:
      replicas: 3
```

### Load Balancing

Use nginx as load balancer:

```nginx
upstream mlat_api {
    server mlat-api-1:5000;
    server mlat-api-2:5000;
    server mlat-api-3:5000;
}

server {
    location /api/ {
        proxy_pass http://mlat_api;
    }
}
```

## 🐛 Troubleshooting

### Check Service Status

```bash
docker-compose ps
docker-compose logs mlat-processor
docker-compose logs mlat-api
```

### Common Issues

**1. Database locked**
```bash
# Stop all services
docker-compose down

# Remove lock
rm data/mlat_data.db-shm data/mlat_data.db-wal

# Restart
docker-compose up -d
```

**2. Out of memory**
```bash
# Check memory usage
docker stats

# Increase Docker memory limit
# Edit /etc/docker/daemon.json
{
  "default-ulimits": {
    "memlock": {
      "Hard": -1,
      "Name": "memlock",
      "Soft": -1
    }
  }
}
```

**3. Network connectivity**
```bash
# Check network
docker network ls
docker network inspect mlat-network

# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

## 📋 Maintenance Tasks

### Daily
- Monitor logs for errors
- Check API health endpoint
- Verify data is being stored

### Weekly
- Review statistics
- Check disk space usage
- Update error logs

### Monthly
- Update Docker images
- Clean old data
- Review and optimize database
- Security updates

### Cleanup Script

```bash
#!/bin/bash
# cleanup.sh

# Clean old positions (30 days)
docker exec mlat-api python -c "
from database.mlat_db import MLATDatabase
db = MLATDatabase('/app/data/mlat_data.db')
db.connect()
db.cleanup_old_data(days=30)
db.close()
"

# Docker cleanup
docker system prune -f
```

## 🎯 Performance Optimization

1. **Database Indexing**: Already optimized in schema
2. **Connection Pooling**: Use for high load
3. **Caching**: Add Redis for recent positions
4. **CDN**: Use CloudFlare for dashboard static assets
5. **Compression**: Enable gzip in nginx

## ✅ Production Checklist

- [ ] Environment variables configured
- [ ] CKB and 4DSky configuration added
- [ ] SSL certificates installed
- [ ] Firewall rules configured
- [ ] Monitoring setup
- [ ] Backup strategy implemented
- [ ] Log rotation configured
- [ ] Health checks enabled
- [ ] Documentation updated
- [ ] Team trained on operations

---

**Your MLAT system is now production-ready!** 🚀
