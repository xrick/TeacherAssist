# 多平台支援說明

TeacherAssist 支援 **AMD64 (x86_64)** 和 **ARM64 (Apple Silicon / aarch64)** 兩種架構。

## 自動平台偵測

系統會在啟動時**自動偵測**您的硬體架構，並選擇適合的 Docker 映像檔。

### 支援的平台

| 平台 | 架構 | 範例設備 |
|------|------|----------|
| **AMD64** | x86_64 | Intel/AMD 處理器的 PC/Mac |
| **ARM64** | aarch64 | Apple Silicon (M1/M2/M3), Raspberry Pi 4+ |

## 使用方式

### 1. 一般使用（自動偵測）

直接執行啟動腳本，系統會自動處理：

```bash
./scripts/start_system.sh
```

腳本會：
1. 偵測您的系統架構
2. 檢查本地是否有對應架構的映像檔
3. 自動配置 `DOCKER_PLATFORM`、`BACKEND_IMAGE`、`PRESENTON_IMAGE` 環境變數
4. 啟動服務

### 2. 測試平台偵測（不啟動服務）

如果您想確認偵測結果，可以執行測試腳本：

```bash
./scripts/test_platform_detection.sh
```

輸出範例：
```
🧪 平台偵測測試
===============

ℹ️  系統架構: arm64
ℹ️  Docker 架構: arm64

✅ 平台: ARM64
✅ Backend: teacherassist-backend:latest (ARM64, 217MB)
ℹ️    映像檔 ID: 691b04772244
✅ Presenton: presenton:arm64-local (本地 ARM64)

📦 最終配置:
  • DOCKER_PLATFORM: linux/arm64
  • BACKEND_IMAGE: teacherassist-backend:latest
  • PRESENTON_IMAGE: presenton:arm64-local
```

### 3. 手動覆寫（進階）

如果需要手動指定平台配置，可以建立 `.env.platform` 檔案：

```bash
# 複製範例檔案
cp .env.platform.example .env.platform

# 編輯檔案設定您的偏好
nano .env.platform
```

`.env.platform` 範例內容：

```bash
# 強制使用 ARM64
DOCKER_PLATFORM=linux/arm64
BACKEND_IMAGE=teacherassist-backend:latest
PRESENTON_IMAGE=presenton:arm64-local
```

> **注意**: `.env.platform` 的設定會**覆寫**自動偵測結果。

## 映像檔配置邏輯

### AMD64 平台

```yaml
DOCKER_PLATFORM: linux/amd64
BACKEND_IMAGE: teacherassist-backend:latest
PRESENTON_IMAGE: ghcr.io/presenton/presenton:latest  # 官方映像檔
```

### ARM64 平台

```yaml
DOCKER_PLATFORM: linux/arm64
BACKEND_IMAGE: teacherassist-backend:latest  # 本地建置
PRESENTON_IMAGE:
  - 優先: presenton:arm64-local           # 本地 ARM64 版本
  - 備選: ghcr.io/presenton/presenton:latest  # 官方（需模擬）
```

## 建置 ARM64 映像檔

### Backend (已完成)

您的 Backend 映像檔已經是 ARM64 版本：

```bash
# 檢查映像檔資訊
docker image inspect teacherassist-backend:latest --format '{{.Architecture}}'
# 輸出: arm64
```

### Presenton ARM64 版本（選用）

如果您有 Presenton 的原始碼，可以建置 ARM64 版本：

```bash
# 使用 Docker Buildx 建置多平台映像檔
docker buildx build \
  --platform linux/arm64 \
  -t presenton:arm64-local \
  /path/to/presenton/source

# 或從 Dockerfile 建置
docker build \
  --platform linux/arm64 \
  -t presenton:arm64-local \
  /path/to/presenton
```

如果沒有原始碼，系統會使用官方映像檔，Docker Desktop 會自動處理平台模擬。

## 疑難排解

### 問題 1: 映像檔架構不符

**症狀**: 啟動時出現 "platform mismatch" 警告

**解決方法**:
```bash
# 重新建置 Backend 映像檔
cd backend
docker build --platform linux/arm64 -t teacherassist-backend:latest .

# 或清除舊映像檔後重新啟動
docker rmi teacherassist-backend:latest
./scripts/start_system.sh
```

### 問題 2: Presenton 在 ARM64 上效能慢

**原因**: 使用官方 AMD64 映像檔需要平台模擬

**解決方法**:
1. 建置本地 ARM64 版本（如上所述）
2. 或接受模擬的效能損耗（通常仍可接受）

### 問題 3: 想強制使用特定平台

**解決方法**:
```bash
# 建立 .env.platform 檔案
cat > .env.platform << EOF
DOCKER_PLATFORM=linux/arm64
BACKEND_IMAGE=teacherassist-backend:latest
PRESENTON_IMAGE=presenton:arm64-local
EOF

# 重新啟動
./scripts/start_system.sh
```

## 效能比較

| 場景 | AMD64 原生 | ARM64 原生 | ARM64 模擬 AMD64 |
|------|-----------|-----------|-----------------|
| Backend | 100% | 100% | N/A (原生) |
| Presenton (ARM64) | N/A | 100% | N/A |
| Presenton (官方) | 100% | 60-80% | 60-80% |

> **建議**: ARM64 用戶建議建置本地 Presenton 映像檔以獲得最佳效能。

## 檢查清單

在提交 Issue 之前，請確認：

- [ ] 已執行 `./scripts/test_platform_detection.sh` 確認偵測正確
- [ ] 已檢查 `docker images` 確認映像檔存在且架構正確
- [ ] 已檢查 `docker-compose config` 查看最終配置
- [ ] 已查看 `docker-compose logs` 檢查錯誤訊息

## 技術細節

### 實作方式

1. **Shell 腳本偵測**: `start_system.sh` 使用 `uname -m` 偵測系統架構
2. **映像檔驗證**: 使用 `docker image inspect` 確認本地映像檔架構
3. **環境變數傳遞**: 透過 `export` 傳遞給 `docker-compose`
4. **動態配置**: `docker-compose.yml` 使用 `${VAR:-default}` 語法支援環境變數

### 相關檔案

- `scripts/start_system.sh` - 主要啟動腳本（含平台偵測邏輯）
- `scripts/test_platform_detection.sh` - 平台偵測測試腳本
- `docker-compose.yml` - Docker Compose 配置（支援環境變數）
- `.env.platform.example` - 手動配置範例
- `.env.platform` - 使用者自訂配置（Git 忽略）

## 版本歷史

- **v1.0** (2025-01-05): 初次實作多平台支援
  - 自動架構偵測
  - ARM64 和 AMD64 支援
  - 環境變數覆寫機制
