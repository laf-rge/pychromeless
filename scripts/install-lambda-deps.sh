#!/bin/bash
# Install Lambda function dependencies
# Installs Python packages for Lambda runtime environment (Linux x86_64)

set -euo pipefail

# Default values
BUILD_DIR="${BUILD_DIR:-build}"
PIP_PLATFORM="${PIP_PLATFORM:-manylinux2014_x86_64}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Change to project root
cd "$PROJECT_ROOT"

info "Installing Lambda dependencies..."
info "Build directory: $BUILD_DIR"
info "Platform: $PIP_PLATFORM"
echo ""

# Create build directory if it doesn't exist
if [ ! -d "$BUILD_DIR" ]; then
    info "Creating build directory: $BUILD_DIR"
    mkdir -p "$BUILD_DIR"
fi

# Change to build directory
cd "$BUILD_DIR"

# Lambda dependencies to install
LAMBDA_DEPS=(
    "pyjwt"
    "cryptography"
    "cffi"
)

info "Installing dependencies for Lambda runtime..."
info "Dependencies: ${LAMBDA_DEPS[*]}"
echo ""

# Install dependencies
if pip install --upgrade \
    --platform "$PIP_PLATFORM" \
    --only-binary :all: \
    --implementation cp \
    --target ./ \
    "${LAMBDA_DEPS[@]}"; then
    success "Lambda dependencies installed successfully"
else
    error "Failed to install Lambda dependencies"
    exit 1
fi

success "Lambda dependency installation complete"
