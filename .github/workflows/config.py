import os

class Settings:
    app_name = os.getenv("APP_NAME", "JVM Technologies AI")
    ai_provider = os.getenv("AI_PROVIDER", "openai_compatible")
    ai_base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1")
    ai_api_key = os.getenv("AI_API_KEY", "")
    ai_model = os.getenv("AI_MODEL", "")
    ai_timeout_seconds = float(os.getenv("AI_TIMEOUT_SECONDS", "120"))

settings = Settings()
