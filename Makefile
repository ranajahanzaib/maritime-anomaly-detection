.PHONY: setup demo train evaluate test run-backend run-frontend up down clean

setup:
	uv venv
	uv pip install -e ".[dev]"
	cd frontend && pnpm install

demo:
	PYTHONPATH=. .venv/bin/python scripts/generate_demo_data.py

train:
	PYTHONPATH=. .venv/bin/python scripts/train_model.py TCN_AUTOENCODER

evaluate:
	PYTHONPATH=. .venv/bin/python scripts/run_evaluation.py

test:
	PYTHONPATH=. .venv/bin/pytest tests/ -v

run-backend:
	PYTHONPATH=. .venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && pnpm run dev

up:
	docker compose up --build

down:
	docker compose down

clean:
	rm -rf data/storage/* data/models/* data/vessel_behavior.db
