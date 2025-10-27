# PPT/PDF 下載失敗問題修復指南

## 問題描述

### 症狀
系統可以成功生成 6 頁 PPT，但在嘗試下載 PPT 或 PDF 時失敗，出現以下錯誤：

```json
{
  "detail": "下載失敗: Exported file not found at /app_data/exports/[檔案名稱].pdf. Ensure volume mount ./app_data/exports is configured for both presenton and backend containers."
}
```

### 發生時間
- **日期**: 2025-10-27
- **環境**: Linux PC (AMD64)，Docker Compose
- **PPT 生成**: ✅ 成功（能生成 6 頁）
- **下載功能**: ❌ 失敗（找不到匯出的檔案）

## 根本原因分析

### 1. Volume Mount 配置不完整

在 `docker-compose.yml` 中：

**Backend 服務** (✅ 正確配置):
```yaml
backend:
  volumes:
    - ./backend:/app
    - ./output:/app/output
    - ./app_data/exports:/app_data/exports  # 已配置
```

**Presenton 服務** (❌ 缺失配置):
```yaml
presenton:
  # volumes 區段完全缺失！
```

### 2. 為什麼需要共享 Volume?

```
生成流程:
Backend → 請求 Presenton → Presenton 生成 PPT/PDF → 儲存到 /app_data/exports
                                                              ↓
下載流程:                                                    檔案位置
Backend → 讀取 /app_data/exports/檔案 → 回傳給使用者
         ↑
         找不到！因為 Presenton 的 /app_data/exports
         與 Backend 的 /app_data/exports 不是同一個目錄
```

**問題**: Presenton 容器內的 `/app_data/exports` 與 Backend 容器的 `/app_data/exports` 是**隔離的**，兩者無法共享檔案。

## 解決方案

### Step 1: 修改 docker-compose.yml

在 `presenton` 服務中加入 `volumes` 區段：

```yaml
services:
  presenton:
    image: ghcr.io/presenton/presenton:latest
    container_name: presenton-api
    environment:
      - PRESENTON_API_KEY=sk-presenton-xxx...
      - LLM=ollama
      - OLLAMA_URL=http://host.docker.internal:11434
      - OLLAMA_MODEL=phi4-mini:3.8b
      - IMAGE_PROVIDER=pexels
      - PEXELS_API_KEY=xxx...
    extra_hosts:
      - "host.docker.internal:host-gateway"
    volumes:
      - ./app_data:/app_data    # ← 加入這行！
    networks:
      - app-network
    restart: unless-stopped
```

**重點**: 將本地的 `./app_data` 目錄掛載到容器內的 `/app_data`，這樣 Presenton 和 Backend 就能共享同一個目錄。

### Step 2: 確認目錄存在

```bash
# 確保 app_data/exports 目錄存在
mkdir -p app_data/exports

# 檢查目錄權限
ls -la app_data/
```

### Step 3: 重啟服務

```bash
# 停止並移除舊容器
docker compose down

# 重新建立並啟動服務
docker compose up -d

# 等待服務啟動
sleep 5
```

### Step 4: 驗證 Volume Mount

```bash
# 檢查 Presenton 容器的 volume 掛載
docker inspect presenton-api --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'

# 預期輸出:
# /home/mapleleaf/LCJRepos/projects/TeacherAssist/app_data -> /app_data
```

### Step 5: 測試下載功能

1. 開啟前端頁面: `http://localhost:8080`
2. 輸入測試內容並生成 PPT
3. 點擊「下載 PPT」或「下載 PDF」
4. 確認下載成功

## 驗證檢查清單

✅ **配置驗證**:
```bash
# 1. 檢查 docker-compose.yml 中 presenton 服務有 volumes 區段
grep -A 2 "presenton:" docker-compose.yml | grep "volumes"

# 2. 確認 app_data/exports 目錄存在
ls -la app_data/exports/

# 3. 檢查服務健康狀態
curl -s http://localhost:5050/api/health | python3 -m json.tool

# 4. 檢查 Presenton 容器 volume 掛載
docker inspect presenton-api --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}'
```

✅ **功能驗證**:
1. 能成功生成 PPT ✅
2. 能下載 PPTX 檔案 ✅
3. 能下載 PDF 檔案 ✅

## 技術細節

### Docker Volume Mount 原理

```
主機檔案系統:
└── app_data/
    └── exports/          ← 實際儲存檔案的地方

Presenton 容器:           Backend 容器:
└── /app_data/ ────┐      └── /app_data/
    └── exports/   │          └── exports/ ────┐
                   │                            │
                   └────────────┬───────────────┘
                                │
                          共享相同的主機目錄
                          ./app_data/exports/
```

### 為什麼註解行已經提示了正確做法?

在 `docker-compose.yml` 第 3-4 行有註解：

```yaml
#docker run -it --name presonton -p 5000:80 -v "./app_data:/app_data"
#ghcr.io/presenton/presenton:latest
```

這個註解是 Presenton 官方文檔提供的啟動指令範例，其中的 `-v "./app_data:/app_data"` 就是正確的 volume mount 配置。

**教訓**: 仔細閱讀註解和官方文檔，很多時候答案已經在那裡！

## 常見問題排除

### Q1: 修改後下載仍然失敗怎麼辦?

```bash
# 1. 確認容器已重啟
docker compose ps

# 2. 查看容器日誌
docker compose logs presenton | tail -30
docker compose logs backend | tail -30

# 3. 檢查目錄權限
ls -la app_data/exports/

# 4. 手動測試容器內部
docker exec presenton-api ls -la /app_data/exports/
docker exec ppt-backend ls -la /app_data/exports/
```

### Q2: exports 目錄是空的?

**可能原因**:
1. PPT 生成失敗（檢查 Presenton 日誌）
2. Presenton 使用了不同的匯出路徑
3. 檔案權限問題

**排查方法**:
```bash
# 查看 Presenton 容器內部的檔案結構
docker exec presenton-api find /app_data -type f -name "*.pptx" -o -name "*.pdf"

# 查看 Backend 日誌中的檔案路徑
docker compose logs backend | grep "export"
```

### Q3: 權限錯誤 (Permission denied)?

```bash
# 檢查目錄擁有者
ls -la app_data/

# 如果 exports 目錄擁有者是 root，修改權限
sudo chown -R $USER:$USER app_data/exports/
chmod -R 755 app_data/exports/
```

## 相關文檔

- `claudedocs/two_env_start_system_fix.md` - 跨環境啟動問題修復
- `claudedocs/ollama_model_fix.md` - 模型配置問題修復
- `claudedocs/set_ollama_model.md` - 模型切換指南

## 總結

**核心問題**: Presenton 服務缺少 volume mount 配置，導致生成的檔案無法被 Backend 讀取。

**解決方法**: 在 `docker-compose.yml` 的 `presenton` 服務中加入 `volumes: - ./app_data:/app_data`。

**驗證成功**:
```bash
✅ Volume 掛載正確
✅ 所有服務健康
✅ PPT 生成成功
✅ 下載功能正常
```

---

**修復日期**: 2025-10-27
**環境**: Linux (AMD64), Docker Compose
**狀態**: ✅ 已解決
