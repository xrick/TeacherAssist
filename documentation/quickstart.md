# Quick Start Guide 🚀

Get your Teaching PPT Generator running in 5 minutes!

## Prerequisites Check ✓

Before starting, ensure you have:
- ✅ Docker & Docker Compose installed
- ✅ Python 3.9+ installed
- ✅ Internet connection

## Step-by-Step Setup

### 1️⃣ Install Ollama (2 minutes)

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Download the AI models
ollama pull qwen-oss:20      # For content analysis
ollama pull zephyr:7b         # For transcript generation

# Verify (should show both models in the list)
ollama list
```

### 2️⃣ Create Project Structure (1 minute)

```bash
# Create main directory
mkdir teaching-ppt-generator
cd teaching-ppt-generator

# Create subdirectories
mkdir -p backend/app/{api,services,utils}
mkdir -p frontend
mkdir -p output
```

### 3️⃣ Add Project Files (1 minute)

Copy all the artifact files provided into the structure:

```
teaching-ppt-generator/
├── docker-compose.yml          ← Copy here
├── .env                        ← Copy here
├── README.md                   ← Copy here
├── CHECKLIST.md               ← Copy here
├── setup.sh                   ← Copy here
├── test.sh                    ← Copy here
├── backend/
│   ├── Dockerfile             ← Copy here
│   ├── requirements.txt       ← Copy here
│   └── app/
│       ├── __init__.py        ← Create empty file
│       ├── main.py            ← Copy here
│       ├── config.py          ← Copy here
│       ├── models.py          ← Copy here
│       ├── api/
│       │   ├── __init__.py    ← Create empty file
│       │   └── routes.py      ← Copy here
│       └── services/
│           ├── __init__.py    ← Create empty file
│           ├── ollama_service.py        ← Copy here
│           ├── pexels_service.py        ← Copy here
│           ├── presenton_service.py     ← Copy here
│           └── content_processor.py     ← Copy here
└── frontend/
    └── index.html             ← Copy here
```

### 4️⃣ Start Everything (1 minute)

```bash
# Make scripts executable
chmod +x setup.sh test.sh

# Run setup
./setup.sh

# Or manually:
docker-compose up -d
```

### 5️⃣ Test the System (30 seconds)

```bash
# Run test suite
./test.sh

# Or manually test:
curl http://localhost:5000/api/health
```

### 6️⃣ Open Frontend (10 seconds)

```bash
# Option 1: Direct file
open frontend/index.html  # macOS
xdg-open frontend/index.html  # Linux

# Option 2: Local server (recommended)
cd frontend
python3 -m http.server 8080
# Then visit: http://localhost:8080
```

## 🎯 Quick Test

1. **Open the frontend** (http://localhost:8080)
2. **Enter test content**:
   ```
   今天我們要討論人工智慧在教育領域的應用。首先介紹機器學習的基本概念，包括監督學習和非監督學習。接著探討深度學習在教育中的實際應用案例。最後分析AI輔助教學的未來發展趨勢。
   ```
3. **Select template**: 教學簡報 (Educational)
4. **Click**: 生成簡報 (Generate)
5. **Wait**: 30-60 seconds
6. **Download**: PowerPoint or PDF
7. **Generate Transcript** (Optional):
   - Click "生成演講稿"
   - Select style (教學式/正式/對話式)
   - Wait 30-60 seconds
   - Download transcript text file

## 🔧 Troubleshooting

### Problem: Docker containers won't start
```bash
# Check Docker is running
docker ps

# Restart Docker
sudo systemctl restart docker  # Linux
# Or restart Docker Desktop

# Rebuild
docker-compose down
docker-compose up -d --build
```

### Problem: Ollama not responding
```bash
# Check Ollama status
ps aux | grep ollama

# Start Ollama
ollama serve

# Check models
ollama list

# Pull missing models if needed
ollama pull qwen-oss:20
ollama pull zephyr:7b
```

### Problem: Port already in use
```bash
# Find what's using port 5000
lsof -i :5000

# Kill the process or change port in docker-compose.yml
```

### Problem: Backend returns errors
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Wait 30 seconds for services to fully start
# - Check .env file has correct API keys
# - Verify Ollama is running: curl http://localhost:11434/api/tags
```

## 📊 Verify Everything Works

Run these commands to check all services:

```bash
# 1. Check Ollama
curl http://localhost:11434/api/tags

# 2. Check Backend
curl http://localhost:5000/api/health

# 3. Check Presenton (might take a minute to start)
curl http://localhost:8000/health

# 4. View running containers
docker-compose ps

# All should show "Up" status
```

## 🎓 Your First Presentation

### Example Content (Copy & Paste):

**For Educational Template:**
```
本課程介紹Python程式設計基礎。首先學習變數和資料型態，包括數字、字串和布林值。接著探討條件判斷和迴圈結構。然後學習函數的定義和使用。最後介紹物件導向程式設計的基本概念。透過實作練習，學生將能夠撰寫基本的Python程式。
```

**For Administrative Template:**
```
本季度營運報告摘要。第一季營收達成率102%，超越預期目標。主要成長動能來自新產品線的推出。人力資源方面，招募10名新同仁。下季度將持續優化產品品質，並擴大市場覆蓋率。預期第二季營收將成長15%。
```

**For General Template:**
```
永續發展策略規劃。目標在2030年達成碳中和。具體措施包括：採用再生能源、提升能源效率、推動循環經濟、加強供應鏈管理。預期投資金額5000萬元。預期效益包括降低營運成本20%，提升企業形象，符合國際ESG標準。
```

## 📁 Output Files

Generated presentations are saved in:
- **Docker**: `/app/output/` (inside container)
- **Local**: `./output/` (on your machine)

Files are automatically downloaded when you click the download buttons.

## 🔄 Daily Usage

### Start the system:
```bash
cd teaching-ppt-generator
docker-compose up -d
```

### Stop the system:
```bash
docker-compose down
```

### View logs:
```bash
docker-compose logs -f
```

### Restart everything:
```bash
docker-compose restart
```

## 📞 Need Help?

1. **Check logs**: `docker-compose logs -f`
2. **Run health check**: `curl http://localhost:5000/api/health`
3. **Review**: README.md and CHECKLIST.md
4. **Test script**: `./test.sh`

## 🎉 Success Checklist

- [ ] Ollama responds at http://localhost:11434
- [ ] Backend responds at http://localhost:5000
- [ ] Frontend opens in browser
- [ ] Can generate a test presentation
- [ ] Can download PPTX and PDF files
- [ ] All templates work
- [ ] Can generate transcript (Zephyr 7B available)
- [ ] Can download transcript text file

**If all checked: You're ready to create amazing presentations! 🚀**

---

## 💡 Pro Tips

1. **Better Content = Better Slides**: Provide structured content with clear points
2. **Template Selection**: Choose based on your audience and purpose
3. **Image Keywords**: The AI generates English keywords for better image results
4. **Length**: 200-1000 characters work best for quality presentations
5. **Multiple Attempts**: Try different templates for the same content

## 🔒 Security Note

Never commit your `.env` file to version control. It contains sensitive API keys.

## 📈 Next Steps

After successful setup:
1. Read the full [README.md](README.md) for advanced features
2. Review [CHECKLIST.md](CHECKLIST.md) for comprehensive testing
3. Check API documentation at http://localhost:5000/docs
4. Customize templates and styles as needed
5. Consider production deployment options

---

**Ready to start? Run `./setup.sh` and you're good to go! 🎓**