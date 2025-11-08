# 🐳 Docker Testing Guide - Local Full Stack Testing

This guide walks you through testing your complete application (Frontend + Backend) using Docker locally before deploying to production.

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ **Docker Desktop** installed (or Docker Engine + Docker Compose)
  - [Download Docker Desktop](https://www.docker.com/products/docker-desktop/)
- ✅ **Git** installed
- ✅ **API Keys** ready (see `.env.example`)
- ✅ **At least 4GB RAM** available for Docker
- ✅ **10GB disk space** for images and containers

### Verify Docker Installation

```bash
# Check Docker version
docker --version
# Output: Docker version 24.x.x or higher

# Check Docker Compose version
docker-compose --version
# Output: Docker Compose version v2.x.x or higher

# Verify Docker is running
docker ps
# Should show empty list or running containers
```

---

## 🚀 Quick Start (TL;DR)

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 2. Build and start everything
docker-compose up --build

# 3. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:3000/api/health (proxied through nginx)
# API Docs: http://localhost:3000/api/docs
```

---

## 📖 Detailed Step-by-Step Guide

### Step 1: Prepare Your Environment

#### 1.1 Clone or Navigate to Project
```bash
cd /path/to/Finassistant
```

#### 1.2 Create Environment File
```bash
# Copy the example file
cp .env.example .env

# Edit with your favorite editor
nano .env
# or
code .env
# or
vim .env
```

#### 1.3 Add Your API Keys
Edit the `.env` file with your actual API keys:

```env
GOOGLE_API_KEY=AIzaSy...your-actual-key
NEWS_API_KEY=215f16...your-actual-key
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/...

# Optional keys (add if you have them)
OPENAI_API_KEY=sk-proj-...
GROQ_API_KEY=gsk_...
ALPHA_VANTAGE_API_KEY=...
```

**Important**: Never commit your `.env` file to version control!

---

### Step 2: Build Docker Images

This step compiles your application into Docker images.

```bash
# Build both frontend and backend images
docker-compose build

# Expected output:
# [+] Building backend...
# [+] Building frontend...
# Successfully tagged finassistant-backend:latest
# Successfully tagged finassistant-frontend:latest
```

**What happens during build:**
- ✅ Backend: Python dependencies installed, code copied
- ✅ Frontend: npm packages installed, React app built, nginx configured

**Build time**: ~3-5 minutes on first build (subsequent builds are faster due to caching)

---

### Step 3: Start the Containers

```bash
# Start all services in detached mode (runs in background)
docker-compose up -d

# Expected output:
# Creating network "finassistant_finassistant-network" ... done
# Creating finassistant-backend ... done
# Creating finassistant-frontend ... done
```

**What's happening:**
1. Docker creates a private network for your services
2. Backend container starts and waits for health check
3. Frontend container starts after backend is healthy
4. Services connect and communicate

---

### Step 4: Verify Services Are Running

#### 4.1 Check Container Status
```bash
docker-compose ps

# Expected output:
# NAME                    STATUS                   PORTS
# finassistant-backend    Up (healthy)             8000/tcp
# finassistant-frontend   Up (healthy)             0.0.0.0:3000->80/tcp
```

**Status meanings:**
- `Up (healthy)` - ✅ Container is running and passed health checks
- `Up (health: starting)` - ⏳ Container is starting, wait a moment
- `Exit 1` - ❌ Container failed, check logs

#### 4.2 View Logs
```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs backend
docker-compose logs frontend

# Last 50 lines
docker-compose logs --tail=50 backend
```

**What to look for in logs:**

**Backend logs (healthy):**
```
finassistant-backend | INFO:     Started server process [1]
finassistant-backend | INFO:     Waiting for application startup.
finassistant-backend | INFO:     Application startup complete.
finassistant-backend | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend logs (healthy):**
```
finassistant-frontend | /docker-entrypoint.sh: Configuration complete; ready for start up
```

---

### Step 5: Test the Application

#### 5.1 Access the Frontend
Open your browser and navigate to:

```
http://localhost:3000
```

**You should see:**
- ✅ Financial Assistant UI loads
- ✅ Chat interface is visible
- ✅ No error messages in browser console

#### 5.2 Test Backend API Health
```bash
# Test via nginx proxy (frontend → backend)
curl http://localhost:3000/api/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-11-07T...",
  "version": "1.0.0"
}
```

#### 5.3 Test API Documentation
Open in browser:
```
http://localhost:3000/api/docs
```

You should see the interactive FastAPI Swagger documentation.

#### 5.4 Test a Chat Query
```bash
# Quick test via API
curl -X POST "http://localhost:3000/api/chat?query=What%20is%20Apple%27s%20current%20stock%20price%3F"

# Expected response (will take 3-5 seconds):
{
  "success": true,
  "query": "What is Apple's current stock price?",
  "query_type": "chat",
  "result": "Apple (AAPL) is currently trading at...",
  "timestamp": "2024-11-07T...",
  "metadata": {
    "execution_time_seconds": 3.2,
    "session_id": "..."
  }
}
```

#### 5.5 Test via Frontend UI
1. Go to http://localhost:3000
2. Select "Chat" mode
3. Type: "What is Tesla's P/E ratio?"
4. Press Enter or click Send
5. **Expected**: You get a response within 3-5 seconds

#### 5.6 Test Think Mode
1. In the UI, switch to "Think" mode
2. Type: "Analyze Apple's financial health"
3. Press Enter
4. **Expected**: You get a comprehensive report in 15-30 seconds

---

### Step 6: Test Communication Between Containers

#### 6.1 Verify Network Communication
```bash
# Access backend container shell
docker exec -it finassistant-backend /bin/sh

# Inside backend container, test if it's running
curl http://localhost:8000/api/health

# Exit container
exit
```

#### 6.2 Verify Frontend → Backend Proxy
```bash
# Access frontend container
docker exec -it finassistant-frontend /bin/sh

# Inside frontend container, test proxy
wget -O- http://backend:8000/api/health

# Exit
exit
```

**This confirms**: Frontend nginx is correctly proxying requests to backend.

---

### Step 7: Inspect Containers (Advanced)

#### 7.1 View Container Resource Usage
```bash
docker stats

# Output shows:
# CONTAINER          CPU %    MEM USAGE / LIMIT    NET I/O
# finassistant-back  5%       500MB / 4GB          10MB / 5MB
# finassistant-front 1%       20MB / 4GB           5MB / 10MB
```

#### 7.2 Inspect Container Details
```bash
# Backend inspection
docker inspect finassistant-backend

# Check environment variables
docker exec finassistant-backend env | grep API_KEY

# Check mounted volumes
docker inspect finassistant-backend | grep -A 10 Mounts
```

#### 7.3 Check Network Configuration
```bash
# List Docker networks
docker network ls

# Inspect the application network
docker network inspect finassistant_finassistant-network

# Should show both containers connected
```

---

## 🧪 Testing Scenarios

### Scenario 1: Fresh Build Test
```bash
# Clean everything
docker-compose down -v
docker system prune -f

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d

# Verify
docker-compose logs -f
```

**When to use**: Testing that your Dockerfiles work correctly without cached layers.

---

### Scenario 2: Development Mode with Hot Reload
If you want to test code changes without rebuilding:

**Edit `docker-compose.yml`:**
```yaml
backend:
  volumes:
    - ./agent:/app/agent
    - ./api:/app/api
  command: uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

**Restart:**
```bash
docker-compose down
docker-compose up -d
```

Now code changes in `agent/` and `api/` will reload automatically.

---

### Scenario 3: Test Persistence (Data Survival)
```bash
# Make a query that saves to MongoDB
curl -X POST "http://localhost:3000/api/chat?query=Test%20query"

# Stop containers
docker-compose down

# Start again
docker-compose up -d

# Check if session history is preserved
curl "http://localhost:3000/api/sessions?user_id=default_user"

# Should show previous sessions
```

---

### Scenario 4: Simulate Production Environment
Test with production-like settings:

```bash
# Use production environment
export COMPOSE_FILE=docker-compose.yml
export COMPOSE_PROJECT_NAME=finassistant-prod

# Start with production config
docker-compose -f docker-compose.yml up -d

# Test under load (install Apache Bench)
ab -n 100 -c 10 http://localhost:3000/api/health
```

---

## 🔍 Troubleshooting

### Problem 1: Container Won't Start

**Symptoms:**
```bash
docker-compose ps
# Shows: Exit 1 or Restarting
```

**Solution:**
```bash
# Check logs for errors
docker-compose logs backend

# Common issues:
# - Missing environment variable: Add to .env
# - Port already in use: Change ports in docker-compose.yml
# - Out of memory: Increase Docker memory limit in settings
```

---

### Problem 2: "Cannot Connect to Backend"

**Symptoms:**
- Frontend loads but queries fail
- Console error: "Network Error" or "ERR_CONNECTION_REFUSED"

**Solution:**
```bash
# Check if backend is healthy
docker-compose ps backend
# Should show: Up (healthy)

# Check backend logs
docker-compose logs backend | grep ERROR

# Test backend directly
curl http://localhost:3000/api/health

# If that fails, check nginx proxy
docker exec finassistant-frontend cat /etc/nginx/conf.d/default.conf
```

---

### Problem 3: MongoDB Connection Failed

**Symptoms:**
```
WARNING: MongoDB connection failed: ...
```

**Solution:**
```bash
# Verify MONGODB_URL in .env
cat .env | grep MONGODB_URL

# Test MongoDB connection
docker exec -it finassistant-backend python -c "
from pymongo import MongoClient
import os
client = MongoClient(os.getenv('MONGODB_URL'))
print('Connected:', client.server_info())
"

# Common fixes:
# - IP whitelist: Add 0.0.0.0/0 in MongoDB Atlas
# - Wrong credentials: Check username/password
# - Network issue: Test from host machine
```

---

### Problem 4: "Build Failed" Errors

**Symptoms:**
```
ERROR [build X/Y] RUN npm ci
```

**Solution:**
```bash
# Clear Docker cache
docker builder prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check disk space
docker system df

# Clean up if needed
docker system prune -a --volumes
```

---

### Problem 5: Slow Performance

**Symptoms:**
- Queries take >30 seconds
- High CPU/memory usage

**Solution:**
```bash
# Check resource usage
docker stats

# Increase Docker resources
# Docker Desktop → Settings → Resources
# - CPUs: 4+
# - Memory: 4GB+

# Check logs for bottlenecks
docker-compose logs backend | grep -i "slow\|timeout"
```

---

### Problem 6: Frontend Shows Blank Page

**Symptoms:**
- http://localhost:3000 loads but shows nothing
- Browser console shows errors

**Solution:**
```bash
# Check frontend build
docker-compose logs frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Check browser console (F12)
# Look for:
# - API_URL configuration errors
# - CORS errors
# - JavaScript errors

# Check nginx is serving files
docker exec finassistant-frontend ls -la /usr/share/nginx/html
# Should show: index.html, assets/, etc.
```

---

## 🛑 Stopping and Cleaning Up

### Stop Services (Keep Data)
```bash
# Stop all containers
docker-compose down

# Containers stopped, data volumes preserved
```

### Complete Cleanup (Remove Everything)
```bash
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove images
docker rmi finassistant-backend finassistant-frontend

# Clean up all unused Docker resources
docker system prune -a --volumes
```

**Warning**: This deletes ALL data including ChromaDB and cached SEC filings!

---

## 📊 Monitoring and Logs

### Real-Time Monitoring
```bash
# Watch logs live
docker-compose logs -f

# Watch specific service
docker-compose logs -f backend

# Show timestamps
docker-compose logs -f --timestamps

# Filter logs
docker-compose logs backend | grep ERROR
```

### Resource Monitoring
```bash
# Live stats
docker stats

# Export stats to file
docker stats --no-stream > docker-stats.txt
```

### Health Checks
```bash
# Check health status
docker inspect finassistant-backend | grep -A 5 Health

# View health check logs
docker inspect finassistant-backend | jq '.[0].State.Health'
```

---

## ✅ Verification Checklist

Before considering your Docker setup complete, verify:

- [ ] `docker-compose ps` shows both containers as "Up (healthy)"
- [ ] `curl http://localhost:3000/api/health` returns `{"status": "healthy"}`
- [ ] Frontend loads at http://localhost:3000
- [ ] Chat query returns a response
- [ ] Think query generates a report
- [ ] API docs accessible at http://localhost:3000/api/docs
- [ ] Logs show no errors: `docker-compose logs | grep ERROR`
- [ ] MongoDB connection works (check logs)
- [ ] Session history persists across restarts
- [ ] Resource usage is reasonable: `docker stats`

---

## 🎯 Next Steps After Local Testing

Once everything works locally:

1. **Tag and Version Your Images**
   ```bash
   docker tag finassistant-backend:latest yourdockerhub/finassistant-backend:v1.0
   docker tag finassistant-frontend:latest yourdockerhub/finassistant-frontend:v1.0
   ```

2. **Push to Docker Hub** (Optional)
   ```bash
   docker login
   docker push yourdockerhub/finassistant-backend:v1.0
   docker push yourdockerhub/finassistant-frontend:v1.0
   ```

3. **Deploy to Production**
   - Backend: Follow [DEPLOYMENT_BACKEND.md](DEPLOYMENT_BACKEND.md)
   - Frontend: Follow [DEPLOYMENT_FRONTEND.md](DEPLOYMENT_FRONTEND.md)

4. **Setup CI/CD**
   - Automate builds with GitHub Actions
   - Auto-deploy on git push

---

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: `docker-compose logs -f`
2. **Verify environment**: `docker exec finassistant-backend env`
3. **Test connectivity**: `docker exec finassistant-frontend ping backend`
4. **Review this guide**: Most issues are covered in Troubleshooting
5. **Check Docker resources**: Ensure enough CPU/RAM allocated

**Still stuck?**
- Create an issue with logs and error messages
- Include: `docker-compose ps`, `docker-compose logs`, `docker stats`

---

## 📝 Quick Reference Commands

```bash
# Build and start
docker-compose up --build -d

# Stop
docker-compose down

# Restart a service
docker-compose restart backend

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Clean up
docker-compose down -v && docker system prune -a

# Access container shell
docker exec -it finassistant-backend /bin/sh

# Run commands in container
docker exec finassistant-backend python -m agent.agent chat "test query"

# Export container
docker export finassistant-backend > backend.tar

# Monitor resources
docker stats
```

---

## 🎉 Success!

If you've reached this point and all checks pass, congratulations! Your Docker setup is working perfectly. You're ready to deploy to production or continue development with confidence that your containerized environment matches production.

**What you've achieved:**
- ✅ Reproducible development environment
- ✅ Isolated services with proper networking
- ✅ Production-like testing locally
- ✅ Confidence in your deployment process

Happy coding! 🚀
