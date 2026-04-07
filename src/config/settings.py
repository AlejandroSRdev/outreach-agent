from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    port: int = 8000
    environment: str = "development"
    log_level: str = "INFO"
    openai_api_key: str
    max_concurrent_pipelines: int = 10
    max_batch_size: int = 20
    research_timeout_s: int = 30
    generation_timeout_s: int = 30
    refinement_timeout_s: int = 20


settings = Settings()
