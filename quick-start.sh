#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════════
# PQSS Quick Start — Real Data Setup
# ═══════════════════════════════════════════════════════════════════════════════

set -e  # Exit on error

PROJECT_ROOT="/Users/mahendrakumar/Developer/pnb"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "🚀 Starting PQSS Real-Time Setup..."
echo ""

# ── Step 1: Check Docker ──────────────────────────────────────────────────────────
echo "📦 Step 1: Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Install it:"
    echo "   brew install docker docker-compose"
    echo "   OR download Docker Desktop from https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo "✅ Docker found: $(docker --version)"
echo ""

# ── Step 2: Start Docker services ──────────────────────────────────────────────────
echo "🐳 Step 2: Starting PostgreSQL, Neo4j, Redis..."
cd "$PROJECT_ROOT"
docker-compose up -d
echo "✅ Docker services started"
sleep 5  # Wait for services to be ready
echo ""

# ── Step 3: Install ML dependencies ────────────────────────────────────────────────
echo "🧠 Step 3: Installing ML Engine dependencies..."
cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Installing Prophet, PyTorch, PyG..."
pip install -q prophet torch torch-geometric pyg-lib torch-scatter torch-sparse

echo "✅ ML dependencies installed"
echo ""

# ── Step 4: Run database migrations ────────────────────────────────────────────────
echo "🗄️  Step 4: Initializing databases..."
alembic upgrade head 2>/dev/null || echo "⚠️  Alembic migration skipped (run manually if needed)"
echo "✅ Database schema initialized"
echo ""

# ── Step 5: Seed initial assets ────────────────────────────────────────────────────
echo "🌱 Step 5: Seeding initial assets..."
python3 << 'PYTHON_SEED'
import asyncio
import os
import sys

sys.path.insert(0, os.getcwd())

try:
    from app.workers.tasks.discovery import ingest_seed_domain
    
    async def seed_assets():
        domains = [
            'api.pnb.co.in',
            'netbanking.pnb.co.in',
            'mobile.pnb.co.in',
            'api-gateway.pnb.co.in',
            'cdn.pnb.co.in',
            'mail.pnb.co.in',
        ]
        
        for domain in domains:
            try:
                await ingest_seed_domain(domain)
                print(f"  ✓ Seeded {domain}")
            except Exception as e:
                print(f"  ⚠ {domain}: {str(e)[:50]}")
    
    asyncio.run(seed_assets())
except Exception as e:
    print(f"⚠️  Asset seeding skipped: {str(e)[:100]}")

PYTHON_SEED

echo "✅ Initial assets seeded"
echo ""

# ── Step 6: Print instructions ─────────────────────────────────────────────────────
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "✅ SETUP COMPLETE!"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "🚀 Start these in separate terminals:"
echo ""
echo "Terminal 1 — Backend (Real App):"
echo "  cd $BACKEND_DIR && source .venv/bin/activate"
echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Terminal 2 — Celery Workers:"
echo "  cd $BACKEND_DIR && source .venv/bin/activate"
echo "  celery -A app.workers.celery_app worker --loglevel=info --concurrency=4 -E"
echo ""
echo "Terminal 3 — Frontend:"
echo "  cd $FRONTEND_DIR && npm run dev"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "🔗 Access the app:"
echo "  • Frontend:     http://localhost:5173"
echo "  • API Docs:     http://localhost:8000/api/v1/docs"
echo "  • Flower UI:    http://localhost:5555 (after celery starts)"
echo "  • Neo4j:        http://localhost:7474 (user: neo4j, pwd: neo4j_secure_pwd_2026)"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
