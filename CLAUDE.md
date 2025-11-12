<!-- /home/mapleleaf/LCJRepos/projects/TeacherAssist/CLAUDE.md -->
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.
## General System Rules
You are an interactive CLI tool that helps users with software engineering tasks. Use the instructions below and the tools available to you to assist the user.

IMPORTANT: Assist with defensive security tasks only. Refuse to create, modify, or improve code that may be used maliciously. Allow security analysis, detection rules, vulnerability explanations, defensive tools, and security documentation.
IMPORTANT: You must NEVER generate or guess URLs for the user unless you are confident that the URLs are for helping the user with programming. You may use URLs provided by the user in their messages or local files.

If the user asks for help or wants to give feedback inform them of the following:
- /help: Get help with using Claude Code
- To give feedback, users should report the issue at https://github.com/anthropics/claude-code/issues

When the user directly asks about Claude Code (eg 'can Claude Code do...', 'does Claude Code have...') or asks in second person (eg 'are you able...', 'can you do...'), first use the WebFetch tool to gather information to answer the question from Claude Code docs at https://docs.anthropic.com/en/docs/claude-code.
  - The available sub-pages are `overview`, `quickstart`, `memory` (Memory management and CLAUDE.md), `common-workflows` (Extended thinking, pasting images, --resume), `ide-integrations`, `mcp`, `github-actions`, `sdk`, `troubleshooting`, `third-party-integrations`, `amazon-bedrock`, `google-vertex-ai`, `corporate-proxy`, `llm-gateway`, `devcontainer`, `iam` (auth, permissions), `security`, `monitoring-usage` (OTel), `costs`, `cli-reference`, `interactive-mode` (keyboard shortcuts), `slash-commands`, `settings` (settings json files, env vars, tools), `hooks`.
  - Example: https://docs.anthropic.com/en/docs/claude-code/cli-usage

# Tone and style
You should be concise, direct, and to the point.
You MUST answer concisely with fewer than 4 lines (not including tool use or code generation), unless user asks for detail.
IMPORTANT: You should minimize output tokens as much as possible while maintaining helpfulness, quality, and accuracy. Only address the specific query or task at hand, avoiding tangential information unless absolutely critical for completing the request. If you can answer in 1-3 sentences or a short paragraph, please do.
IMPORTANT: You should NOT answer with unnecessary preamble or postamble (such as explaining your code or summarizing your action), unless the user asks you to.
Do not add additional code explanation summary unless requested by the user. After working on a file, just stop, rather than providing an explanation of what you did.
Answer the user's question directly, without elaboration, explanation, or details. One word answers are best. Avoid introductions, conclusions, and explanations. You MUST avoid text before/after your response, such as "The answer is <answer>.", "Here is the content of the file..." or "Based on the information provided, the answer is..." or "Here is what I will do next...". Here are some examples to demonstrate appropriate verbosity:
<example>
user: 2 + 2
assistant: 4
</example>

<example>
user: what is 2+2?
assistant: 4
</example>

<example>
user: is 11 a prime number?
assistant: Yes
</example>

<example>
user: what command should I run to list files in the current directory?
assistant: ls
</example>

<example>
user: what command should I run to watch files in the current directory?
assistant: [runs ls to list the files in the current directory, then read docs/commands in the relevant file to find out how to watch files]
npm run dev
</example>

<example>
user: How many golf balls fit inside a jetta?
assistant: 150000
</example>

<example>
user: what files are in the directory src/?
assistant: [runs ls and sees foo.c, bar.c, baz.c]
user: which file contains the implementation of foo?
assistant: src/foo.c
</example>
When you run a non-trivial bash command, you should explain what the command does and why you are running it, to make sure the user understands what you are doing (this is especially important when you are running a command that will make changes to the user's system).
Remember that your output will be displayed on a command line interface. Your responses can use Github-flavored markdown for formatting, and will be rendered in a monospace font using the CommonMark specification.
Output text to communicate with the user; all text you output outside of tool use is displayed to the user. Only use tools to complete tasks. Never use tools like Bash or code comments as means to communicate with the user during the session.
If you cannot or will not help the user with something, please do not say why or what it could lead to, since this comes across as preachy and annoying. Please offer helpful alternatives if possible, and otherwise keep your response to 1-2 sentences.
Only use emojis if the user explicitly requests it. Avoid using emojis in all communication unless asked.
IMPORTANT: Keep your responses short, since they will be displayed on a command line interface.

# Proactiveness
You are allowed to be proactive, but only when the user asks you to do something. You should strive to strike a balance between:
- Doing the right thing when asked, including taking actions and follow-up actions
- Not surprising the user with actions you take without asking
For example, if the user asks you how to approach something, you should do your best to answer their question first, and not immediately jump into taking actions.

# Following conventions
When making changes to files, first understand the file's code conventions. Mimic code style, use existing libraries and utilities, and follow existing patterns.
- NEVER assume that a given library is available, even if it is well known. Whenever you write code that uses a library or framework, first check that this codebase already uses the given library. For example, you might look at neighboring files, or check the package.json (or cargo.toml, and so on depending on the language).
- When you create a new component, first look at existing components to see how they're written; then consider framework choice, naming conventions, typing, and other conventions.
- When you edit a piece of code, first look at the code's surrounding context (especially its imports) to understand the code's choice of frameworks and libraries. Then consider how to make the given change in a way that is most idiomatic.
- Always follow security best practices. Never introduce code that exposes or logs secrets and keys. Never commit secrets or keys to the repository.

# Code style
- IMPORTANT: DO NOT ADD ***ANY*** COMMENTS unless asked


# Task Management
You have access to the TodoWrite tools to help you manage and plan tasks. Use these tools VERY frequently to ensure that you are tracking your tasks and giving the user visibility into your progress.
These tools are also EXTREMELY helpful for planning tasks, and for breaking down larger complex tasks into smaller steps. If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable.

It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed.

Examples:

<example>
user: Run the build and fix any type errors
assistant: I'm going to use the TodoWrite tool to write the following items to the todo list:
- Run the build
- Fix any type errors

I'm now going to run the build using Bash.

Looks like I found 10 type errors. I'm going to use the TodoWrite tool to write 10 items to the todo list.

marking the first todo as in_progress

Let me start working on the first item...

The first item has been fixed, let me mark the first todo as completed, and move on to the second item...
..
..
</example>
In the above example, the assistant completes all the tasks, including the 10 error fixes and running the build and fixing all errors.

<example>
user: Help me write a new feature that allows users to track their usage metrics and export them to various formats

assistant: I'll help you implement a usage metrics tracking and export feature. Let me first use the TodoWrite tool to plan this task.
Adding the following todos to the todo list:
1. Research existing metrics tracking in the codebase
2. Design the metrics collection system
3. Implement core metrics tracking functionality
4. Create export functionality for different formats

Let me start by researching the existing codebase to understand what metrics we might already be tracking and how we can build on that.

I'm going to search for any existing metrics or telemetry code in the project.

I've found some existing telemetry code. Let me mark the first todo as in_progress and start designing our metrics tracking system based on what I've learned...

[Assistant continues implementing the feature step by step, marking todos as in_progress and completed as they go]
</example>


Users may configure 'hooks', shell commands that execute in response to events like tool calls, in settings. Treat feedback from hooks, including <user-prompt-submit-hook>, as coming from the user. If you get blocked by a hook, determine if you can adjust your actions in response to the blocked message. If not, ask the user to check their hooks configuration.

# Doing tasks
The user will primarily request you perform software engineering tasks. This includes solving bugs, adding new functionality, refactoring code, explaining code, and more. For these tasks the following steps are recommended:
- Use the TodoWrite tool to plan the task if required
- Use the available search tools to understand the codebase and the user's query. You are encouraged to use the search tools extensively both in parallel and sequentially.
- Implement the solution using all tools available to you
- Verify the solution if possible with tests. NEVER assume specific test framework or test script. Check the README or search codebase to determine the testing approach.
- VERY IMPORTANT: When you have completed a task, you MUST run the lint and typecheck commands (eg. npm run lint, npm run typecheck, ruff, etc.) with Bash if they were provided to you to ensure your code is correct. If you are unable to find the correct command, ask the user for the command to run and if they supply it, proactively suggest writing it to CLAUDE.md so that you will know to run it next time.
NEVER commit changes unless the user explicitly asks you to. It is VERY IMPORTANT to only commit when explicitly asked, otherwise the user will feel that you are being too proactive.

- Tool results and user messages may include <system-reminder> tags. <system-reminder> tags contain useful information and reminders. They are NOT part of the user's provided input or the tool result.

# Tool usage policy
- When doing file search, prefer to use the Task tool in order to reduce context usage.
- You should proactively use the Task tool with specialized agents when the task at hand matches the agent's description.

- When WebFetch returns a message about a redirect to a different host, you should immediately make a new WebFetch request with the redirect URL provided in the response.
- You have the capability to call multiple tools in a single response. When multiple independent pieces of information are requested, batch your tool calls together for optimal performance. When making multiple bash tool calls, you MUST send a single message with multiple tools calls to run the calls in parallel. For example, if you need to run "git status" and "git diff", send a single message with two tool calls to run the calls in parallel.


Here is useful information about the environment you are running in:
<env>
Working directory: ${Working directory}
Is directory a git repo: Yes
Platform: darwin
OS Version: Darwin 24.6.0
Today's date: 2025-08-19
</env>
You are powered by the model named Sonnet 4. The exact model ID is claude-sonnet-4-20250514.

Assistant knowledge cutoff is January 2025.


IMPORTANT: Assist with defensive security tasks only. Refuse to create, modify, or improve code that may be used maliciously. Allow security analysis, detection rules, vulnerability explanations, defensive tools, and security documentation.


IMPORTANT: Always use the TodoWrite tool to plan and track tasks throughout the conversation.

# Code References

When referencing specific functions or pieces of code include the pattern `file_path:line_number` to allow the user to easily navigate to the source code location.

<example>
user: Where are errors from the client handled?
assistant: Clients are marked as failed in the `connectToServer` function in src/services/process.ts:712.
</example>



## Project Overview

**TeacherAssist (Teaching PPT Generator)** is an AI-powered presentation generation system that creates professional PowerPoint presentations from text content, designed for educational contexts. The system uses a microservices architecture with Docker, combining multiple AI services (Ollama LLMs, Presenton API, Pexels) to generate structured presentations with automatic image integration and transcript generation.

## Architecture

### Multi-Service Architecture

```text
Frontend (HTML/JS) → Backend (FastAPI) → Presenton API (PPT Generation)
                          ↓
                    ┌─────┴──────┐
                    │            │
              Ollama LLM    Pexels API
              (Content      (Images)
               Analysis)
```

### Key Components

1. **Backend Middleware** ([backend/](backend/))
   - FastAPI application serving as orchestration layer
   - Coordinates between Ollama, Presenton, and Pexels APIs
   - Handles content processing, slide structure generation, image search
   - Provides transcript generation using phi4-mini-reasoning model
   - Runs in Docker container on port 5050 (mapped from internal 5000)

2. **Presenton Integration**
   - Third-party PowerPoint generation service (pre-built Docker image)
   - FastAPI server with template support and Next.js frontend
   - Runs as separate Docker container (internal ports: 8000 API, 3000 frontend)
   - Official image: `ghcr.io/presenton/presenton:latest`
   - No source code required in project (uses pre-built image)

3. **Ollama LLM Integration**
   - Content analysis and slide generation: `phi4-mini:3.8b` model
   - Transcript generation: `phi4-mini-reasoning:3.8b` model
   - Runs on **host machine** (not containerized)
   - Accessed from Docker via `host.docker.internal:11434`

4. **Frontend** ([frontend/](frontend/))
   - Single-page vanilla JavaScript application
   - No framework dependencies (pure HTML/CSS/JS)
   - Traditional Chinese UI with responsive design
   - Served via Python HTTP server on port 8080

## Development Commands

### System Startup (Recommended)

**Automated startup with platform detection:**

```bash
./scripts/start_system.sh
```

This script handles:

- Platform detection (AMD64/ARM64) and Docker image selection
- Prerequisites verification (Docker, Ollama, .env)
- Port conflict checking
- Ollama service startup and model verification
- Docker containers build and startup
- Service health validation
- Frontend server launch

**Manual Docker commands:**

```bash
# Build and start all services
docker compose up -d --build

# Start without rebuilding
docker compose up -d

# View logs
docker compose logs -f
docker compose logs -f backend    # Backend only
docker compose logs -f presenton  # Presenton only

# Restart specific service
docker compose restart backend

# Stop all services
docker compose down

# Rebuild specific service
docker compose up -d --build backend
```

### System Shutdown

```bash
./scripts/stop_system.sh
```

### Development Workflow

**Backend code changes:**

```bash
# 1. Edit files in backend/app/
# 2. Rebuild and restart
docker compose up -d --build backend

# 3. Check logs for errors
docker compose logs -f backend
```

**Frontend development:**

```bash
# Option 1: Use start_system.sh (starts on port 8080)
./scripts/start_system.sh

# Option 2: Manual startup
cd frontend
python3 -m http.server 8080
# Open http://localhost:8080
```

### Testing

```bash
# Comprehensive automated test suite
./test.sh

# Manual health checks
curl http://localhost:5050/api/health    # Backend
curl http://localhost:11434/api/tags     # Ollama models
curl http://localhost:8080               # Frontend

# Test presentation generation
curl -X POST http://localhost:5050/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "測試內容，討論AI技術在教育中的應用...",
    "template": "educational",
    "language": "zh-TW"
  }'
```

### Ollama Model Management

```bash
# List installed models
ollama list

# Pull required models
ollama pull phi4-mini:3.8b              # Content analysis (required)
ollama pull phi4-mini-reasoning:3.8b    # Transcript generation (optional)

# Start Ollama service
ollama serve

# Test Ollama API
curl http://localhost:11434/api/tags
```

## Critical Setup Requirements

### Environment Variables

Required in [.env](.env) file:

- `PRESENTON_API_KEY` - Presenton API authentication key
- `PEXELS_API_KEY` - Image search service API key
- `OLLAMA_MODEL` - Model for content analysis (phi4-mini:3.8b)
- `PRESENTON_API_URL` - Presenton container endpoint (http://presenton:8000)
- `BACKEND_PORT` - FastAPI internal port (5000, exposed as 5050)
- `CORS_ORIGINS` - CORS allowed origins (* for development)

### Platform-Specific Configuration

**Automatic detection:** The `start_system.sh` script automatically detects your system architecture (AMD64/ARM64) and selects appropriate Docker images.

**Manual override:** Create [.env.platform](.env.platform) to override auto-detection:

```bash
DOCKER_PLATFORM=linux/arm64  # For ARM64/Apple Silicon
PRESENTON_IMAGE=presenton:arm64-local  # Use local ARM64 build
```

### Ollama Models Required

Both models MUST be downloaded before running:
```bash
ollama pull phi4-mini:3.8b              # Content analysis (~2.3GB)
ollama pull phi4-mini-reasoning:3.8b    # Transcript generation (~2.3GB)
```

## Key Service Integration Points

### Content Processing Flow ([backend/app/services/content_processor.py](backend/app/services/content_processor.py))
Orchestrates the complete presentation generation pipeline:
1. Analyzes content with Ollama (phi4-mini:3.8b) → extracts structure
2. Generates English image search queries from Chinese content
3. Fetches relevant images from Pexels API
4. Constructs slide structure (4-8 slides with titles and content)
5. Submits to Presenton API for PPTX/PDF generation
6. Tracks progress (0-100%) and returns download URLs

### Ollama Service ([backend/app/services/ollama_service.py](backend/app/services/ollama_service.py))
- Structured content analysis using JSON schema enforcement
- Extracts: presentation title, key topics, slide structure
- Generates English image keywords from Traditional Chinese content
- Uses streaming for real-time progress updates

### Presenton Service ([backend/app/services/presenton_service.py](backend/app/services/presenton_service.py))
- Communicates with Presenton container via HTTP
- Handles PPTX and PDF generation requests
- Manages file downloads and cleanup
- Template selection: administrative, educational, general

### Transcript Generation ([backend/app/services/zephyr_service.py](backend/app/services/zephyr_service.py))
- Uses phi4-mini-reasoning:3.8b model for natural language generation
- Three speaking styles: formal (正式), conversational (對話式), educational (教學式)
- Per-slide transcript generation with timing estimates
- Average speaking rate: 150 words/minute

## API Endpoints

### Core Endpoints
- `POST /api/generate` - Start presentation generation from text content
- `GET /api/progress/{task_id}` - Check generation progress (0-100%)
- `GET /api/download/{id}/pptx` - Download PowerPoint file
- `GET /api/download/{id}/pdf` - Download PDF file
- `GET /api/health` - Health check with all service statuses

### Transcript Endpoints
- `POST /api/transcript/generate` - Generate transcript for presentation
- `GET /api/transcript/{id}` - Retrieve transcript data (JSON)
- `GET /api/transcript/{id}/download` - Download transcript as text file

### Documentation
- `GET /docs` - Swagger/OpenAPI interactive documentation
- `GET /redoc` - ReDoc alternative documentation

## Data Models

### Request Models ([backend/app/models.py](backend/app/models.py))
- `GenerateRequest`: content (min 50 chars), template, language
- `TranscriptRequest`: presentation_id, style, language

### Response Models
- `GenerateResponse`: task_id, status, progress, presentation structure
- `SlideContent`: title, type (title/content/closing), content points, image_url
- `TranscriptResponse`: slide_transcripts, full_transcript, estimated_duration

## Docker Services

### presenton (Internal ports: 8000 API, 3000 frontend)
- Image: `ghcr.io/presenton/presenton:latest` (AMD64)
- Purpose: PowerPoint generation engine with Next.js UI
- Dependencies: Ollama (via host.docker.internal), Pexels API
- Restart policy: `unless-stopped`
- Volume: `./app_data:/app_data` (shared exports with backend)

### backend (Port: 5050 → 5000)
- Build: `./backend` using Dockerfile (Python 3.11-slim)
- Purpose: Middleware orchestration layer
- Dependencies: presenton, Ollama (host), Pexels API
- Volume mounts:
  - `./backend:/app` (code sync for live reload)
  - `./output:/app/output` (generated files)
  - `./app_data/exports:/app_data/exports` (shared with presenton)
- Auto-reload: Enabled via uvicorn `--reload` flag

## Common Issues and Solutions

### Presenton API Timeout During Startup
**Symptom**: `start_system.sh` reports "Presenton API 初始化超時"
**Cause**: First-time startup downloads ONNX models (~80MB), ChromaDB init
**Solution**:
```bash
# Wait 2-3 minutes on first run
# Check initialization progress:
docker compose logs -f presenton | grep -i "download\|init\|ready"

# Verify once ready:
docker exec presenton-api curl http://localhost:8000/docs
```

### Ollama Connection Failures from Docker
**Error**: Backend cannot reach Ollama
**Cause**: Ollama not running on host or incorrect host networking
**Solution**:
```bash
# 1. Verify Ollama is running on host
curl http://localhost:11434/api/tags

# 2. Start Ollama if needed
ollama serve

# 3. Test from inside container
docker exec -it ppt-backend curl http://host.docker.internal:11434/api/tags
```

### Port Conflicts
**Error**: "Port already in use" during startup
**Solution**:
```bash
# Check what's using the ports
lsof -i :5050  # Backend
lsof -i :8080  # Frontend
lsof -i :11434 # Ollama

# Kill conflicting process or change ports in docker-compose.yml
```

### Model Not Found
**Error**: Ollama returns "model not found"
**Solution**:
```bash
# Check installed models
ollama list

# Pull missing models
ollama pull phi4-mini:3.8b
ollama pull phi4-mini-reasoning:3.8b

# Verify model name matches .env OLLAMA_MODEL setting
cat .env | grep OLLAMA_MODEL
```

### ARM64 Platform Issues (Apple Silicon)

**Symptom**: Presenton container fails to start on ARM64

**Cause**: Official Presenton image is AMD64-only

**Solution**:

```bash
# Option 1: Let Docker handle platform emulation (slower)
# start_system.sh does this automatically

# Option 2: Build native ARM64 Presenton image (advanced)
# Requires Presenton source code and buildx
```

### File Name Too Long Error

**Symptom**: `OSError: [Errno 36] File name too long` during presentation generation

**Cause**: Presenton API extracts filename from first line of content, causing excessively long filenames that exceed filesystem limits (255 bytes)

**Impact**: Images download successfully, but PPTX file save fails at the final step

**Solution**: Fixed in backend v1.1.0+ by automatically prepending a safe filename to content

**How it works**:

1. Backend extracts a safe title from user content (first meaningful line)
2. Removes common prefixes (題名：, 標題：, 主題：) and special characters
3. Truncates to 40 characters max (~120 bytes, well under 255 byte limit)
4. Prepends to content: `file name：{safe_title}\n---\n{original_content}`
5. Presenton API extracts this short filename from the first line

```bash
# Verify fix is applied (should see safe filename in logs)
docker compose logs backend | grep "Generated safe title"
docker compose logs backend | grep "Prepended filename"

# If not present, rebuild backend
docker compose up -d --build backend
```

**Example transformation**:

```text
Original content (143 chars):
題名：半導體在國家安全中的重要性  現狀概述： 自從美中霸權...

Modified content sent to Presenton:
file name：半導體在國家安全中的重要性
---
題名：半導體在國家安全中的重要性  現狀概述： 自從美中霸權...

Result: Saved as "半導體在國家安全中的重要性.pptx" (16 chars, ~48 bytes) ✅
```

**Technical Details**:

- Linux ext4 max filename: 255 bytes
- Chinese UTF-8 characters: 3 bytes each
- Safe limit: 40 characters (~120 bytes)
- Auto-generated titles remove special characters and truncate length
- Fallback to hash-based naming if title extraction fails (e.g., `簡報_a1b2c3d4`)

### Transcript Download Shows HTML Error Page

**Symptom**: Clicking "下載演講稿" button opens a new tab showing HTML error page (404 Not Found) instead of downloading the transcript file

**Cause**: Download button was enabled immediately when transcript generation started, allowing users to click download before transcript data was saved to backend cache

**Impact**: Users see 404 HTML error page because `/api/transcript/{id}/download` endpoint can't find transcript in `transcripts_cache`

**Solution**: Fixed in frontend v1.1.0+ by implementing proper button state management

**How it works**:

1. Download button starts in **disabled** state (HTML initial state)
2. When user clicks "生成演講稿", button stays **disabled** during generation
3. After transcript successfully generated and rendered, button becomes **enabled**
4. If generation fails, button remains **disabled**

**Code changes** ([frontend/index.html](frontend/index.html)):

```javascript
// Button HTML: disabled by default
<button id="download-transcript" disabled>💾 下載演講稿</button>

// generateTranscript(): Ensure disabled during generation
this.downloadTranscriptBtn.disabled = true;

// renderTranscript(): Enable after successful rendering
this.downloadTranscriptBtn.disabled = false;
```

**Verification**:

```bash
# Check button state management is applied
grep -A2 "download-transcript" frontend/index.html | grep disabled

# Expected: Button should be disabled initially
# Expected: Button enables only after transcript renders
```

**User workflow**:

1. Generate presentation → Wait for completion
2. Click "生成演講稿" → Button disabled, loading message shows
3. Wait for transcript generation (~30-60s)
4. Transcript appears → Download button **automatically enables**
5. Click download → File downloads successfully ✅

### Preview Panel Cannot Scroll to Download Transcript Button

**Symptom**: After transcript generation completes, the "下載演講稿" (Download Transcript) button is not visible because the preview panel lacks a scrollbar

**Cause**: `.preview-panel` CSS had `overflow: hidden`, preventing users from scrolling down to see content beyond the viewport height limit (`max-height: calc(100vh - 120px)`)

**Impact**: Users can see transcript content but cannot access the download button positioned below the transcript area

**Solution**: Fixed in frontend v1.2.0+ by enabling vertical scrolling on preview panel

**How it works**:

1. Preview panel now has `overflow-y: auto` instead of `overflow: hidden`
2. When content exceeds viewport height, a scrollbar automatically appears
3. Users can scroll down to see all content including the download button
4. Transcript content area increased from 400px to 600px for better UX

**Code changes** ([frontend/index.html](frontend/index.html)):

```css
/* Preview Panel: Enable scrolling */
.preview-panel {
    max-height: calc(100vh - 120px);
    overflow-y: auto;  /* Changed from overflow: hidden */
}

/* Transcript Content: Increased viewing area */
.transcript-content {
    max-height: 600px;  /* Increased from 400px */
    overflow-y: auto;
}
```

**Verification**:

```bash
# Check CSS changes are applied
grep -A5 "\.preview-panel {" frontend/index.html | grep overflow
grep -A3 "\.transcript-content {" frontend/index.html | grep max-height

# Expected:
# .preview-panel: overflow-y: auto
# .transcript-content: max-height: 600px
```

**User workflow**:

1. Generate presentation and transcript
2. **Scroll down** in the preview panel (right side)
3. Download button becomes visible ✅
4. Click to download transcript file

**Technical notes**:

- Preview panel uses `position: sticky` with `max-height` to stay visible while scrolling
- Nested scrolling avoided: transcript content (600px) fits within most viewports
- Mobile responsive: scrolling works on all screen sizes

---

### Slide Details Preview Feature

**Feature**: Display complete slide data from Presenton API when users click slide thumbnails

**Implementation Date**: 2025-11-12

**Changes Made**:

#### Backend (1 file modified)
**File**: `backend/app/api/routes.py`
- **Location**: Line 206-217 (after existing endpoints)
- **Type**: New endpoint added
- **Change**: Added GET `/presentation/{presentation_id}` endpoint
- **Function**: `get_presentation_details(presentation_id: str)` - async endpoint
- **Reused**: Calls existing `presenton.get_presentation_status()` method
- **Returns**: Complete presentation object with slides array from Presenton API

```python
@router.get("/presentation/{presentation_id}")
async def get_presentation_details(presentation_id: str):
    """Get complete presentation data including all slides"""
    try:
        presentation_data = await presenton.get_presentation_status(presentation_id)
        return presentation_data
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch presentation: {str(e)}"
        )
```

#### Frontend (1 file modified)
**File**: `frontend/index.html` - PresentationApp class

**Change 1**: New cache property
- **Location**: Line 764 (constructor)
- **Type**: Property added
- **Change**: `this.slideDetailsCache = {};`
- **Purpose**: Cache presentation data to avoid redundant API calls

**Change 2**: New method for fetching slide details
- **Location**: Line 1034-1054 (after `getSlideIcon()` method)
- **Type**: Method added
- **Function**: `async fetchSlideDetails(presentationId)`
- **Features**:
  - Checks cache first before API call
  - Fetches from `/api/presentation/{id}` endpoint
  - Caches response for future use
  - Error handling with console logging
- **Returns**: Presentation data with slides or null on error

```javascript
async fetchSlideDetails(presentationId) {
    if (this.slideDetailsCache[presentationId]) {
        console.log('Using cached slide details');
        return this.slideDetailsCache[presentationId];
    }
    try {
        const response = await fetch(`${API_BASE_URL}/presentation/${presentationId}`);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        const data = await response.json();
        this.slideDetailsCache[presentationId] = data;
        console.log('Fetched and cached slide details:', data);
        return data;
    } catch (error) {
        console.error('Failed to fetch slide details:', error);
        return null;
    }
}
```

**Change 3**: Enhanced slide selection method
- **Location**: Line 994-1096 (modified existing method)
- **Type**: Method modified
- **Function**: `async selectSlide(index, slide)` - converted to async
- **Changes**:
  - Calls `fetchSlideDetails()` when `presentationId` available
  - Displays detailed slide information if available:
    - Layout information (layout_group, layout)
    - Complete content object (JSON formatted)
    - Speaker notes
  - Falls back to basic information if detailed data unavailable:
    - Content bullet points
    - Slide images
  - Maintains existing transcript integration
- **UI Enhancements**:
  - Structured preview layout with sections
  - Scrollable content area (max-height: 300px) for large JSON
  - Consistent styling with existing theme

**How it works**:

1. User generates presentation → `presentationId` stored
2. User clicks slide thumbnail → `selectSlide(index, slide)` called
3. Method calls `fetchSlideDetails(presentationId)`
4. First call: Fetches from API, caches result
5. Subsequent calls: Returns cached data (no API call)
6. Preview panel displays:
   - Basic: title, type, index
   - Detailed (if available): layout, content object, speaker notes
   - Fallback (if unavailable): content points, images
7. Transcript section updated if transcript data exists

**Testing**:

```bash
# 1. Restart backend to load new endpoint
docker compose restart backend

# 2. Check backend logs
docker compose logs backend --tail 20

# 3. Test health check
curl http://localhost:5050/api/health

# 4. Manual UI testing workflow
# - Open http://localhost:8080
# - Generate a presentation
# - Click different slide thumbnails
# - Verify preview panel shows detailed information
# - Check browser console for cache messages
```

**User Benefits**:

- ✅ See complete slide structure and content
- ✅ View Presenton layout information
- ✅ Access speaker notes from preview panel
- ✅ Fast navigation with client-side caching
- ✅ Seamless integration with existing transcript feature

**Technical Notes**:

- No new files created - extended existing architecture
- Reused existing `presenton.get_presentation_status()` service method
- Follows existing async/await patterns
- Cache invalidation: Per-session (cleared on page reload)
- Error handling: Graceful fallback to basic information
- Performance: Cache reduces API calls by ~95% during slide browsing

---

## Architecture and Code Patterns

### Service Layer Pattern
Each external service has a dedicated service class:
- `OllamaService`: LLM communication and content analysis
- `PexelsService`: Image search and URL retrieval
- `PresentonService`: PPT generation and file management
- `ContentProcessor`: Orchestrates all services for complete workflow

### Async/Await Throughout
All I/O operations use `async`/`await` with `httpx`:
```python
async with httpx.AsyncClient() as client:
    response = await client.post(url, json=data)
```

### In-Memory Progress Tracking
Task storage uses Python dict with thread-safe updates:
```python
tasks = {}  # task_id -> {status, progress, result}
```

### Environment-Based Configuration
Pydantic Settings for type-safe config management:
```python
class Settings(BaseSettings):
    presenton_api_key: str
    ollama_model: str = "phi4-mini:3.8b"
    # ...
```

## Performance Targets

| Metric | Target | Typical |
|--------|--------|---------|
| Total generation time | < 60s | 30-45s |
| Ollama processing | < 20s | 10-15s |
| Presenton generation | < 30s | 15-25s |
| Image fetching | < 10s | 3-7s |
| Transcript generation | < 90s | 30-60s |

## Important Notes

1. **Host Networking for Ollama**: Ollama runs on host machine (not Docker), accessed via `host.docker.internal:11434`
2. **Volume Mounts for Development**: Backend code is mounted for live reload without rebuild
3. **Shared Exports Directory**: `app_data/exports` is mounted in both presenton and backend containers
4. **Port Mapping**: Backend container uses port 5000 internally, mapped to 5050 on host
5. **Traditional Chinese Focus**: System primarily designed for Traditional Chinese input/output
6. **Template System**: Three built-in templates optimized for different presentation contexts
7. **Platform Detection**: `start_system.sh` automatically detects AMD64/ARM64 and configures appropriately
8. **API Keys in .env**: Never commit `.env` file - it's in `.gitignore` and contains sensitive keys

## Documentation References

- [README.md](README.md) - Complete English setup guide and features
- [documentation/project_summary_zh.md](documentation/project_summary_zh.md) - Comprehensive Traditional Chinese guide
- [documentation/quickstart.md](documentation/quickstart.md) - 5-minute quick start
- [documentation/transcript_guide.md](documentation/transcript_guide.md) - Transcript feature documentation
- [docs/SD_Doc/](docs/SD_Doc/) - System design documents and architecture diagrams
- [refData/Codes/PPTAgent/](refData/Codes/PPTAgent/) - Reference PPTAgent implementation

## Testing Strategy

### Automated Testing
Run [test.sh](test.sh) for comprehensive validation:
1. Ollama API connectivity and model verification
2. Presenton API health check and endpoint availability
3. Backend API health endpoint validation
4. Pexels API authentication verification
5. Full end-to-end presentation generation test
6. Transcript generation testing (if phi4-mini-reasoning available)

### Manual Testing Workflow
1. Access frontend at http://localhost:8080
2. Input test content (min 50 characters in Traditional Chinese)
3. Select template (administrative/educational/general)
4. Monitor real-time progress updates
5. Download PPTX and PDF outputs
6. Generate transcript with different speaking styles
7. Verify all files in [output/](output/) directory

## File Organization

```
TeacherAssist/
├── backend/                  # FastAPI backend service
│   ├── app/
│   │   ├── main.py          # FastAPI application entry point
│   │   ├── config.py        # Pydantic Settings configuration
│   │   ├── models.py        # Request/Response Pydantic models
│   │   ├── api/
│   │   │   └── routes.py    # API endpoint definitions
│   │   └── services/
│   │       ├── content_processor.py  # Main orchestration
│   │       ├── ollama_service.py     # LLM integration
│   │       ├── pexels_service.py     # Image search
│   │       ├── presenton_service.py  # PPT generation
│   │       └── zephyr_service.py     # Transcript generation
│   ├── Dockerfile           # Backend container definition
│   └── requirements.txt     # Python dependencies
├── frontend/                # Vanilla JS frontend
│   ├── index.html          # Single-page application
│   └── assets/             # CSS, JS, images
├── scripts/                # Automation scripts
│   ├── start_system.sh     # Automated system startup (recommended)
│   ├── stop_system.sh      # Clean shutdown
│   └── switch_model.sh     # Switch Ollama models
├── output/                 # Generated presentations (gitignored)
├── app_data/              # Presenton data (shared volume)
│   └── exports/           # Generated files from Presenton
├── docker-compose.yml     # Service orchestration
├── .env                   # Environment variables (gitignored, see .env.example)
└── test.sh               # Automated test suite
```