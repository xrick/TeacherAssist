# 建立並使用一個 builder（可重複使用）
docker buildx create --name presentonx --use

# 建置 ARM64 單架構映像（本機載入）
## docker buildx build \
##  --platform linux/arm64 \
##  -t presenton:arm64-local \
##  --load \
##  .

# 本機測試
## docker run -it --rm -p 5000:80 -v "$(pwd)/app_data:/app_data" presenton:arm64-local
# 然後打開 http://localhost:5000
