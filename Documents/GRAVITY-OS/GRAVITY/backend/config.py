from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://gravity:gravity_dev@localhost:5432/gravity"
    redis_url: str = "redis://localhost:6379"
    secret_key: str = "gravity-dev-secret-change-in-prod"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080
    ai_provider: str = "groq"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    debug: bool = True
    app_name: str = "Gravity API"
    # MinIO object storage
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "gravity"
    minio_secret_key: str = "gravity_dev_minio"
    minio_secure: bool = False
    minio_bucket: str = "gravity-files"

    class Config:
        env_file = ".env"
        extra = "allow"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
