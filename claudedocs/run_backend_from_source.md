<!-- claudedocs/run_backend_from_source.md -->
# Running Backend from Source (Hybrid Setup)

**Date**: 2025-10-13
**Purpose**: Run backend from source code for debugging while keeping Presenton in Docker

---

## Overview

This guide explains how to run the backend service directly from source code (not in Docker) while keeping Presenton running in Docker. This is useful for:
- Debugging backend code with better visibility
- Faster development iteration (no Docker rebuild)
- Direct access to backend logs and error messages
- Easy code modification and testing

## Architecture (雙 Ollama 配置)

```
┌─────────────────────────────────────────────────────────┐
│              Your Development Machine                    │
│                                                          │
│  ┌────────────────────┐      ┌──────────────┐         │
│  │ Backend (Source)   │      │  Presenton   │         │
│  │  Python/FastAPI    │◄─────┤  (Docker)    │         │
│  │  localhost:5000    │      │  port 8000   │         │
│  │  (realtime logger) │      └──────┬───────┘         │
│  └────┬───────┬───────┘             │                  │
│       │       │                     │                  │
│       │       │                     ▼                  │
│       │       │           ┌──────────────┐            │
│       │       │           │  Ollama #1   │            │
│       │       │           │ gpt-oss:20b  │            │
│       │       └──────────►│ port 11434   │            │
│       │                   └──────────────┘            │
│       │                    (簡報內容生成)              │
│       │                                                │
│       │                   ┌──────────────┐            │
│       │                   │  Ollama #2   │            │
│       └──────────────────►│  Zephyr 7B   │            │
│                           │ port 11435   │            │
│                           └──────────────┘            │
│                            (演講稿生成)                 │
│                                                        │
└────────────────────────────┬───────────────────────────┘
                             │
                             ▼
                    ┌──────────────┐
                    │  Pexels API  │
                    │   (Cloud)    │
                    └──────────────┘
```

### 架構要點

- **Backend 從源碼運行**: 提供 realtime logger，方便調試
- **Ollama #1 (port 11434)**: gpt-oss:20b 模型，用於簡報內容分析和生成
- **Ollama #2 (port 11435)**: Zephyr 7B 模型，專門用於演講稿生成
- **Presenton (Docker)**: PPT 生成引擎，連接到 Ollama #1

---

## Prerequisites

### 1. System Requirements

- Python 3.11+ installed
- pip and virtualenv/venv
- Ollama installed and running (需要兩個實例)
- Docker and Docker Compose (for Presenton)

### 2. Verify Prerequisites

```bash
# Check Python version
python3 --version
# Should show: Python 3.11.x or higher

# Check pip
pip3 --version

# Check Ollama
ollama --version

# Check models (需要兩個模型)
ollama list
# Should show gpt-oss:20b and zephyr:7b

# Check if Ollama instances are running
curl http://localhost:11434/api/tags  # Ollama #1
curl http://localhost:11435/api/tags  # Ollama #2 (if already started)

# Check Docker
docker --version
docker-compose --version
```

---

## Step-by-Step Setup

### Step 1: Stop Docker Backend (Keep Presenton)

First, we need to stop the backend container but keep Presenton running.

```bash
# Stop backend container only
docker-compose stop backend

# Verify Presenton is still running
docker-compose ps
# Should show presenton-api as Up, backend as Exited
```

### Step 2: Create Python Virtual Environment

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate

# Your prompt should now show (venv)
```

### Step 3: Install Dependencies

```bash
# Ensure you're in the backend directory with venv activated
pip install --upgrade pip

# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list | grep -E "fastapi|uvicorn|httpx"
```

**Expected packages**:
- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- httpx==0.25.1
- pydantic==2.5.0
- python-dotenv==1.0.0

### Step 4: Configure Environment Variables

The backend needs to access the `.env` file in the project root.

```bash
# Check if .env exists in project root
ls -la ../.env

# If it exists, you can either:
# Option A: Copy .env to backend directory
cp ../.env .

# Option B: Create symlink (recommended)
ln -s ../.env .env

# Verify .env is accessible
cat .env | head -5
```

**Important**: Make sure these environment variables are set correctly:

```bash
# .env file should contain:
PRESENTON_API_KEY=sk-presenton-...
PRESENTON_API_URL=http://localhost:8000  # ← Important: localhost, not container name
OLLAMA_URL=http://localhost:11434       # Ollama #1 (gpt-oss:20b)
OLLAMA_MODEL=gpt-oss:20b                # ← Important: correct model name
PEXELS_API_KEY=...
BACKEND_PORT=5000
CORS_ORIGINS=*
DEBUG=True
OUTPUT_DIR=./output
```

**Critical Changes for Source Mode**:
- When running from source, `PRESENTON_API_URL` should be `http://localhost:8000`
- In Docker, it's `http://presenton:8000` (container name)
- `OLLAMA_URL` 指向 Ollama #1 (port 11434)
- Ollama #2 (port 11435) 由 ZephyrService 內部配置處理

### Step 5: Update Configuration for Local Development

Create or verify the configuration loads correctly:

```bash
# Test configuration loading
python3 -c "
from app.config import get_settings
settings = get_settings()
print(f'Presenton URL: {settings.presenton_api_url}')
print(f'Ollama URL: {settings.ollama_url}')
print(f'Backend Port: {settings.backend_port}')
"
```

**Expected output**:
```
Presenton URL: http://localhost:8000
Ollama URL: http://localhost:11434
Backend Port: 5000
```

### Step 6: Create Output Directory

```bash
# Create output directory if it doesn't exist
mkdir -p output

# Verify permissions
ls -ld output
```

### Step 7: Run Backend Server

Now you can start the backend server from source:

```bash
# Method 1: Using uvicorn directly (recommended for development)
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# Method 2: Using Python module
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# Method 3: Run main.py directly (if configured)
python3 -m app.main
```

**Expected output**:
```
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Flags explanation**:
- `--host 0.0.0.0`: Listen on all interfaces (accessible from localhost and network)
- `--port 5000`: Use port 5000 (must match frontend expectation)
- `--reload`: Auto-reload on code changes (great for development!)

---

## Step 8: Verify Everything Works

### 8.1 Check Backend Health

Open a new terminal (keep backend running) and test:

```bash
# Test backend health endpoint
curl http://localhost:5000/api/health | python3 -m json.tool

# Expected response:
{
    "status": "healthy",
    "services": {
        "presenton": "connected",
        "ollama": "connected",
        "pexels": "connected",
        "zephyr": "available"
    }
}

# Note: 如果 zephyr 顯示 "not_installed" 或 "not_available"，
# 表示 Ollama #2 未正確啟動或 Zephyr 7B 模型未安裝
```

### 8.2 Check API Documentation

Open browser:
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

### 8.3 Check All Services

```bash
# Check Presenton (Docker)
curl http://localhost:8000/

# Check Ollama #1 (Host - gpt-oss:20b)
curl http://localhost:11434/api/tags

# Check Ollama #2 (Host - Zephyr 7B)
curl http://localhost:11435/api/tags

# Check Frontend (if running)
curl -I http://localhost:8080/

# Check all Ollama models
ollama list
# Should show both gpt-oss:20b and zephyr:7b
```

---

## Troubleshooting Common Issues

### Issue 1: ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'app'`

**Solution**:
```bash
# Make sure you're in the backend directory
pwd  # Should show: .../TeacherAssist/backend

# Make sure venv is activated
which python3  # Should show: .../backend/venv/bin/python3

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue 2: Connection Refused to Presenton

**Error**: `Error checking Presenton: Connection refused`

**Solution**:
```bash
# Check if Presenton container is running
docker-compose ps presenton

# If not running, start it:
docker-compose up -d presenton

# Check Presenton logs
docker-compose logs presenton

# Verify you can reach Presenton from host
curl http://localhost:8000/
```

### Issue 3: Connection Refused to Ollama

**Error**: `Error checking Ollama: Connection refused`

**Solution**:
```bash
# Start Ollama #1 (port 11434) - gpt-oss:20b
ollama serve > /tmp/ollama-11434.log 2>&1 &

# Verify it's running
curl http://localhost:11434/api/tags

# Start Ollama #2 (port 11435) - Zephyr 7B
export OLLAMA_HOST=127.0.0.1:11435
ollama serve > /tmp/ollama-11435.log 2>&1 &

# Verify it's running
curl http://localhost:11435/api/tags

# Reset environment variable
unset OLLAMA_HOST

# Check models are available
ollama list | grep -E "gpt-oss:20b|zephyr:7b"
```

### Issue 4: Port Already in Use

**Error**: `Address already in use: 0.0.0.0:5000`

**Solution**:
```bash
# Find what's using port 5000
lsof -i :5000

# If it's the Docker backend container:
docker-compose stop backend

# If it's another process:
# Kill it or change the port in .env:
# BACKEND_PORT=5001
```

### Issue 5: Can't Import Modules

**Error**: `ImportError: cannot import name 'ZephyrService' from 'app.services'`

**Solution**:
```bash
# Check if all __init__.py files exist
ls -la app/__init__.py
ls -la app/api/__init__.py
ls -la app/services/__init__.py
ls -la app/utils/__init__.py

# If missing, create them:
touch app/__init__.py
touch app/api/__init__.py
touch app/services/__init__.py
touch app/utils/__init__.py
```

### Issue 6: Pydantic Validation Error

**Error**: `ValidationError: 1 validation error for Settings`

**Solution**:
```bash
# Check .env file exists and is readable
cat .env

# Make sure required keys are set:
grep -E "PRESENTON_API_KEY|PEXELS_API_KEY" .env

# If missing, add them to .env
```

---

## Development Workflow

### Making Code Changes

With `--reload` flag, the server automatically reloads when you save files:

1. Edit code in your IDE (e.g., `backend/app/api/routes.py`)
2. Save the file
3. Watch terminal - you'll see:
   ```
   WARNING:  WatchFiles detected changes in 'app/api/routes.py'. Reloading...
   INFO:     Shutting down
   INFO:     Application startup complete.
   ```
4. Test your changes immediately

### Viewing Logs

Running from source gives you direct access to all logs:

- **INFO logs**: Normal operation messages
- **ERROR logs**: Exceptions and errors
- **DEBUG logs**: Detailed debugging info (if DEBUG=True)

All logs appear directly in your terminal in real-time!

### Testing API Endpoints

```bash
# Test generate endpoint
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "This is a test presentation content with more than fifty characters to meet the minimum requirement.",
    "template": "educational",
    "language": "zh-TW"
  }'

# Test progress endpoint
curl http://localhost:5000/api/progress/<task_id>

# Test health endpoint
curl http://localhost:5000/api/health
```

---

## Debugging Tips

### 1. Add Print Statements

```python
# In any service file (e.g., app/services/ollama_service.py)
async def analyze_content(self, content: str):
    print(f"DEBUG: Analyzing content of length {len(content)}")
    # ... rest of code
```

Prints will appear directly in your terminal!

### 2. Use Python Debugger (pdb)

```python
# Add breakpoint in code
import pdb; pdb.set_trace()
```

When code hits this line, you'll get an interactive debugger in your terminal.

### 3. Check Request/Response

Add logging middleware in `app/main.py`:

```python
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response
```

### 4. Environment Variable Debugging

```bash
# Check which .env is being loaded
python3 -c "
from dotenv import load_dotenv, find_dotenv
print(f'Loading .env from: {find_dotenv()}')
load_dotenv()
import os
print(f'PRESENTON_API_URL: {os.getenv(\"PRESENTON_API_URL\")}')
"
```

---

## Modified docker-compose.yml (Optional)

If you want to formalize this setup, create `docker-compose.dev.yml`:

```yaml
version: '3.8'

services:
  presenton:
    image: ghcr.io/presenton/presenton:latest
    container_name: presenton-api
    ports:
      - "8000:8000"
    environment:
      - PRESENTON_API_KEY=${PRESENTON_API_KEY}
      - OLLAMA_URL=http://host.docker.internal:11434
      - IMAGE_PROVIDER=pexels
      - PEXELS_API_KEY=${PEXELS_API_KEY}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

  # Backend is commented out - run from source instead
  # backend:
  #   build: ./backend
  #   ...
```

Usage:
```bash
# Start only Presenton
docker-compose -f docker-compose.dev.yml up -d

# Run backend from source
cd backend && source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

---

## Switching Back to Docker

When you're done debugging and want to switch back to full Docker setup:

### Option 1: Quick Switch

```bash
# Stop source backend (Ctrl+C in terminal)
# Deactivate venv
deactivate

# Start Docker backend
docker-compose up -d backend
```

### Option 2: Full Restart

```bash
# Stop everything
docker-compose down

# Update .env back to container networking if needed
# PRESENTON_API_URL=http://presenton:8000

# Start everything
docker-compose up -d
```

---

## Performance Comparison

| Aspect | Source Mode | Docker Mode |
|--------|-------------|-------------|
| **Startup Time** | ~2 seconds | ~5 seconds (first time: 30s) |
| **Code Changes** | Instant reload | Rebuild + restart |
| **Logs** | Direct terminal | `docker-compose logs` |
| **Debugging** | Native Python tools | Limited access |
| **Dependencies** | Manual install | Isolated container |
| **Portability** | Requires Python setup | Works anywhere |

---

## Best Practices

### 1. Use Virtual Environment Always

```bash
# Always activate venv before working
source venv/bin/activate

# Check you're in venv
which python3
# Should show: .../venv/bin/python3
```

### 2. Keep Requirements Synchronized

```bash
# After installing new packages
pip freeze > requirements.txt

# Document new dependencies
git add requirements.txt
git commit -m "Add new dependency: package-name"
```

### 3. Environment Variable Management

```bash
# Never commit .env to git
echo ".env" >> .gitignore

# Use .env.example as template
cp .env .env.example
# Remove sensitive values from .env.example
```

### 4. Log Management

```bash
# Redirect logs to file for analysis
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload \
  2>&1 | tee backend.log

# Now logs are both on screen and in backend.log
```

---

## Quick Reference Commands

```bash
# === Setup ===
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# === Stop Docker Backend ===
docker-compose stop backend

# === Start Source Backend ===
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload

# === Test ===
curl http://localhost:5000/api/health

# === View Presenton Logs ===
docker-compose logs -f presenton

# === Stop Source Backend ===
# Press Ctrl+C in terminal

# === Restart Docker Backend ===
docker-compose start backend
```

---

## Error Analysis: Your Specific Issue

### The 422 Errors You Saw

```
INFO: POST /api/generate HTTP/1.1" 422 Unprocessable Entity
```

**422 means**: Request validation failed (Pydantic)

**Possible causes**:
1. Content too short (< 50 characters) - Most likely!
2. Invalid template value
3. Missing required field
4. Wrong data type

### Your Input

Your content:
> "As AI agents become increasingly essential to daily workflows..."

**Length**: 459 characters ✅ (more than 50 minimum)

But the 422 error suggests the request format might be incorrect.

### Solution with Source Mode

Running from source, you'll see the exact validation error:

```python
# Add logging in routes.py
@router.post("/generate", response_model=GenerateResponse)
async def generate_presentation(request: GenerateRequest):
    print(f"DEBUG: Received request: {request}")
    print(f"Content length: {len(request.content)}")
    print(f"Template: {request.template}")
    # ... rest of code
```

Now you can see exactly what went wrong!

---

## Next Steps

1. ✅ Follow setup steps above
2. ✅ Run backend from source
3. ✅ Try your presentation generation again
4. ✅ Check terminal for detailed error messages
5. ✅ Debug and fix the issue
6. ✅ Profit! 🎉

---

**Last Updated**: 2025-10-13
**Author**: Claude Code
**Status**: Production Ready
