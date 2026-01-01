#!/bin/bash
# Deploy frontend to Namecheap server via SSH/rsync
# Retrieves deployment configuration from AWS SSM Parameter Store

set -euo pipefail

# Default values
DEPLOY_ENV="${DEPLOY_ENV:-prod}"
FRONTEND_DIR="${FRONTEND_DIR:-frontend/dist}"
SSH_KEY_TEMP_DIR="${SSH_KEY_TEMP_DIR:-/tmp}"

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

# Validate frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    error "Frontend build directory not found: $FRONTEND_DIR"
    error "Please run 'make frontend-build' first"
    exit 1
fi

info "Deploying frontend to Namecheap..."
info "Environment: $DEPLOY_ENV"
info "Source directory: $FRONTEND_DIR"
echo ""

# Function to get SSM parameter
get_ssm_parameter() {
    local param_name=$1
    local param_value

    param_value=$(aws ssm get-parameter \
        --name "$param_name" \
        --query "Parameter.Value" \
        --output text 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$param_value" ]; then
        error "Failed to retrieve SSM parameter: $param_name"
        exit 1
    fi

    echo "$param_value"
}

# Function to get SSM parameter with decryption
get_ssm_parameter_secure() {
    local param_name=$1
    local param_value

    param_value=$(aws ssm get-parameter \
        --name "$param_name" \
        --with-decryption \
        --query "Parameter.Value" \
        --output text 2>/dev/null)

    if [ $? -ne 0 ] || [ -z "$param_value" ]; then
        error "Failed to retrieve SSM parameter: $param_name"
        exit 1
    fi

    echo "$param_value"
}

# Retrieve deployment configuration from SSM
info "Retrieving deployment configuration from AWS SSM..."
HOST=$(get_ssm_parameter "/${DEPLOY_ENV}/frontend/namecheap/host")
REMOTE_USER=$(get_ssm_parameter "/${DEPLOY_ENV}/frontend/namecheap/user")
REMOTE_PATH=$(get_ssm_parameter "/${DEPLOY_ENV}/frontend/namecheap/path")
PORT=$(get_ssm_parameter "/${DEPLOY_ENV}/frontend/namecheap/port")
SSH_KEY=$(get_ssm_parameter_secure "/${DEPLOY_ENV}/frontend/namecheap/ssh_key")

success "Configuration retrieved"
info "Host: $HOST"
info "User: $REMOTE_USER"
info "Path: $REMOTE_PATH"
info "Port: $PORT"
echo ""

# Create temporary SSH key file
KEY_FILE=$(mktemp "${SSH_KEY_TEMP_DIR}/deploy_key_XXXXXX")
trap "rm -f '$KEY_FILE'" EXIT INT TERM

info "Creating temporary SSH key file..."
echo "$SSH_KEY" > "$KEY_FILE"
chmod 600 "$KEY_FILE"
success "SSH key file created: $KEY_FILE"
echo ""

# Deploy using rsync
info "Deploying files via rsync..."
info "Source: $FRONTEND_DIR/"
info "Destination: $REMOTE_USER@$HOST:$REMOTE_PATH/"
echo ""

if rsync -avz --delete \
    -e "ssh -i $KEY_FILE -p $PORT -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null" \
    "$FRONTEND_DIR/" \
    "$REMOTE_USER@$HOST:$REMOTE_PATH/"; then
    success "Deployment successful"
    success "Deployed to $HOST:$REMOTE_PATH"
else
    error "Deployment failed"
    exit 1
fi

# Cleanup is handled by trap
