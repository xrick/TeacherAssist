# Ollama Docker 連接問題修復指南

**問題**: Backend Docker 容器無法連接到 Host 上的 Ollama 服務
**原因**: Ollama 只監聽 `127.0.0.1:11434`，Docker 容器無法訪問
**症狀**: Backend 日誌顯示 "Error checking Zephyr model: All connection attempts failed"

---

## 🔍 問題診斷

### 當前狀態
```bash
# Ollama 監聽狀態
$ ss -tlnp | grep 11434
LISTEN 0      4096       127.0.0.1:11434      0.0.0.0:*
                         ^^^^^^^^^ 只監聽 localhost

# Backend 嘗試訪問
Backend Container → http://host.docker.internal:11434 → ❌ Connection Failed
```

### 驗證問題
```bash
# 從 Host 訪問 (成功)
$ curl http://localhost:11434/api/tags
{"models":[...]}  # ✅ 成功

# 從容器訪問 (失敗)
$ docker exec ppt-backend curl http://host.docker.internal:11434/api/tags
curl: (7) Failed to connect to host.docker.internal port 11434  # ❌ 失敗
```

---

## ✅ 解決方案

### 方案 1: 使用 systemd 服務配置 (推薦)

**適用**: Ollama 作為系統服務運行

#### Step 1: 編輯 systemd 服務文件

```bash
sudo nano /etc/systemd/system/ollama.service
```

#### Step 2: 添加 OLLAMA_HOST 環境變數

在 `[Service]` 區塊添加:
```ini
Environment="OLLAMA_HOST=0.0.0.0:11434"
```

**完整配置範例**:
```ini
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=..."
Environment="OLLAMA_HOST=0.0.0.0:11434"  # ← 添加這行

[Install]
WantedBy=default.target
```

#### Step 3: 重新加載並重啟服務

```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 等待服務啟動
sleep 3

# 驗證服務狀態
systemctl status ollama
```

#### Step 4: 驗證監聽狀態

```bash
# 應該顯示 0.0.0.0:11434
ss -tlnp | grep 11434
# 輸出: LISTEN 0      4096       0.0.0.0:11434      0.0.0.0:*
```

---

### 方案 2: 使用啟動腳本 (臨時解決)

**適用**: 手動啟動 Ollama 或測試階段

#### 使用專案內建腳本

```bash
chmod +x scripts/setup_ollama.sh
sudo scripts/setup_ollama.sh
```

#### 或手動執行

```bash
# 停止現有 Ollama
sudo systemctl stop ollama
# 或
killall ollama

# 啟動 Ollama 監聽所有介面
OLLAMA_HOST=0.0.0.0:11434 ollama serve &

# 驗證
sleep 3
curl http://localhost:11434/api/tags
```

**注意**: 此方案需要每次重啟後手動執行

---

### 方案 3: 使用 Docker 網路模式 (備選)

**適用**: 不想修改 Ollama 配置的情況

修改 `docker-compose.yml` 中的 backend 服務:

```yaml
backend:
  build: ./backend
  network_mode: "host"  # 使用 host 網路模式
  environment:
    - OLLAMA_URL=http://localhost:11434  # 改用 localhost
```

**優點**: 無需修改 Ollama 配置
**缺點**: 破壞容器隔離性，可能產生端口衝突

---

## 🧪 驗證修復

### 1. 檢查 Ollama 監聽狀態

```bash
# 應該顯示 0.0.0.0:11434
ss -tlnp | grep 11434
```

**預期輸出**:
```
LISTEN 0      4096       0.0.0.0:11434      0.0.0.0:*    users:(("ollama",pid=2169,fd=3))
```

### 2. 從容器測試連接

```bash
# 測試網路連接
docker exec ppt-backend curl -s http://host.docker.internal:11434/api/tags | head -20
```

**預期輸出**:
```json
{"models":[
  {"name":"zephyr:7b",...},
  {"name":"gpt-oss:20b",...}
]}
```

### 3. 重啟 Backend 容器

```bash
docker-compose restart backend

# 監控日誌
docker-compose logs -f backend | grep -i ollama
```

**預期日誌**:
```
INFO: Ollama service connected successfully
INFO: Using model: gpt-oss:20b
```

**不應該看到**:
```
Error checking Zephyr model: All connection attempts failed  # ❌
```

### 4. 測試 Backend Health API

```bash
curl http://localhost:5000/api/health
```

**預期輸出**:
```json
{
  "status": "healthy",
  "services": {
    "presenton": "connected",
    "ollama": "connected",      # ✅ 已連接
    "pexels": "connected",
    "zephyr": "available"       # ✅ 可用
  }
}
```

### 5. 端到端功能測試

1. 訪問 http://localhost:8080
2. 輸入測試內容 (>50 字元)
3. 點擊「生成簡報」
4. 觀察進度條 (應該正常到 100%)
5. 下載 PPTX/PDF (應該成功)
6. 點擊「生成演講稿」(應該正常生成)

---

## 🔒 安全考量

### 監聽 0.0.0.0 的安全影響

**風險**: Ollama API 將可從網路訪問

**緩解措施**:

#### 1. 防火牆規則 (推薦)

只允許 Docker 網段訪問:
```bash
sudo ufw allow from 172.17.0.0/16 to any port 11434
sudo ufw deny 11434
```

#### 2. 綁定到特定 IP

如果知道 Docker bridge IP (通常是 172.17.0.1):
```ini
Environment="OLLAMA_HOST=172.17.0.1:11434"
```

#### 3. 使用反向代理

通過 nginx/traefik 添加認證:
```nginx
location /ollama/ {
    auth_basic "Ollama API";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://localhost:11434/;
}
```

---

## 🐛 常見問題

### Q1: 修改配置後 Ollama 無法啟動

**檢查**:
```bash
systemctl status ollama
journalctl -u ollama -f
```

**可能原因**:
- 端口被佔用
- 配置文件語法錯誤
- 權限問題

**解決**:
```bash
# 檢查端口
lsof -i :11434

# 恢復備份
sudo cp /etc/systemd/system/ollama.service.backup.* /etc/systemd/system/ollama.service
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Q2: 容器仍然無法連接

**診斷步驟**:
```bash
# 1. 檢查 Docker 網路
docker network inspect teacherassist_app-network | grep Gateway

# 2. 檢查容器 hosts 文件
docker exec ppt-backend cat /etc/hosts | grep host.docker.internal

# 3. 從容器 ping host
docker exec ppt-backend ping -c 2 host.docker.internal
```

**可能原因**:
- Docker 沒有正確配置 host.docker.internal
- 防火牆阻擋
- SELinux 限制

### Q3: Zephyr 模型仍然顯示 not_installed

**原因**:
- 可能是舊的錯誤日誌
- Zephyr 模型確實未安裝

**解決**:
```bash
# 檢查模型
ollama list | grep zephyr

# 如果沒有，下載模型
ollama pull zephyr:7b

# 重啟 Backend
docker-compose restart backend
```

---

## 📝 代碼中的 Zephyr 引用

### Backend 配置正確性驗證

```bash
# 檢查所有 Zephyr 模型引用
grep -rn "zephyr" backend/app/
```

**應該看到**:
```python
# backend/app/services/zephyr_service.py:12
self.model = "zephyr:7b"  # ✅ 正確

# backend/app/services/zephyr_service.py:221
json={"name": "zephyr:7b"}  # ✅ 正確
```

**不應該看到**:
```python
self.model = "zephyr"      # ❌ 錯誤 (缺少版本號)
json={"name": "zephyr"}    # ❌ 錯誤 (缺少版本號)
```

---

## ✅ 修復檢查清單

- [ ] Ollama 服務添加 `OLLAMA_HOST=0.0.0.0:11434`
- [ ] systemd daemon-reload 完成
- [ ] Ollama 服務已重啟
- [ ] `ss -tlnp | grep 11434` 顯示 `0.0.0.0:11434`
- [ ] 容器可以訪問 `host.docker.internal:11434`
- [ ] Backend 日誌無 connection failed 錯誤
- [ ] Backend health API 顯示 ollama: connected
- [ ] Backend health API 顯示 zephyr: available
- [ ] 簡報生成功能正常
- [ ] 演講稿生成功能正常 (如果已安裝 zephyr:7b)

---

## 📚 相關文檔

- [Ollama Docker Documentation](https://github.com/ollama/ollama/blob/main/docs/docker.md)
- [TeacherAssist CLAUDE.md](../CLAUDE.md)
- [系統修復報告](fix_report_20251014.md)
- [Backend 配置文件](../backend/app/config.py)

---

**修復指南版本**: 1.0
**最後更新**: 2025-10-14
**狀態**: ✅ 驗證有效
