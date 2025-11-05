#!/bin/bash
# scripts/test_platform_detection.sh
# 測試平台偵測邏輯（不實際啟動容器）

set -e

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "🧪 平台偵測測試"
echo "==============="
echo ""

# 檢測系統架構
ARCH=$(uname -m)
print_info "系統架構: $ARCH"

# 檢測 Docker 架構
if command -v docker >/dev/null 2>&1; then
    DOCKER_ARCH=$(docker version -f '{{.Server.Arch}}' 2>/dev/null || echo "unknown")
    print_info "Docker 架構: $DOCKER_ARCH"
fi

echo ""
print_info "測試平台配置邏輯..."
echo ""

# 模擬 start_system.sh 的邏輯
case "$ARCH" in
    x86_64|amd64)
        export DOCKER_PLATFORM="linux/amd64"
        print_success "平台: AMD64"

        if docker images | grep -q "teacherassist-backend.*latest"; then
            export BACKEND_IMAGE="teacherassist-backend:latest"
            print_success "Backend: teacherassist-backend:latest (本地)"
        else
            export BACKEND_IMAGE="teacherassist-backend:latest"
            print_warning "Backend: 將從 Dockerfile 建置"
        fi

        export PRESENTON_IMAGE="ghcr.io/presenton/presenton:latest"
        print_success "Presenton: ghcr.io/presenton/presenton:latest"
        ;;

    arm64|aarch64)
        export DOCKER_PLATFORM="linux/arm64"
        print_success "平台: ARM64"

        if docker images | grep -q "teacherassist-backend.*latest"; then
            IMAGE_ID=$(docker images teacherassist-backend:latest -q | head -1)
            if [ -n "$IMAGE_ID" ]; then
                IMAGE_ARCH=$(docker image inspect "$IMAGE_ID" --format '{{.Architecture}}' 2>/dev/null)
                IMAGE_SIZE=$(docker images teacherassist-backend:latest --format "{{.Size}}")
                if [ "$IMAGE_ARCH" = "arm64" ] || [ "$IMAGE_ARCH" = "aarch64" ]; then
                    export BACKEND_IMAGE="teacherassist-backend:latest"
                    print_success "Backend: teacherassist-backend:latest (ARM64, $IMAGE_SIZE)"
                    print_info "  映像檔 ID: ${IMAGE_ID:0:12}"
                else
                    print_warning "Backend: 本地映像檔是 $IMAGE_ARCH，需要重新建置"
                fi
            fi
        else
            print_warning "Backend: 本地無映像檔，將建置 ARM64 版本"
        fi

        if docker images | grep -q "presenton.*arm64-local"; then
            export PRESENTON_IMAGE="presenton:arm64-local"
            print_success "Presenton: presenton:arm64-local (本地 ARM64)"
        else
            export PRESENTON_IMAGE="ghcr.io/presenton/presenton:latest"
            print_warning "Presenton: 使用官方映像檔（可能需要模擬）"
        fi
        ;;
esac

echo ""
print_info "📦 最終配置:"
echo "  • DOCKER_PLATFORM: $DOCKER_PLATFORM"
echo "  • BACKEND_IMAGE: $BACKEND_IMAGE"
echo "  • PRESENTON_IMAGE: $PRESENTON_IMAGE"

echo ""
print_info "測試 docker-compose 環境變數..."

# 測試環境變數傳遞
export DOCKER_PLATFORM BACKEND_IMAGE PRESENTON_IMAGE

# 顯示 docker-compose 會使用的配置
echo ""
print_success "Docker Compose 配置預覽:"
echo "---"
docker compose config 2>/dev/null | grep -A 2 "image:" | head -20 || print_warning "無法顯示配置預覽"
echo "---"

echo ""
print_success "✅ 平台偵測測試完成！"
print_info "如要實際啟動，請執行: ./scripts/start_system.sh"
