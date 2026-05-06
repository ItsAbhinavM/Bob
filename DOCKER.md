# Docker Setup Guide for Bob - Voice AI Assistant

## Overview

Both frontend and backend have been Dockerized using **multi-stage builds** to keep images lightweight.

### Image Sizes
- **Backend**: 447MB (optimized - excludes venv)
- **Frontend**: 751MB (optimized - excludes node_modules, build artifacts)

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- `.env` file with required API keys in the backend directory

### Run with Docker Compose

```bash
# Start both services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Build Images Individually

### Backend
```bash
cd backend
docker build -t bob-backend:1.0.0 .
```

### Frontend
```bash
cd frontend
docker build -t bob-frontend:1.0.0 .
```

## Run Containers Individually

### Backend
```bash
docker run -d \
  --name bob-backend \
  -p 8000:8000 \
  -e GEMINI_API_KEY=your_key_here \
  -e OPENWEATHER_API_KEY=your_key_here \
  -e SENDER_EMAIL=your_email@gmail.com \
  -e SENDER_PASSWORD=your_app_password \
  -e SMTP_SERVER=smtp.gmail.com \
  -e SMTP_PORT=587 \
  -e DISCORD_WEBHOOK=your_webhook_url \
  -e GITHUB_TOKEN=your_github_token \
  -e GITHUB_DEFAULT_REPO=owner/repo \
  -e AZURE_API_KEY=your_azure_key \
  bob-backend:1.0.0
```

### Frontend
```bash
docker run -d \
  --name bob-frontend \
  -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  bob-frontend:1.0.0
```

## Optimization Details

### Backend Optimization (.dockerignore)
Excludes:
- Python cache (`__pycache__`, `*.pyc`)
- Virtual environments (not needed - copied from builder)
- Test files
- Database files
- Git files
- Source control

**Multi-stage build benefit**: Only the final image includes the venv, saving ~300MB vs copying the entire venv folder.

### Frontend Optimization (.dockerignore)
Excludes:
- node_modules (not needed - copied from builder)
- Build artifacts from build stage
- Git and CI/CD files
- Test files

**Multi-stage build benefit**: Final image only includes the optimized Next.js build and production dependencies.

## Health Checks

Both containers include health checks:

**Backend**: Checks `/health` endpoint every 30 seconds
**Frontend**: Checks HTTP response every 30 seconds

View health status:
```bash
docker ps  # Shows health status in the STATUS column
```

## Environment Variables

Create a `.env` file in the project root or pass variables to docker-compose:

```bash
GEMINI_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_weather_api_key
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
DISCORD_WEBHOOK=your_webhook_url
GITHUB_TOKEN=your_github_token
GITHUB_DEFAULT_REPO=owner/repo
AZURE_API_KEY=your_azure_key
```

## Troubleshooting

### Backend won't start
```bash
# Check logs
docker logs bob-backend

# Verify environment variables
docker exec bob-backend env | grep -i api
```

### Frontend won't connect to backend
```bash
# Ensure backend is healthy
docker ps

# Check if containers are on the same network
docker network inspect bob-network
```

### Port conflicts
```bash
# Kill process using the port
sudo lsof -ti:8000 | xargs kill -9  # for port 8000
sudo lsof -ti:3000 | xargs kill -9  # for port 3000
```

## Production Deployment

For production:

1. **Use environment variables** - Never hardcode secrets
2. **Set `NODE_ENV=production`** in frontend (already done)
3. **Enable HTTPS** - Use nginx reverse proxy
4. **Database persistence** - Mount volumes for SQLite
5. **Resource limits** - Add memory/CPU limits in docker-compose

Example production docker-compose addition:
```yaml
services:
  backend:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

## Cleanup

```bash
# Remove containers
docker-compose down

# Remove images
docker rmi bob-backend:1.0.0 bob-frontend:1.0.0

# Remove volumes (be careful!)
docker volume prune

# Full cleanup
docker system prune -a
```
