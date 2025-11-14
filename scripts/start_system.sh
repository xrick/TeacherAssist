#!/bin/bash
# scripts/start_system.sh
# TeacherAssist 系統啟動腳本（Docker 模式）
# 用途: 自動啟動所有必要服務（統一使用 Docker）

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

echo "🚀 TeacherAssist 系統啟動（Docker 模式）"
echo "========================================"
echo ""

# ===== Step 0: 架構檢測與環境配置 =====
echo "Step 0: 架構檢測與映像檔配置"
echo "-----------------------------"

# 檢測系統架構
ARCH=$(uname -m)
print_info "系統架構: $ARCH"

# 檢測 Docker 支援的平台
if command -v docker >/dev/null 2>&1; then
    DOCKER_ARCH=$(docker version -f '{{.Server.Arch}}' 2>/dev/null || echo "unknown")
    print_info "Docker 架構: $DOCKER_ARCH"
fi

# 平台配置邏輯
case "$ARCH" in
    x86_64|amd64)
        export DOCKER_PLATFORM="linux/amd64"
        print_success "架構: AMD64 (x86_64)"

        # Backend 映像檔選擇
        if docker images | grep -q "teacherassist-backend.*latest"; then
            export BACKEND_IMAGE="teacherassist-backend:latest"
            print_info "Backend: 使用本地映像檔 teacherassist-backend:latest"
        else
            export BACKEND_IMAGE="teacherassist-backend:latest"
            print_warning "Backend: 本地映像檔不存在，將從 Dockerfile 建置"
        fi

        # Presenton 映像檔選擇
        export PRESENTON_IMAGE="ghcr.io/presenton/presenton:latest"
        print_info "Presenton: 使用官方 AMD64 映像檔"
        ;;

    arm64|aarch64)
        export DOCKER_PLATFORM="linux/arm64"
        print_success "架構: ARM64 (Apple Silicon / aarch64)"

        # Backend 映像檔選擇（優先使用本地建置的 ARM64 版本）
        if docker images | grep -q "teacherassist-backend.*latest"; then
            # 檢查映像檔是否為 ARM64
            IMAGE_ID=$(docker images teacherassist-backend:latest -q | head -1)
            if [ -n "$IMAGE_ID" ]; then
                IMAGE_ARCH=$(docker image inspect "$IMAGE_ID" --format '{{.Architecture}}' 2>/dev/null || echo "unknown")
                if [ "$IMAGE_ARCH" = "arm64" ] || [ "$IMAGE_ARCH" = "aarch64" ]; then
                    export BACKEND_IMAGE="teacherassist-backend:latest"
                    print_success "Backend: 使用本地 ARM64 映像檔 (ID: ${IMAGE_ID:0:12})"
                else
                    export BACKEND_IMAGE="teacherassist-backend:latest"
                    print_warning "Backend: 本地映像檔架構為 $IMAGE_ARCH，將重新建置為 ARM64"
                fi
            fi
        else
            export BACKEND_IMAGE="teacherassist-backend:latest"
            print_warning "Backend: 本地映像檔不存在，將從 Dockerfile 建置 ARM64 版本"
        fi

        # Presenton 映像檔選擇（ARM64 需要特殊處理）
        if docker images | grep -q "presenton.*arm64-local"; then
            export PRESENTON_IMAGE="presenton:arm64-local"
            print_success "Presenton: 使用本地 ARM64 映像檔 presenton:arm64-local"
        else
            export PRESENTON_IMAGE="ghcr.io/presenton/presenton:latest"
            print_warning "Presenton: 本地無 ARM64 映像檔"
            print_info "將嘗試使用官方映像檔（Docker 會自動處理平台轉換）"
            print_info "如需原生 ARM64 版本，請執行:"
            print_info "  docker buildx build --platform linux/arm64 -t presenton:arm64-local <presenton_source>"
        fi
        ;;

    *)
        print_error "不支援的架構: $ARCH"
        print_info "支援的架構: x86_64 (AMD64), arm64 (ARM64/Apple Silicon)"
        exit 1
        ;;
esac

# 載入平台特定配置（如果存在，可覆寫自動檢測結果）
if [ -f ".env.platform" ]; then
    print_info "載入 .env.platform 覆寫配置..."
    source .env.platform
    print_warning "使用 .env.platform 中的自訂設定"
fi

# 顯示最終配置
echo ""
print_info "📦 映像檔配置摘要:"
echo "  • 平台: $DOCKER_PLATFORM"
echo "  • Backend: $BACKEND_IMAGE"
echo "  • Presenton: $PRESENTON_IMAGE"

echo ""

# ===== Step 1: 前置需求檢查 =====
echo "Step 1: 檢查前置需求"
echo "-------------------"

# 檢查 Docker
if command -v docker >/dev/null 2>&1; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_success "Docker $DOCKER_VERSION"
else
    print_error "Docker 未安裝"
    echo "請參考: https://docs.docker.com/engine/install/"
    exit 1
fi

# 檢查 Docker Compose (v2)
if docker compose version >/dev/null 2>&1; then
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || echo "v2")
    print_success "Docker Compose $COMPOSE_VERSION"
else
    print_error "Docker Compose (v2) 未安裝"
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

# 檢查 .env 檔案
if [ -f ".env" ]; then
    print_success ".env 檔案存在"
else
    print_error ".env 檔案不存在"
    echo "請參考 .env.example 建立 .env 檔案"
    exit 1
fi

echo ""

# ===== Step 2: Port 衝突檢查 =====
echo "Step 2: 檢查 Port 可用性"
echo "----------------------"

check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port 已被佔用 ($service)"
        echo "當前使用者:"
        lsof -Pi :$port -sTCP:LISTEN | grep -v "^COMMAND" | head -3
        read -p "是否要停止佔用該 port 的程序？(y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            kill $pid 2>/dev/null && print_success "已停止 PID: $pid"
        else
            print_error "Port $port 衝突，無法繼續"
            exit 1
        fi
    else
        print_success "Port $port 可用 ($service)"
    fi
}

check_port 5050 "Backend"
check_port 8001 "Presenton"  # Presenton 映射到 8001
check_port 8080 "Frontend"

echo ""

# ===== Step 3: 啟動 Ollama 服務 =====
echo "Step 3: 啟動 Ollama 服務"
echo "---------------------"

# 檢查 Ollama 是否運行
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_info "啟動 Ollama 服務..."
    # 啟動 Ollama daemon
    if pgrep -x "ollama" > /dev/null; then
        print_info "Ollama 進程已存在"
    else
        ollama serve > /tmp/ollama.log 2>&1 &
        sleep 3
    fi

    # 驗證啟動
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama 服務啟動成功"
    else
        print_error "Ollama 服務啟動失敗"
        cat /tmp/ollama.log | tail -10
        exit 1
    fi
else
    print_success "Ollama 服務已運行"
fi

# 檢查必要模型
print_info "檢查 Ollama 模型..."

# 檢查 gpt-oss:20b（內容分析）
if ollama list | grep -q "gpt-oss:20b"; then
    print_success "gpt-oss:20b 模型可用（內容分析）"
else
    print_warning "phi4-mini:3.8b 模型未安裝（必要）"
    read -p "是否現在下載？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "下載 gpt-oss:20b 模型（約 13 GB）..."
        ollama pull gpt-oss:20b
        print_success "gpt-oss:20b 下載完成"
    else
        print_error "缺少必要模型，無法繼續"
        exit 1
    fi
fi

# 檢查 phi4-mini-reasoning:3.8b（演講稿生成）
if ollama list | grep -qi "gpt-oss:20b"; then
    print_success "gpt-oss:20b 模型可用（演講稿生成）"
else
    print_warning "gpt-oss:20b 模型未安裝（用於演講稿功能）"
    read -p "是否現在下載？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "下載 gpt-oss:20b 模型..."
        ollama pull gpt-oss:20b
        print_success "pgpt-oss:20b 下載完成"
    else
        print_warning "跳過 gpt-oss:20b，演講稿功能將不可用"
    fi
fi

echo ""

# ===== Step 4: 停止舊容器（清理） =====
echo "Step 4: 清理舊容器"
echo "----------------"

print_info "停止並移除舊容器..."
docker compose down 2>/dev/null || true
print_success "舊容器已清理"

echo ""

# ===== Step 5: 啟動 Docker 服務 =====
echo "Step 5: 啟動 Docker 服務"
echo "----------------------"

# 檢查 Docker daemon
if ! docker info >/dev/null 2>&1; then
    print_error "Docker daemon 未運行"
    echo "請執行: sudo systemctl start docker"
    exit 1
fi

# 構建並啟動服務
print_info "構建並啟動 Docker 容器..."

# 先建置 backend（避免平台衝突）
print_info "建置 Backend 容器..."
docker compose build backend

# 啟動服務（使用 --no-build 避免重複建置）
print_info "啟動所有服務..."
if docker compose up -d --no-build 2>&1 | grep -q "platform.*does not match"; then
    print_warning "檢測到平台衝突，分別啟動服務..."

    # 手動啟動 Backend
    docker compose up -d backend

    # 手動啟動 Presenton（處理平台問題）
    print_info "啟動 Presenton 容器（處理平台轉換）..."

    # 檢查是否已有 Presenton 容器運行
    if docker ps -a | grep -q "presenton-api"; then
        docker rm -f presenton-api 2>/dev/null || true
    fi

    # 使用 docker run 直接啟動（明確指定平台）
    docker run -d --name presenton-api \
        --platform linux/amd64 \
        --network teacherassist_app-network \
        --network-alias presenton \
        -p 8001:8000 \
        -e "PRESENTON_API_KEY=${PRESENTON_API_KEY:-sk-presenton-2a1d7db68395f4aaedbca4eb3a82b5c8797c26e3187ea4c2ab5079693e6b9822f576ac900b00e02bc63f44eefb5111db45decec946e95ad482cf73655f2c356e}" \
        -e "LLM=ollama" \
        -e "WEB_GROUNDING=false" \
        -e "TOOL_CALLS=false" \
        -e "OLLAMA_URL=${OLLAMA_URL:-http://192.168.200.48:11434}" \
        -e "OLLAMA_MODEL=${OLLAMA_MODEL:-gpt-oss:20b}" \
        -e "IMAGE_PROVIDER=pexels" \
        -e "PEXELS_API_KEY=${PEXELS_API_KEY:-kKOp88XcQabMQH1lCUMSMjqNRByDrHuFNe3ED4FzkQ4rsg2Yv9peyRA6}" \
        --add-host host.docker.internal:host-gateway \
        -v "$(pwd)/app_data:/app_data" \
        --restart unless-stopped \
        "$PRESENTON_IMAGE"

    print_success "Presenton 容器已啟動（平台: linux/amd64）"
else
    print_success "服務啟動成功"
fi

# 等待服務啟動
print_info "等待服務啟動..."
sleep 5

echo ""

# ===== Step 6: 驗證服務狀態 =====
echo "Step 6: 驗證服務狀態"
echo "------------------"

# 檢查 Presenton
print_info "檢查 Presenton 服務..."

# 策略 1: 檢查容器狀態（跨平台相容）
if ! docker ps --filter "name=presenton-api" --filter "status=running" | grep -q "presenton-api"; then
    print_error "Presenton 容器未運行"
    docker compose logs presenton | tail -30
    exit 1
fi
print_success "Presenton 容器運行中"

# 策略 2: 等待 Presenton 完整初始化（包含模型下載）
print_info "檢查 Presenton 內部服務（包含模型初始化，可能需要 1-2 分鐘）..."

# Presenton 啟動階段：
# 1. Nginx (5秒)
# 2. Ollama (10秒)
# 3. Next.js (10秒)
# 4. ONNX模型下載 (30-60秒，首次啟動)
# 5. ChromaDB初始化 (10秒)

MAX_WAIT=120  # 最多等待 2 分鐘
ELAPSED=0
LAST_LOG_LINE=""

while [ $ELAPSED -lt $MAX_WAIT ]; do
    # 檢查 API 端點是否可用
    HTTP_CODE=$(docker exec presenton-api curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
        print_success "Presenton API 服務正常 (耗時: ${ELAPSED}秒)"
        break
    fi

    # 顯示初始化進度（每 10 秒更新一次）
    if [ $((ELAPSED % 10)) -eq 0 ] && [ $ELAPSED -gt 0 ]; then
        # 取得最新日誌，檢查初始化狀態
        RECENT_LOG=$(docker logs presenton-api 2>&1 | tail -3 | head -1)
        if [ "$RECENT_LOG" != "$LAST_LOG_LINE" ]; then
            if echo "$RECENT_LOG" | grep -q "Downloading\|Initializing\|Starting"; then
                print_info "  ⏳ $RECENT_LOG"
            fi
            LAST_LOG_LINE="$RECENT_LOG"
        fi
    fi

    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

# 最終驗證
if docker exec presenton-api curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null | grep -q "200"; then
    print_success "Presenton API 完全就緒"
else
    print_error "Presenton API 初始化超時或失敗"
    print_warning "這可能是因為："
    print_info "  1. 首次啟動需要下載 ONNX 模型（~80MB）"
    print_info "  2. 網路連線較慢"
    print_info "  3. 系統資源不足"
    echo ""
    print_info "最近的日誌："
    docker compose logs presenton | tail -20
    echo ""
    read -p "是否繼續啟動其他服務？(y/N): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    print_warning "跳過 Presenton 驗證，繼續啟動..."
fi

# 檢查 Backend
print_info "檢查 Backend 服務..."
for i in {1..30}; do
    if curl -s http://localhost:5050/api/health >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

if curl -s http://localhost:5050/api/health >/dev/null 2>&1; then
    print_success "Backend API 運行正常 (http://localhost:5050)"

    # 顯示健康狀態詳情
    HEALTH_JSON=$(curl -s http://localhost:5050/api/health)
    STATUS=$(echo "$HEALTH_JSON" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('status', 'unknown'))" 2>/dev/null || echo "unknown")

    if [ "$STATUS" = "healthy" ]; then
        print_success "健康狀態: $STATUS"

        # 顯示各服務連線狀態
        echo "$HEALTH_JSON" | python3 -c "
import sys, json
data = json.load(sys.stdin)
services = data.get('services', {})
for svc, status in services.items():
    icon = '✅' if status in ['connected', 'available'] else '⚠️'
    print(f'  {icon} {svc}: {status}')
" 2>/dev/null || true
    else
        print_warning "健康狀態: $STATUS"
    fi
else
    print_error "Backend API 無回應"
    docker compose logs backend | tail -20
    exit 1
fi

echo ""

# ===== Step 7: 啟動 Frontend =====
echo "Step 7: 啟動 Frontend 伺服器"
echo "---------------------------"

# 檢查 frontend 目錄
if [ ! -f "frontend/index.html" ]; then
    print_error "frontend/index.html 不存在"
    exit 1
fi

# 啟動 Frontend
print_info "啟動 Frontend HTTP 伺服器..."
cd frontend
nohup python3 -m http.server 8080 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > /tmp/frontend.pid
cd ..

sleep 2

# 驗證 Frontend
if curl -s -I http://localhost:8080/ 2>&1 | grep -q "200 OK"; then
    print_success "Frontend 伺服器運行中 (PID: $FRONTEND_PID)"
else
    print_error "Frontend 啟動失敗"
    cat /tmp/frontend.log | tail -10
    exit 1
fi

echo ""

# ===== 完成 =====
echo "✨ 系統啟動完成！"
echo "================"
echo ""
echo "📋 服務狀態："
echo "  ✅ Ollama:      http://localhost:11434"
echo "  ✅ Presenton:   http://localhost:8000"
echo "  ✅ Backend:     http://localhost:5050"
echo "  ✅ Frontend:    http://localhost:8080"
echo ""
echo "🌐 訪問應用程式："
echo "  http://localhost:8080"
echo ""
echo "📊 API 文件："
echo "  http://localhost:5050/docs"
echo ""
echo "📝 查看即時日誌："
echo "  Backend:   docker compose logs -f backend"
echo "  Presenton: docker compose logs -f presenton"
echo "  Frontend:  tail -f /tmp/frontend.log"
echo "  Ollama:    tail -f /tmp/ollama.log"
echo ""
echo "🛑 停止系統："
echo "  ./scripts/stop_system.sh"
echo ""
echo "🐛 除錯指令："
echo "  docker compose ps              # 查看容器狀態"
echo "  docker compose logs backend    # 查看 Backend 日誌"
echo "  curl http://localhost:5050/api/health  # 測試 Backend"
echo ""
echo "🎉 準備就緒！開始使用 TeacherAssist 吧！"
