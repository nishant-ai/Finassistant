# Backend Deployment Guide (EC2)

This guide covers deploying the Financial Assistant backend (API + Agent) to AWS EC2 using Docker.

## Important Note

**For EC2 deployment, we use `docker-compose.backend.yml` which:**
- Starts **only the backend** container
- Exposes port **8000** to the host (accessible externally)
- Does **not** start the frontend (frontend will be on S3 + CloudFront)

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for details on all docker-compose files.

## Prerequisites

- AWS Account with EC2 access
- Domain name (optional, for SSL/HTTPS)
- All required API keys (see `.env.example`)

## Architecture Overview

```
Internet → EC2 Instance → Docker Container (Backend API on port 8000)
```

## Step 1: Launch EC2 Instance

### 1.1 Create EC2 Instance
```bash
# Recommended specifications:
- AMI: Ubuntu 22.04 LTS
- Instance Type: t3.medium or larger (2 vCPU, 4GB RAM minimum)
- Storage: 20GB gp3 SSD minimum
- VPC: Default or custom
```

### 1.2 Configure Security Group
Create or update security group with these inbound rules:

| Type  | Protocol | Port Range | Source    | Description           |
|-------|----------|------------|-----------|-----------------------|
| SSH   | TCP      | 22         | Your IP   | SSH access            |
| HTTP  | TCP      | 80         | 0.0.0.0/0 | HTTP traffic          |
| HTTPS | TCP      | 443        | 0.0.0.0/0 | HTTPS traffic         |
| Custom| TCP      | 8000       | 0.0.0.0/0 | API (dev only)        |

**Note**: For production, restrict port 8000 or use a reverse proxy (nginx).

### 1.3 Allocate Elastic IP (Optional but Recommended)
Associate an Elastic IP to have a permanent public IP address.

## Step 2: Connect and Setup EC2

### 2.1 SSH into EC2
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### 2.2 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2.3 Install Docker
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Start Docker
sudo systemctl enable docker
sudo systemctl start docker

# Log out and back in for group changes to take effect
exit
```

SSH back in:
```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

### 2.4 Install Docker Compose
```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```

## Step 3: Deploy Application

### 3.1 Clone Repository
```bash
cd ~
git clone https://github.com/yourusername/Finassistant.git
cd Finassistant
```

### 3.2 Create Environment File
```bash
nano .env
```

Add your environment variables (copy from `.env.example` and fill in real values):
```env
OPENAI_API_KEY=your_actual_key
PINECONE_API_KEY=your_actual_key
GOOGLE_API_KEY=your_actual_key
GROQ_API_KEY=your_actual_key
ALPHA_VANTAGE_API_KEY=your_actual_key
NEWS_API_KEY=your_actual_key
MONGODB_URL=your_mongodb_connection_string
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### 3.3 Build and Run with Docker Compose (Backend Only)
```bash
# Build the backend image
docker-compose -f docker-compose.backend.yml build

# Start the backend service
docker-compose -f docker-compose.backend.yml up -d

# Check logs
docker-compose -f docker-compose.backend.yml logs -f
```

**Note**: We use `docker-compose.backend.yml` which only starts the backend container with port 8000 exposed.

### 3.4 Verify Deployment
```bash
# Check if container is running
docker ps
# Should show: finassistant-backend with ports 8000/tcp

# Test API locally on EC2
curl http://localhost:8000/api/health

# Test from your computer (replace with your actual EC2 public IP)
curl http://your-ec2-public-ip:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-08T...",
  "version": "1.0.0"
}
```

## Step 4: Setup Reverse Proxy with Nginx (Production)

### 4.1 Install Nginx
```bash
sudo apt install nginx -y
```

### 4.2 Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/finassistant
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or EC2 public IP

    client_max_body_size 10M;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # WebSocket support
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 4.3 Enable Site and Restart Nginx
```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/finassistant /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 4.4 Test Nginx Proxy
```bash
curl http://your-domain-or-ip/api/health
```

## Step 5: Setup SSL with Let's Encrypt (Optional)

### 5.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 5.2 Obtain SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com
```

Follow the prompts. Certbot will automatically update your Nginx configuration.

### 5.3 Auto-renewal Setup
```bash
# Test renewal
sudo certbot renew --dry-run

# Renewal is automatic via systemd timer
sudo systemctl status certbot.timer
```

## Step 6: Setup Systemd Service (Alternative to Docker Compose)

If you prefer systemd over docker-compose:

### 6.1 Create Service File
```bash
sudo nano /etc/systemd/system/finassistant.service
```

Add:
```ini
[Unit]
Description=Financial Assistant Backend
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/Finassistant
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

### 6.2 Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable finassistant
sudo systemctl start finassistant
sudo systemctl status finassistant
```

## Step 7: Monitoring and Maintenance

### 7.1 View Logs
```bash
# Docker Compose logs
docker-compose logs -f backend

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 7.2 Update Application
```bash
cd ~/Finassistant
git pull
docker-compose -f docker-compose.backend.yml build
docker-compose -f docker-compose.backend.yml up -d
```

### 7.3 Backup Data
```bash
# Backup ChromaDB and SEC filings
sudo tar -czf backup-$(date +%Y%m%d).tar.gz chroma_db/ sec-edgar-filings/

# Copy to S3 (optional)
aws s3 cp backup-$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

### 7.4 Monitor Resource Usage
```bash
# System resources
htop

# Docker stats
docker stats

# Disk usage
df -h
```

## Step 8: Security Best Practices

### 8.1 Firewall Configuration
```bash
# Enable UFW
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 8.2 Update CORS Settings
Edit [api/app.py:54-60](api/app.py#L54-L60) to restrict CORS origins:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 8.3 Secure Environment Variables
```bash
# Ensure .env has proper permissions
chmod 600 .env
```

### 8.4 Enable AWS CloudWatch (Optional)
Configure CloudWatch for logs and metrics monitoring.

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker-compose -f docker-compose.backend.yml logs

# Check if port is in use
sudo lsof -i :8000

# Restart container
docker-compose -f docker-compose.backend.yml restart
```

### Cannot Connect to MongoDB
- Verify MongoDB Atlas IP whitelist includes your EC2 IP
- Check MONGODB_URL in .env file
- Test connection: `mongo "your-mongodb-url"`

### High Memory Usage
```bash
# Check memory
free -h

# Restart container with memory limit
docker-compose -f docker-compose.backend.yml down
# Edit docker-compose.backend.yml and add under backend service:
#   mem_limit: 2g
docker-compose -f docker-compose.backend.yml up -d
```

### API Returns 502 Bad Gateway
- Check if backend container is running: `docker ps`
- Check nginx error logs: `sudo tail -f /var/log/nginx/error.log`
- Verify nginx proxy configuration

## Performance Optimization

### 8.1 Enable Docker Logging Driver
Edit `docker-compose.yml`:
```yaml
services:
  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 8.2 Use Gunicorn Workers (Optional)
If you need multiple workers for higher concurrency, update Dockerfile CMD:
```dockerfile
CMD ["gunicorn", "api.app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Add gunicorn to requirements.txt:
```
gunicorn>=21.0.0
```

Then rebuild:
```bash
docker-compose -f docker-compose.backend.yml build
docker-compose -f docker-compose.backend.yml up -d
```

## Cost Optimization

- Use t3.medium for production (around $30-40/month)
- Consider Reserved Instances or Savings Plans for discounts
- Monitor with AWS Cost Explorer
- Use CloudWatch alarms for budget alerts

## Next Steps

1. Configure CI/CD with GitHub Actions
2. Setup automated backups
3. Configure CloudWatch monitoring
4. Implement log aggregation
5. Deploy frontend to S3 + CloudFront (see DEPLOYMENT_FRONTEND.md)

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review API docs: `http://your-domain/docs`
- MongoDB connection issues: Verify IP whitelist in Atlas
