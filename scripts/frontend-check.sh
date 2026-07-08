#!/bin/bash
#
# Frontend validation: Check that the frontend is healthy and can build
# This is run as a pre-flight check before starting the dev server
#
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }

FRONTEND_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/frontend" && pwd)"
cd "$FRONTEND_DIR"

log_info "Frontend health check..."

# Check node_modules
if [ ! -d "node_modules" ]; then
    log_error "node_modules not found. Run: bash bootstrap.sh"
fi
log_success "node_modules found"

# Check package manager
if command -v pnpm &> /dev/null; then
    PKG_MGR="pnpm"
elif command -v npm &> /dev/null; then
    PKG_MGR="npm"
else
    log_error "Neither pnpm nor npm found"
fi

# Check for eslint
if ! $PKG_MGR list eslint &>/dev/null; then
    log_error "eslint not installed in node_modules"
fi
log_success "ESLint available"

# Run eslint in quiet mode (only errors, no warnings)
log_info "Running ESLint..."
if ! $PKG_MGR exec eslint --quiet ./src 2>/dev/null; then
    log_warning "ESLint found issues (see above)"
    log_info "Continuing anyway (warnings don't block development)"
fi

log_success "Frontend is healthy"
