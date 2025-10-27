#!/bin/bash
# scripts/switch_model.sh
# 快速切換 Ollama 模型

set -e

# 顏色定義
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 專案根目錄
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 可用模型
declare -A MODELS=(
    ["1"]="phi4-mini:3.8b|快速輕量（當前）|2.5 GB|⚡⚡⚡"
    ["2"]="phi4-mini-reasoning:3.8b|推理增強|3.2 GB|⚡⚡"
    ["3"]="zephyr:7b|對話專家|4.1 GB|⚡"
    ["4"]="gpt-oss:20b|最強質量|13 GB|🐌"
)

echo -e "${BLUE}════════════════════════════════════════${NC}"
echo -e "${BLUE}  Ollama 模型切換工具${NC}"
echo -e "${BLUE}════════════════════════════════════════${NC}"
echo ""

# 顯示當前配置
CURRENT=$(grep "OLLAMA_MODEL=" docker-compose.yml | head -1 | cut -d= -f2)
echo -e "${GREEN}當前模型：${CURRENT}${NC}"
echo ""

# 顯示選項
echo "請選擇要切換的模型："
echo ""
for key in $(echo "${!MODELS[@]}" | tr ' ' '\n' | sort); do
    IFS='|' read -r model desc size speed <<< "${MODELS[$key]}"
    echo -e "${key}) ${YELLOW}${model}${NC}"
    echo "   描述：${desc}"
    echo "   大小：${size}  速度：${speed}"
    echo ""
done

# 讀取選擇
read -p "請輸入選項 (1-4) 或 q 退出: " choice

if [ "$choice" = "q" ]; then
    echo "已取消"
    exit 0
fi

# 驗證選擇
if [ -z "${MODELS[$choice]}" ]; then
    echo -e "${YELLOW}⚠️  無效選項${NC}"
    exit 1
fi

# 提取模型名稱
IFS='|' read -r NEW_MODEL desc size speed <<< "${MODELS[$choice]}"

# 確認切換
echo ""
echo -e "${YELLOW}即將切換到：${NEW_MODEL}${NC}"
echo -e "描述：${desc}"
echo -e "大小：${size}  速度：${speed}"
echo ""
read -p "確定要切換嗎？(y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "已取消"
    exit 0
fi

# 執行切換
echo -e "${BLUE}正在切換模型...${NC}"

# 使用 sed 替換
sed -i "s/OLLAMA_MODEL=.*/OLLAMA_MODEL=${NEW_MODEL}/g" docker-compose.yml

# 驗證修改
if grep -q "OLLAMA_MODEL=${NEW_MODEL}" docker-compose.yml; then
    echo -e "${GREEN}✅ docker-compose.yml 已更新${NC}"
else
    echo -e "${YELLOW}⚠️  更新失敗${NC}"
    exit 1
fi

# 重啟服務
echo -e "${BLUE}正在重啟服務...${NC}"
docker compose restart

echo ""
echo -e "${GREEN}✅ 模型切換完成！${NC}"
echo ""
echo "等待服務啟動（約 15 秒）..."
sleep 15

# 驗證新配置
echo ""
echo -e "${BLUE}驗證新配置：${NC}"
ACTUAL=$(docker exec presenton-api env 2>/dev/null | grep OLLAMA_MODEL | cut -d= -f2)
if [ "$ACTUAL" = "$NEW_MODEL" ]; then
    echo -e "${GREEN}✅ Presenton: ${ACTUAL}${NC}"
else
    echo -e "${YELLOW}⚠️  Presenton: ${ACTUAL} (預期: ${NEW_MODEL})${NC}"
fi

ACTUAL_BACKEND=$(docker exec ppt-backend env 2>/dev/null | grep OLLAMA_MODEL | cut -d= -f2)
if [ "$ACTUAL_BACKEND" = "$NEW_MODEL" ]; then
    echo -e "${GREEN}✅ Backend: ${ACTUAL_BACKEND}${NC}"
else
    echo -e "${YELLOW}⚠️  Backend: ${ACTUAL_BACKEND} (預期: ${NEW_MODEL})${NC}"
fi

echo ""
echo -e "${GREEN}🎉 切換完成！現在可以測試 PPT 生成功能${NC}"
echo ""
echo "提示："
echo "  - 新模型生成速度可能不同"
echo "  - 質量較高的模型需要更長時間"
echo "  - 可以在前端測試效果"
