# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TeacherAssist (Teaching PPT Generator)** is an AI-powered presentation generation system that creates professional PowerPoint presentations from text content, designed for educational contexts. The system uses a microservices architecture with Docker, combining multiple AI services (Ollama LLMs, Presenton API, Pexels) to generate structured presentations with automatic image integration and transcript generation.

## Architecture

### Multi-Service Architecture
```
Frontend (HTML/JS) → Backend (FastAPI) → Presenton API (PPT Generation)
                          ↓
                    ┌─────┴──────┐
                    │            │
              Ollama LLM    Pexels API
              (Content      (Images)
               Analysis)
```

### Key Components

1. **Backend Middleware** (`src/backend/` and `backend/`)
   - FastAPI application serving as orchestration layer
   - Coordinates between Ollama, Presenton, and Pexels
   - Handles content processing, slide structure generation, image search
   - Provides transcript generation using Zephyr 7B model
   - Located in TWO places: `src/backend/` (reference) and `backend/` (deployment)

2. **Presenton Integration** (`src/APIs/presenton/`)
   - Third-party open-source PowerPoint generation engine
   - FastAPI server with template support
   - Runs as separate Docker container (port 8000)
   - Reference implementation in `src/APIs/presenton/`

3. **Ollama LLM Integration**
   - Content analysis: `qwen-oss:20` model
   - Transcript generation: `zephyr:7b` model
   - Runs on host machine (not containerized)
   - Accessed via `host.docker.internal:11434`

4. **Frontend** (`src/frontend/` and `frontend/`)
   - Single-page vanilla JavaScript application
   - No framework dependencies
   - Traditional Chinese UI with responsive design

## Critical Setup Requirements

### Docker Configuration Issue
⚠️ **IMPORTANT**: The `backend/` deployment directory is INCOMPLETE and missing critical files:
- `backend/Dockerfile` - Docker build configuration (MISSING)
- `backend/app/*.py` - Application code files (MISSING)
- These files exist in `src/backend/` but must be copied to `backend/` for Docker deployment

### Environment Variables
Required in `.env` file:
- `PRESENTON_API_KEY` - Presenton API authentication
- `PEXELS_API_KEY` - Image search service
- `OLLAMA_URL` - Local Ollama endpoint (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model for content analysis (qwen-oss:20)
- `BACKEND_PORT` - FastAPI server port (default: 5000)

### Ollama Models Required
Both models MUST be downloaded before running:
```bash
ollama pull qwen-oss:20   # Content analysis (required)
ollama pull zephyr:7b     # Transcript generation (optional but recommended)
```

## Development Workflow

### Setup and Build Commands

**Initial Setup** (automated script):
```bash
./setup.sh
```

**Manual Setup Steps**:
```bash
# 1. Verify prerequisites
docker --version
docker-compose --version
python3 --version
ollama --version

# 2. Download Ollama models
ollama pull qwen-oss:20
ollama pull zephyr:7b

# 3. Verify .env configuration
cat .env

# 4. Build and start services
docker-compose build
docker-compose up -d

# 5. Check service health
curl http://localhost:5000/api/health
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
```

### Running Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
docker-compose logs -f backend    # Backend only
docker-compose logs -f presenton  # Presenton only

# Restart specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build backend
```

### Testing

```bash
# Run comprehensive test suite
./test.sh

# Manual API tests
curl http://localhost:5000/api/health              # Backend health
curl http://localhost:11434/api/tags               # Ollama models
curl http://localhost:8000/health                  # Presenton status

# Frontend development
cd frontend
python3 -m http.server 8080
# Open http://localhost:8080
```

### Development in Backend

**For backend changes, work in `src/backend/` then sync to `backend/`:**
```bash
# Edit files in src/backend/app/
# Copy to deployment directory
cp -r src/backend/* backend/

# Rebuild and restart
docker-compose up -d --build backend
```

## Key Service Integration Points

### Content Processing Flow (`src/backend/app/services/content_processor.py`)
Orchestrates the complete presentation generation pipeline:
1. Analyzes content with Ollama (qwen-oss:20) → extracts structure
2. Generates image search queries
3. Fetches images from Pexels
4. Constructs slide structure (4-8 slides)
5. Submits to Presenton API for PPTX/PDF generation
6. Tracks progress and returns download URLs

### Ollama Service (`src/backend/app/services/ollama_service.py`)
- Structured content analysis using JSON schema
- Extracts: title, key topics, slide structure
- Generates English image keywords from Chinese content
- Uses streaming for real-time progress

### Presenton Service (`src/backend/app/services/presenton_service.py`)
- Communicates with Presenton container via HTTP
- Handles PPTX and PDF generation
- Manages file downloads and cleanup
- Template selection: administrative, educational, general

### Transcript Generation (`src/backend/app/services/zephyr_service.py`)
- Uses Zephyr 7B model for natural language generation
- Three speaking styles: formal, conversational, educational
- Per-slide transcript generation with timing estimates
- Average speaking rate: 150 words/minute

## API Endpoints

### Core Endpoints
- `POST /api/generate` - Start presentation generation
- `GET /api/progress/{task_id}` - Check generation progress
- `GET /api/download/{id}/pptx` - Download PowerPoint file
- `GET /api/download/{id}/pdf` - Download PDF file
- `GET /api/health` - Health check with service status

### Transcript Endpoints
- `POST /api/transcript/generate` - Generate transcript for presentation
- `GET /api/transcript/{id}` - Retrieve transcript data
- `GET /api/transcript/{id}/download` - Download transcript as text file

### Documentation
- `GET /docs` - Swagger/OpenAPI interactive documentation
- `GET /redoc` - ReDoc documentation

## Data Models

### Request Models (`src/backend/app/models.py`)
- `GenerateRequest`: content (min 50 chars), template, language
- `TranscriptRequest`: presentation_id, style, language

### Response Models
- `GenerateResponse`: task_id, status, progress, presentation structure
- `SlideContent`: title, type, content points, image_url
- `TranscriptResponse`: per-slide transcripts, full_transcript, duration

## Docker Services

### presenton (Port 8000)
- Image: `ghcr.io/pptxpro/presenton:latest`
- Purpose: PowerPoint generation engine
- Dependencies: Ollama (via host.docker.internal), Pexels API
- Restart policy: `unless-stopped`

### backend (Port 5000)
- Build: `./backend` (requires Dockerfile - currently missing!)
- Purpose: Middleware orchestration layer
- Dependencies: presenton, Ollama, Pexels
- Volume mounts: `./backend:/app`, `./output:/app/output`
- Auto-reload: Enabled for development

## Common Issues and Solutions

### Setup Script Fails at Step 6
**Error**: `no configuration file provided: not found`
**Cause**: `backend/Dockerfile` is missing
**Solution**: Copy from reference or create minimal Dockerfile for FastAPI:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
```

### Ollama Connection Failures
**Error**: Docker containers cannot reach Ollama
**Solution**: Ollama must run on host, Docker uses `host.docker.internal:11434`
```bash
# Verify Ollama is running
ollama serve

# Check from inside container
docker exec -it ppt-backend curl http://host.docker.internal:11434/api/tags
```

### Port Conflicts
**Solution**: Check for processes on ports 5000, 8000, 11434
```bash
lsof -i :5000
lsof -i :8000
# Kill process or change ports in docker-compose.yml
```

### Model Not Found
**Solution**: Download required Ollama models
```bash
ollama list                # Check what's installed
ollama pull qwen-oss:20    # Download if missing
ollama pull zephyr:7b      # For transcript generation
```

## Documentation

- `README.md` - Complete English documentation with setup instructions
- `documentation/project_summary_zh.md` - Comprehensive Traditional Chinese guide
- `documentation/quickstart.md` - 5-minute setup guide
- `documentation/transcript_guide.md` - Transcript generation documentation
- `docs/SD_Doc/` - System design documents and architecture diagrams
- `refData/Codes/PPTAgent/` - Reference implementation (PPTAgent project)

## Testing Strategy

### Automated Testing (`test.sh`)
1. Ollama API connectivity and model verification
2. Presenton API health check
3. Backend API health endpoint validation
4. Pexels API authentication verification
5. Full end-to-end presentation generation test
6. Transcript generation testing (if zephyr:7b available)

### Manual Testing Workflow
1. Generate test presentation via frontend
2. Monitor progress in real-time
3. Download PPTX and PDF outputs
4. Generate transcript with different styles
5. Verify file outputs in `./output` directory

## Performance Targets

| Metric | Target | Typical |
|--------|--------|---------|
| Total generation time | < 60s | 30-45s |
| Ollama processing | < 20s | 10-15s |
| Presenton generation | < 30s | 15-25s |
| Image fetching | < 10s | 3-7s |
| Transcript generation | < 90s | 30-60s |

## Code Organization Patterns

- **Service Layer Pattern**: Each external service has dedicated service class
- **Async/Await**: All I/O operations use async httpx for non-blocking calls
- **Progress Tracking**: In-memory task storage with progress updates (0-100%)
- **Error Handling**: Try/except with detailed error messages and logging
- **Environment Config**: Pydantic Settings for type-safe configuration management

## Important Notes

1. **Two Backend Locations**: `src/backend/` contains reference code, `backend/` is deployment target
2. **Host Networking**: Ollama runs on host, not in Docker, accessed via `host.docker.internal`
3. **Volume Mounts**: Backend code and output directory are mounted for live reload
4. **API Keys**: Never commit `.env` file - it's in `.gitignore`
5. **Chinese Content**: System primarily designed for Traditional Chinese input/output
6. **Template System**: Three built-in templates (administrative, educational, general)
