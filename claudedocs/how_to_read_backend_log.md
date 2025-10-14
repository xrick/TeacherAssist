# Backend 日誌查看指南

**目的**: 提供快速查看和診斷 Backend 服務日誌的方法
**適用**: TeacherAssist 專案的 Backend 服務除錯

---

## 📋 快速參考

### 最常用命令

```bash
# 即時追蹤日誌 (推薦用於開發除錯)
docker-compose logs -f backend

# 查看最近 50 行日誌
docker-compose logs --tail=50 backend

# 查看最近 100 行並持續追蹤
docker-compose logs -f --tail=100 backend
```

---

## 🔍 基本日誌查看

### 1. 查看即時日誌

**持續顯示新日誌** (按 Ctrl+C 退出):
```bash
docker-compose logs -f backend
```

**範例輸出**:
```
ppt-backend  | INFO:     Uvicorn running on http://0.0.0.0:5000
ppt-backend  | INFO:     Started server process [8]
ppt-backend  | INFO:     Application startup complete.
ppt-backend  | INFO:     172.19.0.1:41402 - "POST /api/generate HTTP/1.1" 200 OK
```

### 2. 查看歷史日誌

```bash
# 查看所有日誌 (可能很長)
docker-compose logs backend

# 查看最近 N 行
docker-compose logs --tail=50 backend
docker-compose logs --tail=100 backend
```

### 3. 查看帶時間戳的日誌

```bash
docker-compose logs -f -t backend
```

**輸出格式**:
```
2025-10-14T15:19:28.123456789+08:00 ppt-backend  | INFO: Request received
```

---

## 🎯 過濾和搜尋日誌

### 搜尋特定關鍵字

```bash
# 搜尋錯誤訊息
docker-compose logs backend | grep -i error

# 搜尋警告訊息
docker-compose logs backend | grep -i warning

# 搜尋 Ollama 相關日誌
docker-compose logs backend | grep -i ollama

# 搜尋 Zephyr 相關日誌
docker-compose logs backend | grep -i zephyr

# 搜尋 API 請求
docker-compose logs backend | grep "POST\|GET"
```

### 即時過濾日誌

```bash
# 即時追蹤並過濾錯誤
docker-compose logs -f backend | grep -i error

# 即時追蹤並過濾 Ollama 相關
docker-compose logs -f backend | grep -i ollama

# 多關鍵字過濾
docker-compose logs -f backend | grep -E "error|warning|failed"
```

### 排除某些內容

```bash
# 排除健康檢查日誌
docker-compose logs -f backend | grep -v "health"

# 排除 INFO 級別，只看錯誤和警告
docker-compose logs -f backend | grep -v "INFO"
```

---

## 🚨 診斷常見問題

### 檢查服務啟動狀態

```bash
# 查看啟動日誌
docker-compose logs backend | head -30
```

**健康的啟動日誌**:
```
ppt-backend  | INFO:     Will watch for changes in these directories: ['/app']
ppt-backend  | INFO:     Uvicorn running on http://0.0.0.0:5000 (Press CTRL+C to quit)
ppt-backend  | INFO:     Started reloader process [1] using WatchFiles
ppt-backend  | INFO:     Started server process [8]
ppt-backend  | INFO:     Waiting for application startup.
ppt-backend  | INFO:     Application startup complete.
```

### 檢查 Ollama 連接問題

```bash
# 查看 Ollama 相關日誌
docker-compose logs backend | grep -i ollama
```

**正常連接**:
```
ppt-backend  | INFO: Ollama service connected successfully
ppt-backend  | INFO: Using model: gpt-oss:20b
```

**連接失敗**:
```
ppt-backend  | Error checking Zephyr model: All connection attempts failed
ppt-backend  | ERROR: Failed to connect to Ollama at http://host.docker.internal:11434
```

**修復建議**: 參考 [ollama_docker_fix.md](ollama_docker_fix.md)

### 檢查 API 請求錯誤

```bash
# 查看所有 4xx 和 5xx 錯誤
docker-compose logs backend | grep -E " [45][0-9]{2} "

# 查看 404 錯誤
docker-compose logs backend | grep "404"

# 查看 500 錯誤
docker-compose logs backend | grep "500"
```

### 檢查 Python 異常

```bash
# 查看 Python traceback
docker-compose logs backend | grep -A 10 "Traceback"

# 查看異常類型
docker-compose logs backend | grep -E "Error:|Exception:"
```

---

## 📊 進階日誌分析

### 按時間範圍查看

```bash
# Docker 不直接支援時間過濾，使用 since
docker-compose logs --since 10m backend  # 最近 10 分鐘
docker-compose logs --since 1h backend   # 最近 1 小時
docker-compose logs --since 2h30m backend  # 最近 2.5 小時
```

### 統計日誌資訊

```bash
# 統計錯誤數量
docker-compose logs backend | grep -i error | wc -l

# 統計各 HTTP 狀態碼
docker-compose logs backend | grep -oE "HTTP/1\.[01]\" [0-9]{3}" | sort | uniq -c

# 統計各 API 端點訪問次數
docker-compose logs backend | grep -oE "(GET|POST|PUT|DELETE) /api/[^ ]+" | sort | uniq -c
```

### 提取特定資訊

```bash
# 提取所有 API 請求時間
docker-compose logs backend | grep -oE "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}"

# 提取所有 IP 地址
docker-compose logs backend | grep -oE "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"

# 提取所有錯誤訊息
docker-compose logs backend | grep -i error | cut -d'|' -f2-
```

---

## 💾 儲存日誌到文件

### 基本儲存

```bash
# 儲存完整日誌
docker-compose logs backend > backend.log

# 儲存最近日誌
docker-compose logs --tail=500 backend > backend_recent.log

# 帶時間戳儲存
docker-compose logs -t backend > backend_$(date +%Y%m%d_%H%M%S).log
```

### 自動分類儲存

```bash
# 建立診斷日誌目錄
mkdir -p logs/$(date +%Y%m%d)

# 儲存各類日誌
docker-compose logs --tail=1000 backend > logs/$(date +%Y%m%d)/full.log
docker-compose logs backend | grep -i error > logs/$(date +%Y%m%d)/errors.log
docker-compose logs backend | grep -i warning > logs/$(date +%Y%m%d)/warnings.log
docker-compose logs backend | grep -i ollama > logs/$(date +%Y%m%d)/ollama.log
```

### 持續記錄日誌

```bash
# 背景記錄日誌 (持續運行)
docker-compose logs -f backend >> backend_continuous.log 2>&1 &

# 查看背景任務
jobs

# 停止記錄
kill %1  # 或使用對應的 job 號碼
```

---

## 🔄 即時監控技巧

### 多窗口監控

**Terminal 1** - 監控錯誤:
```bash
docker-compose logs -f backend | grep -i error
```

**Terminal 2** - 監控 API 請求:
```bash
docker-compose logs -f backend | grep -E "POST|GET"
```

**Terminal 3** - 監控所有日誌:
```bash
docker-compose logs -f backend
```

### 使用 watch 定期檢查

```bash
# 每 2 秒檢查最新 10 行日誌
watch -n 2 'docker-compose logs --tail=10 backend'

# 每 5 秒檢查錯誤數量
watch -n 5 'docker-compose logs backend | grep -i error | wc -l'
```

### 顏色高亮顯示

```bash
# 安裝 ccze (如果需要)
sudo apt-get install ccze

# 帶顏色顯示日誌
docker-compose logs -f backend | ccze -A

# 或使用 grep 顏色
docker-compose logs -f backend | grep --color=always -E "ERROR|WARNING|$"
```

---

## 🐛 除錯流程範例

### 場景 1: 簡報生成失敗

```bash
# Step 1: 查看最近錯誤
docker-compose logs --tail=100 backend | grep -i error

# Step 2: 查看完整請求流程
docker-compose logs --tail=200 backend | grep -A 5 "/api/generate"

# Step 3: 檢查 Ollama 連接
docker-compose logs backend | grep -i ollama | tail -20

# Step 4: 查看詳細 traceback
docker-compose logs backend | grep -A 15 "Traceback"
```

### 場景 2: 容器無法啟動

```bash
# Step 1: 查看啟動日誌
docker-compose logs backend

# Step 2: 檢查 Python 錯誤
docker-compose logs backend | grep -E "Error|Exception|Traceback"

# Step 3: 檢查依賴問題
docker-compose logs backend | grep -i "import\|module"

# Step 4: 檢查環境變數
docker-compose logs backend | grep -i "environment\|config"
```

### 場景 3: API 響應緩慢

```bash
# Step 1: 查看請求處理時間
docker-compose logs -f backend | grep -E "[0-9]+ms|[0-9]+s"

# Step 2: 監控 Ollama 請求
docker-compose logs -f backend | grep -i "ollama"

# Step 3: 查看並發請求
docker-compose logs --tail=100 backend | grep "POST /api/generate" | wc -l
```

---

## 🛠️ 其他有用命令

### 查看容器狀態

```bash
# 查看容器運行狀態
docker-compose ps

# 查看容器詳細資訊
docker inspect ppt-backend

# 查看容器資源使用
docker stats ppt-backend --no-stream
```

### 進入容器內部

```bash
# 進入容器 shell
docker exec -it ppt-backend /bin/bash

# 執行單一命令
docker exec ppt-backend ls -la /app

# 查看容器內日誌文件 (如果有)
docker exec ppt-backend cat /app/logs/app.log
```

### 重啟和清理

```bash
# 重啟 Backend 容器
docker-compose restart backend

# 查看重啟後日誌
docker-compose logs -f backend

# 完全重建容器
docker-compose up -d --build backend

# 清理舊日誌 (重建容器)
docker-compose down backend
docker-compose up -d backend
```

---

## 📚 日誌級別說明

### 常見日誌級別

| 級別 | 描述 | 範例 |
|------|------|------|
| **DEBUG** | 詳細診斷資訊 | `DEBUG: Variable x = 123` |
| **INFO** | 一般資訊訊息 | `INFO: Request received` |
| **WARNING** | 警告但不影響功能 | `WARNING: Slow query detected` |
| **ERROR** | 錯誤但程式繼續運行 | `ERROR: Failed to connect` |
| **CRITICAL** | 嚴重錯誤程式可能停止 | `CRITICAL: Database unavailable` |

### 過濾特定級別

```bash
# 只看 ERROR 和 CRITICAL
docker-compose logs backend | grep -E "ERROR|CRITICAL"

# 排除 DEBUG 和 INFO
docker-compose logs backend | grep -v -E "DEBUG|INFO"

# 只看非 INFO 日誌
docker-compose logs backend | grep -v "INFO"
```

---

## 🔗 相關文檔

- [Docker Compose 日誌文檔](https://docs.docker.com/compose/reference/logs/)
- [Backend 配置文件](../backend/app/config.py)
- [系統修復報告](fix_report_20251014.md)
- [Ollama 連接修復指南](ollama_docker_fix.md)

---

## 💡 最佳實踐

1. **開發時**: 使用 `docker-compose logs -f backend` 即時監控
2. **除錯時**: 結合 `grep` 過濾相關日誌
3. **診斷時**: 儲存完整日誌到文件後分析
4. **生產環境**: 定期清理舊日誌，避免佔用空間
5. **分享問題**: 儲存關鍵錯誤日誌，便於他人協助診斷

---

## 🚀 快速診斷命令組合

```bash
# 一鍵診斷腳本
cat > diagnose_backend.sh << 'EOF'
#!/bin/bash
echo "=== Backend 診斷報告 ==="
echo ""
echo "1. 容器狀態:"
docker-compose ps backend
echo ""
echo "2. 最近 20 行日誌:"
docker-compose logs --tail=20 backend
echo ""
echo "3. 錯誤統計:"
echo "總錯誤數: $(docker-compose logs backend | grep -i error | wc -l)"
echo ""
echo "4. Ollama 連接狀態:"
docker-compose logs backend | grep -i ollama | tail -5
echo ""
echo "5. 最近 API 請求:"
docker-compose logs --tail=100 backend | grep -E "POST|GET" | tail -5
EOF

chmod +x diagnose_backend.sh
./diagnose_backend.sh
```

---

**版本**: 1.0
**最後更新**: 2025-10-14
**維護者**: SuperClaude
**狀態**: ✅ 持續更新
