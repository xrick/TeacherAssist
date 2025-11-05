# 故障排除指南

## 常見問題與解決方案

### 問題 1: Presenton 啟動超時

**症狀**:
```
❌ Presenton API 內部服務異常
```

**原因**:
Presenton 首次啟動需要下載並初始化 ONNX 模型（約 80MB），這個過程可能需要 1-2 分鐘。

**解決方案**:

1. **正常情況**：耐心等待，新版啟動腳本已延長等待時間至 2 分鐘

2. **手動檢查服務狀態**：
   ```bash
   # 使用診斷腳本
   ./scripts/check_presenton_status.sh

   # 或手動檢查
   docker exec presenton-api curl -s http://localhost:8000/docs
   ```

3. **查看詳細日誌**：
   ```bash
   # 即時日誌
   docker logs -f presenton-api

   # 最近 50 行
   docker logs presenton-api --tail 50
   ```

4. **重新啟動服務**：
   ```bash
   docker restart presenton-api

   # 等待 1-2 分鐘後檢查
   ./scripts/check_presenton_status.sh
   ```

**預期啟動流程**:
```
1. Nginx 啟動 (5秒) ✓
2. 容器內 Ollama 啟動 (10秒) ✓
3. Next.js 前端啟動 (10秒) ✓
4. ONNX 模型下載 (30-60秒，僅首次) ⏳
5. ChromaDB 初始化 (10秒) ✓
6. API 完全就緒 (總計 1-2 分鐘) ✅
```

---

### 問題 2: 平台架構不符

**症狀**:
```
WARNING: The requested image's platform (linux/amd64) does not match the detected host platform
```

**解決方案**:
已在最新版本中修復，請參考 [PLATFORM_SUPPORT.md](PLATFORM_SUPPORT.md)

---

### 問題 3: Port 衝突

**症狀**:
```
Error: bind: address already in use
```

**檢查佔用**:
```bash
# 檢查 Port 使用情況
lsof -i :5050  # Backend
lsof -i :8000  # Presenton
lsof -i :8080  # Frontend
lsof -i :11434 # Ollama
```

**解決方案**:
```bash
# 停止衝突的服務
kill <PID>

# 或修改 docker-compose.yml 中的 port 映射
# 例如: "5050:5000" 改為 "5051:5000"
```

---

### 問題 4: Ollama 模型未安裝

**症狀**:
```
Model 'phi4-mini-reasoning:3.8b' not found
```

**解決方案**:
```bash
# 下載必要模型
ollama pull phi4-mini:3.8b
ollama pull phi4-mini-reasoning:3.8b

# 驗證
ollama list
```

---

### 問題 5: 投影片生成失敗 (IndexError)

**症狀**:
```
IndexError: list index out of range
at presentation.py:680
```

**原因**:
請求的投影片數量超過模板支援的佈局數量。

**解決方案**:
已在最新版本修復：
- Backend 會自動查詢模板限制
- 自動調整投影片數量
- 前端新增投影片數量選擇器（3-12 張）

詳見投影片生成修復說明。

---

### 問題 6: Docker Compose version 警告

**症狀**:
```
WARN[0000] version is obsolete
```

**解決方案**:
已在 docker-compose.yml 中移除 `version: '3.8'` 欄位，與 Docker Compose v2 相容。

---

## 診斷工具

### 1. Presenton 狀態診斷

```bash
./scripts/check_presenton_status.sh
```

輸出範例：
```
🔍 Presenton 服務診斷
====================

ℹ️  1. 檢查容器狀態...
✅ 容器運行中

ℹ️  2. 檢查內部進程...
✅ Nginx, Ollama, Next.js 運行中

ℹ️  3. 檢查容器內 Ollama 服務...
✅ Ollama 服務運行中

ℹ️  4. 檢查 Next.js 前端 (port 3000)...
✅ Next.js 前端就緒 (HTTP 200)

ℹ️  5. 檢查 API 端點 (port 8000)...
✅ API 端點就緒 (HTTP 200)

📊 綜合狀態:
✅ 所有服務正常運行
```

### 2. 平台偵測測試

```bash
./scripts/test_platform_detection.sh
```

### 3. 系統健康檢查

```bash
# Backend 健康檢查
curl http://localhost:5050/api/health | python3 -m json.tool

# Presenton 健康檢查
docker exec presenton-api curl -s http://localhost:8000/health | python3 -m json.tool
```

---

## 完整重啟流程

如果遇到難以解決的問題，建議完整重啟：

```bash
# 1. 停止所有服務
./scripts/stop_system.sh

# 或手動停止
docker compose down
pkill -f "python3 -m http.server"

# 2. 清理 (選用，會刪除容器和資料)
docker compose down -v

# 3. 重新啟動
./scripts/start_system.sh
```

---

## 日誌位置

### Docker 容器日誌
```bash
# Backend
docker logs ppt-backend

# Presenton
docker logs presenton-api

# 即時追蹤
docker logs -f ppt-backend
docker logs -f presenton-api
```

### 本地日誌
```bash
# Ollama
tail -f /tmp/ollama.log

# Frontend
tail -f /tmp/frontend.log
```

---

## 效能最佳化

### 首次啟動優化

首次啟動會下載模型，建議：

1. **預先下載模型**：
   ```bash
   # 在啟動前手動下載
   ollama pull phi4-mini:3.8b
   ollama pull phi4-mini-reasoning:3.8b
   ```

2. **使用有線網路**：模型下載較大，建議使用有線網路

3. **增加等待時間**：如果網路很慢，可修改 `start_system.sh` 中的 `MAX_WAIT` 值

### 記憶體優化

```bash
# 檢查 Docker 記憶體使用
docker stats

# 如果記憶體不足，可以：
# 1. 增加 Docker Desktop 的記憶體限制
# 2. 關閉其他不必要的應用程式
# 3. 減少 Ollama 的並行模型數量
```

---

## 取得協助

如果問題仍未解決：

1. 收集診斷資訊：
   ```bash
   ./scripts/check_presenton_status.sh > diagnosis.txt
   docker logs ppt-backend > backend.log
   docker logs presenton-api > presenton.log
   docker compose ps >> diagnosis.txt
   ```

2. 查看文件：
   - [README.md](../README.md) - 完整設定指南
   - [PLATFORM_SUPPORT.md](PLATFORM_SUPPORT.md) - 多平台支援
   - [project_summary_zh.md](project_summary_zh.md) - 專案概述

3. 提交 Issue 時請包含：
   - 作業系統和架構 (`uname -a`)
   - Docker 版本 (`docker --version`)
   - 錯誤訊息和日誌
   - 診斷資訊 (`diagnosis.txt`)
