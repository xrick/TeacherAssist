#!/bin/bash
# TeacherAssist 系統啟動腳本
# 用途: 自動啟動所有必要服務（Backend 從源碼運行）

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 專案根目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 工具函數
print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "🚀 TeacherAssist 系統啟動"
echo "================================"
echo ""

# ===== Step 1: 前置需求檢查 =====
echo "Step 1: 檢查前置需求"
echo "-------------------"

# 檢查 Python
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    print_success "Python $PYTHON_VERSION"
else
    print_error "Python 3 未安裝"
    exit 1
fi

# 檢查 Docker
if command -v docker >/dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker $DOCKER_VERSION"
else
    print_error "Docker 未安裝"
    exit 1
fi

# 檢查 Ollama
if command -v ollama >/dev/null 2>&1; then
    print_success "Ollama installed"
else
    print_error "Ollama 未安裝"
    echo "請執行: curl https://ollama.ai/install.sh | sh"
    exit 1
fi

# 檢查虛擬環境
if [ -d "backend/venv" ]; then
    print_success "Python 虛擬環境存在"
else
    print_warning "虛擬環境不存在，正在建立..."
    cd backend
    python3 -m venv venv
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    deactivate
    cd ..
    print_success "虛擬環境已建立"
fi

echo ""

# ===== Step 2: 啟動 Ollama #1 (gpt-oss:20b) =====
echo "Step 2: 啟動 Ollama #1 (gpt-oss:20b - Port 11434)"
echo "-----------------------------------------------"

# 檢查 port 11434 是否有 Ollama 運行
if lsof -Pi :11434 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_info "Ollama #1 已在 port 11434 運行"
else
    print_info "啟動 Ollama #1 (port 11434)..."
    nohup ollama serve > /tmp/ollama-11434.log 2>&1 &
    sleep 3

    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama #1 (11434) 啟動成功"
    else
        print_error "Ollama #1 (11434) 啟動失敗"
        cat /tmp/ollama-11434.log | tail -10
        exit 1
    fi
fi

# 檢查 gpt-oss:20b 模型
print_info "檢查 gpt-oss:20b 模型..."
if ollama list | grep -q "gpt-oss:20b"; then
    print_success "gpt-oss:20b 模型可用"
else
    print_warning "gpt-oss:20b 模型未安裝"
    echo "請執行: ollama pull gpt-oss:20b"
    read -p "是否現在下載？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ollama pull gpt-oss:20b
    else
        print_error "缺少必要模型，無法繼續"
        exit 1
    fi
fi

echo ""

# ===== Step 2b: 啟動 Ollama #2 (Zephyr 7B) =====
echo "Step 2b: 啟動 Ollama #2 (Zephyr 7B - Port 11435)"
echo "-----------------------------------------------"

# 檢查 port 11435 是否有 Ollama 運行
if lsof -Pi :11435 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_info "Ollama #2 已在 port 11435 運行"
else
    print_info "啟動 Ollama #2 (port 11435)..."
    # 設置 OLLAMA_HOST 並啟動第二個實例
    OLLAMA_HOST=127.0.0.1:11435 nohup ollama serve > /tmp/ollama-11435.log 2>&1 &
    sleep 3

    if curl -s http://localhost:11435/api/tags >/dev/null 2>&1; then
        print_success "Ollama #2 (11435) 啟動成功"
    else
        print_error "Ollama #2 (11435) 啟動失敗"
        cat /tmp/ollama-11435.log | tail -10
        exit 1
    fi
fi

# 檢查 Zephyr 7B 模型
print_info "檢查 Zephyr 7B 模型..."
if OLLAMA_HOST=127.0.0.1:11435 ollama list | grep -q "zephyr:7b"; then
    print_success "zephyr:7b 模型可用"
else
    print_warning "zephyr:7b 模型未安裝（演講稿功能需要）"
    read -p "是否現在下載？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        OLLAMA_HOST=127.0.0.1:11435 ollama pull zephyr:7b
    else
        print_warning "跳過 Zephyr 7B 下載，演講稿功能將不可用"
    fi
fi

echo ""

# ===== Step 3: 啟動 Presenton =====
echo "Step 3: 啟動 Presenton (Docker)"
echo "------------------------------"

# 停止 backend 容器（如果在運行）
docker-compose stop backend 2>/dev/null || true

# 啟動 Presenton
print_info "啟動 Presenton 容器..."
docker-compose up -d presenton

print_info "等待 Presenton 啟動..."
for i in {1..30}; do
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 驗證 Presenton
if docker-compose ps presenton 2>/dev/null | grep -q "Up"; then
    print_success "Presenton 容器運行中"
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        print_success "Presenton API 響應正常"
    else
        print_warning "Presenton API 尚未就緒"
    fi
else
    print_error "Presenton 容器啟動失敗"
    docker-compose logs presenton 2>/dev/null | tail -20
    exit 1
fi

echo ""

# ===== Step 4: 啟動 Backend =====
echo "Step 4: 啟動 Backend (從源碼)"
echo "----------------------------"

# 檢查 .env 檔案
if [ -f ".env" ]; then
    print_success ".env 檔案存在"
else
    print_error ".env 檔案不存在"
    exit 1
fi

# 檢查 backend/.env 連結
if [ ! -f "backend/.env" ]; then
    print_info "建立 .env 符號連結..."
    cd backend && ln -s ../.env .env && cd ..
fi

# 啟動 Backend
print_info "啟動 Backend 服務..."
cd backend
source venv/bin/activate

# 建立日誌目錄
mkdir -p logs

# 啟動 uvicorn
nohup uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload \
    > logs/backend.log 2>&1 &

BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid

cd ..

print_info "等待 Backend 啟動..."
for i in {1..15}; do
    if curl -s http://localhost:5000/api/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 驗證 Backend
if curl -s http://localhost:5000/api/health >/dev/null 2>&1; then
    print_success "Backend API 運行中 (PID: $BACKEND_PID)"

    # 顯示健康狀態
    HEALTH_JSON=$(curl -s http://localhost:5000/api/health)
    STATUS=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
    print_info "健康狀態: $STATUS"
else
    print_error "Backend 啟動失敗"
    cat backend/logs/backend.log 2>/dev/null | tail -20
    exit 1
fi

echo ""

# ===== Step 5: 啟動 Frontend =====
echo "Step 5: 啟動 Frontend 伺服器"
echo "---------------------------"

# 檢查 frontend/index.html
if [ ! -f "frontend/index.html" ]; then
    if [ -f "src/frontend/index.html" ]; then
        print_warning "frontend/index.html 不存在，從 src/frontend 複製..."
        cp src/frontend/index.html frontend/
    else
        print_error "找不到 index.html"
        exit 1
    fi
fi

# 啟動 Frontend
print_info "啟動 Frontend HTTP 伺服器..."
cd frontend
nohup python3 -m http.server 8080 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 2

# 驗證 Frontend
if curl -s -I http://localhost:8080/ 2>&1 | grep -q "200 OK"; then
    print_success "Frontend 伺服器運行中 (PID: $FRONTEND_PID)"
else
    print_error "Frontend 啟動失敗"
    exit 1
fi

echo ""

# ===== 完成 =====
echo "✨ 系統啟動完成！"
echo "================"
echo ""
echo "📋 服務狀態："
echo "  ✅ Ollama #1 (gpt-oss):    http://localhost:11434"
echo "  ✅ Ollama #2 (Zephyr):     http://localhost:11435"
echo "  ✅ Presenton:              http://localhost:8000"
echo "  ✅ Backend (realtime log): http://localhost:5000"
echo "  ✅ Frontend:               http://localhost:8080"
echo ""
echo "🌐 訪問應用程式："
echo "  http://localhost:8080"
echo ""
echo "📊 API 文件："
echo "  http://localhost:5000/docs"
echo ""
echo "📝 查看即時日誌："
echo "  Backend:  tail -f backend/logs/backend.log"
echo "  Ollama 1: tail -f /tmp/ollama-11434.log"
echo "  Ollama 2: tail -f /tmp/ollama-11435.log"
echo "  Frontend: tail -f /tmp/frontend.log"
echo "  Presenton: docker-compose logs -f presenton"
echo ""
echo "🛑 停止系統："
echo "  ./scripts/stop_system.sh"
echo ""
echo "🎉 準備就緒！開始使用 TeacherAssist 吧！"
