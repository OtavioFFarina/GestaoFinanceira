"""
Application settings — reads from environment variables or .env file.
Uses pydantic-settings for type-safe config management (SOLID: Single Responsibility).
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── MySQL Connection ─────────────────────────────────────────────────────
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "gestao_financeira"

    # SQLAlchemy DSN (built from individual settings)
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    # ── API Config ───────────────────────────────────────────────────────────
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://192.168.1.112:3000",   # IP da rede local
    ]
    DEBUG: bool = True

    # ── AI Config (Avocado AI) ───────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    # Optional: set to override endpoint (e.g. Groq, Gemini, local Ollama)
    # Example: OPENAI_BASE_URL=https://api.groq.com/openai/v1
    OPENAI_BASE_URL: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
