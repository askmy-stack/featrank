"""Global settings loaded from environment variables via pydantic-settings."""

from __future__ import annotations

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    groq_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    llm_provider: str = "groq"
    llm_model: str = "llama-3.3-70b-versatile"
    ollama_model: str = "gemma3:4b"

    # Embeddings
    embedding_model: str = "all-mpnet-base-v2"
    embedding_batch_size: int = 64
    cache_dir: str = ".cache/embeddings"

    # GitHub
    github_token: str = ""
    github_repo: str = ""

    # Intercom
    intercom_token: str = ""

    # Zendesk
    zendesk_subdomain: str = ""
    zendesk_email: str = ""
    zendesk_api_token: str = ""

    # Scoring weights
    weight_frequency: float = 0.20
    weight_segment_value: float = 0.40
    weight_github_signal: float = 0.20
    weight_roadmap_fit: float = 0.20

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # HDBSCAN
    hdbscan_min_cluster_size: int = 5
    hdbscan_min_samples: int = 3
    hdbscan_metric: str = "euclidean"
    hdbscan_cluster_selection_epsilon: float = 0.3

    @model_validator(mode="after")
    def weights_must_sum_to_one(self) -> "Settings":
        total = round(
            self.weight_frequency
            + self.weight_segment_value
            + self.weight_github_signal
            + self.weight_roadmap_fit,
            6,
        )
        if abs(total - 1.0) > 1e-4:
            raise ValueError(
                f"Scoring weights must sum to 1.0, got {total}. "
                "Check WEIGHT_* env vars."
            )
        return self

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        allowed = {"groq", "ollama"}
        if v not in allowed:
            raise ValueError(f"llm_provider must be one of {allowed}, got '{v}'")
        return v


settings = Settings()
