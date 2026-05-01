"""Settings — loaded from .env and environment variables.

Single source of truth for all runtime configuration. Used by CLI, services,
backends. Never read os.environ directly elsewhere — go through Settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Top-level settings, loaded from .env at startup."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="FACTORY_",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Postgres ----------------------------------------------------------
    postgres_user: str = "factory"
    postgres_password: str = "factory_dev_password_change_me"
    postgres_db: str = "factory"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # --- MinIO -------------------------------------------------------------
    minio_endpoint: str = "http://localhost:9000"
    minio_access_key: str = "factory"
    minio_secret_key: str = "factory_dev_password_change_me"
    minio_bucket_dvc: str = "factory-dvc"
    minio_bucket_mlflow: str = "factory-mlflow"
    minio_bucket_trajectories: str = "factory-trajectories"

    # --- Prefect / MLflow --------------------------------------------------
    prefect_api_url: str = "http://localhost:4200/api"
    mlflow_tracking_uri: str = "http://localhost:5000"

    # --- Hardware budgets (NFR-15) ----------------------------------------
    gpu_min_free_vram_gb: float = 20.0
    gpu_max_batch_fallback_steps: int = Field(default=3, ge=1, le=10)
    disk_trajectory_retention_days: int = Field(default=7, ge=0)

    # --- HPC backend ------------------------------------------------------
    backend: str = Field(default="local", description="local | slurm | runpod | aws_batch | lumi")

    # --- IP / patent flags ------------------------------------------------
    ip_mode: str = Field(default="open", description="open | hybrid")

    # --- Workspace --------------------------------------------------------
    workspace_dir: Path = Field(default=Path.home() / "sinanofactory")

    @property
    def postgres_dsn(self) -> str:
        """SQLAlchemy-compatible Postgres DSN."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings accessor. Override in tests via:

    >>> from sinanofactory.config import get_settings
    >>> get_settings.cache_clear()
    """
    return Settings()


__all__ = ["Settings", "get_settings"]
