import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "Aquaculture Intelligence System"
    APP_ENV: str = "development"
    SECRET_KEY: str = "default_secret_key"
    DEBUG: bool = True

    # Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "ais_admin"
    DB_PASSWORD: str = "ais_password_123"
    DB_NAME: str = "ais_db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_TOPIC_PREFIX: str = "pond"

    # MinIO S3
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minio_admin"
    MINIO_SECRET_KEY: str = "minio_secret_password"
    MINIO_BUCKET_NAME: str = "ais-storage"

    # Gen AI Provider (Flexible / Configurable)
    LLM_PROVIDER: str = "configurable"
    LLM_API_KEY: str = ""
    LLM_MODEL_NAME: str = "gpt-4o-or-claude-3-5-sonnet"

    # Model Registry
    MODEL_REGISTRY_DIR: str = "./models/registry"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

settings = Settings()
