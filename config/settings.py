from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    database_url: str = Field(
        default="postgresql://neo_user:neo_password@localhost:5432/neo_sousse"
    )

    # LLM
    openai_api_key: str = Field(default="")
    use_mock_llm: bool = Field(default=False)
    openai_model: str = Field(default="gpt-4o-mini")
    openai_base_url: str = Field(default="")

    # FSM behavior
    hors_service_alert_delay_seconds: int = Field(default=86400)
    fsm_history_enabled: bool = Field(default=True)

    # Features
    timescale_enabled: bool = Field(default=True)

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
