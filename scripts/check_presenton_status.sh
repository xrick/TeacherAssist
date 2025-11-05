#!/bin/bash
# scripts/check_presenton_status.sh
# 檢查 Presenton 服務詳細狀態

set -e

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error() { echo -e "${RED}❌ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "🔍 Presenton 服務診斷"
echo "===================="
echo ""

# 檢查容器狀態
print_info "1. 檢查容器狀態..."
if docker ps --filter "name=presenton-api" --filter "status=running" | grep -q "presenton-api"; then
    print_success "容器運行中"
    docker ps --filter "name=presenton-api" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    print_error "容器未運行"
    exit 1
fi

echo ""

# 檢查內部進程
print_info "2. 檢查內部進程..."
docker exec presenton-api ps aux | grep -E "nginx|ollama|node|next" || print_warning "未找到關鍵進程"

echo ""

# 檢查 Ollama 狀態
print_info "3. 檢查容器內 Ollama 服務..."
if docker exec presenton-api curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    print_success "Ollama 服務運行中"
    docker exec presenton-api curl -s http://localhost:11434/api/tags | python3 -m json.tool 2>/dev/null | head -20 || true
else
    print_warning "Ollama 服務未就緒"
fi

echo ""

# 檢查 Next.js 前端
print_info "4. 檢查 Next.js 前端 (port 3000)..."
NEXT_CODE=$(docker exec presenton-api curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null || echo "000")
if [ "$NEXT_CODE" = "200" ]; then
    print_success "Next.js 前端就緒 (HTTP $NEXT_CODE)"
else
    print_warning "Next.js 前端未就緒 (HTTP $NEXT_CODE)"
fi

echo ""

# 檢查 API 端點 (port 8000)
print_info "5. 檢查 API 端點 (port 8000)..."
API_CODE=$(docker exec presenton-api curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs 2>/dev/null || echo "000")
if [ "$API_CODE" = "200" ]; then
    print_success "API 端點就緒 (HTTP $API_CODE)"
else
    print_warning "API 端點未就緒 (HTTP $API_CODE)"
fi

echo ""

# 檢查最近日誌
print_info "6. 最近的日誌 (最後 15 行)..."
echo "---"
docker logs presenton-api 2>&1 | tail -15
echo "---"

echo ""

# 綜合狀態
print_info "📊 綜合狀態:"
if [ "$API_CODE" = "200" ] && [ "$NEXT_CODE" = "200" ]; then
    print_success "所有服務正常運行"
    echo ""
    echo "可用的端點:"
    echo "  • Next.js 前端: http://localhost:3000"
    echo "  • API 文件: http://localhost:8000/docs"
    echo "  • API 健康檢查: http://localhost:8000/health"
else
    print_warning "部分服務未就緒，可能仍在初始化中"
    echo ""
    echo "建議操作:"
    echo "  1. 等待 1-2 分鐘讓服務完全啟動"
    echo "  2. 檢查是否有錯誤: docker logs presenton-api"
    echo "  3. 重新啟動: docker restart presenton-api"
fi
