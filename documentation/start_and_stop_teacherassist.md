# TeacherAssist 系統啟動與停止指南

**版本**: 1.0.0
**日期**: 2025-10-13
**配置**: Backend from Source + Presenton in Docker

---

## 📋 目錄

1. [系統架構概覽](#系統架構概覽)
2. [前置需求檢查](#前置需求檢查)
3. [啟動系統](#啟動系統)
4. [停止系統](#停止系統)
5. [自動化腳本](#自動化腳本)
6. [疑難排解](#疑難排解)
7. [日誌管理](#日誌管理)

---

## 系統架構概覽

### 運行模式

```
┌─────────────────────────────────────────────────┐
│              TeacherAssist 系統                  │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. Ollama #1 (gpt-oss)   (Host - Background)   │
│     └─ localhost:11434    (簡報內容生成)        │
│                                                  │
│  2. Ollama #2 (Zephyr)    (Host - Background)   │
│     └─ localhost:11435    (演講稿生成)          │
│                                                  │
│  3. Presenton API         (Docker Container)    │
│     └─ localhost:8000                           │
│                                                  │
│  4. Backend API           (Source - Foreground) │
│     └─ localhost:5000     (Real-time logs)      │
│                                                  │
│  5. Frontend Server       (Python HTTP Server)  │
│     └─ localhost:8080                           │
│                                                  │
└─────────────────────────────────────────────────┘
```

### 服務依賴關係

```
Frontend (8080)
    ↓
Backend (5000) ──→ Presenton (8000) ──→ Ollama #1 (11434 - gpt-oss:20b)
    ↓
    ├──→ Ollama #1 (11434) ─────────────────┘
    │
    ├──→ Ollama #2 (11435 - Zephyr 7B - 演講稿生成)
    │
    └──→ Pexels API (External - 圖片)
```

### 啟動順序

1. **Python venv** (激活虛擬環境)
2. **Ollama #1 (gpt-oss:20b)** - Port 11434 (簡報內容生成)
3. **Ollama #2 (Zephyr 7B)** - Port 11435 (演講稿生成，需設置 `OLLAMA_HOST=127.0.0.1:11435`)
4. **Presenton** (Docker 容器)
5. **Backend** (從源碼運行，有 realtime logger)
6. **Frontend** (靜態檔案伺服器)

---

## 前置需求檢查

### 必要軟體

```bash
# 檢查所有必要軟體
./scripts/check_prerequisites.sh

# 或手動檢查：
python3 --version    # 需要 3.11+
docker --version
docker-compose --version
ollama --version
```

### 必要模型

```bash
# 檢查 Ollama 模型
ollama list

# 必須要有：
# - gpt-oss:20b   (簡報內容生成 - Port 11434)
# - zephyr:7b     (演講稿生成 - Port 11435)

# 如果缺少模型，請下載：
ollama pull gpt-oss:20b
ollama pull zephyr:7b
```

### 環境變數

```bash
# 檢查 .env 檔案
cat .env | grep -E "PRESENTON_API_KEY|PEXELS_API_KEY|OLLAMA_MODEL"

# 必須配置：
# - PRESENTON_API_KEY
# - PEXELS_API_KEY
# - OLLAMA_MODEL=gpt-oss:20b
```

### Python 虛擬環境

```bash
# 檢查 backend venv 是否存在
ls -la backend/venv/

# 如果不存在，建立它：
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 啟動系統

### 🚀 方法 1: 自動化腳本（推薦）

```bash
# 使用自動化啟動腳本
./scripts/start_system.sh

# 腳本會自動：
# 1. 檢查前置需求
# 2. 啟動所有服務（依正確順序）
# 3. 驗證服務健康狀態
# 4. 顯示訪問 URL
```

### 🔧 方法 2: 手動啟動（逐步）

#### Step 1: 激活 Python 虛擬環境

```bash
cd /path/to/TeacherAssist/backend
source venv/bin/activate

# 確認在 venv 中
which python3
# 應該顯示: .../backend/venv/bin/python3
```

#### Step 2: 啟動 Ollama #1 (gpt-oss:20b) - Port 11434

```bash
# 檢查 Ollama 是否已運行在 port 11434
ps aux | grep "ollama serve" | grep -v grep

# 如果未運行，啟動它（預設 port 11434）：
ollama serve &

# 等待 2 秒讓服務啟動
sleep 2

# 驗證 Ollama #1 運行
curl -s http://localhost:11434/api/tags | grep -q "models" && echo "✅ Ollama #1 (11434) is running" || echo "❌ Ollama #1 failed"

# 驗證 gpt-oss:20b 模型可用
ollama list | grep "gpt-oss:20b"
```

#### Step 2b: 啟動 Ollama #2 (Zephyr 7B) - Port 11435

```bash
# 設置 OLLAMA_HOST 環境變數指向 port 11435
export OLLAMA_HOST=127.0.0.1:11435

# 啟動第二個 Ollama 實例
ollama serve &

# 等待 2 秒讓服務啟動
sleep 2

# 驗證 Ollama #2 運行（仍然使用 OLLAMA_HOST 環境變數）
curl -s http://localhost:11435/api/tags | grep -q "models" && echo "✅ Ollama #2 (11435) is running" || echo "❌ Ollama #2 failed"

# 驗證 Zephyr 7B 模型可用
OLLAMA_HOST=127.0.0.1:11435 ollama list | grep "zephyr:7b"

# 重置 OLLAMA_HOST（後續操作使用預設 port）
unset OLLAMA_HOST
```

**重要注意事項**：
- 必須啟動 **兩個獨立的** Ollama 實例
- Ollama #1 (11434): 用於簡報內容生成 (gpt-oss:20b)
- Ollama #2 (11435): 用於演講稿生成 (Zephyr 7B)
- 第二個實例需要設置 `OLLAMA_HOST=127.0.0.1:11435`
- 兩個實例都必須在背景運行
- 建議在不同終端運行，或使用 `nohup` 和日誌分離

#### Step 3: 啟動 Presenton (Docker)

```bash
# 停止任何運行中的 backend 容器（我們將從源碼運行）
docker-compose stop backend 2>/dev/null

# 只啟動 Presenton
docker-compose up -d presenton

# 等待容器啟動
echo "等待 Presenton 啟動..."
sleep 10

# 驗證 Presenton 運行
docker-compose ps presenton
curl -s http://localhost:8000/ && echo "✅ Presenton is running" || echo "❌ Presenton failed"
```

**檢查點**：
```bash
# Presenton 容器應該顯示 "Up"
docker-compose ps presenton
# NAME: presenton-api
# STATUS: Up
# PORTS: 0.0.0.0:8000->8000/tcp
```

#### Step 4: 啟動 Backend (從源碼，帶 realtime logger)

```bash
# 開啟新終端或使用 tmux/screen
cd /path/to/TeacherAssist/backend

# 激活虛擬環境
source venv/bin/activate

# 確認在 venv 中
which python3
# 應該顯示: .../backend/venv/bin/python3

# 啟動 Backend (前景模式，可看到實時日誌)
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

**預期輸出**：
```
INFO:     Will watch for changes in these directories: ['.../backend']
INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**驗證 Backend** (開新終端):
```bash
curl -s http://localhost:5000/api/health | python3 -m json.tool

# 預期回應：
{
    "status": "healthy",
    "services": {
        "presenton": "connected",
        "ollama": "connected",
        "pexels": "connected",
        "zephyr": "available"
    }
}
```

#### Step 5: 啟動 Frontend

```bash
# 開啟新終端
cd /path/to/TeacherAssist/frontend

# 啟動 HTTP 伺服器
python3 -m http.server 8080
```

**預期輸出**：
```
Serving HTTP on 0.0.0.0 port 8080 (http://0.0.0.0:8080/) ...
```

**驗證 Frontend**:
```bash
# 開新終端
curl -I http://localhost:8080/
# 應返回: HTTP/1.0 200 OK
```

#### Step 6: 訪問系統

```bash
# 開啟瀏覽器
# 方法 1: 使用命令列
xdg-open http://localhost:8080  # Linux
open http://localhost:8080      # macOS

# 方法 2: 手動在瀏覽器輸入
# http://localhost:8080
```

---

## 停止系統

### 🛑 方法 1: 自動化腳本（推薦）

```bash
# 使用自動化停止腳本
./scripts/stop_system.sh

# 腳本會自動：
# 1. 優雅地停止 Frontend
# 2. 優雅地停止 Backend
# 3. 停止 Presenton 容器
# 4. (可選) 停止 Ollama
# 5. 清理臨時檔案
```

### 🔧 方法 2: 手動停止（逐步）

#### Step 1: 停止 Frontend

```bash
# 在運行 Frontend 的終端按 Ctrl+C

# 或找到 PID 並 kill
ps aux | grep "python3.*http.server.*8080" | grep -v grep | awk '{print $2}' | xargs kill

# 驗證
curl -I http://localhost:8080/ 2>&1 | grep -q "Connection refused" && echo "✅ Frontend stopped"
```

#### Step 2: 停止 Backend

```bash
# 在運行 Backend 的終端按 Ctrl+C

# 或找到 PID 並 kill
ps aux | grep "uvicorn app.main" | grep -v grep | awk '{print $2}' | xargs kill

# 驗證
curl -I http://localhost:5000/ 2>&1 | grep -q "Connection refused" && echo "✅ Backend stopped"
```

**重要**：優雅停止確保：
- 當前請求完成
- 檔案正確儲存
- 資源正確釋放

#### Step 3: 停止 Presenton

```bash
# 停止 Presenton 容器
docker-compose stop presenton

# 驗證
docker-compose ps presenton
# STATUS 應該顯示 "Exited"

# 或完全移除容器
# docker-compose down presenton
```

#### Step 4: 停止 Ollama 實例 (可選)

```bash
# 注意：Ollama 實例通常保持運行供其他應用使用
# 只在確定不需要時才停止

# 找到所有 Ollama PID
ps aux | grep "ollama serve" | grep -v grep

# 停止兩個 Ollama 實例
pkill -f "ollama serve"

# 驗證 Ollama #1 (11434)
curl -I http://localhost:11434/ 2>&1 | grep -q "Connection refused" && echo "✅ Ollama #1 (11434) stopped"

# 驗證 Ollama #2 (11435)
curl -I http://localhost:11435/ 2>&1 | grep -q "Connection refused" && echo "✅ Ollama #2 (11435) stopped"
```

**重要**：此步驟會停止 **兩個** Ollama 實例 (ports 11434 和 11435)

---

## 自動化腳本

### 啟動腳本: `scripts/start_system.sh`

```bash
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
    print_success "Docker $(docker --version | awk '{print $3}' | sed 's/,//')"
else
    print_error "Docker 未安裝"
    exit 1
fi

# 檢查 Ollama
if command -v ollama >/dev/null 2>&1; then
    print_success "Ollama $(ollama --version 2>&1 | grep -oP 'version is \K[0-9.]+')"
else
    print_error "Ollama 未安裝"
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

# ===== Step 2: 啟動 Ollama =====
echo "Step 2: 啟動 Ollama 服務"
echo "----------------------"

if ps aux | grep "ollama serve" | grep -v grep >/dev/null; then
    print_info "Ollama 已在運行"
else
    print_info "啟動 Ollama..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3

    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "Ollama 啟動成功"
    else
        print_error "Ollama 啟動失敗"
        exit 1
    fi
fi

# 檢查必要模型
print_info "檢查 Ollama 模型..."
if ollama list | grep -q "gpt-oss:20b"; then
    print_success "gpt-oss:20b 模型可用"
else
    print_warning "gpt-oss:20b 模型未安裝"
    echo "請執行: ollama pull gpt-oss:20b"
fi

if ollama list | grep -q "zephyr:7b"; then
    print_success "zephyr:7b 模型可用"
else
    print_warning "zephyr:7b 模型未安裝（演講稿功能需要）"
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
sleep 10

# 驗證 Presenton
if docker-compose ps presenton | grep -q "Up"; then
    print_success "Presenton 容器運行中"
    if curl -s http://localhost:8000/ >/dev/null 2>&1; then
        print_success "Presenton API 響應正常"
    else
        print_warning "Presenton API 尚未就緒，可能需要更多時間"
    fi
else
    print_error "Presenton 容器啟動失敗"
    docker-compose logs presenton | tail -20
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
    ln -s ../.env backend/.env
fi

# 啟動 Backend (在背景，日誌輸出到檔案)
print_info "啟動 Backend 服務..."
cd backend
source venv/bin/activate

# 建立日誌目錄
mkdir -p logs

# 啟動 uvicorn 並將日誌輸出到檔案
nohup uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload \
    > logs/backend.log 2>&1 &

BACKEND_PID=$!
echo $BACKEND_PID > logs/backend.pid

cd ..

print_info "等待 Backend 啟動..."
sleep 5

# 驗證 Backend
if curl -s http://localhost:5000/api/health >/dev/null 2>&1; then
    print_success "Backend API 運行中 (PID: $BACKEND_PID)"

    # 顯示健康狀態
    HEALTH_STATUS=$(curl -s http://localhost:5000/api/health | python3 -c "import sys,json; data=json.load(sys.stdin); print(f\"{data['status']} - {', '.join([k for k,v in data['services'].items() if v in ['connected','available']])}\")")
    print_info "健康狀態: $HEALTH_STATUS"
else
    print_error "Backend 啟動失敗"
    cat backend/logs/backend.log | tail -20
    exit 1
fi

echo ""

# ===== Step 5: 啟動 Frontend =====
echo "Step 5: 啟動 Frontend 伺服器"
echo "---------------------------"

# 檢查 frontend/index.html
if [ ! -f "frontend/index.html" ]; then
    print_warning "frontend/index.html 不存在，從 src/frontend 複製..."
    cp src/frontend/index.html frontend/
fi

# 啟動 Frontend
print_info "啟動 Frontend HTTP 伺服器..."
cd frontend
nohup python3 -m http.server 8080 > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

sleep 2

# 驗證 Frontend
if curl -s -I http://localhost:8080/ | grep -q "200 OK"; then
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
echo "  ✅ Ollama:     http://localhost:11434"
echo "  ✅ Presenton:  http://localhost:8000"
echo "  ✅ Backend:    http://localhost:5000"
echo "  ✅ Frontend:   http://localhost:8080"
echo ""
echo "🌐 訪問應用程式："
echo "  http://localhost:8080"
echo ""
echo "📊 API 文件："
echo "  http://localhost:5000/docs"
echo ""
echo "📝 查看日誌："
echo "  Backend:  tail -f backend/logs/backend.log"
echo "  Frontend: tail -f /tmp/frontend.log"
echo "  Ollama:   tail -f /tmp/ollama.log"
echo "  Presenton: docker-compose logs -f presenton"
echo ""
echo "🛑 停止系統："
echo "  ./scripts/stop_system.sh"
echo ""
echo "🎉 準備就緒！開始使用 TeacherAssist 吧！"
```

### 停止腳本: `scripts/stop_system.sh`

```bash
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

echo "🛑 TeacherAssist 系統停止"
echo "================================"
echo ""

# ===== Step 1: 停止 Frontend =====
echo "Step 1: 停止 Frontend"
echo "--------------------"

FRONTEND_PIDS=$(ps aux | grep "python3.*http.server.*8080" | grep -v grep | awk '{print $2}')
if [ -n "$FRONTEND_PIDS" ]; then
    print_info "停止 Frontend (PID: $FRONTEND_PIDS)..."
    echo "$FRONTEND_PIDS" | xargs kill 2>/dev/null
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
        kill $BACKEND_PID 2>/dev/null
        sleep 2

        # 如果還在運行，強制停止
        if ps -p $BACKEND_PID >/dev/null 2>&1; then
            kill -9 $BACKEND_PID 2>/dev/null
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
        echo "$BACKEND_PIDS" | xargs kill 2>/dev/null
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

if docker-compose ps presenton | grep -q "Up"; then
    print_info "停止 Presenton 容器..."
    docker-compose stop presenton
    print_success "Presenton 已停止"
else
    print_info "Presenton 未運行"
fi

echo ""

# ===== Step 4: 停止 Ollama (可選) =====
echo "Step 4: 停止 Ollama (可選)"
echo "------------------------"

read -p "是否停止 Ollama 服務？(y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    OLLAMA_PIDS=$(ps aux | grep "ollama serve" | grep -v grep | awk '{print $2}')
    if [ -n "$OLLAMA_PIDS" ]; then
        print_info "停止 Ollama (PID: $OLLAMA_PIDS)..."
        echo "$OLLAMA_PIDS" | xargs kill 2>/dev/null
        sleep 1
        print_success "Ollama 已停止"
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
    if curl -s -o /dev/null -w "%{http_code}" "$1" 2>&1 | grep -q "000\|Connection refused"; then
        echo "  ⭕ $2: 已停止"
    else
        echo "  ⚠️  $2: 仍在運行"
    fi
}

check_service "http://localhost:11434" "Ollama"
check_service "http://localhost:8000" "Presenton"
check_service "http://localhost:5000" "Backend"
check_service "http://localhost:8080" "Frontend"

echo ""
echo "🔄 重新啟動系統："
echo "  ./scripts/start_system.sh"
echo ""
```

---

## 疑難排解

### 問題 1: Ollama 連線失敗

**錯誤訊息**: `Connection refused: http://localhost:11434` 或 `http://localhost:11435`

**解決方案**:
```bash
# 檢查兩個 Ollama 實例是否運行
ps aux | grep "ollama serve"
netstat -tlnp | grep -E "11434|11435"

# 如果 Ollama #1 (11434) 未運行，啟動它
ollama serve > /tmp/ollama-11434.log 2>&1 &

# 驗證 Ollama #1
curl http://localhost:11434/api/tags

# 如果 Ollama #2 (11435) 未運行，啟動它
export OLLAMA_HOST=127.0.0.1:11435
ollama serve > /tmp/ollama-11435.log 2>&1 &

# 驗證 Ollama #2
curl http://localhost:11435/api/tags

# 重置環境變數
unset OLLAMA_HOST
```

### 問題 2: Presenton 容器無法啟動

**錯誤訊息**: `Container presenton-api failed`

**解決方案**:
```bash
# 查看 Presenton 日誌
docker-compose logs presenton

# 常見原因：
# 1. Port 8000 被占用
lsof -i :8000

# 2. Docker 資源不足
docker system df
docker system prune

# 3. Image 問題
docker-compose pull presenton
docker-compose up -d presenton --force-recreate
```

### 問題 3: Backend 啟動但無法連線

**錯誤訊息**: `500 Internal Server Error`

**解決方案**:
```bash
# 查看 Backend 日誌
tail -f backend/logs/backend.log

# 檢查常見問題：
# 1. .env 檔案
cat backend/.env

# 2. Python 套件
cd backend && source venv/bin/activate
pip list | grep fastapi

# 3. 手動啟動查看錯誤
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

### 問題 4: Frontend 404 錯誤

**錯誤訊息**: `404 Not Found: index.html`

**解決方案**:
```bash
# 確認 index.html 存在
ls -la frontend/index.html

# 如果不存在，複製它
cp src/frontend/index.html frontend/

# 重新啟動 Frontend
pkill -f "python3.*http.server.*8080"
cd frontend && python3 -m http.server 8080
```

### 問題 5: Port 衝突

**錯誤訊息**: `Address already in use`

**解決方案**:
```bash
# 找出佔用 port 的程序
lsof -i :5000  # Backend
lsof -i :8000  # Presenton
lsof -i :8080  # Frontend
lsof -i :11434 # Ollama

# Kill 程序
kill -9 <PID>

# 或修改 .env 使用不同 port
# BACKEND_PORT=5001
```

---

## 日誌管理

### 查看即時日誌

```bash
# Backend (最詳細，從源碼運行)
tail -f backend/logs/backend.log

# Presenton (Docker)
docker-compose logs -f presenton

# Ollama
tail -f /tmp/ollama.log

# Frontend
tail -f /tmp/frontend.log
```

### 查看歷史日誌

```bash
# Backend 日誌（最近 100 行）
tail -100 backend/logs/backend.log

# Presenton 日誌
docker-compose logs --tail=100 presenton

# 搜尋特定錯誤
grep "Error\|Exception\|Failed" backend/logs/backend.log
```

### 日誌檔案位置

```
TeacherAssist/
├── backend/logs/
│   ├── backend.log        # Backend 主日誌
│   └── backend.pid        # Backend PID
├── /tmp/
│   ├── ollama.log         # Ollama 日誌
│   └── frontend.log       # Frontend 日誌
└── (Docker logs via docker-compose)
```

### 清理日誌

```bash
# 清理所有日誌（謹慎使用）
./scripts/clean_logs.sh

# 或手動清理：
> backend/logs/backend.log
> /tmp/ollama.log
> /tmp/frontend.log
```

---

## 健康檢查

### 快速健康檢查

```bash
# 檢查所有服務
./scripts/health_check.sh

# 或手動檢查：
curl http://localhost:5000/api/health | python3 -m json.tool
```

### 完整系統驗證

```bash
# 1. Ollama
curl http://localhost:11434/api/tags

# 2. Presenton
curl http://localhost:8000/

# 3. Backend
curl http://localhost:5000/api/health

# 4. Frontend
curl -I http://localhost:8080/

# 5. 端到端測試
curl -X POST http://localhost:5000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"content":"測試內容測試內容測試內容測試內容測試內容測試內容測試內容測試內容","template":"educational","language":"zh-TW"}'
```

---

## 效能監控

### 即時監控

```bash
# CPU 和記憶體使用
watch -n 1 'ps aux | grep -E "ollama|uvicorn|python3.*http.server" | grep -v grep'

# Port 監聽狀態
watch -n 1 'netstat -tlnp | grep -E "5000|8000|8080|11434"'
```

### 資源使用統計

```bash
# Backend 資源使用
ps aux | grep "uvicorn" | awk '{print "CPU: "$3"% | MEM: "$4"%"}'

# Presenton 容器資源使用
docker stats presenton-api --no-stream

# Ollama 資源使用（可能很高，正常）
ps aux | grep "ollama" | awk '{print "CPU: "$3"% | MEM: "$4"%"}'
```

---

## 開發模式 vs 生產模式

### 當前配置（開發模式）

- ✅ Backend 從源碼運行（即時日誌）
- ✅ Auto-reload 啟用
- ✅ DEBUG=True
- ✅ 詳細錯誤訊息
- ✅ 本地端口直接訪問

### 切換到生產模式

```bash
# 1. 更新 .env
DEBUG=False
CORS_ORIGINS=https://your-domain.com

# 2. 使用 Docker 運行所有服務
docker-compose up -d

# 3. 使用 Nginx 反向代理
# (參見 docs/deployment/nginx.conf)
```

---

## 快速參考指令

```bash
# === 啟動 ===
./scripts/start_system.sh              # 自動啟動所有服務

# === 停止 ===
./scripts/stop_system.sh               # 自動停止所有服務

# === 重啟 ===
./scripts/stop_system.sh && ./scripts/start_system.sh

# === 狀態檢查 ===
curl http://localhost:5000/api/health  # Backend 健康檢查
docker-compose ps                      # Docker 服務狀態
ps aux | grep -E "ollama|uvicorn"     # 主機服務狀態

# === 日誌 ===
tail -f backend/logs/backend.log       # Backend 即時日誌
docker-compose logs -f presenton       # Presenton 即時日誌

# === 疑難排解 ===
./scripts/health_check.sh              # 完整健康檢查
./scripts/clean_logs.sh                # 清理日誌
docker-compose restart presenton       # 重啟 Presenton
```

---

## 附錄

### A. 環境變數完整列表

```bash
# Presenton
PRESENTON_API_KEY=sk-presenton-...
PRESENTON_API_URL=http://localhost:8000

# Ollama
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b

# Pexels
PEXELS_API_KEY=...

# Backend
BACKEND_PORT=5000
CORS_ORIGINS=*
DEBUG=True
OUTPUT_DIR=./output
```

### B. 預設 Port 列表

| 服務 | Port | 用途 |
|------|------|------|
| Ollama | 11434 | LLM API |
| Presenton | 8000 | PPT 生成 |
| Backend | 5000 | API 中介層 |
| Frontend | 8080 | Web UI |

### C. 目錄結構

```
TeacherAssist/
├── backend/              # Backend 源碼
│   ├── venv/            # Python 虛擬環境
│   ├── logs/            # 日誌檔案
│   └── app/             # 應用程式碼
├── frontend/            # Frontend 檔案
│   └── index.html
├── scripts/             # 自動化腳本
│   ├── start_system.sh
│   ├── stop_system.sh
│   └── health_check.sh
├── documentation/       # 文件
├── output/             # 生成的簡報
└── .env                # 環境變數
```

---

**最後更新**: 2025-10-13
**版本**: 1.0.0
**作者**: Claude Code
**狀態**: Production Ready ✅
