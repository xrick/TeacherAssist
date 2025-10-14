<!-- claudedocs/docker_network_explained.md -->
# Docker 網路隔離與 Backend 連接問題詳解

**核心問題**: 為什麼 Backend 容器無法連接 `host.docker.internal:11434`？
**解答**: Docker 容器網路隔離 + Ollama 只監聽 localhost

---

## 🏗️ Docker 網路隔離原理

### 1. 容器網路命名空間 (Network Namespace)

Docker 容器運行在**獨立的網路命名空間**中，與 Host 系統網路完全隔離。

```
┌─────────────────────────────────────────┐
│           Host System (ai)              │
│  IP: 192.168.1.100                      │
│  ┌───────────────────────────────┐     │
│  │  Network Namespace: host      │     │
│  │  - lo: 127.0.0.1              │     │
│  │  - eth0: 192.168.1.100        │     │
│  │  - docker0: 172.17.0.1        │     │
│  └───────────────────────────────┘     │
│                                         │
│  ┌───────────────────────────────┐     │
│  │  Docker Container: ppt-backend│     │
│  │  Network Namespace: container │     │
│  │  - lo: 127.0.0.1 (isolated)   │     │
│  │  - eth0: 172.17.0.2           │     │
│  │  - gateway: 172.17.0.1        │     │
│  └───────────────────────────────┘     │
└─────────────────────────────────────────┘
```

**關鍵點**:
- 容器的 `127.0.0.1` ≠ Host 的 `127.0.0.1`
- 容器內訪問 `localhost` 只能訪問容器自己的服務
- 需要特殊機制才能從容器訪問 Host 服務

---

## 🔍 為什麼無法連接 host.docker.internal:11434

### 問題分解

#### Step 1: Ollama 監聽狀態

```bash
# Host 上執行
$ ss -tlnp | grep 11434
LISTEN 0  4096  127.0.0.1:11434  0.0.0.0:*
              ^^^^^^^^^^^
              只綁定到 localhost (Host 的 127.0.0.1)
```

**含義**:
- Ollama 只接受來自 `127.0.0.1` 的連接
- 拒絕所有其他 IP 的連接 (包括 `172.17.0.1`, `192.168.1.100`)

#### Step 2: host.docker.internal 解析

```bash
# 容器內執行
$ docker exec ppt-backend cat /etc/hosts | grep host.docker.internal
172.17.0.1	host.docker.internal
          ^^^^^^^^^^^
          指向 Docker bridge gateway IP
```

**含義**:
- `host.docker.internal` 解析到 `172.17.0.1` (Docker bridge IP)
- 容器嘗試連接 `172.17.0.1:11434`

#### Step 3: 連接嘗試失敗

```
Container (172.17.0.2)
    ↓
    請求: GET http://host.docker.internal:11434/api/tags
    ↓ DNS 解析
    目標: 172.17.0.1:11434
    ↓ TCP 連接
Host (172.17.0.1)
    ↓ 路由到 Ollama
Ollama 監聽檢查:
    - 檢查綁定地址: 127.0.0.1 ❌
    - 來源 IP: 172.17.0.1 ❌
    - 不匹配! → 拒絕連接
    ↓
Container 收到: Connection Refused
```

---

## 🆚 從程式碼啟動 vs Docker 啟動的差異

### 場景 A: Backend 在 Host 上運行 (程式碼直接執行)

```bash
# 直接執行 Backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 5000
```

**網路拓撲**:
```
┌─────────────────────────────────────┐
│      Host System (ai)               │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   Backend    │  │   Ollama    │ │
│  │ (5000)       │  │  (11434)    │ │
│  │ 127.0.0.1    │→ │ 127.0.0.1   │ │
│  └──────────────┘  └─────────────┘ │
│         ↑                           │
│         同一個網路命名空間           │
└─────────────────────────────────────┘
```

**連接流程**:
```python
# Backend 程式碼
OLLAMA_URL = "http://localhost:11434"  # 或 127.0.0.1

# 連接嘗試
Backend (127.0.0.1) → Ollama (127.0.0.1:11434)
                   ↓
                   ✅ 成功! (同一個 localhost)
```

**為什麼成功**:
- Backend 和 Ollama 在同一個網路命名空間
- `localhost` 指向同一個迴環介面
- Ollama 監聽 `127.0.0.1` 可以接受來自同一 Host 的連接

---

### 場景 B: Backend 在 Docker 容器運行

```bash
# Docker 啟動 Backend
docker-compose up -d backend
```

**網路拓撲**:
```
┌─────────────────────────────────────────┐
│      Host System (ai)                   │
│                                         │
│  ┌─────────────┐                       │
│  │   Ollama    │                       │
│  │  (11434)    │                       │
│  │ 127.0.0.1   │                       │
│  └─────────────┘                       │
│        ↑                                │
│        │ 拒絕外部連接                   │
│        │                                │
│  ┌─────┴──────────────────────┐        │
│  │  Docker Bridge (172.17.0.1)│        │
│  └────────────────────────────┘        │
│        ↑                                │
│        │                                │
│  ┌─────┴──────────────────────┐        │
│  │  Container: ppt-backend    │        │
│  │  IP: 172.17.0.2            │        │
│  │  Isolated Network NS       │        │
│  └────────────────────────────┘        │
└─────────────────────────────────────────┘
```

**連接流程**:
```python
# Backend 在容器內
OLLAMA_URL = "http://host.docker.internal:11434"

# 連接嘗試
Container (172.17.0.2)
    ↓ 解析 host.docker.internal
    ↓ 目標: 172.17.0.1:11434
    ↓
Docker Bridge (172.17.0.1)
    ↓ 轉發到 Host
    ↓
Ollama 檢查監聽地址:
    - 綁定: 127.0.0.1 ❌
    - 來源: 172.17.0.1 ❌
    ↓
    ❌ Connection Refused
```

**為什麼失敗**:
- 容器和 Host 在不同的網路命名空間
- 容器的 `localhost` ≠ Host 的 `localhost`
- Ollama 只監聽 `127.0.0.1`，拒絕來自 `172.17.0.1` 的連接

---

## 💡 解決方案比較

### 方案 1: 修改 Ollama 監聽地址 (推薦 ⭐)

**改變**: Ollama 監聽 `0.0.0.0:11434`

```bash
# 修改 systemd 服務
sudo nano /etc/systemd/system/ollama.service
# 添加: Environment="OLLAMA_HOST=0.0.0.0:11434"

sudo systemctl daemon-reload
sudo systemctl restart ollama
```

**監聽變化**:
```bash
# 修改前
LISTEN 0  4096  127.0.0.1:11434  0.0.0.0:*
              ^^^^^^^^^^^
              只監聽 localhost

# 修改後
LISTEN 0  4096  0.0.0.0:11434    0.0.0.0:*
              ^^^^^^^^^
              監聽所有介面
```

**連接流程**:
```
Container (172.17.0.2)
    ↓ host.docker.internal:11434
    ↓ 172.17.0.1:11434
    ↓
Ollama 檢查:
    - 綁定: 0.0.0.0 ✅ (接受所有來源)
    - 來源: 172.17.0.1 ✅
    ↓
    ✅ Connection Accepted
```

**優點**:
- ✅ 保持容器隔離性
- ✅ 適合生產環境
- ✅ 其他容器也可訪問

**缺點**:
- ⚠️ Ollama API 暴露在網路上 (需要防火牆規則)

---

### 方案 2: Backend 使用 Host 網路模式

**改變**: Backend 容器使用 Host 網路

```yaml
# docker-compose.yml
backend:
  build: ./backend
  network_mode: "host"  # 使用 host 網路
  environment:
    - OLLAMA_URL=http://localhost:11434  # 改用 localhost
```

**網路拓撲**:
```
┌─────────────────────────────────────┐
│      Host System (ai)               │
│  (共享網路命名空間)                  │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   Backend    │  │   Ollama    │ │
│  │ Container    │  │  (11434)    │ │
│  │ (host mode)  │→ │ 127.0.0.1   │ │
│  └──────────────┘  └─────────────┘ │
│         ↑                           │
│         直接訪問 localhost           │
└─────────────────────────────────────┘
```

**連接流程**:
```
Backend Container (host network)
    ↓ 訪問 localhost:11434
    ↓ 直接使用 Host 的 127.0.0.1
    ↓
Ollama (127.0.0.1:11434)
    ↓
    ✅ 成功! (同一個 localhost)
```

**優點**:
- ✅ 無需修改 Ollama 配置
- ✅ 連接成功
- ✅ 性能略好 (無 NAT 開銷)

**缺點**:
- ❌ 破壞容器隔離性
- ❌ 端口衝突風險 (5000 需在 Host 可用)
- ❌ 不適合多容器環境
- ❌ 不符合容器最佳實踐

---

### 方案 3: Backend 在 Host 上直接執行

**改變**: 不使用 Docker 容器，直接執行 Python 程式

```bash
# 停止 Docker backend
docker-compose stop backend

# 在 Host 執行
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

**網路拓撲**:
```
┌─────────────────────────────────────┐
│      Host System (ai)               │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │   Backend    │  │   Ollama    │ │
│  │   (Python)   │  │  (11434)    │ │
│  │ 127.0.0.1    │→ │ 127.0.0.1   │ │
│  └──────────────┘  └─────────────┘ │
│         ↑                           │
│         同一個 Host，無隔離          │
└─────────────────────────────────────┘
```

**連接流程**:
```
Backend Process (Host)
    ↓ 訪問 localhost:11434
    ↓
Ollama (127.0.0.1:11434)
    ↓
    ✅ 成功! (同一個 Host)
```

**優點**:
- ✅ 無需修改 Ollama 配置
- ✅ 無網路隔離問題
- ✅ 開發調試方便

**缺點**:
- ❌ 失去容器化優勢
- ❌ 環境一致性差 (開發/生產不同)
- ❌ 依賴管理複雜
- ❌ 部署困難

---

## 📊 方案對比表

| 特性 | 方案1: 修改Ollama監聽 | 方案2: Host網路模式 | 方案3: 直接執行 |
|------|---------------------|-------------------|----------------|
| **容器隔離** | ✅ 保持 | ❌ 破壞 | ❌ 無容器化 |
| **環境一致性** | ✅ 開發=生產 | ⚠️ 配置複雜 | ❌ 不一致 |
| **部署難度** | ⭐ 簡單 | ⭐⭐ 中等 | ⭐⭐⭐ 困難 |
| **維護性** | ✅ 好 | ⚠️ 中等 | ❌ 差 |
| **擴展性** | ✅ 好 | ❌ 差 | ❌ 差 |
| **安全性** | ⚠️ 需防火牆 | ✅ 較好 | ⚠️ 看配置 |
| **適用場景** | 生產環境 | 快速測試 | 本地開發 |
| **推薦度** | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ |

---

## 🎯 推薦方案

### 生產環境: 方案 1 (修改 Ollama 監聽)

```bash
# 1. 修改 Ollama 服務
sudo nano /etc/systemd/system/ollama.service
# 添加: Environment="OLLAMA_HOST=0.0.0.0:11434"

# 2. 重啟服務
sudo systemctl daemon-reload
sudo systemctl restart ollama

# 3. 配置防火牆 (可選但推薦)
sudo ufw allow from 172.17.0.0/16 to any port 11434
sudo ufw deny 11434

# 4. 重啟 Backend
docker-compose restart backend
```

### 開發環境: 方案 3 (直接執行)

```bash
# 1. 停止 Docker backend
docker-compose stop backend

# 2. 設置環境
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. 設置環境變數
export OLLAMA_URL=http://localhost:11434
export PRESENTON_API_URL=http://localhost:8000
# ... 其他環境變數

# 4. 啟動 Backend
uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload
```

**開發環境優勢**:
- 程式碼修改立即生效 (--reload)
- 直接使用 IDE 調試
- 無 Docker 重建開銷

---

## 🔬 深入理解：網路監聽原理

### 127.0.0.1 vs 0.0.0.0

**127.0.0.1 (localhost)**:
- 只接受來自**本機**的連接
- 本機 = 同一個網路命名空間
- 容器和 Host 是**不同的網路命名空間**

```c
// Ollama 綁定到 127.0.0.1
bind(sockfd, 127.0.0.1, 11434);

// 檢查來源
if (source_ip == "127.0.0.1") {
    accept();  // ✅
} else {
    reject();  // ❌ 包括 172.17.0.1
}
```

**0.0.0.0 (所有介面)**:
- 接受來自**任何介面**的連接
- 包括: localhost, docker bridge, eth0, 等

```c
// Ollama 綁定到 0.0.0.0
bind(sockfd, 0.0.0.0, 11434);

// 檢查來源
if (dest_port == 11434) {
    accept();  // ✅ 接受所有來源
}
```

### Linux 網路命名空間

```bash
# 查看 Host 網路命名空間
ip netns list

# 查看容器網路命名空間
docker inspect ppt-backend -f '{{.NetworkSettings.SandboxKey}}'

# 進入容器網路命名空間
nsenter --net=/var/run/docker/netns/xxx ip addr
```

---

## 📚 相關文檔

- [Docker 網路官方文檔](https://docs.docker.com/network/)
- [Ollama Docker 配置](https://github.com/ollama/ollama/blob/main/docs/docker.md)
- [Linux Network Namespaces](https://man7.org/linux/man-pages/man7/network_namespaces.7.html)

---

## 💡 總結回答

### Q: 為什麼 Backend 容器無法連接 host.docker.internal:11434？

**A**: 因為 Docker 容器在**獨立的網路命名空間**運行，容器訪問 `host.docker.internal:11434` 實際上是通過 Docker bridge (`172.17.0.1`) 連接，而 Ollama 只監聽 `127.0.0.1`，拒絕來自其他 IP 的連接。

### Q: 是否改成從程式碼啟動 backend 就不會有這問題？

**A**: **是的**！如果 Backend 直接在 Host 上執行（不用 Docker），Backend 和 Ollama 在**同一個網路命名空間**，可以直接通過 `localhost` 連接，無網路隔離問題。

**但是**：
- ✅ 開發階段可以這樣做（方便調試）
- ❌ 生產環境不推薦（失去容器化優勢）
- ⭐ 最佳方案：修改 Ollama 監聽 `0.0.0.0`，保持 Backend 容器化

---

**文檔版本**: 1.0
**最後更新**: 2025-10-14
**狀態**: ✅ 完整說明
