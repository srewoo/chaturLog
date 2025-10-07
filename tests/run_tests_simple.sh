#!/bin/bash
#
# Simple ChaturLog Test Runner
# Assumes backend is already running on port 8001
#

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RESET='\033[0m'

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BLUE}║         ChaturLog Test Suite (Simple Runner)          ║${RESET}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${RESET}\n"

# Check if backend is running
echo -e "${BLUE}▶ Checking backend server...${RESET}"
if curl -s http://localhost:8001/api/analyses > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend server is running on port 8001${RESET}\n"
else
    echo -e "${RED}✗ Backend server is NOT running!${RESET}"
    echo -e "${YELLOW}Please start the backend first:${RESET}"
    echo -e "  ${BLUE}cd backend${RESET}"
    echo -e "  ${BLUE}python3 server.py${RESET}\n"
    exit 1
fi

# Test selection
echo -e "${BLUE}Select which tests to run:${RESET}"
echo -e "  ${YELLOW}1${RESET}) Python Test Generation Validation"
echo -e "  ${YELLOW}2${RESET}) JavaScript Test Generation Validation  "
echo -e "  ${YELLOW}3${RESET}) API Endpoint Tests (pytest)"
echo -e "  ${YELLOW}4${RESET}) All Python Tests"
echo -e "  ${YELLOW}5${RESET}) Setup Test User Only"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo -e "\n${BLUE}Running Python Test Generation Validation...${RESET}\n"
        python3 test_generation_validation.py
        ;;
    2)
        echo -e "\n${BLUE}Running JavaScript Test Generation Validation...${RESET}\n"
        if command -v node &> /dev/null; then
            node test_generation_validation.test.js
        else
            echo -e "${RED}✗ Node.js not found!${RESET}"
            exit 1
        fi
        ;;
    3)
        echo -e "\n${BLUE}Running API Endpoint Tests...${RESET}\n"
        pytest test_api_endpoints.py -v --tb=short
        ;;
    4)
        echo -e "\n${BLUE}Running All Python Tests...${RESET}\n"
        echo -e "${BLUE}Test 1: Test Generation Validation${RESET}"
        python3 test_generation_validation.py
        echo -e "\n${BLUE}Test 2: API Endpoints${RESET}"
        pytest test_api_endpoints.py -v --tb=short
        ;;
    5)
        echo -e "\n${BLUE}Setting up test user...${RESET}\n"
        python3 setup_test_user.py
        ;;
    *)
        echo -e "${RED}Invalid choice!${RESET}"
        exit 1
        ;;
esac

echo -e "\n${GREEN}╔════════════════════════════════════════════════════════╗${RESET}"
echo -e "${GREEN}║                    Test Run Complete!                   ║${RESET}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${RESET}\n"
