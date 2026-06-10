from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://ids_user:change_me@postgres:5432/ids"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_key: str = "dev-insecure-change-in-production"
    model_registry_path: Path = Path("/data/models")
    training_data_path: Path = Path("/data/raw/training_data.parquet")
    random_seed: int = 42
    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
