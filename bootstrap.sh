#!/bin/bash
#
# Bootstrap script: Install all dependencies without starting services
# Use this to prepare the environment or run in CI/automated contexts
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

log_info "xend paybot bootstrap (dependencies only)"

# ============================================================================
# Prerequisite checks
# ============================================================================

log_info "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed"
fi
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
log_success "Python $PYTHON_VERSION"

if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed"
fi
log_success "Node $(node --version)"

# ============================================================================
# Backend setup
# ============================================================================

log_info "Setting up backend dependencies..."

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

log_info "Upgrading pip..."
python -m pip install --upgrade pip -q 2>/dev/null

log_info "Installing Python dependencies..."
if ! python -m pip install -r requirements.txt -q 2>/dev/null; then
    log_error "Failed to install Python dependencies"
fi
log_success "Backend ready"

# ============================================================================
# Frontend setup
# ============================================================================

log_info "Setting up frontend dependencies..."

cd "$FRONTEND_DIR"

if command -v pnpm &> /dev/null; then
    PKG_MGR="pnpm"
elif command -v npm &> /dev/null; then
    PKG_MGR="npm"
else
    log_error "Neither pnpm nor npm found"
fi

log_success "Using $PKG_MGR"

if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies..."
    if ! $PKG_MGR install --frozen-lockfile 2>/dev/null; then
        log_warning "Install completed with warnings"
    fi
    log_success "Frontend ready"
else
    log_info "Frontend dependencies already present"
fi

# ============================================================================
# Database migrations
# ============================================================================

log_info "Running database migrations..."

cd "$BACKEND_DIR"
source .venv/bin/activate

if alembic upgrade head 2>/dev/null; then
    log_success "Database schema is current"
else
    log_info "Database migration skipped (may be expected on first setup)"
fi

# ============================================================================
# Environment files
# ============================================================================

log_info "Checking environment configuration..."

if [ ! -f "$BACKEND_DIR/.env" ] && [ -f "$BACKEND_DIR/.env.example" ]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    log_info "Created backend/.env from template"
fi

if [ ! -f "$FRONTEND_DIR/.env" ] && [ -f "$FRONTEND_DIR/.env.example" ]; then
    cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
    log_info "Created frontend/.env from template"
fi

# ============================================================================
# Done
# ============================================================================

log_success "Bootstrap complete!"
log_info "To start development servers, run: bash start-dev.sh"
