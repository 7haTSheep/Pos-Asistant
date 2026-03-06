#!/bin/bash
# Test runner script for POS-Assistant Server
# 
# Usage:
#   ./run_tests.sh           - Run all tests
#   ./run_tests.sh unit      - Run only unit tests
#   ./run_tests.sh coverage  - Run with coverage report
#   ./run_tests.sh clean     - Clean test cache

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Change to script directory
cd "$(dirname "$0")"

echo -e "${GREEN}POS-Assistant Server Tests${NC}"
echo "============================"
echo ""

case "${1:-all}" in
    all)
        echo -e "${YELLOW}Running all tests...${NC}"
        pytest tests/ -v
        ;;
    
    unit)
        echo -e "${YELLOW}Running unit tests...${NC}"
        pytest tests/ -v -m unit
        ;;
    
    integration)
        echo -e "${YELLOW}Running integration tests...${NC}"
        pytest tests/ -v -m integration
        ;;
    
    coverage)
        echo -e "${YELLOW}Running tests with coverage...${NC}"
        pytest tests/ --cov=server --cov-report=html --cov-report=term-missing
        echo ""
        echo -e "${GREEN}Coverage report generated:${NC} htmlcov/index.html"
        ;;
    
    cov)
        echo -e "${YELLOW}Running tests with coverage (JSON)...${NC}"
        pytest tests/ --cov=server --cov-report=json --cov-fail-under=70
        ;;
    
    clean)
        echo -e "${YELLOW}Cleaning test cache...${NC}"
        rm -rf .pytest_cache
        rm -rf __pycache__
        rm -rf htmlcov
        rm -rf .coverage
        rm -rf coverage.xml
        find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
        echo -e "${GREEN}Clean complete${NC}"
        ;;
    
    watch)
        echo -e "${YELLOW}Running tests in watch mode...${NC}"
        if command -v pytest-watch &> /dev/null; then
            pytest-watch -- --cov=server
        else
            echo -e "${RED}pytest-watch not installed. Install with: pip install pytest-watch${NC}"
            exit 1
        fi
        ;;
    
    *)
        echo -e "${RED}Unknown command: ${1}${NC}"
        echo ""
        echo "Usage:"
        echo "  ./run_tests.sh           - Run all tests"
        echo "  ./run_tests.sh unit      - Run only unit tests"
        echo "  ./run_tests.sh coverage  - Run with coverage report"
        echo "  ./run_tests.sh clean     - Clean test cache"
        echo "  ./run_tests.sh watch     - Run in watch mode (requires pytest-watch)"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Done!${NC}"
