from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MeetLens"
    host: str = "0.0.0.0"
    port: int = 8000
    database_url: str = "sqlite:///./data/meetlens.db"
    llm_base_url: str = "http://localhost:8001/v1"
    llm_model: str = "deepseek-ai/DeepSeek-V4-Flash"
    llm_api_key: str = "local"
    llm_timeout_seconds: int = 120
    max_candidates_per_cluster: int = 2
    question_similarity_threshold: float = 0.82
    privacy_mode: str = "strict"
    enable_asr: bool = False
    enable_diarization: bool = False
    asr_model: str = "small"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")

    @property
    def data_dir(self) -> Path:
        return Path("data")


@lru_cache

def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
