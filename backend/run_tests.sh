#!/bin/bash
# backend/run_tests.sh
# Run all tests for enhancement pipeline

echo "Running Enhancement Pipeline Tests"
echo "==================================="

# Run unit tests
echo ""
echo "1. Testing PythonPptxAnalyzer..."
python -m pytest tests/test_pptx_analyzer.py -v

echo ""
echo "2. Testing ContentImprover..."
python -m pytest tests/test_content_improver.py -v

echo ""
echo "3. Testing PresentationRebuilder..."
python -m pytest tests/test_presentation_rebuilder.py -v

echo ""
echo "4. Testing Enhancement Integration..."
python -m pytest tests/test_enhancement_integration.py -v

echo ""
echo "==================================="
echo "All tests completed"
