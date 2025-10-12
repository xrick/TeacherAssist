# Teaching PPT Generator 🎓

A complete AI-powered presentation generation system that creates professional PowerPoint presentations from text content. Built with FastAPI backend, Presenton API for PPT generation, Ollama LLM for content analysis, and Pexels for image integration.

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Frontend  │─────▶│   Backend    │─────▶│  Presenton  │
│  (Browser)  │      │  Middleware  │      │     API     │
└─────────────┘      └──────┬───────┘      └─────────────┘
                            │
                      ┌─────┴──────┐
                      │            │
                 ┌────▼────┐  ┌───▼────┐
                 │ Ollama  │  │ Pexels │
                 │   LLM   │  │  API   │
                 └─────────┘  └────────┘
```

### **Run on ollama**
docker run -it --name presenton -p 5000:80 -e LLM="ollama" -e OLLAMA_MODEL="llama3.2:3b" -e IMAGE_PROVIDER="pexels" -e PEXELS_API_KEY="*******" -e CAN_CHANGE_KEYS="false" -v "./app_data:/app_data" ghcr.io/presenton/presenton:latest



## 📋 Features

- **AI Content Analysis**: Uses Ollama (qwen-oss:20) to analyze and structure content
- **Automatic Slide Generation**: Creates 4-8 slides with proper structure
- **Image Integration**: Automatically fetches relevant images from Pexels
- **Transcript Generation**: Generate presentation scripts using Zephyr 7B model
- **Multiple Templates**: Administrative, Educational, and General styles
- **Progress Tracking**: Real-time generation progress updates
- **Export Options**: Download as PowerPoint (PPTX), PDF, or transcript text
- **Modern UI**: Responsive, professional interface in Traditional Chinese

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.9+
- Ollama installed locally
- Internet connection (for Pexels API)

### Step 1: Install Ollama and Download Model

```bash
# Install Ollama (if not already installed)
curl https://ollama.ai/install.sh | sh

# Download the model
ollama pull qwen-oss:20

# Verify installation
ollama list
```

### Step 2: Clone and Setup

```bash
# Create project directory
mkdir teaching-ppt-generator
cd teaching-ppt-generator

# Create directory structure
mkdir -p backend/app/{api,services,utils}
mkdir -p frontend
mkdir -p output
```

### Step 3: Create Configuration Files

Copy all the provided files from the artifacts into their respective directories:

```
teaching-ppt-generator/
├── docker-compose.yml
├── .env
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── config.py
│       ├── models.py
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes.py
│       └── services/
│           ├── __init__.py
│           ├── ollama_service.py
│           ├── pexels_service.py
│           ├── presenton_service.py
│           └── content_processor.py
└── frontend/
    └── index.html
```

### Step 4: Start Services

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify services are running
curl http://localhost:5000/api/health
```

### Step 5: Open Frontend

Open `frontend/index.html` in your browser, or serve it with:

```bash
# Using Python
cd frontend
python3 -m http.server 8080

# Then visit: http://localhost:8080
```

## 📚 API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:5000/docs
- ReDoc: http://localhost:5000/redoc

### Main Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/generate` | Start presentation generation |
| GET | `/api/progress/{task_id}` | Check generation progress |
| GET | `/api/download/{id}/pptx` | Download PowerPoint file |
| GET | `/api/download/{id}/pdf` | Download PDF file |
| GET | `/api/health` | Health check |

## 🔧 Configuration

Environment variables in `.env`:

```bash
# Presenton API
PRESENTON_API_KEY=sk-presenton-...
PRESENTON_API_URL=http://localhost:8000

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen-oss:20

# Pexels
PEXELS_API_KEY=your_key_here

# Backend
BACKEND_PORT=5000
CORS_ORIGINS=*
```

## 🎨 Template Types

1. **Administrative** (行政簡報)
   - Professional, formal, structured style
   - Best for business reports, meetings

2. **Educational** (教學簡報)
   - Clear, teaching-oriented, easy to understand
   - Best for courses, tutorials, training

3. **General** (一般簡報)
   - Flexible, universal, visual style
   - Best for general presentations

## 📖 Usage Guide

1. **Input Content**:
   - Minimum 50 characters required
   - Supports: meeting notes, course outlines, product intros, research, proposals

2. **Select Template**:
   - Choose from 3 available templates
   - Each optimized for different use cases

3. **Generate**:
   - Click "生成簡報" (Generate)
   - Wait 30-60 seconds for processing
   - Watch real-time progress updates

4. **Download**:
   - Download as PowerPoint (.pptx)
   - Download as PDF (.pdf)
   - Generate and download presentation transcript (.txt)

## 🎤 Transcript Generation

The system uses **Zephyr 7B** model to generate professional presentation scripts:

### Features
- **Three Speaking Styles**: 
  - Educational (教學式) - Clear, step-by-step explanations
  - Formal (正式) - Professional business language
  - Conversational (對話式) - Easy, relatable style

- **Smart Duration Estimation**: Calculates speaking time based on content
- **Slide-by-Slide Scripts**: Individual scripts for each slide
- **Full Transcript**: Complete presentation script with timing

### Usage
1. Generate a presentation first
2. Click "生成演講稿" (Generate Transcript)
3. Select speaking style
4. Wait 30-60 seconds for generation
5. Download as text file

### Example Transcript Output
```
【投影片 1: 人工智慧教育應用】
[預估時間: 45秒]
各位老師、同學們大家好！今天我們要一起探討一個令人興奮的主題...

【投影片 2: 學習目標】
[預估時間: 60秒]
在開始之前，讓我們先了解今天的學習目標。首先...
```

## 🔍 Troubleshooting

### Ollama Connection Issues
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check available models
ollama list

# Pull missing models
ollama pull qwen-oss:20
ollama pull zephyr:7b

# Restart Ollama if needed
ollama serve
```

### Presenton API Issues
```bash
# Check Presenton container logs
docker logs presenton-api

# Restart Presenton
docker-compose restart presenton
```

### Backend Issues
```bash
# Check backend logs
docker-compose logs backend

# Rebuild backend
docker-compose up -d --build backend
```

## 🛠️ Development

### Run Backend Locally (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 5000
```

### Testing

```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Test generation (replace content with your text)
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "content": "這是一個測試內容，用於生成教學簡報。主要討論AI技術在教育中的應用。包括機器學習、深度學習等主題。",
    "template": "educational",
    "language": "zh-TW"
  }'
```

## 📦 Project Structure

```
teaching-ppt-generator/
├── backend/                    # Backend API service
│   ├── app/
│   │   ├── main.py            # FastAPI application
│   │   ├── config.py          # Configuration management
│   │   ├── models.py          # Pydantic models
│   │   ├── api/
│   │   │   └── routes.py      # API endpoints
│   │   └── services/
│   │       ├── ollama_service.py       # LLM integration
│   │       ├── pexels_service.py       # Image search
│   │       ├── presenton_service.py    # PPT generation
│   │       └── content_processor.py    # Main orchestrator
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Frontend web interface
│   └── index.html             # Single-page application
├── output/                     # Generated presentations
├── docker-compose.yml         # Docker orchestration
├── .env                       # Environment variables
└── README.md                  # This file
```

## 🔐 Security Notes

- **API Keys**: Never commit `.env` file to version control
- **CORS**: Set proper origins in production (not `*`)
- **Rate Limiting**: Consider adding rate limiting for production
- **File Cleanup**: Implement periodic cleanup of `/output` directory

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**
   ```bash
   # Use production URLs
   PRESENTON_API_URL=https://your-presenton-domain.com
   CORS_ORIGINS=https://your-frontend-domain.com
   DEBUG=False
   ```

2. **Reverse Proxy**
   - Use nginx or Caddy in front of the backend
   - Enable HTTPS with Let's Encrypt

3. **Monitoring**
   - Add logging service (e.g., ELK stack)
   - Monitor Ollama performance
   - Track API usage and costs

4. **Scaling**
   - Use Redis for task queue
   - Add load balancer for multiple backend instances
   - Consider Kubernetes for orchestration

## 📊 Performance

- **Average Generation Time**: 30-60 seconds
- **Ollama Processing**: 10-20 seconds
- **Presenton Generation**: 15-30 seconds
- **Image Fetching**: 5-10 seconds

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **Presenton**: PPT generation engine
- **Ollama**: Local LLM inference
- **Pexels**: Free stock photos
- **FastAPI**: Modern Python web framework

## 📞 Support

For issues and questions:
1. Check the Troubleshooting section
2. Review API documentation at `/docs`
3. Check Docker logs: `docker-compose logs`
4. Verify Ollama status: `ollama list`

## 🔄 Updates

### Version 1.0.0 (2025-01-XX)
- Initial release
- Support for 3 template types
- Ollama integration (qwen-oss:20)
- Pexels image integration
- PPTX and PDF export

## 🎯 Roadmap

- [ ] Add more template styles
- [ ] Support for custom branding
- [ ] Batch processing
- [ ] User authentication
- [ ] Presentation history
- [ ] Custom image uploads
- [ ] Multi-language support
- [ ] Advanced editing features

---

**Made with ❤️ for educators and presenters**