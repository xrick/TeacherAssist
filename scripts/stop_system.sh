#!/bin/bash
# TeacherAssist 系統停止腳本
# 用途: 優雅地停止所有服務

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

echo "🛑 TeacherAssist 系統停止"
echo "================================"
echo ""

# ===== Step 1: 停止 Frontend =====
echo "Step 1: 停止 Frontend"
echo "--------------------"

FRONTEND_PIDS=$(ps aux | grep "python3.*http.server.*8080" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PIDS" ]; then
    print_info "停止 Frontend (PID: $FRONTEND_PIDS)..."
    echo "$FRONTEND_PIDS" | xargs kill 2>/dev/null || true
    sleep 1
    print_success "Frontend 已停止"
else
    print_info "Frontend 未運行"
fi

echo ""

# ===== Step 2: 停止 Backend =====
echo "Step 2: 停止 Backend"
echo "-------------------"

# 從 PID 檔案讀取
if [ -f "backend/logs/backend.pid" ]; then
    BACKEND_PID=$(cat backend/logs/backend.pid)
    if ps -p $BACKEND_PID >/dev/null 2>&1; then
        print_info "停止 Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null || true
        sleep 2

        # 如果還在運行，強制停止
        if ps -p $BACKEND_PID >/dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null || true
        fi

        rm -f backend/logs/backend.pid
        print_success "Backend 已停止"
    else
        print_info "Backend PID 檔案存在但程序未運行"
        rm -f backend/logs/backend.pid
    fi
else
    # 嘗試找到所有 uvicorn 程序
    BACKEND_PIDS=$(ps aux | grep "uvicorn app.main" | grep -v grep | awk '{print $2}')
    if [ -n "$BACKEND_PIDS" ]; then
        print_info "停止 Backend (PID: $BACKEND_PIDS)..."
        echo "$BACKEND_PIDS" | xargs kill 2>/dev/null || true
        sleep 1
        print_success "Backend 已停止"
    else
        print_info "Backend 未運行"
    fi
fi

echo ""

# ===== Step 3: 停止 Presenton =====
echo "Step 3: 停止 Presenton"
echo "---------------------"

if docker-compose ps presenton 2>/dev/null | grep -q "Up"; then
    print_info "停止 Presenton 容器..."
    docker-compose stop presenton
    print_success "Presenton 已停止"
else
    print_info "Presenton 未運行"
fi

echo ""

# ===== Step 4: 停止 Ollama 實例 (可選) =====
echo "Step 4: 停止 Ollama 實例 (可選)"
echo "------------------------------"

print_warning "Ollama 服務可能被其他應用使用"
read -p "是否停止所有 Ollama 實例？(y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 查找所有 ollama serve 進程
    OLLAMA_PIDS=$(pgrep -f "ollama serve" 2>/dev/null || true)

    if [ -n "$OLLAMA_PIDS" ]; then
        print_info "找到 Ollama 進程: $OLLAMA_PIDS"

        # 停止所有 Ollama 實例
        print_info "停止所有 Ollama 實例..."
        pkill -f "ollama serve" 2>/dev/null || true
        sleep 2

        # 驗證停止
        if pgrep -f "ollama serve" >/dev/null 2>&1; then
            print_warning "部分 Ollama 進程仍在運行，嘗試強制停止..."
            pkill -9 -f "ollama serve" 2>/dev/null || true
            sleep 1
        fi

        print_success "Ollama 實例已停止"
    else
        print_info "Ollama 未運行"
    fi
else
    print_info "保持 Ollama 運行"
fi

echo ""

# ===== 完成 =====
echo "✅ 系統停止完成！"
echo "==============="
echo ""
echo "📋 服務狀態："
echo ""

# 檢查各服務狀態
check_service() {
    local url=$1
    local name=$2
    if curl -s -o /dev/null -w "%{http_code}" "$url" 2>&1 | grep -q "000\|Connection refused"; then
        echo "  ⭕ $name: 已停止"
    else
        echo "  ⚠️  $name: 仍在運行"
    fi
}

check_service "http://localhost:11434" "Ollama #1 (11434)"
check_service "http://localhost:11435" "Ollama #2 (11435)"
check_service "http://localhost:8000" "Presenton"
check_service "http://localhost:5000" "Backend"
check_service "http://localhost:8080" "Frontend"

echo ""
echo "🔄 重新啟動系統："
echo "  ./scripts/start_system.sh"
echo ""
