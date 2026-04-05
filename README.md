<<<<<<< HEAD
# PQCC (Post Quantum Cryptography Checker)

PQCC is a full-stack platform that helps security and infrastructure teams assess cryptographic risk, generate CBOM intelligence, and plan migration toward post-quantum cryptography (PQC).

## Description

The project combines a React dashboard, a FastAPI backend, asynchronous workers, and data services to provide operational visibility for cryptography posture in enterprise environments. It supports asset discovery, TLS scan intelligence, CBOM tracking, risk scoring, compliance workflows, and graph-based attack path analysis.

## Project Type

- Full-stack application
- Frontend: React + TypeScript + Vite
- Backend: Python + FastAPI
- Data/Infra: PostgreSQL, Neo4j, Redis, Celery, Docker Compose, Kubernetes manifests

## Key Features

- Asset inventory and scan orchestration
- TLS/SSL metadata and cryptographic posture collection
- CBOM (Cryptography Bill of Materials) analysis
- Risk scoring and readiness insights
- Compliance playbooks and approval gate workflows
- Graph-based topology/attack path support
- Real-time and batch processing with Celery workers

## Tech Stack

### Frontend
- React 18
- TypeScript
- Vite
- Tailwind CSS
- React Router
- D3 / Chart.js

### Backend
- FastAPI
- SQLAlchemy + Alembic
- Pydantic
- Celery + Redis
- Neo4j driver
- Structlog

### Platform / DevOps
- Docker / Docker Compose
- Kubernetes manifests (worker deployment + HPA)
- Nginx config for reverse proxying

## Repository Structure

```text
backend/         FastAPI app, models, services, workers, tests
frontend/        React dashboard application
ml_engine/       ML utilities (forecasting, clustering, graph analysis)
k8s/             Kubernetes manifests for runtime scaling
deploy/          Deployment configs (nginx, infra scripts)
UI_WIREFRAMES/   Design reference screens
```

## Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker and Docker Compose (recommended for integrated setup)

### 1) Clone

```bash
git clone https://github.com/shwetagore16/PQCC.git
cd PQCC
```

### 2) Backend setup

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3) Frontend setup

```bash
cd ../frontend
npm install
```

### 4) Environment

Create a `.env` file for backend/runtime secrets. Do not commit `.env`.

## Usage

### Option A: Local development

Start backend:

```bash
cd backend
python dev_server.py
```

Start frontend:

```bash
cd frontend
npm run dev
```

### Option B: Containerized stack

```bash
docker compose up --build
```

## API Endpoints

Base API prefix: `/api/v1`

- `GET /health` - Service health
- `GET /api/v1/assets` - List assets
- `POST /api/v1/assets` - Create asset
- `POST /api/v1/assets/{asset_id}/scan` - Trigger scan
- `GET /api/v1/cbom/*` - CBOM-related routes
- `GET /api/v1/compliance/*` - Compliance routes
- `GET /api/v1/topology/*` - Topology/graph routes
- `GET /api/v1/dev/*` - Development/helper routes

Interactive docs (when backend is running):

- `/api/v1/docs`
- `/api/v1/redoc`

## Security Notes

- `.env` and secret files are excluded by `.gitignore`.
- Keep database credentials, tokens, and API keys in environment variables only.
- Rotate credentials before production deployments.

## Future Scope (PQC Engine Improvements)

- Expand algorithm fingerprinting for deeper CBOM fidelity
- Add automated crypto-agility recommendations by asset criticality
- Integrate NIST PQC migration pathways and control mappings
- Improve attack-path scoring using temporal graph learning
- Add confidence scoring and explainability outputs for ML results
- Introduce policy-as-code checks for PQC readiness gates

## License

Add your preferred license in this repository (MIT/Apache-2.0/Proprietary).
=======
# PQCC
>>>>>>> origin/main
