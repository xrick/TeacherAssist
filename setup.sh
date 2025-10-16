# setup.sh
#!/bin/bash

# Teaching PPT Generator - Setup Script
# This script automates the setup process

set -e  # Exit on error

echo "🎓 Teaching PPT Generator - Setup Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Prerequisites
echo "Step 1: Checking Prerequisites..."
echo "--------------------------------"

if command_exists docker; then
    print_success "Docker is installed"
    docker --version
else
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if command_exists docker-compose; then
    print_success "Docker Compose is installed"
    docker-compose --version
else
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if command_exists python3; then
    print_success "Python 3 is installed"
    python3 --version
else
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

if command_exists ollama; then
    print_success "Ollama is installed"
    ollama --version
else
    print_error "Ollama is not installed. Please install Ollama first."
    echo "Run: curl https://ollama.ai/install.sh | sh"
    exit 1
fi

echo ""

# Step 2: Check Ollama Model
echo "Step 2: Checking Ollama Models..."
echo "--------------------------------"

if ollama list | grep -q "gpt-oss:20"; then
    print_success "Ollama model gpt-oss:20 is downloaded"
else
    print_info "Downloading Ollama model gpt-oss:20..."
    ollama pull gpt-oss:20
    print_success "Model downloaded successfully"
fi

if ollama list | grep -q "zephyr"; then
    print_success "Ollama model zephyr:7b is downloaded"
else
    print_info "Downloading Ollama model zephyr:7b (for transcript generation)..."
    ollama pull zephyr:7b
    print_success "Model downloaded successfully"
fi

echo ""

# Step 3: Create Directory Structure
echo "Step 3: Creating Directory Structure..."
echo "---------------------------------------"

mkdir -p backend/app/{api,services,utils}
mkdir -p backend/tests
mkdir -p frontend/{js,css,assets}
mkdir -p output
mkdir -p docs

print_success "Directory structure created"

echo ""

# Step 4: Check .env file
echo "Step 4: Checking Environment Configuration..."
echo "---------------------------------------------"

if [ -f ".env" ]; then
    print_success ".env file exists"
else
    print_error ".env file not found. Please create it from .env.example"
    exit 1
fi

# Verify required variables
if grep -q "PRESENTON_API_KEY=sk-presenton-" .env && \
   grep -q "PEXELS_API_KEY=" .env && \
   ! grep -q "PEXELS_API_KEY=your_pexels_api_key_here" .env; then
    print_success "API keys configured"
else
    print_error "API keys not properly configured in .env"
    exit 1
fi

echo ""

# Step 5: Create __init__.py files
echo "Step 5: Creating Python Package Files..."
echo "----------------------------------------"

touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/services/__init__.py
touch backend/app/utils/__init__.py

print_success "Python package files created"

echo ""

# Step 6: Build Docker Images
echo "Step 6: Building Docker Images..."
echo "---------------------------------"

print_info "This may take a few minutes..."
docker-compose build

print_success "Docker images built successfully"

echo ""

# Step 7: Start Services
echo "Step 7: Starting Services..."
echo "---------------------------"

docker-compose up -d

print_info "Waiting for services to start..."
sleep 10

print_success "Services started"

echo ""

# Step 8: Verify Services
echo "Step 8: Verifying Services..."
echo "-----------------------------"

# Check Ollama
if curl -s http://localhost:11434/api/tags > /dev/null; then
    print_success "Ollama is responding"
else
    print_error "Ollama is not responding"
fi

# Check Presenton
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    print_success "Presenton API is responding"
else
    print_info "Presenton API may still be starting... (this is normal)"
fi

# Check Backend
sleep 5
if curl -s http://localhost:5050/api/health > /dev/null 2>&1; then
    print_success "Backend API is responding"
else
    print_info "Backend API may still be starting... (this is normal)"
fi

echo ""

# Step 9: Display Status
echo "Step 9: System Status"
echo "--------------------"

docker-compose ps

echo ""

# Step 10: Final Instructions
echo "✨ Setup Complete! ✨"
echo "===================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Check service logs:"
echo "   docker-compose logs -f"
echo ""
echo "2. Test the API:"
echo "   curl http://localhost:5050/api/health"
echo ""
echo "3. Open the frontend:"
echo "   cd frontend && python3 -m http.server 8080"
echo "   Then visit: http://localhost:8080"
echo ""
echo "4. View API documentation:"
echo "   http://localhost:5050/docs"
echo ""
echo "5. Monitor containers:"
echo "   docker-compose ps"
echo ""
echo "🎤 Transcript Generation:"
echo "   - Model: Zephyr 7B"
echo "   - Generate scripts for presentations"
echo "   - Three speaking styles available"
echo "   - Download as text file"
echo ""
echo "📚 For troubleshooting, see:"
echo "   - README.md"
echo "   - CHECKLIST.md"
echo "   - docker-compose logs"
echo ""
echo "🎉 Happy presenting!"
echo ""