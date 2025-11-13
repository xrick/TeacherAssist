#!/bin/bash
# Test script to check Presenton API response format

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}=== Presentation API Test ===${NC}\n"

# Check if presentation_id is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: $0 <presentation_id>${NC}"
    echo -e "${YELLOW}Example: $0 cm3uu7mmi000008kyfnjd5uy1${NC}"
    exit 1
fi

PRESENTATION_ID="$1"
BACKEND_URL="http://localhost:5050"

echo -e "${BLUE}Testing endpoint:${NC} GET /api/presentation/${PRESENTATION_ID}\n"

# Make API request
response=$(curl -s "${BACKEND_URL}/api/presentation/${PRESENTATION_ID}")

# Check if response is valid JSON
if echo "$response" | python3 -m json.tool > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Valid JSON response${NC}\n"

    # Pretty print full response
    echo -e "${BLUE}=== Full Response ===${NC}"
    echo "$response" | python3 -m json.tool

    # Extract first slide content structure
    echo -e "\n${BLUE}=== First Slide Content Structure ===${NC}"
    echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'slides' in data and len(data['slides']) > 0:
    slide = data['slides'][0]
    print(json.dumps(slide, indent=2, ensure_ascii=False))
else:
    print('No slides found in response')
"

    # List all content fields in first slide
    echo -e "\n${BLUE}=== First Slide Content Fields ===${NC}"
    echo "$response" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if 'slides' in data and len(data['slides']) > 0:
    content = data['slides'][0].get('content', {})
    if isinstance(content, dict):
        print('Content fields:')
        for key in sorted(content.keys()):
            value = content[key]
            value_type = type(value).__name__
            value_preview = str(value)[:50] if value else 'null'
            print(f'  - {key}: ({value_type}) {value_preview}...')
    else:
        print(f'Content is not a dict: {type(content).__name__}')
"

else
    echo -e "${YELLOW}❌ Invalid JSON or error response${NC}"
    echo "$response"
    exit 1
fi

echo -e "\n${GREEN}=== Test Complete ===${NC}"
