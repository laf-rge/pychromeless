#!/bin/bash
# Check for required development and deployment tools
# Exit with error code if any prerequisite is missing

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# Function to check if a command exists
check_command() {
    local cmd=$1
    local name=$2
    local required=${3:-true}

    if command -v "$cmd" >/dev/null 2>&1; then
        local version
        version=$($cmd --version 2>&1 | head -n 1)
        echo -e "${GREEN}✓${NC} $name found: $version"
        return 0
    else
        if [ "$required" = "true" ]; then
            echo -e "${RED}✗${NC} $name not found"
            echo "  Install: $4"
            ERRORS=$((ERRORS + 1))
        else
            echo -e "${YELLOW}⚠${NC} $name not found (optional)"
            echo "  Install: $4"
            WARNINGS=$((WARNINGS + 1))
        fi
        return 1
    fi
}

# Function to check Python version
check_python() {
    if command -v python3 >/dev/null 2>&1; then
        local version
        version=$(python3 --version 2>&1)
        local major minor
        major=$(echo "$version" | sed -E 's/Python ([0-9]+)\.[0-9]+\.[0-9]+/\1/')
        minor=$(echo "$version" | sed -E 's/Python [0-9]+\.([0-9]+)\.[0-9]+/\1/')

        if [ "$major" -ge 3 ] && [ "$minor" -ge 11 ]; then
            echo -e "${GREEN}✓${NC} Python found: $version (>= 3.11 required)"
            return 0
        else
            echo -e "${RED}✗${NC} Python version too old: $version (>= 3.11 required)"
            echo "  Upgrade Python: https://www.python.org/downloads/"
            ERRORS=$((ERRORS + 1))
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Python 3 not found"
        echo "  Install: https://www.python.org/downloads/"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check pip
check_pip() {
    if command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1; then
        local pip_cmd
        pip_cmd=$(command -v pip3 || command -v pip)
        local version
        version=$($pip_cmd --version 2>&1)
        echo -e "${GREEN}✓${NC} pip found: $version"
        return 0
    else
        echo -e "${RED}✗${NC} pip not found"
        echo "  Install: python3 -m ensurepip --upgrade"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check Docker
check_docker() {
    if command -v docker >/dev/null 2>&1; then
        local version
        version=$(docker --version 2>&1)
        echo -e "${GREEN}✓${NC} Docker found: $version"

        # Check if Docker daemon is running
        if docker info >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Docker daemon is running"
            return 0
        else
            echo -e "${RED}✗${NC} Docker daemon is not running"
            echo "  Start Docker: https://docs.docker.com/get-docker/"
            ERRORS=$((ERRORS + 1))
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Docker not found"
        echo "  Install: https://docs.docker.com/get-docker/"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check AWS CLI
check_aws_cli() {
    if command -v aws >/dev/null 2>&1; then
        local version
        version=$(aws --version 2>&1)
        echo -e "${GREEN}✓${NC} AWS CLI found: $version"

        # Check if AWS credentials are configured
        if aws sts get-caller-identity >/dev/null 2>&1; then
            local account_id
            account_id=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
            echo -e "${GREEN}✓${NC} AWS credentials configured (Account: $account_id)"
            return 0
        else
            echo -e "${YELLOW}⚠${NC} AWS CLI found but credentials not configured"
            echo "  Configure: aws configure"
            WARNINGS=$((WARNINGS + 1))
            return 1
        fi
    else
        echo -e "${RED}✗${NC} AWS CLI not found"
        echo "  Install: https://aws.amazon.com/cli/"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check Terraform
check_terraform() {
    if command -v terraform >/dev/null 2>&1; then
        local version
        version=$(terraform --version 2>&1 | head -n 1)
        echo -e "${GREEN}✓${NC} Terraform found: $version"
        return 0
    else
        echo -e "${RED}✗${NC} Terraform not found"
        echo "  Install: https://www.terraform.io/downloads"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Function to check Bun
check_bun() {
    if command -v bun >/dev/null 2>&1; then
        local version
        version=$(bun --version 2>&1)
        local major
        major=$(echo "$version" | cut -d. -f1)

        if [ "$major" -ge 1 ]; then
            echo -e "${GREEN}✓${NC} Bun found: v$version (>= 1.0.0 required)"
            return 0
        else
            echo -e "${RED}✗${NC} Bun version too old: v$version (>= 1.0.0 required)"
            echo "  Upgrade: https://bun.sh/docs/installation"
            ERRORS=$((ERRORS + 1))
            return 1
        fi
    else
        echo -e "${RED}✗${NC} Bun not found"
        echo "  Install: https://bun.sh/docs/installation"
        ERRORS=$((ERRORS + 1))
        return 1
    fi
}

# Main execution
echo "Checking prerequisites..."
echo ""

# Required for all operations
echo "=== Core Requirements ==="
check_python
check_pip

# Required for deployment
echo ""
echo "=== Deployment Requirements ==="
check_docker
check_aws_cli
check_terraform

# Required for frontend
echo ""
echo "=== Frontend Requirements ==="
check_bun

# Summary
echo ""
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}All prerequisites satisfied!${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}Prerequisites satisfied with $WARNINGS warning(s)${NC}"
    exit 0
else
    echo -e "${RED}Found $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo "Please install missing prerequisites before continuing."
    exit 1
fi
