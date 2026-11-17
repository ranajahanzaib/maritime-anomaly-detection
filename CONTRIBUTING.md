# Contributing to Vessel Behavior Analysis

Thank you for your interest in contributing to the Vessel Behavior Analysis platform! We welcome contributions from researchers, geospatial engineers, data scientists, and frontend developers.

## Development Setup

### Prerequisites

- Python 3.12+ (Python 3.13 supported)
- [uv](https://docs.astral.sh/uv/) for high-performance Python package management
- Node.js 20+ and [pnpm](https://pnpm.io/) (v9 or v10)
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/ranajahanzaib/maritime-anomaly-detection.git
cd maritime-anomaly-detection
```

### 2. Backend Environment Setup

Create a virtual environment and install the package along with development dependencies:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Initialize the local analytical SQLite database and generate the deterministic synthetic demonstration dataset:

```bash
python scripts/generate_demo_data.py
```

### 3. Frontend Environment Setup

Install frontend dependencies using `pnpm`:

```bash
cd frontend
pnpm install
cd ..
```

---

## Running the Application Locally

Start the backend API server (runs on `http://localhost:8000`):

```bash
uvicorn backend.app.main:app --reload --port 8000
```

In a separate terminal, start the Next.js development server (runs on `http://localhost:3000`):

```bash
cd frontend
pnpm run dev
```

Alternatively, run the complete stack via Docker Compose:

```bash
docker compose up --build
```

---

## Testing & Quality Assurance

Before submitting any code, verify that all unit and integration tests pass and that the frontend compiles cleanly:

```bash
# Run pytest test suite (21 unit, integration, and E2E tests)
pytest

# Type-check and build Next.js frontend
cd frontend
pnpm run build
cd ..
```

---

## Making Changes

1. **Create a Topic Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. **Follow Code Conventions:**
   - Follow PEP 8 guidelines for Python code.
   - Use explicit type annotations on public functions and classes.
   - For detection rules, provide quantitative `evidence_payload` dictionaries and operational zone context.
   - For UI changes, ensure responsive layouts and consistent Tailwind dark-theme styling.
3. **Add Tests:** Include unit tests under `tests/unit/` or integration tests under `tests/integration/` for any new functionality.
4. **Commit Your Work:** Use clear, descriptive commit messages adhering to standard conventional commit prefixes (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`).
5. **Open a Pull Request:** Open a PR against the `main` branch with a summary of changes, motivation, and evidence of passed test suites.

---

## Code of Conduct

All contributors are expected to uphold our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior through our security or issue channels.
