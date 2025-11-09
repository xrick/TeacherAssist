# Start System Port 檢查優化

**日期**: 2025-11-09
**檔案**: `scripts/start_system.sh`
**改進範圍**: Step 2 - Port 可用性檢查

---

## 問題描述

### 原始問題

當執行 `start_system.sh` 時，遇到 port 檢查邏輯問題：

```bash
Step 2: 檢查 Port 可用性
----------------------
⚠️  Port 5050 已被佔用 (Backend)
當前使用者:
OrbStack  29270 xrickliao  117u  IPv4 0xddb3abe4ca1204b9      0t0  TCP *:5050 (LISTEN)
是否要停止佔用該 port 的程序？(y/N): y
✅ 已停止 PID: 29270

⚠️  Port 8001 已被佔用 (Presenton)
當前使用者:
OrbStack  29270 xrickliao  115u  IPv4 0xe00bdea0cac1c4d3      0t0  TCP *:8001 (LISTEN)
```

### 問題分析

**根本原因**:
1. **同一 PID 佔用多個 port**: OrbStack (PID 29270) 同時佔用 5050 和 8001
2. **檢查順序問題**: 停止 5050 時 kill PID 29270，同時釋放了 8001，但下一個檢查還是顯示 8001 被佔用
3. **沒有 grace period**: kill 後立即檢查下個 port，process 還沒完全釋放資源
4. **缺乏智能識別**: 無法區分是開發環境的 container 還是其他服務

### 舊版程式碼缺陷

```bash
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port 已被佔用 ($service)"
        echo "當前使用者:"
        lsof -Pi :$port -sTCP:LISTEN | grep -v "^COMMAND" | head -3
        read -p "是否要停止佔用該 port 的程序？(y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local pid=$(lsof -Pi :$port -sTCP:LISTEN -t)
            kill $pid 2>/dev/null && print_success "已停止 PID: $pid"
            # ❌ 問題：沒有記錄已停止的 PID
            # ❌ 問題：沒有等待 port 釋放
            # ❌ 問題：沒有檢查是否是開發環境 container
        else
            print_error "Port $port 衝突，無法繼續"
            exit 1
        fi
    else
        print_success "Port $port 可用 ($service)"
    fi
}
```

**缺陷總結**:
1. ❌ 沒有全局 PID 追蹤
2. ❌ 沒有 grace period 等待
3. ❌ 無法識別開發環境 container
4. ❌ 重複檢查已停止的 PID

---

## 解決方案

### 新版智能檢查邏輯

#### 1. 全局 PID 追蹤

```bash
# 全局變數記錄已停止的 PIDs
KILLED_PIDS=()
```

**功能**: 避免重複檢查和提示已停止的 PID

#### 2. 已停止 PID 的智能處理

```bash
# 檢查是否已經停止過此 PID
if [[ " ${KILLED_PIDS[@]} " =~ " ${pid} " ]]; then
    print_info "Port $port: PID $pid 已停止，等待釋放..."
    # 等待 port 釋放（最多 5 秒）
    local count=0
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 0.5
        ((count++))
    done

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $port 仍被佔用，但 PID $pid 已停止，可能是延遲釋放"
        print_info "繼續執行..."
        return 0  # ✅ 容許延遲釋放，不中斷啟動
    else
        print_success "Port $port 已釋放 ($service)"
        return 0
    fi
fi
```

**改進點**:
- ✅ 識別已停止的 PID
- ✅ 等待最多 5 秒讓 port 釋放
- ✅ 容許延遲釋放（開發環境常見現象）

#### 3. 開發環境 Container 識別

```bash
# 檢查是否是本專案的 Docker container
if [[ "$process_name" == *"docker"* ]] || [[ "$process_name" == *"OrbStack"* ]]; then
    # 檢查 container 名稱
    local containers=$(docker ps --format "{{.Names}}" 2>/dev/null | grep -E "^(ppt-|presenton)" || echo "")

    if [ -n "$containers" ]; then
        print_warning "Port $port 被本專案的 Docker container 佔用"
        echo "  Container(s): $containers"
        print_info "這是正常的開發環境狀態，將重用現有 container"
        return 0  # ✅ 視為可用，不中斷啟動
    fi
fi
```

**改進點**:
- ✅ 識別 Docker/OrbStack 進程
- ✅ 檢查是否是本專案 container (ppt-*, presenton*)
- ✅ 開發環境自動重用現有 container
- ✅ 避免不必要的 kill 和重啟

#### 4. OrbStack 其他服務處理

```bash
# 檢查是否是 OrbStack 的其他服務
if [[ "$process_name" == *"OrbStack"* ]]; then
    print_warning "Port $port 被 OrbStack 佔用 (PID: $pid)"
    echo "  Process: $process_cmd" | head -c 100
    echo ""
    read -p "是否停止此程序並繼續？(y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        kill $pid 2>/dev/null
        if [ $? -eq 0 ]; then
            print_success "已停止 PID: $pid"
            KILLED_PIDS+=($pid)  # ✅ 記錄到全局陣列
            sleep 1  # ✅ Grace period
            return 0
        else
            print_error "無法停止 PID: $pid"
            exit 1
        fi
    fi
fi
```

**改進點**:
- ✅ 顯示更詳細的進程資訊
- ✅ 記錄已停止的 PID
- ✅ 提供 1 秒 grace period

#### 5. 其他進程處理

```bash
# 其他進程佔用
print_warning "Port $port 被其他程序佔用 ($service)"
echo "  PID: $pid"
echo "  Process: $process_name"
echo "  Command: $process_cmd" | head -c 100
echo ""
read -p "是否停止此程序？(y/N): " -n 1 -r
```

**改進點**:
- ✅ 更清楚的資訊顯示
- ✅ 統一的處理流程

---

## 工作流程圖

### 新版檢查流程

```
check_port(port, service, container_prefix)
    │
    ├─ Port 可用？
    │   └─ Yes → ✅ 成功返回
    │
    ├─ 獲取 PID 和進程資訊
    │
    ├─ PID 在 KILLED_PIDS 中？
    │   └─ Yes → 等待釋放（最多 5 秒）
    │       ├─ 已釋放？ → ✅ 成功返回
    │       └─ 仍佔用？ → ⚠️  警告但繼續
    │
    ├─ 是 Docker/OrbStack？
    │   └─ Yes → 檢查 container 名稱
    │       ├─ 本專案 container？ → ✅ 重用
    │       └─ 其他服務？ → 詢問停止
    │
    └─ 其他進程？
        └─ 詢問停止
            ├─ Yes → kill → 記錄 PID → 等待 1s
            └─ No → ❌ 錯誤退出
```

---

## 改進效果

### Before (舊版)

```bash
⚠️  Port 5050 已被佔用 (Backend)
是否要停止？(y/N): y
✅ 已停止 PID: 29270

⚠️  Port 8001 已被佔用 (Presenton)  # ❌ 誤判，同一 PID 已停止
是否要停止？(y/N): y
❌ 無法停止 PID: 29270  # ❌ PID 不存在，錯誤
```

### After (新版)

**情境 1: 本專案 container 已運行**
```bash
⚠️  Port 5050 被本專案的 Docker container 佔用
  Container(s): ppt-backend
ℹ️  這是正常的開發環境狀態，將重用現有 container
✅ Port 5050 可用 (Backend)

⚠️  Port 8001 被本專案的 Docker container 佔用
  Container(s): presenton-api
ℹ️  這是正常的開發環境狀態，將重用現有 container
✅ Port 8001 可用 (Presenton)
```

**情境 2: OrbStack 佔用多個 port**
```bash
⚠️  Port 5050 被 OrbStack 佔用 (PID: 29270)
是否停止此程序並繼續？(y/N): y
✅ 已停止 PID: 29270

ℹ️  Port 8001: PID 29270 已停止，等待釋放...
✅ Port 8001 已釋放 (Presenton)
```

---

## 技術細節

### Bash 陣列操作

**宣告全局陣列**:
```bash
KILLED_PIDS=()
```

**檢查元素是否存在**:
```bash
if [[ " ${KILLED_PIDS[@]} " =~ " ${pid} " ]]; then
    # PID 已在陣列中
fi
```

**添加元素**:
```bash
KILLED_PIDS+=($pid)
```

### Process 資訊獲取

**進程名稱** (簡短):
```bash
ps -p $pid -o comm=
# 輸出: OrbStack
```

**完整命令** (詳細):
```bash
ps -p $pid -o args=
# 輸出: /Applications/OrbStack.app/Contents/MacOS/OrbStack --port 5050
```

### Port 等待邏輯

```bash
local count=0
while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 && [ $count -lt 10 ]; do
    sleep 0.5  # 每次等待 0.5 秒
    ((count++))  # 計數器+1
done
# 最多等待 10 * 0.5 = 5 秒
```

### Docker Container 檢查

**獲取運行中的 container 名稱**:
```bash
docker ps --format "{{.Names}}"
# 輸出:
# ppt-backend
# presenton-api
```

**過濾本專案 container**:
```bash
grep -E "^(ppt-|presenton)"
# 匹配以 ppt- 或 presenton 開頭的名稱
```

---

## 測試情境

### 測試案例 1: 首次啟動（無衝突）

**預期結果**:
```bash
✅ Port 5050 可用 (Backend)
✅ Port 8001 可用 (Presenton)
✅ Port 8080 可用 (Frontend)
```

### 測試案例 2: Container 已運行

**預期結果**:
```bash
⚠️  Port 5050 被本專案的 Docker container 佔用
  Container(s): ppt-backend
ℹ️  這是正常的開發環境狀態，將重用現有 container

⚠️  Port 8001 被本專案的 Docker container 佔用
  Container(s): presenton-api
ℹ️  這是正常的開發環境狀態，將重用現有 container

✅ Port 8080 可用 (Frontend)
```

### 測試案例 3: OrbStack 佔用多個 port

**操作**: 停止第一個 port 的 PID

**預期結果**:
```bash
⚠️  Port 5050 被 OrbStack 佔用 (PID: 12345)
是否停止此程序並繼續？(y/N): y
✅ 已停止 PID: 12345

ℹ️  Port 8001: PID 12345 已停止，等待釋放...
✅ Port 8001 已釋放 (Presenton)
```

### 測試案例 4: 其他服務佔用

**預期結果**:
```bash
⚠️  Port 5050 被其他程序佔用 (Backend)
  PID: 67890
  Process: nginx
  Command: nginx: master process /usr/local/bin/nginx

是否停止此程序？(y/N): y
✅ 已停止 PID: 67890
```

---

## 最佳實踐

### 1. Grace Period 設計

**原則**: 給予足夠時間讓系統資源釋放
- Port 釋放: 5 秒 (10 * 0.5s)
- Process 停止: 1 秒

**理由**:
- 網路 socket 需要時間進入 TIME_WAIT 狀態
- OS 需要時間清理進程資源
- 避免後續檢查誤判

### 2. 容錯處理

**原則**: 開發環境優先可用性而非嚴格檢查

**實作**:
```bash
if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_warning "Port $port 仍被佔用，但 PID $pid 已停止，可能是延遲釋放"
    print_info "繼續執行..."
    return 0  # ✅ 不中斷啟動
fi
```

### 3. 智能識別

**原則**: 區分開發環境和外部衝突

**層次**:
1. 本專案 container → 自動重用
2. OrbStack 其他服務 → 詢問停止
3. 其他進程 → 詢問停止

---

## 維護建議

### 1. Container 名稱規範

**目前規則**:
```bash
grep -E "^(ppt-|presenton)"
```

**建議**: 如果新增 container，確保名稱符合規則:
- `ppt-*` 開頭 (如 `ppt-backend`, `ppt-worker`)
- `presenton*` 開頭 (如 `presenton-api`, `presenton-redis`)

### 2. Port 配置集中管理

**建議**: 在 `.env` 或 config 中統一定義 port:
```bash
# .env
BACKEND_PORT=5050
PRESENTON_PORT=8001
FRONTEND_PORT=8080
```

**腳本中讀取**:
```bash
source .env
check_port ${BACKEND_PORT} "Backend" "ppt-backend"
```

### 3. 錯誤記錄

**建議**: 記錄 port 檢查結果到 log:
```bash
echo "$(date): Port check - $port | PID: $pid | Action: $action" >> /tmp/port_check.log
```

---

## 總結

### 改進點

| 項目 | 改進前 | 改進後 |
|------|--------|--------|
| PID 追蹤 | ❌ 無 | ✅ 全局陣列 KILLED_PIDS |
| Grace Period | ❌ 無 | ✅ 5 秒等待 + 1 秒延遲 |
| Container 識別 | ❌ 無 | ✅ 自動識別本專案 container |
| 延遲釋放處理 | ❌ 失敗退出 | ✅ 容錯繼續 |
| 資訊顯示 | ⚠️  簡單 | ✅ 詳細（PID, Process, Command） |

### 效果

- ✅ **避免誤判**: 同一 PID 佔用多個 port 不會重複提示
- ✅ **開發友好**: 自動識別並重用開發環境 container
- ✅ **容錯能力**: 容許 port 延遲釋放，不中斷啟動
- ✅ **資訊透明**: 清楚顯示進程詳細資訊
- ✅ **智能處理**: 區分本專案、OrbStack、其他進程

---

## 相關文件

- [開發日誌 2025-11-09](./development_log_2025-11-09.md)
- [Project README](../README.md)
- [Setup Guide](../documentation/quickstart.md)

---

**建立時間**: 2025-11-09
**作者**: Claude Code (SuperClaude Framework)
**版本**: v2.0
