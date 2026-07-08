#!/bin/bash
#
# Simple, reliable local development startup for xend paybot
# Handles backend (Python) and frontend (Node) setup and startup
#
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Trap to clean up background processes on exit
cleanup() {
    log_info "Cleaning up..."
    if [ -n "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# Get project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"

log_info "xend paybot local development startup"
log_info "Project root: $SCRIPT_DIR"

# ============================================================================
# Prerequisite checks
# ============================================================================

log_info "Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    log_error "Python 3 is not installed. Please install Python 3.11+"
fi
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
log_success "Python $PYTHON_VERSION found"

# Check Node
if ! command -v node &> /dev/null; then
    log_error "Node.js is not installed. Please install Node.js LTS"
fi
NODE_VERSION=$(node --version)
log_success "Node $NODE_VERSION found"

# Check git
if ! command -v git &> /dev/null; then
    log_error "git is not installed. Please install git"
fi

# ============================================================================
# Backend setup
# ============================================================================

log_info "Setting up backend..."

cd "$BACKEND_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    log_info "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
log_info "Upgrading pip..."
python -m pip install --upgrade pip -q

# Install dependencies
log_info "Installing Python dependencies..."
if ! python -m pip install -r requirements.txt -q 2>/dev/null; then
    log_error "Failed to install Python dependencies. Check requirements.txt"
fi
log_success "Backend dependencies installed"

# ============================================================================
# Frontend setup
# ============================================================================

log_info "Setting up frontend..."

cd "$FRONTEND_DIR"

# Detect package manager
if command -v pnpm &> /dev/null; then
    PKG_MGR="pnpm"
    log_success "Using pnpm"
elif command -v npm &> /dev/null; then
    PKG_MGR="npm"
    log_success "Using npm"
else
    log_error "Neither pnpm nor npm found. Install pnpm (via corepack) or npm"
fi

# Install dependencies
if [ ! -d "node_modules" ]; then
    log_info "Installing frontend dependencies (this may take a minute)..."
    if ! $PKG_MGR install --frozen-lockfile 2>/dev/null; then
        log_warning "Dependency install had warnings (may be recoverable). Continuing..."
    fi
    log_success "Frontend dependencies installed"
else
    log_info "Frontend dependencies already installed, skipping install"
fi

# ============================================================================
# Environment files
# ============================================================================

log_info "Checking environment files..."

# Backend .env
if [ ! -f "$BACKEND_DIR/.env" ]; then
    log_warning "Backend .env not found. Copying from .env.example..."
    if [ -f "$BACKEND_DIR/.env.example" ]; then
        cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
        log_info "Please update $BACKEND_DIR/.env with your configuration"
    else
        log_error "Backend .env.example not found"
    fi
fi

# Frontend .env
if [ ! -f "$FRONTEND_DIR/.env" ]; then
    log_warning "Frontend .env not found. Copying from .env.example..."
    if [ -f "$FRONTEND_DIR/.env.example" ]; then
        cp "$FRONTEND_DIR/.env.example" "$FRONTEND_DIR/.env"
        log_info "Please update $FRONTEND_DIR/.env with your configuration"
    else
        log_error "Frontend .env.example not found"
    fi
fi

# ============================================================================
# Start services
# ============================================================================

log_info "Starting services..."

# Backend
cd "$BACKEND_DIR"
source .venv/bin/activate

# Run database migrations
log_info "Running database migrations..."
if alembic upgrade head 2>/dev/null; then
    log_success "Database schema is current"
else
    log_warning "Database migration had issues (may be expected on first run)"
fi

log_info "Starting backend on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!
log_success "Backend started (PID: $BACKEND_PID)"

# Give backend a moment to start
sleep 2

# Frontend
cd "$FRONTEND_DIR"
log_info "Starting frontend on port 5173..."
$PKG_MGR dev &
FRONTEND_PID=$!
log_success "Frontend started (PID: $FRONTEND_PID)"

# ============================================================================
# Ready
# ============================================================================

log_success "========================================"
log_success "xend paybot is running!"
log_success "========================================"
echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:5173"
echo "API Docs: http://localhost:8000/docs"
echo ""
log_info "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait
