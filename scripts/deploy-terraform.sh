#!/bin/bash
# Deploy infrastructure using Terraform
# Supports dry-run mode and workspace selection

set -euo pipefail

# Default values
TERRAFORM_DIR="${TERRAFORM_DIR:-terraform}"
DRY_RUN="${DRY_RUN:-false}"
TERRAFORM_WORKSPACE="${TERRAFORM_WORKSPACE:-}"

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

# Validate Terraform directory exists
if [ ! -d "$TERRAFORM_DIR" ]; then
    error "Terraform directory not found: $TERRAFORM_DIR"
    exit 1
fi

info "Starting Terraform deployment..."
info "Terraform directory: $TERRAFORM_DIR"
if [ -n "$TERRAFORM_WORKSPACE" ]; then
    info "Workspace: $TERRAFORM_WORKSPACE"
fi
if [ "$DRY_RUN" = "true" ]; then
    warning "DRY RUN MODE - No changes will be applied"
fi
echo ""

# Change to Terraform directory
cd "$TERRAFORM_DIR"

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    info "Initializing Terraform..."
    if terraform init; then
        success "Terraform initialization successful"
    else
        error "Terraform initialization failed"
        exit 1
    fi
    echo ""
fi

# Select workspace if specified
if [ -n "$TERRAFORM_WORKSPACE" ]; then
    info "Selecting Terraform workspace: $TERRAFORM_WORKSPACE"
    if terraform workspace select "$TERRAFORM_WORKSPACE" 2>/dev/null || \
       terraform workspace new "$TERRAFORM_WORKSPACE"; then
        success "Workspace selected: $TERRAFORM_WORKSPACE"
    else
        error "Failed to select workspace: $TERRAFORM_WORKSPACE"
        exit 1
    fi
    echo ""
fi

# Run Terraform plan
info "Running Terraform plan..."
if terraform plan -out=tfplan; then
    success "Terraform plan successful"
else
    error "Terraform plan failed"
    exit 1
fi
echo ""

# Apply changes (unless dry run)
if [ "$DRY_RUN" = "true" ]; then
    warning "Dry run mode - skipping terraform apply"
    info "Review the plan above. To apply, run without DRY_RUN=true"
    success "Dry run complete"
else
    info "Applying Terraform changes..."
    if terraform apply tfplan; then
        success "Terraform apply successful"
        # Clean up plan file
        rm -f tfplan
    else
        error "Terraform apply failed"
        exit 1
    fi
fi

success "Terraform deployment complete"
