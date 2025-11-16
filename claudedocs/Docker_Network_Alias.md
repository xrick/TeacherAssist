## Docker Network Alias 解釋

### 問題背景

在 Docker 環境中，容器之間需要互相通訊。Backend 容器需要連接到 Presenton 容器的 API (port 8000)。

### 什麼是 Network Alias？

**Network Alias (網路別名)** 是 Docker 內部 DNS 的一個功能，讓容器可以用「名稱」而非 IP 位址來找到其他容器。

### 實際例子

 **Backend 程式碼中** ：

```python
# backend/app/config.py
PRESENTON_API_URL = "http://presenton:8000"
                            ^^^^^^^^
                            這是 hostname，不是 IP
```

Backend 嘗試連接 `http://presenton:8000` 時，Docker 需要將 `"presenton"` 這個名稱解析成實際的容器 IP 位址。

### 三種設定 Network Alias 的方式

#### 1. **Docker Compose 自動設定** (正常情況)

```yaml
# docker-compose.yml
services:
  presenton:
    container_name: presenton-api  # Docker 自動用這個名稱建立 alias
    networks:
      - app-network

  backend:
    depends_on:
      - presenton  # Backend 可以用 "presenton" 找到它
    networks:
      - app-network
```

Docker Compose 會自動：

* 建立 network alias: `presenton` → 容器 IP
* Backend 內部 DNS 可解析 `presenton` 為 Presenton 容器的 IP

#### 2. **Docker Run 手動設定** (我們的修正)

當使用 `docker run` 手動啟動時， **必須明確指定 network alias** ：

```bash
docker run -d --name presenton-api \
    --network teacherassist_app-network \
    --network-alias presenton \  # ← 這行很重要！
    ...
```

**為什麼需要 `--network-alias presenton`？**

* `--name presenton-api`：容器名稱（外部使用）
* `--network-alias presenton`：網路內部的 DNS 別名（容器間通訊使用）

如果沒有 `--network-alias`，Backend 嘗試連接 `http://presenton:8000` 時會失敗：

```
[Errno -3] Temporary failure in name resolution
```

#### 3. **驗證 Network Alias 是否生效**

```bash
# 從 backend 容器內測試
docker exec ppt-backend curl http://presenton:8000/docs

# 成功 → 返回 200 OK (alias 正常)
# 失敗 → "Could not resolve host: presenton" (alias 未設定)
```

### 總結

| 情境                                       | Network Alias 如何設定  | Backend 能否解析 `presenton` |
| ------------------------------------------ | ----------------------- | ------------------------------ |
| Docker Compose 正常啟動                    | 自動建立 (service name) | ✅ 可以                        |
| Docker Run**有** `--network-alias` | 手動指定                | ✅ 可以                        |
| Docker Run**無** `--network-alias` | 未設定                  | ❌ 無法解析                    |

 **關鍵點** ：

* `--network-alias presenton` 告訴 Docker：「在 `teacherassist_app-network` 這個網路裡，把這個容器註冊為 `presenton` 這個名稱」
* 其他容器（如 Backend）就可以用 `http://presenton:8000` 來連接，而不需要知道實際 IP 位址

/sc:explain ```
目前的start_system.sh仍然可以使用嗎？

```


是的，修正後的 `start_system.sh`  **可以正常使用** ，並且已經處理了平台衝突問題。

## 修正內容摘要

### 1. Port 檢查修正 ✅

```bash
# Line 190-192
check_port 5050 "Backend"      # 修正: 5151 → 5050
check_port 8001 "Presenton"    # 修正: 8000 → 8001 (映射 port)
check_port 8080 "Frontend"
```

### 2. 平台衝突自動處理 ✅

```bash
# Line 282-327: 智能啟動邏輯
1. 先建置 Backend (docker compose build backend)
2. 嘗試用 docker compose 啟動
3. 若偵測到平台衝突 → 自動切換手動啟動模式：
   - Backend: docker compose up -d backend
   - Presenton: docker run --platform linux/amd64 (明確指定平台)
```

### 3. 關鍵改進

 **自動化錯誤處理** ：

```bash
if docker compose up -d --no-build 2>&1 | grep -q "platform.*does not match"; then
    # 檢測到平台衝突 → 切換到 docker run 手動模式
    docker run -d --name presenton-api \
        --platform linux/amd64 \          # 明確指定 AMD64
        --network-alias presenton \       # 確保 DNS 解析
        ...
```

 **環境變數支援** ：

* 從 `.env` 讀取配置
* 提供 fallback 預設值
* 支援 `.env.platform` 覆寫

## 使用方式

```bash
./scripts/start_system.sh
```

 **預期行為** ：

1. ✅ 檢查正確的 ports (5050, 8001, 8080)
2. ✅ 自動建置 Backend
3. ✅ 嘗試正常啟動
4. ✅ 若平台衝突 → 自動切換手動模式
5. ✅ 設定 network alias 確保容器通訊
6. ✅ 驗證所有服務健康狀態

## 測試建議

執行後檢查容器狀態：

```bash
docker ps --filter "name=backend\|presenton"
# 預期: 兩個容器都在運行

docker exec ppt-backend curl -s http://presenton:8000/docs
# 預期: 200 OK (DNS 解析正常)

curl http://localhost:5050/api/health
# 預期: {"status":"healthy",...}
```

 **結論** ：修正後的腳本已經可以正常使用，並且會自動處理平台衝突問題。
