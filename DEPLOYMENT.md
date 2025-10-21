# Deployment Guide

Comprehensive guide for deploying GenAI Job Assistant in various environments.

## Table of Contents

- [Local Deployment](#local-deployment)
- [Docker Deployment](#docker-deployment)
- [Cloud Deployment](#cloud-deployment)
- [Production Considerations](#production-considerations)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Local Deployment

### Linux/Mac

#### 1. Setup as Systemd Service

Create service file: `/etc/systemd/system/job-assistant-ui.service`

```ini
[Unit]
Description=GenAI Job Assistant UI
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/genai-job-assistant
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create scheduler service: `/etc/systemd/system/job-assistant-scheduler.service`

```ini
[Unit]
Description=GenAI Job Assistant Scheduler
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/genai-job-assistant
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python scripts/run_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable job-assistant-ui
sudo systemctl enable job-assistant-scheduler

# Start services
sudo systemctl start job-assistant-ui
sudo systemctl start job-assistant-scheduler

# Check status
sudo systemctl status job-assistant-ui
sudo systemctl status job-assistant-scheduler

# View logs
sudo journalctl -u job-assistant-ui -f
sudo journalctl -u job-assistant-scheduler -f
```

#### 3. Setup Nginx Reverse Proxy (Optional)

Install Nginx:
```bash
sudo apt-get install nginx
```

Create config: `/etc/nginx/sites-available/job-assistant`

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/job-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Windows

#### 1. Setup as Windows Service (using NSSM)

Download NSSM: https://nssm.cc/download

Install UI service:
```cmd
nssm install JobAssistantUI "C:\path\to\venv\Scripts\streamlit.exe" "run app.py --server.port=8501"
nssm set JobAssistantUI AppDirectory "C:\path\to\genai-job-assistant"
nssm set JobAssistantUI DisplayName "GenAI Job Assistant UI"
nssm set JobAssistantUI Description "GenAI Job Assistant Streamlit UI"
nssm set JobAssistantUI Start SERVICE_AUTO_START
nssm start JobAssistantUI
```

Install scheduler service:
```cmd
nssm install JobAssistantScheduler "C:\path\to\venv\Scripts\python.exe" "scripts\run_scheduler.py"
nssm set JobAssistantScheduler AppDirectory "C:\path\to\genai-job-assistant"
nssm set JobAssistantScheduler DisplayName "GenAI Job Assistant Scheduler"
nssm set JobAssistantScheduler Description "GenAI Job Assistant Background Scheduler"
nssm set JobAssistantScheduler Start SERVICE_AUTO_START
nssm start JobAssistantScheduler
```

#### 2. Manage Services

```cmd
# Start services
nssm start JobAssistantUI
nssm start JobAssistantScheduler

# Stop services
nssm stop JobAssistantUI
nssm stop JobAssistantScheduler

# Check status
nssm status JobAssistantUI
nssm status JobAssistantScheduler

# Remove services
nssm remove JobAssistantUI confirm
nssm remove JobAssistantScheduler confirm
```

## Docker Deployment

### Basic Docker Compose

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down

# Rebuild after changes
docker-compose up -d --build
```

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  job-assistant:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: genai-job-assistant
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - OLLAMA_HOST=http://ollama:11434
    env_file:
      - .env.production
    depends_on:
      - ollama
    networks:
      - job-assistant-network
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G

  scheduler:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: genai-job-assistant-scheduler
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
      - OLLAMA_HOST=http://ollama:11434
    env_file:
      - .env.production
    depends_on:
      - ollama
    networks:
      - job-assistant-network
    restart: always
    command: python scripts/run_scheduler.py

  ollama:
    image: ollama/ollama:latest
    container_name: ollama-service
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
    networks:
      - job-assistant-network
    restart: always
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - job-assistant
    networks:
      - job-assistant-network
    restart: always

volumes:
  ollama-data:
    driver: local

networks:
  job-assistant-network:
    driver: bridge
```

Deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Cloud Deployment

### AWS EC2

#### 1. Launch Instance

```bash
# Launch EC2 instance (Ubuntu 22.04 LTS)
# Instance type: t3.medium or larger
# Storage: 30GB minimum
# Security group: Allow ports 22, 80, 443, 8501
```

#### 2. Setup Instance

```bash
# Connect to instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.10 python3-pip python3-venv git

# Clone repository
git clone <your-repo-url>
cd genai-job-assistant

# Run setup
chmod +x scripts/setup.sh
./scripts/setup.sh

# Setup systemd services (see Local Deployment section)
```

#### 3. Configure Security

```bash
# Setup firewall
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Setup SSL with Let's Encrypt
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

#### 4. Setup CloudWatch Monitoring

Install CloudWatch agent:
```bash
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure agent
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

### Google Cloud Platform

#### 1. Create Compute Engine Instance

```bash
# Create instance
gcloud compute instances create job-assistant \
    --machine-type=e2-medium \
    --zone=us-central1-a \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=30GB \
    --tags=http-server,https-server

# SSH into instance
gcloud compute ssh job-assistant --zone=us-central1-a
```

#### 2. Setup Application

Follow same steps as AWS EC2 setup.

#### 3. Configure Firewall

```bash
# Allow HTTP/HTTPS
gcloud compute firewall-rules create allow-http \
    --allow tcp:80 \
    --target-tags http-server

gcloud compute firewall-rules create allow-https \
    --allow tcp:443 \
    --target-tags https-server
```

### DigitalOcean

#### 1. Create Droplet

- Choose Ubuntu 22.04 LTS
- Select plan: Basic ($12/month or higher)
- Add SSH key
- Create droplet

#### 2. Setup Application

```bash
# SSH into droplet
ssh root@your-droplet-ip

# Follow setup steps from AWS EC2 section
```

## Production Considerations

### Security

1. **Environment Variables**
   - Never commit `.env` to version control
   - Use secrets management (AWS Secrets Manager, HashiCorp Vault)
   - Rotate encryption keys regularly

2. **Network Security**
   - Use firewall rules
   - Enable HTTPS with SSL certificates
   - Restrict database access
   - Use VPN for admin access

3. **Application Security**
   - Keep dependencies updated
   - Regular security audits
   - Monitor for vulnerabilities
   - Implement rate limiting

### Performance

1. **Database Optimization**
   ```bash
   # Regular maintenance
   sqlite3 data/job_assistant.db "VACUUM;"
   sqlite3 data/job_assistant.db "ANALYZE;"
   ```

2. **LLM Optimization**
   - Use appropriate model size
   - Implement response caching
   - Set reasonable timeouts

3. **Resource Limits**
   - Set memory limits in Docker
   - Configure max workers for Streamlit
   - Implement request queuing

### Backup Strategy

1. **Automated Backups**
   ```bash
   # Add to crontab
   0 2 * * * cd /path/to/app && /path/to/venv/bin/python scripts/backup_db.py backup
   ```

2. **Backup Retention**
   - Keep daily backups for 7 days
   - Keep weekly backups for 4 weeks
   - Keep monthly backups for 12 months

3. **Offsite Backups**
   ```bash
   # Sync to S3
   aws s3 sync data/backups/ s3://your-bucket/backups/
   
   # Sync to Google Cloud Storage
   gsutil rsync -r data/backups/ gs://your-bucket/backups/
   ```

### Logging

1. **Centralized Logging**
   - Use ELK stack (Elasticsearch, Logstash, Kibana)
   - Or use cloud logging (CloudWatch, Stackdriver)

2. **Log Rotation**
   ```bash
   # Configure logrotate
   sudo nano /etc/logrotate.d/job-assistant
   ```

   ```
   /path/to/genai-job-assistant/logs/*.log {
       daily
       rotate 7
       compress
       delaycompress
       notifempty
       create 0644 user user
   }
   ```

## Monitoring and Maintenance

### Health Checks

1. **Application Health**
   ```bash
   # Check services
   systemctl status job-assistant-ui
   systemctl status job-assistant-scheduler
   
   # Check Ollama
   curl http://localhost:11434/api/tags
   
   # Check database
   python scripts/init_app.py
   ```

2. **Automated Monitoring**
   - Use Uptime Robot or similar
   - Monitor HTTP endpoint
   - Alert on failures

### Maintenance Tasks

1. **Daily**
   - Check logs for errors
   - Verify scheduler execution
   - Monitor disk space

2. **Weekly**
   - Review application metrics
   - Check backup integrity
   - Update dependencies

3. **Monthly**
   - Security updates
   - Performance optimization
   - Database maintenance

### Troubleshooting

1. **Service Won't Start**
   ```bash
   # Check logs
   sudo journalctl -u job-assistant-ui -n 50
   
   # Check permissions
   ls -la /path/to/genai-job-assistant
   
   # Check dependencies
   python scripts/init_app.py
   ```

2. **High Memory Usage**
   ```bash
   # Check processes
   ps aux | grep python
   
   # Monitor resources
   htop
   
   # Restart services
   sudo systemctl restart job-assistant-ui
   ```

3. **Database Locked**
   ```bash
   # Check for locks
   lsof data/job_assistant.db
   
   # Kill blocking process
   kill -9 <pid>
   ```

## Scaling

### Horizontal Scaling

For multiple users, consider:
- Load balancer (Nginx, HAProxy)
- Multiple application instances
- Shared database (PostgreSQL instead of SQLite)
- Redis for caching

### Vertical Scaling

Increase resources:
- More CPU cores for LLM processing
- More RAM for larger models
- Faster storage for database

## Support

For deployment issues:
1. Check logs: `logs/job_assistant.log`
2. Run diagnostics: `python scripts/init_app.py`
3. Review configuration: `config/config.yaml`
4. Check service status: `systemctl status job-assistant-*`
