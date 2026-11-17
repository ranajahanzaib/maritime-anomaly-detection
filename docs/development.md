# Local Development & Engineering Guide

This guide describes how to run and test the complete platform locally without cloud dependencies.

---

## Prerequisites

- **Python:** 3.12+ (tested on Python 3.12 and 3.13)
- **Node.js:** v20+ or v22+
- **pnpm:** v9+ or v10+
- **uv:** (recommended Python package manager)

---

## Quickstart

```bash
# 1. Setup virtual environment & dependencies
make setup

# 2. Generate deterministic synthetic demonstration dataset
make demo

# 3. Train the Temporal Convolutional Autoencoder
make train

# 4. Run automated test suite
make test

# 5. Start Backend API Server (Port 8000)
make run-backend

# 6. Start Frontend Web Interface (Port 3000 in a separate terminal)
make run-frontend
```

---

## Running with Docker Compose

To run the complete platform including PostgreSQL/PostGIS:

```bash
docker compose up --build
```

- Web UI: http://localhost:3000
- API Docs: http://localhost:8000/api/v1/docs
