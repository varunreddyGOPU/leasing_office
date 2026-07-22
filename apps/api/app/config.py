from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://auburn:auburn@localhost:5432/auburn_ridge"
    redis_url: str = "redis://localhost:6379/0"

    ollama_api_key: str = ""
    ollama_url: str = "https://ollama.com/api/chat"
    ollama_model: str = "llama3.1:70b"

    news_api_key: str = ""
    sentry_dsn: str = ""
    environment: str = "development"

    secret_key: str = "dev-secret-change-me"
    admin_api_key: str = "dev-admin"
    upload_dir: str = "./uploads"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
