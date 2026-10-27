from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "JVM Technologies AI"
    jwt_secret: str = "change-this-secret"
    access_token_expire_minutes: int = 1440
    database_url: str = "sqlite:///./jvm_ai.db"
    ai_provider: str = "ollama"
    ai_base_url: str = "http://localhost:11434"
    ai_api_key: str = ""
    ai_model: str = "llama3.2"
    ai_timeout_seconds: int = 120
    cors_origins: str = "http://localhost:8000,http://127.0.0.1:8000"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
