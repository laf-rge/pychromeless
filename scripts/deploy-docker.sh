#!/bin/bash
# Deploy Docker image to ECR
# Handles ECR login, build, tag, and push operations

set -euo pipefail

# Default values (can be overridden by environment variables)
ECR_REGISTRY="${ECR_REGISTRY:-262877227567.dkr.ecr.us-east-2.amazonaws.com}"
ECR_REPOSITORY="${ECR_REPOSITORY:-wmc}"
AWS_REGION="${AWS_REGION:-us-east-2}"
DOCKER_IMAGE_TAG="${DOCKER_IMAGE_TAG:-latest}"
DOCKER_PLATFORM="${DOCKER_PLATFORM:-linux/amd64}"

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

info "Starting Docker deployment..."
info "ECR Registry: $ECR_REGISTRY"
info "Repository: $ECR_REPOSITORY"
info "Region: $AWS_REGION"
info "Tag: $DOCKER_IMAGE_TAG"
info "Platform: $DOCKER_PLATFORM"
echo ""

# Step 1: ECR Login
info "Logging into ECR..."
if aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$ECR_REGISTRY"; then
    success "ECR login successful"
else
    error "ECR login failed"
    exit 1
fi
echo ""

# Step 2: Docker Build
info "Building Docker image..."
info "Image: $ECR_REGISTRY/$ECR_REPOSITORY:$DOCKER_IMAGE_TAG"
if DOCKER_BUILDKIT=1 docker build \
    --platform "$DOCKER_PLATFORM" \
    -t "$ECR_REPOSITORY:$DOCKER_IMAGE_TAG" \
    --no-cache \
    .; then
    success "Docker build successful"
else
    error "Docker build failed"
    exit 1
fi
echo ""

# Step 3: Docker Tag
info "Tagging Docker image..."
FULL_IMAGE_NAME="$ECR_REGISTRY/$ECR_REPOSITORY:$DOCKER_IMAGE_TAG"
if docker tag "$ECR_REPOSITORY:$DOCKER_IMAGE_TAG" "$FULL_IMAGE_NAME"; then
    success "Docker tag successful: $FULL_IMAGE_NAME"
else
    error "Docker tag failed"
    exit 1
fi
echo ""

# Step 4: Docker Push
info "Pushing Docker image to ECR..."
if docker push "$FULL_IMAGE_NAME"; then
    success "Docker push successful"
    success "Deployment complete: $FULL_IMAGE_NAME"
else
    error "Docker push failed"
    exit 1
fi
