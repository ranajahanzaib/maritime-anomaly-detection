from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Vessel Behavior Analysis"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database: SQLite by default for zero-friction standalone run, Postgres/PostGIS in production/Docker
    DATABASE_URL: str = "sqlite:///./data/vessel_behavior.db"

    # Base paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    STORAGE_DIR: Path = Path("./data/storage")
    MODELS_DIR: Path = Path("./data/models")
    DEMO_DATA_DIR: Path = Path("./data/demo")

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Trajectory & Ingestion parameters
    MAX_TIME_GAP_MINUTES: float = 45.0
    MIN_OBSERVATIONS_PER_TRAJECTORY: int = 5
    SIMPLIFICATION_TOLERANCE_DEG: float = 0.0005
    MAX_PLAUSIBLE_SPEED_KNOTS: float = 55.0
    MAX_PLAUSIBLE_ACCELERATION_MS2: float = 4.0

    # Worker parameters
    WORKER_CONCURRENCY: int = 2
    WORKER_POLL_INTERVAL_SECONDS: float = 1.0


settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)
settings.DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
